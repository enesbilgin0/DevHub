"""Etiket router'ı."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ...models import QuestionTag, Tag
from ..deps import CurrentUser, SessionDep
from ..schemas import Page, TagCreate, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=Page[TagOut])
async def list_tags(
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    sort: str = Query("questions", pattern="^(name|questions)$"),
    search: str | None = Query(None, min_length=1, max_length=64),
) -> Page[TagOut]:
    qcount = (
        select(QuestionTag.tag_id, func.count().label("cnt"))
        .group_by(QuestionTag.tag_id)
        .subquery()
    )
    base = select(
        Tag.id, Tag.name, Tag.description, func.coalesce(qcount.c.cnt, 0).label("question_count")
    ).join(qcount, qcount.c.tag_id == Tag.id, isouter=True)

    if search:
        base = base.where(Tag.name.ilike(f"%{search}%"))

    if sort == "name":
        base = base.order_by(Tag.name.asc())
    else:
        base = base.order_by(func.coalesce(qcount.c.cnt, 0).desc(), Tag.name.asc())

    total = (await session.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()
    rows = (await session.execute(
        base.offset((page - 1) * page_size).limit(page_size)
    )).all()

    items = [
        TagOut(id=r.id, name=r.name, description=r.description, question_count=r.question_count)
        for r in rows
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{name}", response_model=TagOut)
async def get_tag(name: str, session: SessionDep) -> TagOut:
    row = (await session.execute(
        select(
            Tag.id, Tag.name, Tag.description,
            select(func.count())
            .select_from(QuestionTag)
            .where(QuestionTag.tag_id == Tag.id)
            .scalar_subquery()
            .label("question_count"),
        ).where(Tag.name == name)
    )).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagOut(id=row.id, name=row.name, description=row.description, question_count=row.question_count)


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate, session: SessionDep, _user: CurrentUser
) -> TagOut:
    tag = Tag(name=payload.name, description=payload.description)
    session.add(tag)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Tag already exists")
    return TagOut(id=tag.id, name=tag.name, description=tag.description, question_count=0)
