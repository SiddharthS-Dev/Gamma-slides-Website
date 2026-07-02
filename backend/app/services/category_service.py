"""Category and tag service."""

import re
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.department import Department
from app.models.tag import Tag
from app.models.presentation import Presentation, PresentationTag
from app.schemas.category import (
    CategoryCreate, CategoryResponse,
    DepartmentCreate, DepartmentResponse,
    TagCreate, TagResponse, TagPopular,
)


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


async def list_categories(db: AsyncSession) -> list[CategoryResponse]:
    """List all categories with presentation counts."""
    query = (
        select(Category)
        .order_by(Category.sort_order, Category.name)
    )
    result = await db.execute(query)
    categories = result.scalars().all()

    responses = []
    for cat in categories:
        # Get presentation count
        count_query = select(func.count()).where(Presentation.category_id == cat.id)
        count = (await db.execute(count_query)).scalar() or 0

        resp = CategoryResponse.model_validate(cat)
        resp.presentation_count = count
        responses.append(resp)

    return responses


async def create_category(db: AsyncSession, data: CategoryCreate) -> CategoryResponse:
    """Create a new category."""
    category = Category(
        name=data.name,
        slug=_slugify(data.name),
        description=data.description,
        color=data.color,
        icon=data.icon,
        sort_order=data.sort_order,
    )
    db.add(category)
    await db.flush()
    return CategoryResponse.model_validate(category)


async def get_category_by_slug(db: AsyncSession, slug: str) -> Optional[CategoryResponse]:
    """Get category by slug."""
    query = select(Category).where(Category.slug == slug)
    result = await db.execute(query)
    cat = result.scalar_one_or_none()
    if not cat:
        return None
    return CategoryResponse.model_validate(cat)


async def list_departments(db: AsyncSession) -> list[DepartmentResponse]:
    """List all departments in hierarchical structure."""
    query = select(Department).where(Department.parent_id.is_(None)).order_by(Department.sort_order, Department.name)
    result = await db.execute(query)
    departments = result.scalars().all()
    return [DepartmentResponse.model_validate(d) for d in departments]


async def create_department(db: AsyncSession, data: DepartmentCreate) -> DepartmentResponse:
    """Create a new department."""
    dept = Department(
        name=data.name,
        slug=_slugify(data.name),
        description=data.description,
        parent_id=data.parent_id,
        sort_order=data.sort_order,
    )
    db.add(dept)
    await db.flush()
    return DepartmentResponse.model_validate(dept)


async def list_tags(db: AsyncSession) -> list[TagResponse]:
    """List all tags."""
    query = select(Tag).order_by(Tag.name)
    result = await db.execute(query)
    return [TagResponse.model_validate(t) for t in result.scalars().all()]


async def get_popular_tags(db: AsyncSession, limit: int = 20) -> list[TagPopular]:
    """Get tags sorted by usage count."""
    query = (
        select(Tag, func.count(PresentationTag.c.presentation_id).label("count"))
        .outerjoin(PresentationTag, Tag.id == PresentationTag.c.tag_id)
        .group_by(Tag.id)
        .order_by(desc("count"))
        .limit(limit)
    )
    result = await db.execute(query)
    tags = []
    for row in result.all():
        tag, count = row
        tags.append(TagPopular(
            id=tag.id,
            name=tag.name,
            slug=tag.slug,
            color=tag.color,
            count=count,
        ))
    return tags


async def create_tag(db: AsyncSession, data: TagCreate) -> TagResponse:
    """Create a new tag."""
    tag = Tag(
        name=data.name,
        slug=_slugify(data.name),
        color=data.color,
    )
    db.add(tag)
    await db.flush()
    return TagResponse.model_validate(tag)


async def get_or_create_tag(db: AsyncSession, name: str) -> Tag:
    """Get existing tag or create new one."""
    slug = _slugify(name)
    query = select(Tag).where(Tag.slug == slug)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    if tag:
        return tag

    tag = Tag(name=name.title(), slug=slug, color="#8b5cf6")
    db.add(tag)
    await db.flush()
    return tag
