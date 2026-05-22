"""Soru ve oy router'ı."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, func, insert, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ...models import (
    Answer,
    Question,
    QuestionTag,
    Tag,
    User,
    Vote,
)
from ..cache import cache_get, cache_set, invalidate
from ..deps import CurrentUser, SessionDep
from ..schemas import (
    Page,
    QuestionCreate,
    QuestionDetail,
    QuestionSummary,
    QuestionUpdate,
    UserSummary,
    VoteIn,
    VoteOut,
)
from ..ws import manager as ws_manager

router = APIRouter(prefix="/questions", tags=["questions"])

VALID_SORT = {"created", "votes", "views", "answers"}

QLIST_KEY = "qlist:{sort}:{desc}:{tag}:{author}:{page}:{page_size}"


def _escape_like(value: str) -> str:
    """LIKE/ILIKE wildcard'larını ('%', '_', '\\') kaçışla; kullanıcı girdisini
    desen sayma. Kullanım: `column.ilike(f"%{_escape_like(q)}%", escape="\\\\")`."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
QDETAIL_KEY = "question:{qid}"
QLIST_PATTERN = "qlist:*"
ALIST_PATTERN_FOR = "alist:{qid}:*"
TAGLIST_PATTERN = "taglist:*"


def _qdetail_key(qid: int) -> str:
    return QDETAIL_KEY.format(qid=qid)


async def _invalidate_question(qid: int) -> None:
    await invalidate([QLIST_PATTERN, _qdetail_key(qid)])


async def _get_question_or_404(session: SessionDep, qid: int) -> Question:
    q = (await session.execute(select(Question).where(Question.id == qid))).scalar_one_or_none()
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


async def _resolve_tags(session: SessionDep, names: list[str]) -> list[int]:
    """İsim listesine karşılık tag ID'lerini dön; yoksa yarat."""
    if not names:
        return []
    unique = sorted({n.lower().strip() for n in names if n.strip()})
    existing_rows = (
        await session.execute(select(Tag.id, Tag.name).where(Tag.name.in_(unique)))
    ).all()
    existing = {r.name: r.id for r in existing_rows}
    missing = [n for n in unique if n not in existing]
    if missing:
        await session.execute(insert(Tag), [{"name": n, "description": None} for n in missing])
        new_rows = (await session.execute(select(Tag.id, Tag.name).where(Tag.name.in_(missing)))).all()
        for r in new_rows:
            existing[r.name] = r.id
    return [existing[n] for n in unique]


async def _summary_row(session: SessionDep, qid: int) -> dict:
    """QuestionSummary için gerekli aggregate'leri tek sorguda topla."""
    row = (await session.execute(
        select(
            Question.id,
            Question.title,
            Question.body,
            Question.created_at,
            Question.updated_at,
            Question.view_count,
            User.id.label("author_id"),
            User.username.label("author_username"),
            User.reputation.label("author_reputation"),
            func.coalesce(
                select(func.sum(Vote.value))
                .where(Vote.target_type == "question", Vote.target_id == Question.id)
                .scalar_subquery(),
                0,
            ).label("vote_score"),
            select(func.count())
            .select_from(Answer)
            .where(Answer.question_id == Question.id)
            .scalar_subquery()
            .label("answer_count"),
            select(func.count())
            .select_from(Answer)
            .where(Answer.question_id == Question.id, Answer.is_accepted.is_(True))
            .scalar_subquery()
            .label("accepted_count"),
        )
        .join(User, User.id == Question.user_id)
        .where(Question.id == qid)
    )).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Question not found")
    tag_names = list((await session.execute(
        select(Tag.name)
        .join(QuestionTag, QuestionTag.tag_id == Tag.id)
        .where(QuestionTag.question_id == qid)
        .order_by(Tag.name)
    )).scalars().all())
    return {
        "id": row.id,
        "title": row.title,
        "body": row.body,
        "author": UserSummary(id=row.author_id, username=row.author_username, reputation=row.author_reputation),
        "tags": tag_names,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "view_count": row.view_count,
        "vote_score": int(row.vote_score),
        "answer_count": row.answer_count,
        "has_accepted": row.accepted_count > 0,
    }


