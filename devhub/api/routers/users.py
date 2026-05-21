"""Kullanıcı profili — istatistik, rozet ve aktivite (GitHub-stili)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import func, select, text

from ...models import Answer, Question, User
from ..cache import cache_get, cache_set
from ..deps import SessionDep
from ..schemas import (
    ActivityDay,
    Badge,
    Page,
    UserAnswer,
    UserListItem,
    UserProfile,
    UserStats,
)

router = APIRouter(prefix="/users", tags=["users"])

VALID_USER_SORT = {"reputation", "joined", "username"}
USERLIST_KEY = "userlist:{sort}:{desc}:{page}:{page_size}"


def _escape_like(value: str) -> str:
    """LIKE wildcard escape; bkz. questions.py'deki aynı yardımcı."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def _get_user_or_404(session: SessionDep, username: str) -> User:
    user = (
        await session.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _badges(stats: UserStats, reputation: int) -> list[Badge]:
    """İstatistiklerden kazanılan rozetleri türet (gamification)."""
    earned: list[Badge] = [
        Badge(key="acemi", label="Acemi", description="DevHub'a katıldı")
    ]
    rules: list[tuple[bool, str, str, str]] = [
        (stats.questions >= 1, "ilk-soru", "İlk Soru", "İlk sorusunu sordu"),
        (stats.questions >= 10, "merakli", "Meraklı", "10+ soru sordu"),
        (stats.questions >= 50, "soru-ustasi", "Soru Ustası", "50+ soru sordu"),
        (stats.answers >= 10, "yardimsever", "Yardımsever", "10+ cevap yazdı"),
        (stats.accepted_answers >= 1, "bilge", "Bilge", "Bir cevabı kabul edildi"),
        (stats.accepted_answers >= 10, "aydinlatan", "Aydınlatan", "10+ cevabı kabul edildi"),
        (reputation >= 1000, "saygin", "Saygın", "1000+ itibar"),
        (reputation >= 3000, "efsane", "Efsane", "3000+ itibar"),
    ]
    for ok, key, label, desc in rules:
        if ok:
            earned.append(Badge(key=key, label=label, description=desc))
    return earned


@router.get(
    "",
    response_model=Page[UserListItem],
    summary="Kullanıcıları listele (public)",
    description=(
        "Sıralama: reputation/joined/username. Arama: search (username, ILIKE)."
        " Yalnızca public alanlar döner; email bilgisi paylaşılmaz."
    ),
)
async def list_users(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    sort: str = Query("reputation"),
    desc: bool = Query(True),
    search: str | None = Query(None, min_length=1, max_length=64),
) -> Page[UserListItem]:
    if sort not in VALID_USER_SORT:
        raise HTTPException(status_code=400, detail=f"sort must be one of {VALID_USER_SORT}")

    search_norm = search.strip() if search else None
    if search_norm == "":
        search_norm = None

    # Aramayken cache'i atla — rastgele input'la cache şişirilmesin.
    cache_key = USERLIST_KEY.format(
        sort=sort, desc=int(desc), page=page, page_size=page_size,
    )
    if search_norm is None:
        cached = await cache_get(cache_key)
        if cached is not None:
            return Response(content=cached, media_type="application/json")  # type: ignore[return-value]

    q_count_sq = (
        select(func.count())
        .select_from(Question)
        .where(Question.user_id == User.id)
        .scalar_subquery()
        .label("question_count")
    )
    a_count_sq = (
        select(func.count())
        .select_from(Answer)
        .where(Answer.user_id == User.id)
        .scalar_subquery()
        .label("answer_count")
    )

    stmt = select(
        User.id,
        User.username,
        User.reputation,
        User.joined_at,
        User.bio,
        q_count_sq,
        a_count_sq,
    )
    if search_norm:
        pattern = f"%{_escape_like(search_norm)}%"
        stmt = stmt.where(User.username.ilike(pattern, escape="\\"))

    sort_cols = {
        "reputation": User.reputation,
        "joined": User.joined_at,
        "username": User.username,
    }
    col = sort_cols[sort]
    stmt = stmt.order_by(col.desc() if desc else col.asc(), User.id.asc())

    total = (await session.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    rows = (await session.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    )).all()

    items = [
        UserListItem(
            id=r.id,
            username=r.username,
            reputation=r.reputation,
            joined_at=r.joined_at,
            bio=r.bio,
            question_count=r.question_count,
            answer_count=r.answer_count,
        )
        for r in rows
    ]
    page_obj = Page[UserListItem](items=items, total=total, page=page, page_size=page_size)
    if search_norm is None:
        await cache_set(cache_key, page_obj.model_dump_json())
    return page_obj


@router.get(
    "/{username}",
    response_model=UserProfile,
    summary="Kullanıcı profili (public)",
    responses={404: {"description": "Kullanıcı bulunamadı"}},
)
async def get_profile(username: str, session: SessionDep) -> UserProfile:
    user = await _get_user_or_404(session, username)

    q_count = (
        await session.execute(
            select(func.count()).select_from(Question).where(Question.user_id == user.id)
        )
    ).scalar_one()
    a_count = (
        await session.execute(
            select(func.count()).select_from(Answer).where(Answer.user_id == user.id)
        )
    ).scalar_one()
    accepted = (
        await session.execute(
            select(func.count())
            .select_from(Answer)
            .where(Answer.user_id == user.id, Answer.is_accepted.is_(True))
        )
    ).scalar_one()
    votes_received = (
        await session.execute(
            text(
                """
                SELECT COALESCE(SUM(v.value), 0) FROM votes v
                WHERE (v.target_type = 'question'
                       AND v.target_id IN (SELECT id FROM questions WHERE user_id = :uid))
                   OR (v.target_type = 'answer'
                       AND v.target_id IN (SELECT id FROM answers WHERE user_id = :uid))
                """
            ),
            {"uid": user.id},
        )
    ).scalar_one()

    stats = UserStats(
        questions=q_count,
        answers=a_count,
        accepted_answers=accepted,
        votes_received=int(votes_received),
    )
    return UserProfile(
        id=user.id,
        username=user.username,
        bio=user.bio,
        joined_at=user.joined_at,
        reputation=user.reputation,
        stats=stats,
        badges=_badges(stats, user.reputation),
    )


@router.get(
    "/{username}/activity",
    response_model=list[ActivityDay],
    summary="Günlük katkı aktivitesi (soru + cevap)",
    description="GitHub tarzı ısı haritası için. Yalnızca aktivite olan günler döner.",
)
async def get_activity(
    username: str,
    session: SessionDep,
    days: int = Query(365, ge=1, le=730),
) -> list[ActivityDay]:
    user = await _get_user_or_404(session, username)
    since = datetime.now(tz=UTC) - timedelta(days=days)
    rows = (
        await session.execute(
            text(
                """
                SELECT to_char(day, 'YYYY-MM-DD') AS day, SUM(c)::int AS count
                FROM (
                    SELECT date(created_at) AS day, COUNT(*) AS c
                    FROM questions WHERE user_id = :uid AND created_at >= :since GROUP BY 1
                    UNION ALL
                    SELECT date(created_at) AS day, COUNT(*) AS c
                    FROM answers WHERE user_id = :uid AND created_at >= :since GROUP BY 1
                ) t
                GROUP BY day ORDER BY day
                """
            ),
            {"uid": user.id, "since": since},
        )
    ).mappings().all()
    return [ActivityDay(day=r["day"], count=r["count"]) for r in rows]


@router.get(
    "/{username}/answers",
    response_model=Page[UserAnswer],
    summary="Kullanıcının cevapları (yeni → eski)",
)
async def get_user_answers(
    username: str,
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[UserAnswer]:
    user = await _get_user_or_404(session, username)

    total = (
        await session.execute(
            select(func.count()).select_from(Answer).where(Answer.user_id == user.id)
        )
    ).scalar_one()
    rows = (
        await session.execute(
            text(
                """
                SELECT a.id, a.question_id, q.title AS question_title,
                       a.created_at, a.is_accepted,
                       COALESCE((SELECT SUM(value) FROM votes
                                 WHERE target_type = 'answer' AND target_id = a.id), 0) AS vote_score
                FROM answers a
                JOIN questions q ON q.id = a.question_id
                WHERE a.user_id = :uid
                ORDER BY a.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"uid": user.id, "limit": page_size, "offset": (page - 1) * page_size},
        )
    ).mappings().all()
    items = [
        UserAnswer(
            id=r["id"],
            question_id=r["question_id"],
            question_title=r["question_title"],
            created_at=r["created_at"],
            is_accepted=r["is_accepted"],
            vote_score=int(r["vote_score"]),
        )
        for r in rows
    ]
    return Page[UserAnswer](items=items, total=total, page=page, page_size=page_size)
