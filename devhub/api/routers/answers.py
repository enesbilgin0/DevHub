"""Cevap router'ı — listele, oluştur, güncelle, sil, kabul et, oy ver."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ...models import Answer, Question, User, Vote
from ..cache import invalidate
from ..deps import CurrentUser, SessionDep
from ..schemas import AnswerCreate, AnswerOut, AnswerUpdate, Page, UserSummary, VoteIn, VoteOut
from ..ws import manager as ws_manager

router = APIRouter(tags=["answers"])

QLIST_PATTERN = "qlist:*"


def _qdetail_key(qid: int) -> str:
    return f"question:{qid}"


async def _invalidate_question(qid: int) -> None:
    await invalidate([QLIST_PATTERN, _qdetail_key(qid)])


async def _get_answer_or_404(session: SessionDep, aid: int) -> Answer:
    a = (await session.execute(select(Answer).where(Answer.id == aid))).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return a


def _answer_row_to_out(row) -> AnswerOut:
    return AnswerOut(
        id=row.id,
        question_id=row.question_id,
        author=UserSummary(id=row.author_id, username=row.author_username, reputation=row.author_reputation),
        body=row.body,
        created_at=row.created_at,
        updated_at=row.updated_at,
        is_accepted=row.is_accepted,
        vote_score=int(row.vote_score),
    )


async def _select_answer(session: SessionDep, aid: int) -> AnswerOut:
    vote_score = func.coalesce(
        select(func.sum(Vote.value))
        .where(Vote.target_type == "answer", Vote.target_id == Answer.id)
        .scalar_subquery(),
        0,
    ).label("vote_score")
    row = (await session.execute(
        select(
            Answer.id,
            Answer.question_id,
            Answer.body,
            Answer.created_at,
            Answer.updated_at,
            Answer.is_accepted,
            User.id.label("author_id"),
            User.username.label("author_username"),
            User.reputation.label("author_reputation"),
            vote_score,
        )
        .join(User, User.id == Answer.user_id)
        .where(Answer.id == aid)
    )).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return _answer_row_to_out(row)


@router.get(
    "/questions/{qid}/answers",
    response_model=Page[AnswerOut],
    summary="Sorunun cevaplarını listele",
    description="Sıralama: kabul edilen ilk → vote_score desc → tarih asc.",
)
async def list_answers(
    qid: int,
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[AnswerOut]:
    if (await session.execute(select(Question.id).where(Question.id == qid))).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Question not found")

    vote_score = func.coalesce(
        select(func.sum(Vote.value))
        .where(Vote.target_type == "answer", Vote.target_id == Answer.id)
        .scalar_subquery(),
        0,
    ).label("vote_score")

    base = (
        select(
            Answer.id,
            Answer.question_id,
            Answer.body,
            Answer.created_at,
            Answer.updated_at,
            Answer.is_accepted,
            User.id.label("author_id"),
            User.username.label("author_username"),
            User.reputation.label("author_reputation"),
            vote_score,
        )
        .join(User, User.id == Answer.user_id)
        .where(Answer.question_id == qid)
        .order_by(
            case((Answer.is_accepted.is_(True), 0), else_=1).asc(),
            vote_score.desc(),
            Answer.created_at.asc(),
        )
    )
    total = (await session.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()
    rows = (await session.execute(base.offset((page - 1) * page_size).limit(page_size))).all()
    items = [_answer_row_to_out(r) for r in rows]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/questions/{qid}/answers",
    response_model=AnswerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Soruya cevap yaz (auth)",
    description="Soru sahibi farklı bir kullanıcıysa WS üzerinden 'answer.created' bildirimi gider.",
)
async def create_answer(
    qid: int,
    payload: AnswerCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> AnswerOut:
    q_owner = (await session.execute(
        select(Question.user_id).where(Question.id == qid)
    )).scalar_one_or_none()
    if q_owner is None:
        raise HTTPException(status_code=404, detail="Question not found")
    a = Answer(question_id=qid, user_id=current_user.id, body=payload.body, is_accepted=False)
    session.add(a)
    await session.flush()
    out = await _select_answer(session, a.id)
    await _invalidate_question(qid)
    if q_owner != current_user.id:
        await ws_manager.send_to_user(q_owner, {
            "type": "answer.created",
            "question_id": qid,
            "answer_id": a.id,
            "from": {"id": current_user.id, "username": current_user.username},
        })
    return out


@router.patch("/answers/{aid}", response_model=AnswerOut, summary="Cevabı güncelle (sahibi)")
async def update_answer(
    aid: int,
    payload: AnswerUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> AnswerOut:
    a = await _get_answer_or_404(session, aid)
    if a.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the answer owner")
    a.body = payload.body
    a.updated_at = datetime.now(UTC)
    await session.flush()
    out = await _select_answer(session, aid)
    await _invalidate_question(a.question_id)
    return out


@router.delete(
    "/answers/{aid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cevabı sil (sahibi)",
)
async def delete_answer(
    aid: int, session: SessionDep, current_user: CurrentUser
) -> Response:
    a = await _get_answer_or_404(session, aid)
    if a.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the answer owner")
    qid = a.question_id
    await session.execute(delete(Answer).where(Answer.id == aid))
    await _invalidate_question(qid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/answers/{aid}/accept",
    response_model=AnswerOut,
    summary="Cevabı kabul et (sadece soru sahibi)",
    description="Aynı sorudaki diğer kabul edilmiş cevaplar kabul-dışı işaretlenir.",
    responses={403: {"description": "Sadece soru sahibi kabul edebilir"}},
)
async def accept_answer(
    aid: int, session: SessionDep, current_user: CurrentUser
) -> AnswerOut:
    a = await _get_answer_or_404(session, aid)
    q_owner = (await session.execute(
        select(Question.user_id).where(Question.id == a.question_id)
    )).scalar_one()
    if q_owner != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the question owner can accept an answer"
        )
    # Aynı soruya ait diğer kabulleri kaldır, hedefi kabul olarak işaretle.
    await session.execute(
        update(Answer)
        .where(Answer.question_id == a.question_id, Answer.is_accepted.is_(True))
        .values(is_accepted=False)
    )
    await session.execute(update(Answer).where(Answer.id == aid).values(is_accepted=True))
    out = await _select_answer(session, aid)
    await _invalidate_question(a.question_id)
    if a.user_id != current_user.id:
        await ws_manager.send_to_user(a.user_id, {
            "type": "answer.accepted",
            "answer_id": aid,
            "question_id": a.question_id,
            "from": {"id": current_user.id, "username": current_user.username},
        })
    return out


@router.post(
    "/answers/{aid}/vote",
    response_model=VoteOut,
    summary="Cevaba oy ver (+1 / -1) — UPSERT",
    responses={400: {"description": "Kendi cevabına oy vermek yasak"}},
)
async def vote_answer(
    aid: int, payload: VoteIn, session: SessionDep, current_user: CurrentUser
) -> VoteOut:
    a = await _get_answer_or_404(session, aid)
    if a.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own answer")
    stmt = pg_insert(Vote).values(
        user_id=current_user.id,
        target_type="answer",
        target_id=aid,
        value=payload.value,
    ).on_conflict_do_update(
        constraint="uq_votes_user_target",
        set_={"value": payload.value},
    )
    await session.execute(stmt)
    score = int((await session.execute(
        select(func.coalesce(func.sum(Vote.value), 0))
        .where(Vote.target_type == "answer", Vote.target_id == aid)
    )).scalar_one())
    await _invalidate_question(a.question_id)
    await ws_manager.send_to_user(a.user_id, {
        "type": "vote.cast",
        "target_type": "answer",
        "target_id": aid,
        "value": payload.value,
        "score": score,
        "from": {"id": current_user.id, "username": current_user.username},
    })
    return VoteOut(target_type="answer", target_id=aid, value=payload.value, score=score)


@router.delete("/answers/{aid}/vote", response_model=VoteOut, summary="Cevaba verilen oyu geri çek")
async def unvote_answer(
    aid: int, session: SessionDep, current_user: CurrentUser
) -> VoteOut:
    a = await _get_answer_or_404(session, aid)
    await session.execute(
        delete(Vote).where(
            Vote.user_id == current_user.id,
            Vote.target_type == "answer",
            Vote.target_id == aid,
        )
    )
    score = int((await session.execute(
        select(func.coalesce(func.sum(Vote.value), 0))
        .where(Vote.target_type == "answer", Vote.target_id == aid)
    )).scalar_one())
    await _invalidate_question(a.question_id)
    return VoteOut(target_type="answer", target_id=aid, value=0, score=score)