@router.get(
    "",
    response_model=Page[QuestionSummary],
    summary="Soruları listele",
    description=(
        "Sıralama: created/votes/views/answers. Filtre: tag, author, q (serbest metin)."
        " Sonuçlar 60 sn cache'lenir; q kullanılırsa cache atlanır."
    ),
)
async def list_questions(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("created"),
    desc: bool = Query(True),
    tag: str | None = Query(None),
    author: str | None = Query(None),
    q: str | None = Query(None, min_length=2, max_length=80, description="Başlık/içerik araması"),
):
    if sort not in VALID_SORT:
        raise HTTPException(status_code=400, detail=f"sort must be one of {VALID_SORT}")

    q_norm = q.strip() if q else None
    if q_norm is not None and len(q_norm) < 2:
        q_norm = None

    # Serbest metinli sorgu: input alanı sınırsız olduğundan cache'i atla
    # (saldırgan rastgele girdilerle cache şişiremez).
    cache_key = QLIST_KEY.format(
        sort=sort, desc=int(desc), tag=tag or "-", author=author or "-",
        page=page, page_size=page_size,
    )
    if q_norm is None:
        cached = await cache_get(cache_key)
        if cached is not None:
            return Response(content=cached, media_type="application/json")

    vote_score = func.coalesce(
        select(func.sum(Vote.value))
        .where(Vote.target_type == "question", Vote.target_id == Question.id)
        .scalar_subquery(),
        0,
    ).label("vote_score")
    answer_count = (
        select(func.count())
        .select_from(Answer)
        .where(Answer.question_id == Question.id)
        .scalar_subquery()
        .label("answer_count")
    )
    accepted_count = (
        select(func.count())
        .select_from(Answer)
        .where(Answer.question_id == Question.id, Answer.is_accepted.is_(True))
        .scalar_subquery()
        .label("accepted_count")
    )

    stmt = (
        select(
            Question.id,
            Question.title,
            Question.created_at,
            Question.updated_at,
            Question.view_count,
            User.id.label("author_id"),
            User.username.label("author_username"),
            User.reputation.label("author_reputation"),
            vote_score,
            answer_count,
            accepted_count,
        )
        .join(User, User.id == Question.user_id)
    )

    if tag:
        stmt = stmt.where(
            Question.id.in_(
                select(QuestionTag.question_id)
                .join(Tag, Tag.id == QuestionTag.tag_id)
                .where(Tag.name == tag)
            )
        )
    if author:
        stmt = stmt.where(User.username == author)
    if q_norm:
        pattern = f"%{_escape_like(q_norm)}%"
        stmt = stmt.where(
            or_(
                Question.title.ilike(pattern, escape="\\"),
                Question.body.ilike(pattern, escape="\\"),
            )
        )

    sort_cols = {
        "created": Question.created_at,
        "views": Question.view_count,
        "votes": vote_score,
        "answers": answer_count,
    }
    col = sort_cols[sort]
    stmt = stmt.order_by(col.desc() if desc else col.asc(), Question.id.desc())

    total = (await session.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    rows = (await session.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    )).all()

    qids = [r.id for r in rows]
    tags_by_qid: dict[int, list[str]] = {qid: [] for qid in qids}
    if qids:
        tag_rows = (await session.execute(
            select(QuestionTag.question_id, Tag.name)
            .join(Tag, Tag.id == QuestionTag.tag_id)
            .where(QuestionTag.question_id.in_(qids))
            .order_by(Tag.name)
        )).all()
        for qid, name in tag_rows:
            tags_by_qid[qid].append(name)

    items = [
        QuestionSummary(
            id=r.id,
            title=r.title,
            author=UserSummary(id=r.author_id, username=r.author_username, reputation=r.author_reputation),
            tags=tags_by_qid[r.id],
            created_at=r.created_at,
            updated_at=r.updated_at,
            view_count=r.view_count,
            vote_score=int(r.vote_score),
            answer_count=r.answer_count,
            has_accepted=r.accepted_count > 0,
        )
        for r in rows
    ]
    page_obj = Page[QuestionSummary](items=items, total=total, page=page, page_size=page_size)
    if q_norm is None:
        await cache_set(cache_key, page_obj.model_dump_json())
    return page_obj


