"""Classification API routes — AI classification, summaries, keywords, similarity, and admin review."""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.presentation import Presentation
from app.models.ai_classification import AISummary, AIKeyword
from app.schemas.classification import (
    ClassificationDetail, SummaryResponse, KeywordItem, KeywordResponse,
    SimilarPresentationItem, SimilarPresentationsResponse, RecommendationSet,
    QualityScores, ReviewRequest, ReclassifyRequest,
    ClassificationQueueItem, ClassificationStats,
)
from app.services.classification_service import (
    classify_presentation, classify_all_pending,
    review_classification, get_classification_stats,
)
from app.services.similarity_service import (
    get_similar_presentations, get_recommendations,
    compute_similarity_for_presentation,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["classification"])
admin_classification_router = APIRouter(prefix="/admin", tags=["admin-classification"])


# ═══════════════════════════════════════════════════════════════
# Public Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/presentations/{presentation_id}/classification", response_model=ClassificationDetail)
async def get_classification(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get AI classification details for a presentation."""
    result = await db.execute(
        select(Presentation).where(Presentation.id == presentation_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")

    return ClassificationDetail(
        presentation_id=pres.id,
        category=pres.ai_category.name if pres.ai_category else (pres.category.name if pres.category else None),
        sub_category=None,  # Would need to check parent relationship
        department=pres.ai_department.name if pres.ai_department else (pres.department.name if pres.department else None),
        business_domain=pres.business_domain,
        difficulty_level=pres.difficulty_level,
        confidence_category=pres.ai_confidence_category,
        confidence_department=pres.ai_confidence_department,
        classification_status=pres.ai_classification_status,
        tags=[t.name for t in pres.tags] if pres.tags else [],
        provider=pres.ai_summary.generated_by if pres.ai_summary else None,
    )


@router.get("/presentations/{presentation_id}/summary", response_model=SummaryResponse)
async def get_summary(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated summaries for a presentation."""
    result = await db.execute(
        select(AISummary).where(AISummary.presentation_id == presentation_id)
    )
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="No summary available. Trigger classification first.")

    # Parse JSON arrays
    learning_objectives = []
    key_topics = []
    try:
        if summary.learning_objectives:
            learning_objectives = json.loads(summary.learning_objectives)
        if summary.key_topics:
            key_topics = json.loads(summary.key_topics)
    except (json.JSONDecodeError, TypeError):
        pass

    return SummaryResponse(
        presentation_id=presentation_id,
        short_summary=summary.short_summary,
        medium_summary=summary.medium_summary,
        executive_summary=summary.executive_summary,
        learning_objectives=learning_objectives,
        key_topics=key_topics,
        generated_by=summary.generated_by,
    )


