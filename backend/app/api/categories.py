"""Category, Department, and Tag API routes."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import category_service
from app.schemas.category import (
    CategoryCreate, CategoryResponse,
    DepartmentCreate, DepartmentResponse,
    TagCreate, TagResponse, TagPopular,
)

router = APIRouter(tags=["Organization"])


# Categories
@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all categories with presentation counts."""
    return await category_service.list_categories(db)


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a new category."""
    return await category_service.create_category(db, data)


@router.get("/categories/{slug}", response_model=CategoryResponse)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    """Get category by slug."""
    result = await category_service.get_category_by_slug(db, slug)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    return result


# Departments
@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db)):
    """List departments in hierarchical structure."""
    return await category_service.list_departments(db)


@router.post("/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(data: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new department."""
    return await category_service.create_department(db, data)


# Tags
@router.get("/tags", response_model=list[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """List all tags."""
    return await category_service.list_tags(db)


@router.get("/tags/popular", response_model=list[TagPopular])
async def popular_tags(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get popular tags sorted by usage count."""
    return await category_service.get_popular_tags(db, limit)


@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tag."""
    return await category_service.create_tag(db, data)