@router.get(
    "/{qid}",
    response_model=QuestionDetail,
    summary="Bir sorunun detayı",
    responses={404: {"description": "Soru bulunamadı"}},
)
async def get_question(qid: int, session: SessionDep):
    cache_key = _qdetail_key(qid)
    cached = await cache_get(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/json")
    data = await _summary_row(session, qid)
    detail = QuestionDetail(**data)
    await cache_set(cache_key, detail.model_dump_json())
    return detail


@router.post(
    "",
    response_model=QuestionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni soru yarat (auth)",
    description="`tags` listesindeki yeni etiketler otomatik oluşturulur.",
)
async def create_question(
    payload: QuestionCreate, session: SessionDep, current_user: CurrentUser
) -> QuestionDetail:
    q = Question(user_id=current_user.id, title=payload.title, body=payload.body)
    session.add(q)
    await session.flush()
    tag_ids = await _resolve_tags(session, payload.tags)
    if tag_ids:
        await session.execute(
            insert(QuestionTag), [{"question_id": q.id, "tag_id": t} for t in tag_ids]
        )
    detail = QuestionDetail(**(await _summary_row(session, q.id)))
    await invalidate([QLIST_PATTERN, TAGLIST_PATTERN])
    return detail


@router.patch(
    "/{qid}",
    response_model=QuestionDetail,
    summary="Soruyu güncelle (sahibi)",
    responses={403: {"description": "Soru sahibi değilsin"}, 404: {"description": "Soru bulunamadı"}},
)
async def update_question(
    qid: int,
    payload: QuestionUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> QuestionDetail:
    q = await _get_question_or_404(session, qid)
    if q.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the question owner")
    changed = False
    if payload.title is not None:
        q.title = payload.title
        changed = True
    if payload.body is not None:
        q.body = payload.body
        changed = True
    if payload.tags is not None:
        await session.execute(delete(QuestionTag).where(QuestionTag.question_id == qid))
        tag_ids = await _resolve_tags(session, payload.tags)
        if tag_ids:
            await session.execute(
                insert(QuestionTag), [{"question_id": qid, "tag_id": t} for t in tag_ids]
            )
        changed = True
    if changed:
        q.updated_at = datetime.now(UTC)
    await session.flush()
    detail = QuestionDetail(**(await _summary_row(session, qid)))
    await _invalidate_question(qid)
    if payload.tags is not None:
        await invalidate([TAGLIST_PATTERN])
    return detail


@router.delete(
    "/{qid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soruyu sil (sahibi)",
    responses={403: {"description": "Soru sahibi değilsin"}, 404: {"description": "Soru bulunamadı"}},
)
async def delete_question(
    qid: int, session: SessionDep, current_user: CurrentUser
) -> Response:
    q = await _get_question_or_404(session, qid)
    if q.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the question owner")
    await session.execute(delete(Question).where(Question.id == qid))
    await _invalidate_question(qid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Voting ---------------------------------------------------------------

async def _vote_score(session: SessionDep, target_type: str, target_id: int) -> int:
    res = (await session.execute(
        select(func.coalesce(func.sum(Vote.value), 0))
        .where(Vote.target_type == target_type, Vote.target_id == target_id)
    )).scalar_one()
    return int(res)


@router.post(
    "/{qid}/vote",
    response_model=VoteOut,
    summary="Soruya oy ver (+1 / -1) — UPSERT",
    responses={400: {"description": "Kendi sorusuna oy vermek yasak"}},
)
async def vote_question(
    qid: int, payload: VoteIn, session: SessionDep, current_user: CurrentUser
) -> VoteOut:
    q = await _get_question_or_404(session, qid)
    if q.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own question")
    stmt = pg_insert(Vote).values(
        user_id=current_user.id,
        target_type="question",
        target_id=qid,
        value=payload.value,
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_votes_user_target",
        set_={"value": payload.value},
    )
    await session.execute(stmt)
    score = await _vote_score(session, "question", qid)
    await _invalidate_question(qid)
    await ws_manager.send_to_user(q.user_id, {
        "type": "vote.cast",
        "target_type": "question",
        "target_id": qid,
        "value": payload.value,
        "score": score,
        "from": {"id": current_user.id, "username": current_user.username},
    })
    return VoteOut(target_type="question", target_id=qid, value=payload.value, score=score)


@router.delete("/{qid}/vote", response_model=VoteOut, summary="Soruya verilen oyu geri çek")
async def unvote_question(
    qid: int, session: SessionDep, current_user: CurrentUser
) -> VoteOut:
    await _get_question_or_404(session, qid)
    await session.execute(
        delete(Vote).where(
            Vote.user_id == current_user.id,
            Vote.target_type == "question",
            Vote.target_id == qid,
        )
    )
    score = await _vote_score(session, "question", qid)
    await _invalidate_question(qid)
    return VoteOut(target_type="question", target_id=qid, value=0, score=score)
