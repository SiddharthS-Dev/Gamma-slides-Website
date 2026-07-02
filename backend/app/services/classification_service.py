"""Classification service — orchestrates content extraction, AI analysis, and persistence.

This is the main entry point for the auto-classification pipeline. It coordinates
content extraction → AI provider → database persistence, with support for batch
operations and admin review workflows.
"""

import hashlib
import json
import logging
from pathlib import Path
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_ai_provider, ContentPayload
from app.config import get_settings
from app.ingestion.content_extractor import extract_full_content
from app.models.presentation import Presentation
from app.models.category import Category
from app.models.department import Department
from app.models.tag import Tag
from app.models.ai_classification import AISummary, AIKeyword, ClassificationReview
from app.services.category_service import get_or_create_tag, _slugify

logger = logging.getLogger(__name__)
settings = get_settings()


async def classify_presentation(
    db: AsyncSession,
    presentation_id: UUID,
    force: bool = False,
) -> dict:
    """Full classification pipeline for a single presentation.

    Steps:
      1. Load presentation and extract content from file
      2. Run AI classification (category, department, difficulty)
      3. Generate intelligent tags (5-20)
      4. Generate multi-level summaries
      5. Extract typed keywords
      6. Compute quality scores
      7. Persist all results
      8. Update search vector

    Args:
        db: Database session
        presentation_id: UUID of the presentation to classify
        force: If True, re-classify even if already classified

    Returns:
        Dict with classification results and confidence scores
    """
    # Load presentation
    result = await db.execute(
        select(Presentation).where(Presentation.id == presentation_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        logger.error(f"Presentation not found: {presentation_id}")
        return {"status": "error", "message": "Presentation not found"}

    # Skip if already classified (unless forced)
    if not force and pres.ai_classification_status in ("classified", "reviewed"):
        logger.info(f"Skipping already classified: {pres.title}")
        return {"status": "skipped", "message": "Already classified"}

    pres.ai_classification_status = "processing"
    await db.flush()

    try:
        # 1. Extract content from file
        file_path = Path(pres.file_path)
        if not file_path.exists():
            logger.warning(f"File not found for classification: {file_path}")
            pres.ai_classification_status = "pending"
            return {"status": "error", "message": "File not found"}

        extracted = extract_full_content(file_path)

        # Store extracted text and its hash
        pres.extracted_text = extracted.body_text[:50000]  # Cap at 50K chars
        if extracted.body_text:
            pres.content_hash = hashlib.sha256(
                extracted.body_text.encode("utf-8", errors="ignore")
            ).hexdigest()

        # 2. Build content payload for AI provider
        content = ContentPayload(
            title=extracted.title or pres.title or "",
            headings=extracted.headings or [],
            body_text=extracted.body_text or "",
            speaker_notes=extracted.speaker_notes or "",
            metadata=extracted.metadata or {},
            slide_texts=extracted.slide_texts or [],
            file_name=pres.file_name or "",
            file_type=pres.file_type or "",
            word_count=extracted.word_count or 0,
        )

        provider = get_ai_provider()

        # 3. Run classification
        classification = await provider.classify(content)

        # Resolve category to database
        category = await _resolve_category(db, classification.category, classification.sub_category)
        if category:
            pres.ai_category_id = category.id
            # Auto-assign if confidence is high enough
            if classification.confidence_category >= settings.classification_confidence_threshold:
                pres.category_id = category.id

        pres.ai_confidence_category = classification.confidence_category
        pres.ai_confidence_department = classification.confidence_department
        pres.difficulty_level = classification.difficulty_level.value
        pres.business_domain = classification.business_domain

        # Resolve department
        department = await _resolve_department(db, classification.department)
        if department:
            pres.ai_department_id = department.id
            if classification.confidence_department >= settings.classification_confidence_threshold:
                pres.department_id = department.id

        # 4. Generate tags
        tag_results = await provider.generate_tags(content)
        for tag_result in tag_results:
            tag = await get_or_create_tag(db, tag_result.name)
            if tag not in pres.tags:
                pres.tags.append(tag)

        # 5. Generate summaries
        summary_result = await provider.generate_summary(content)

        # Upsert AISummary
        existing_summary = await db.execute(
            select(AISummary).where(AISummary.presentation_id == pres.id)
        )
        ai_summary = existing_summary.scalar_one_or_none()
        if ai_summary:
            ai_summary.short_summary = summary_result.short_summary
            ai_summary.medium_summary = summary_result.medium_summary
            ai_summary.executive_summary = summary_result.executive_summary
            ai_summary.learning_objectives = json.dumps(summary_result.learning_objectives)
            ai_summary.key_topics = json.dumps(summary_result.key_topics)
            ai_summary.generated_by = provider.provider_name
        else:
            ai_summary = AISummary(
                presentation_id=pres.id,
                short_summary=summary_result.short_summary,
                medium_summary=summary_result.medium_summary,
                executive_summary=summary_result.executive_summary,
                learning_objectives=json.dumps(summary_result.learning_objectives),
                key_topics=json.dumps(summary_result.key_topics),
                generated_by=provider.provider_name,
            )
            db.add(ai_summary)

        # Update description with short summary if empty
        if not pres.description and summary_result.short_summary:
            pres.description = summary_result.short_summary

        # 6. Extract keywords
        keyword_results = await provider.extract_keywords(content)

        # Clear existing keywords and insert new
        existing_kw = await db.execute(
            select(AIKeyword).where(AIKeyword.presentation_id == pres.id)
        )
        for kw in existing_kw.scalars().all():
            await db.delete(kw)

        for kw_result in keyword_results:
            kw = AIKeyword(
                presentation_id=pres.id,
                keyword=kw_result.keyword,
                keyword_type=kw_result.keyword_type.value,
                relevance_score=kw_result.relevance_score,
            )
            db.add(kw)

        # 7. Compute quality scores
        from app.services.quality_service import compute_quality_scores
        scores = compute_quality_scores(pres, extracted)
        pres.completeness_score = scores["completeness"]
        pres.freshness_score = scores["freshness"]
        pres.knowledge_score = scores["knowledge"]

        # 8. Set classification status
        if classification.confidence_category >= settings.classification_confidence_threshold:
            pres.ai_classification_status = "classified"
        else:
            # Low confidence → needs admin review
            pres.ai_classification_status = "pending_review"

        await db.flush()

        logger.info(
            f"Classified '{pres.title}': "
            f"category={classification.category}({classification.confidence_category:.0%}), "
            f"tags={len(tag_results)}, keywords={len(keyword_results)}"
        )

        return {
            "status": "classified",
            "presentation_id": str(pres.id),
            "category": classification.category,
            "sub_category": classification.sub_category,
            "department": classification.department,
            "confidence_category": classification.confidence_category,
            "confidence_department": classification.confidence_department,
            "difficulty_level": classification.difficulty_level.value,
            "business_domain": classification.business_domain,
            "tags_generated": len(tag_results),
            "keywords_extracted": len(keyword_results),
            "provider": provider.provider_name,
        }

    except Exception as e:
        logger.error(f"Classification failed for '{pres.title}': {e}")
        pres.ai_classification_status = "failed"
        await db.flush()
        return {"status": "error", "message": str(e)}


async def classify_all_pending(db: AsyncSession) -> dict:
    """Batch classify all presentations with pending status.

    Returns summary of results.
    """
    result = await db.execute(
        select(Presentation).where(
            Presentation.ai_classification_status.in_(["pending", "failed"]),
            Presentation.is_active == True,  # noqa: E712
        )
    )
    pending = result.scalars().all()

    stats = {"total": len(pending), "classified": 0, "failed": 0, "skipped": 0}

    for pres in pending:
        try:
            result = await classify_presentation(db, pres.id, force=True)
            if result["status"] == "classified":
                stats["classified"] += 1
            elif result["status"] == "skipped":
                stats["skipped"] += 1
            else:
                stats["failed"] += 1
        except Exception as e:
            logger.error(f"Batch classification failed for {pres.id}: {e}")
            stats["failed"] += 1

    await db.commit()
    logger.info(f"Batch classification complete: {stats}")
    return stats


async def review_classification(
    db: AsyncSession,
    presentation_id: UUID,
    action: str,
    reviewer: str = "admin",
    final_category_id: Optional[UUID] = None,
    final_tag_ids: Optional[list[UUID]] = None,
    notes: Optional[str] = None,
) -> dict:
    """Admin review of an AI classification.

    Actions: accepted, modified, rejected
    """
    result = await db.execute(
        select(Presentation).where(Presentation.id == presentation_id)
    )
    pres = result.scalar_one_or_none()
    if not pres:
        return {"status": "error", "message": "Presentation not found"}

    # Create review record
    review = ClassificationReview(
        presentation_id=pres.id,
        reviewer=reviewer,
        action=action,
        original_category_id=pres.ai_category_id,
        final_category_id=final_category_id or pres.ai_category_id,
        original_tags=json.dumps([str(t.id) for t in pres.tags]),
        notes=notes,
    )

    if action == "accepted":
        # Accept AI classification as-is
        pres.category_id = pres.ai_category_id
        pres.department_id = pres.ai_department_id
        pres.ai_classification_status = "reviewed"

    elif action == "modified":
        # Apply admin's modifications
        if final_category_id:
            pres.category_id = final_category_id
        if final_tag_ids is not None:
            tag_query = select(Tag).where(Tag.id.in_(final_tag_ids))
            tags_result = await db.execute(tag_query)
            pres.tags = list(tags_result.scalars().all())
            review.final_tags = json.dumps([str(tid) for tid in final_tag_ids])
        pres.ai_classification_status = "reviewed"

    elif action == "rejected":
        # Reject — clear AI suggestions
        pres.ai_classification_status = "rejected"

    db.add(review)
    await db.flush()

    logger.info(f"Classification reviewed: {pres.title} → {action} by {reviewer}")
    return {"status": "success", "action": action}


async def get_classification_stats(db: AsyncSession) -> dict:
    """Get dashboard statistics for the classification system."""
    total = await db.execute(
        select(func.count()).select_from(Presentation).where(Presentation.is_active == True)  # noqa: E712
    )
    total_count = total.scalar() or 0

    statuses = {}
    for status in ["pending", "processing", "classified", "pending_review", "reviewed", "rejected", "failed"]:
        count_result = await db.execute(
            select(func.count()).select_from(Presentation).where(
                Presentation.ai_classification_status == status,
                Presentation.is_active == True,  # noqa: E712
            )
        )
        statuses[status] = count_result.scalar() or 0

    avg_confidence = await db.execute(
        select(func.avg(Presentation.ai_confidence_category)).where(
            Presentation.ai_confidence_category.isnot(None),
        )
    )

    return {
        "total_presentations": total_count,
        "by_status": statuses,
        "average_confidence": round(avg_confidence.scalar() or 0, 3),
    }


# Maps old taxonomy names (from RuleBasedProvider) to the 5 consolidated DB category names
_TAXONOMY_TO_CATEGORY: dict[str, str] = {
    "Engineering":        "Technology",
    "Product":            "Technology",
    "IT Infrastructure":  "Technology",
    "Security":           "Security & Compliance",
    "Compliance":         "Security & Compliance",
    "Governance":         "Security & Compliance",
    "ESG":                "Security & Compliance",
    "Finance":            "Business & Operations",
    "Operations":         "Business & Operations",
    "Administration":     "Business & Operations",
    "Human Resources":    "People & HR",
    "Training":           "People & HR",
    "Customer Success":   "People & HR",
    "Sales":              "Sales & Marketing",
    "Marketing":          "Sales & Marketing",
}


async def _resolve_category(
    db: AsyncSession, category_name: str, sub_category_name: Optional[str] = None
) -> Optional[Category]:
    """Find a consolidated DB category, translating old taxonomy names when needed."""
    # Map old taxonomy name → consolidated name
    resolved_name = _TAXONOMY_TO_CATEGORY.get(category_name, category_name)

    result = await db.execute(
        select(Category).where(Category.name == resolved_name)
    )
    return result.scalar_one_or_none()


async def _resolve_department(
    db: AsyncSession, department_name: Optional[str]
) -> Optional[Department]:
    """Find a department by name."""
    if not department_name:
        return None
    result = await db.execute(
        select(Department).where(Department.name == department_name)
    )
    return result.scalar_one_or_none()