@router.get("/presentations/{presentation_id}/keywords", response_model=KeywordResponse)
async def get_keywords(
    presentation_id: UUID,
    keyword_type: str = Query(None, description="Filter by type: technology, product, tool, framework, concept"),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-extracted keywords for a presentation."""
    query = select(AIKeyword).where(AIKeyword.presentation_id == presentation_id)
    if keyword_type:
        query = query.where(AIKeyword.keyword_type == keyword_type)
    query = query.order_by(AIKeyword.relevance_score.desc())

    result = await db.execute(query)
    keywords = result.scalars().all()

    return KeywordResponse(
        presentation_id=presentation_id,
        keywords=[
            KeywordItem(
                keyword=kw.keyword,
                keyword_type=kw.keyword_type,
                relevance_score=kw.relevance_score,
            )
            for kw in keywords
        ],
        total=len(keywords),
    )


@router.get("/presentations/{presentation_id}/similar", response_model=SimilarPresentationsResponse)
async def get_similar(
    presentation_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get similar presentations."""
    similar = await get_similar_presentations(db, presentation_id, limit=limit)

    return SimilarPresentationsResponse(
        presentation_id=presentation_id,
        similar=[
            SimilarPresentationItem(
                id=UUID(s["id"]),
                title=s["title"],
                file_type=s["file_type"],
                thumbnail_url=s.get("thumbnail_url"),
                similarity_score=s["similarity_score"],
                similarity_type=s["similarity_type"],
                category=s.get("category"),
            )
            for s in similar
        ],
    )


@router.get("/presentations/{presentation_id}/recommendations", response_model=RecommendationSet)
async def get_presentation_recommendations(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full recommendation set for a presentation."""
    recs = await get_recommendations(db, presentation_id)

    return RecommendationSet(
        presentation_id=presentation_id,
        similar=[
            SimilarPresentationItem(
                id=UUID(s["id"]),
                title=s["title"],
                file_type=s["file_type"],
                thumbnail_url=s.get("thumbnail_url"),
                similarity_score=s.get("similarity_score", 0),
                similarity_type=s.get("similarity_type", "content"),
                category=s.get("category"),
            )
            for s in recs.get("similar", [])
        ],
        trending=recs.get("trending", []),
        new_in_domain=recs.get("new_in_domain", []),
    )


@router.get("/presentations/{presentation_id}/quality", response_model=QualityScores)
async def get_quality_scores(
    presentation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get quality metrics for a presentation."""
    result = await db.execute(
        select(Presentation).where(Presentation.id == presentation_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")

    # Compute overall score as weighted average
    scores = [
        s for s in [pres.completeness_score, pres.freshness_score, pres.knowledge_score]
        if s is not None
    ]
    overall = sum(scores) / len(scores) if scores else None

    return QualityScores(
        completeness_score=pres.completeness_score,
        freshness_score=pres.freshness_score,
        knowledge_score=pres.knowledge_score,
        popularity_score=pres.popularity_score,
        overall_score=round(overall, 3) if overall is not None else None,
    )


@router.post("/presentations/{presentation_id}/reclassify")
async def reclassify_presentation(
    presentation_id: UUID,
    body: ReclassifyRequest = ReclassifyRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Force re-classification of a presentation."""
    result = await classify_presentation(db, presentation_id, force=body.force)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Classification failed"))

    # Also recompute similarities
    sim_count = await compute_similarity_for_presentation(db, presentation_id)
    result["similarities_computed"] = sim_count

    return result


# ═══════════════════════════════════════════════════════════════
# Admin Endpoints
# ═══════════════════════════════════════════════════════════════

@admin_classification_router.post("/classify-all")
async def batch_classify(
    db: AsyncSession = Depends(get_db),
):
    """Batch classify all pending presentations."""
    stats = await classify_all_pending(db)
    return stats


@admin_classification_router.get("/classification-queue", response_model=list[ClassificationQueueItem])
async def get_classification_queue(
    status: str = Query("pending_review", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get presentations awaiting admin review."""
    result = await db.execute(
        select(Presentation)
        .where(
            Presentation.ai_classification_status == status,
            Presentation.is_active == True,  # noqa: E712
        )
        .order_by(Presentation.created_at.desc())
        .limit(limit)
    )
    presentations = result.scalars().all()

    return [
        ClassificationQueueItem(
            id=p.id,
            title=p.title,
            file_type=p.file_type,
            thumbnail_url=f"/api/v1/thumbnails/{p.id}.webp" if p.thumbnail_path else None,
            ai_category=p.ai_category.name if p.ai_category else None,
            ai_confidence=p.ai_confidence_category,
            tags=[t.name for t in p.tags] if p.tags else [],
            classification_status=p.ai_classification_status,
            created_at=p.created_at,
        )
        for p in presentations
    ]


@admin_classification_router.post("/review/{presentation_id}")
async def review_classification_endpoint(
    presentation_id: UUID,
    body: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept, modify, or reject an AI classification."""
    result = await review_classification(
        db=db,
        presentation_id=presentation_id,
        action=body.action,
        reviewer=body.reviewer,
        final_category_id=body.final_category_id,
        final_tag_ids=body.final_tag_ids,
        notes=body.notes,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@admin_classification_router.get("/classification-stats", response_model=ClassificationStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get classification system dashboard statistics."""
    stats = await get_classification_stats(db)
    return ClassificationStats(**stats)
