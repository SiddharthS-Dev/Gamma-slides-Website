"""Similarity service — computes content similarity between presentations.

Uses TF-IDF cosine similarity on extracted text, tag overlap (Jaccard),
and category matching to identify related, successor, and duplicate content.
"""

import hashlib
import logging
import re
from collections import Counter
from typing import Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.presentation import Presentation
from app.models.ai_classification import PresentationSimilarity

logger = logging.getLogger(__name__)
settings = get_settings()


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words."""
    return re.findall(r'\b[a-z][a-z0-9]{1,30}\b', text.lower())


# Common stop words to filter
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "this", "that", "these", "those", "it", "its", "not",
    "slide", "page", "click", "next", "presentation",
}


def _text_to_vector(text: str) -> Counter:
    """Convert text to a term-frequency vector, filtering stop words."""
    words = _tokenize(text)
    words = [w for w in words if w not in _STOP_WORDS and len(w) > 2]
    return Counter(words)


def _cosine_similarity(vec_a: Counter, vec_b: Counter) -> float:
    """Compute cosine similarity between two term-frequency vectors."""
    if not vec_a or not vec_b:
        return 0.0

    intersection = set(vec_a.keys()) & set(vec_b.keys())
    if not intersection:
        return 0.0

    dot_product = sum(vec_a[term] * vec_b[term] for term in intersection)
    mag_a = sum(v ** 2 for v in vec_a.values()) ** 0.5
    mag_b = sum(v ** 2 for v in vec_b.values()) ** 0.5

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot_product / (mag_a * mag_b)


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def _detect_similarity_type(source: Presentation, target: Presentation, score: float) -> str:
    """Determine the type of similarity relationship."""
    # Duplicate detection: same content hash
    if source.content_hash and source.content_hash == target.content_hash:
        return "duplicate"

    # Successor detection: similar titles with version patterns
    if source.title and target.title:
        # Strip version indicators and compare
        import re
        title_a = re.sub(r'\s*v?\d+(\.\d+)*\s*$', '', source.title.lower()).strip()
        title_b = re.sub(r'\s*v?\d+(\.\d+)*\s*$', '', target.title.lower()).strip()
        if title_a == title_b and source.title != target.title:
            return "successor"

    # High similarity = content match, lower = topic match
    if score >= 0.6:
        return "content"
    else:
        return "topic"


async def compute_similarity_for_presentation(
    db: AsyncSession,
    presentation_id: UUID,
    max_results: int = 10,
) -> int:
    """Compute similarity between one presentation and all others.

    Returns the number of similarity relationships created.
    """
    # Load source presentation
    result = await db.execute(
        select(Presentation).where(
            Presentation.id == presentation_id,
            Presentation.is_active == True,  # noqa: E712
        )
    )
    source = result.scalar_one_or_none()
    if not source or not source.extracted_text:
        return 0

    source_vector = _text_to_vector(source.extracted_text)
    source_tags = {t.slug for t in source.tags} if source.tags else set()

    # Load all other active presentations with extracted text
    others_result = await db.execute(
        select(Presentation).where(
            Presentation.id != presentation_id,
            Presentation.is_active == True,  # noqa: E712
            Presentation.extracted_text.isnot(None),
        )
    )
    others = others_result.scalars().all()

    # Compute similarities
    similarities = []
    for target in others:
        target_vector = _text_to_vector(target.extracted_text)
        target_tags = {t.slug for t in target.tags} if target.tags else set()

        # Weighted similarity: 60% content, 25% tags, 15% category
        content_sim = _cosine_similarity(source_vector, target_vector)
        tag_sim = _jaccard_similarity(source_tags, target_tags)
        category_sim = 1.0 if (source.category_id and source.category_id == target.category_id) else 0.0

        combined = (content_sim * 0.60) + (tag_sim * 0.25) + (category_sim * 0.15)

        if combined >= settings.similarity_threshold:
            sim_type = _detect_similarity_type(source, target, combined)
            similarities.append((target.id, combined, sim_type))

    # Sort by score descending and limit
    similarities.sort(key=lambda x: x[1], reverse=True)
    similarities = similarities[:max_results]

    # Delete existing similarities for this source
    await db.execute(
        delete(PresentationSimilarity).where(
            PresentationSimilarity.source_id == presentation_id
        )
    )

    # Insert new similarities
    for target_id, score, sim_type in similarities:
        sim = PresentationSimilarity(
            source_id=presentation_id,
            target_id=target_id,
            similarity_score=round(score, 4),
            similarity_type=sim_type,
        )
        db.add(sim)

    await db.flush()
    return len(similarities)


async def recompute_all_similarities(db: AsyncSession) -> int:
    """Recompute similarity scores between all presentations.

    Returns total number of similarity relationships created.
    """
    result = await db.execute(
        select(Presentation.id).where(
            Presentation.is_active == True,  # noqa: E712
            Presentation.extracted_text.isnot(None),
        )
    )
    pres_ids = [row[0] for row in result.all()]

    total = 0
    for pres_id in pres_ids:
        count = await compute_similarity_for_presentation(db, pres_id)
        total += count

    await db.commit()
    logger.info(f"Recomputed similarities: {total} relationships across {len(pres_ids)} presentations")
    return total


async def get_similar_presentations(
    db: AsyncSession,
    presentation_id: UUID,
    limit: int = 5,
) -> list[dict]:
    """Get similar presentations for a given presentation.

    Returns list of dicts with presentation info and similarity details.
    """
    result = await db.execute(
        select(PresentationSimilarity, Presentation)
        .join(Presentation, PresentationSimilarity.target_id == Presentation.id)
        .where(
            PresentationSimilarity.source_id == presentation_id,
            Presentation.is_active == True,  # noqa: E712
        )
        .order_by(PresentationSimilarity.similarity_score.desc())
        .limit(limit)
    )

    similar = []
    for sim, pres in result.all():
        similar.append({
            "id": str(pres.id),
            "title": pres.title,
            "file_type": pres.file_type,
            "thumbnail_url": f"/api/v1/thumbnails/{pres.id}.webp" if pres.thumbnail_path else None,
            "similarity_score": round(sim.similarity_score, 3),
            "similarity_type": sim.similarity_type,
            "category": pres.category.name if pres.category else None,
        })

    return similar


async def get_recommendations(
    db: AsyncSession,
    presentation_id: UUID,
    session_id: Optional[str] = None,
) -> dict:
    """Get comprehensive recommendations for a presentation.

    Returns:
      - similar: Similar presentations by content
      - trending: Trending in same category
      - new_in_domain: Recently added in same business domain
    """
    # Get the source presentation
    result = await db.execute(
        select(Presentation).where(Presentation.id == presentation_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        return {"similar": [], "trending": [], "new_in_domain": []}

    # Similar presentations
    similar = await get_similar_presentations(db, presentation_id, limit=5)

    # Trending in same category
    trending = []
    if source.category_id:
        trending_result = await db.execute(
            select(Presentation)
            .where(
                Presentation.category_id == source.category_id,
                Presentation.id != presentation_id,
                Presentation.is_active == True,  # noqa: E712
            )
            .order_by(Presentation.popularity_score.desc())
            .limit(5)
        )
        for p in trending_result.scalars().all():
            trending.append({
                "id": str(p.id),
                "title": p.title,
                "file_type": p.file_type,
                "thumbnail_url": f"/api/v1/thumbnails/{p.id}.webp" if p.thumbnail_path else None,
                "popularity_score": p.popularity_score,
            })

    # New in same business domain
    new_in_domain = []
    if source.business_domain:
        domain_result = await db.execute(
            select(Presentation)
            .where(
                Presentation.business_domain == source.business_domain,
                Presentation.id != presentation_id,
                Presentation.is_active == True,  # noqa: E712
            )
            .order_by(Presentation.created_at.desc())
            .limit(5)
        )
        for p in domain_result.scalars().all():
            new_in_domain.append({
                "id": str(p.id),
                "title": p.title,
                "file_type": p.file_type,
                "thumbnail_url": f"/api/v1/thumbnails/{p.id}.webp" if p.thumbnail_path else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })

    return {
        "similar": similar,
        "trending": trending,
        "new_in_domain": new_in_domain,
    }
