"""Soru ve oy router'ı."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ...models import (
    Answer,
    Question,
    QuestionTag,
    Tag,
    User,
    Vote,
)
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

router = APIRouter(prefix="/questions", tags=["questions"])

VALID_SORT = {"created", "votes", "views", "answers"}


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
        "view_count": row.view_count,
        "vote_score": int(row.vote_score),
        "answer_count": row.answer_count,
        "has_accepted": row.accepted_count > 0,
    }


@router.get("", response_model=Page[QuestionSummary])
async def list_questions(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("created"),
    desc: bool = Query(True),
    tag: str | None = Query(None),
    author: str | None = Query(None),
) -> Page[QuestionSummary]:
    if sort not in VALID_SORT:
        raise HTTPException(status_code=400, detail=f"sort must be one of {VALID_SORT}")

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
            view_count=r.view_count,
            vote_score=int(r.vote_score),
            answer_count=r.answer_count,
            has_accepted=r.accepted_count > 0,
        )
        for r in rows
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{qid}", response_model=QuestionDetail)
async def get_question(qid: int, session: SessionDep) -> QuestionDetail:
    data = await _summary_row(session, qid)
    return QuestionDetail(**data)


@router.post("", response_model=QuestionDetail, status_code=status.HTTP_201_CREATED)
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
    return QuestionDetail(**(await _summary_row(session, q.id)))


@router.patch("/{qid}", response_model=QuestionDetail)
async def update_question(
    qid: int,
    payload: QuestionUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> QuestionDetail:
    q = await _get_question_or_404(session, qid)
    if q.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the question owner")
    if payload.title is not None:
        q.title = payload.title
    if payload.body is not None:
        q.body = payload.body
    if payload.tags is not None:
        await session.execute(delete(QuestionTag).where(QuestionTag.question_id == qid))
        tag_ids = await _resolve_tags(session, payload.tags)
        if tag_ids:
            await session.execute(
                insert(QuestionTag), [{"question_id": qid, "tag_id": t} for t in tag_ids]
            )
    await session.flush()
    return QuestionDetail(**(await _summary_row(session, qid)))


@router.delete("/{qid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    qid: int, session: SessionDep, current_user: CurrentUser
) -> Response:
    q = await _get_question_or_404(session, qid)
    if q.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the question owner")
    await session.execute(delete(Question).where(Question.id == qid))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Voting ---------------------------------------------------------------

async def _vote_score(session: SessionDep, target_type: str, target_id: int) -> int:
    res = (await session.execute(
        select(func.coalesce(func.sum(Vote.value), 0))
        .where(Vote.target_type == target_type, Vote.target_id == target_id)
    )).scalar_one()
    return int(res)


@router.post("/{qid}/vote", response_model=VoteOut)
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
    return VoteOut(target_type="question", target_id=qid, value=payload.value, score=score)


@router.delete("/{qid}/vote", response_model=VoteOut)
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
    return VoteOut(target_type="question", target_id=qid, value=0, score=score)
