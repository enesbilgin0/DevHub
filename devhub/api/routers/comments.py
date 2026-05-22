"""Yorum router'ı — soru veya cevap altına düz metin yorumlar.

Yetki:
- Listeleme: public
- Yazma: auth
- Silme: sadece yorum sahibi (404 vs 403 ayrımı yapmaz; var olmayan yorumda 404)

Notlar:
- Düz metin: Markdown render edilmez. XSS yüzeyini küçültür.
- Düzenleme yok (StackOverflow konvansiyonu). Hatalı yorum silinip yeniden yazılır.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select

from ...models import Answer, Comment, Question, User
from ..deps import CurrentUser, SessionDep
from ..schemas import CommentCreate, CommentOut, Page, UserSummary
from ..ws import manager as ws_manager

router = APIRouter(tags=["comments"])


async def _ensure_target(session: SessionDep, target_type: str, target_id: int) -> int:
    """Hedef var mı kontrol et; hedef sahibinin id'sini dön (bildirim için)."""
    if target_type == "question":
        owner = (await session.execute(
            select(Question.user_id).where(Question.id == target_id)
        )).scalar_one_or_none()
    else:
        owner = (await session.execute(
            select(Answer.user_id).where(Answer.id == target_id)
        )).scalar_one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail=f"{target_type.capitalize()} not found")
    return owner


async def _list_comments(
    session: SessionDep,
    target_type: str,
    target_id: int,
    page: int,
    page_size: int,
) -> Page[CommentOut]:
    base = (
        select(
            Comment.id,
            Comment.target_type,
            Comment.target_id,
            Comment.body,
            Comment.created_at,
            User.id.label("author_id"),
            User.username.label("author_username"),
            User.reputation.label("author_reputation"),
        )
        .join(User, User.id == Comment.user_id)
        .where(Comment.target_type == target_type, Comment.target_id == target_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    total = (await session.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()
    rows = (await session.execute(
        base.offset((page - 1) * page_size).limit(page_size)
    )).all()
    items = [
        CommentOut(
            id=r.id,
            target_type=r.target_type,
            target_id=r.target_id,
            author=UserSummary(
                id=r.author_id,
                username=r.author_username,
                reputation=r.author_reputation,
            ),
            body=r.body,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page[CommentOut](items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/questions/{qid}/comments",
    response_model=Page[CommentOut],
    summary="Sorudaki yorumları listele",
)
async def list_question_comments(
    qid: int,
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> Page[CommentOut]:
    await _ensure_target(session, "question", qid)
    return await _list_comments(session, "question", qid, page, page_size)


@router.get(
    "/answers/{aid}/comments",
    response_model=Page[CommentOut],
    summary="Cevaptaki yorumları listele",
)
async def list_answer_comments(
    aid: int,
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> Page[CommentOut]:
    await _ensure_target(session, "answer", aid)
    return await _list_comments(session, "answer", aid, page, page_size)


async def _create_comment(
    session: SessionDep,
    current_user: User,
    target_type: str,
    target_id: int,
    body: str,
) -> CommentOut:
    owner_id = await _ensure_target(session, target_type, target_id)
    c = Comment(
        user_id=current_user.id,
        target_type=target_type,
        target_id=target_id,
        body=body,
    )
    session.add(c)
    await session.flush()
    out = CommentOut(
        id=c.id,
        target_type=target_type,
        target_id=target_id,
        author=UserSummary(
            id=current_user.id,
            username=current_user.username,
            reputation=current_user.reputation,
        ),
        body=c.body,
        created_at=c.created_at,
    )
    if owner_id != current_user.id:
        await ws_manager.send_to_user(owner_id, {
            "type": "comment.created",
            "target_type": target_type,
            "target_id": target_id,
            "comment_id": c.id,
            "from": {"id": current_user.id, "username": current_user.username},
        })
    return out


@router.post(
    "/questions/{qid}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Soruya yorum ekle (auth)",
)
async def create_question_comment(
    qid: int,
    payload: CommentCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> CommentOut:
    return await _create_comment(session, current_user, "question", qid, payload.body)


@router.post(
    "/answers/{aid}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cevaba yorum ekle (auth)",
)
async def create_answer_comment(
    aid: int,
    payload: CommentCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> CommentOut:
    return await _create_comment(session, current_user, "answer", aid, payload.body)


@router.delete(
    "/comments/{cid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Yorumu sil (sahibi)",
    responses={
        403: {"description": "Yorum sahibi değilsin"},
        404: {"description": "Yorum bulunamadı"},
    },
)
async def delete_comment(
    cid: int, session: SessionDep, current_user: CurrentUser
) -> Response:
    c = (await session.execute(select(Comment).where(Comment.id == cid))).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the comment owner")
    await session.execute(delete(Comment).where(Comment.id == cid))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
