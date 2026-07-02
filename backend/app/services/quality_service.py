"""Quality scoring service — computes completeness, freshness, and knowledge scores.

All formulas are configurable via SLIDEVAULT_QUALITY_* environment variables.
"""

import logging
from datetime import datetime

from app.config import get_settings
from app.ingestion.content_extractor import ExtractedContent

logger = logging.getLogger(__name__)
settings = get_settings()


def compute_quality_scores(presentation, extracted: ExtractedContent) -> dict:
    """Compute quality metrics for a presentation.

    Returns:
        Dict with keys: completeness, freshness, knowledge (each 0.0-1.0)
    """
    completeness = _compute_completeness(presentation, extracted)
    freshness = _compute_freshness(presentation)
    knowledge = _compute_knowledge(presentation, extracted)

    return {
        "completeness": round(completeness, 3),
        "freshness": round(freshness, 3),
        "knowledge": round(knowledge, 3),
    }


def _compute_completeness(presentation, extracted: ExtractedContent) -> float:
    """Score based on presence of expected metadata and content.

    Factors:
      - Has title (10%)
      - Has description (10%)
      - Has author (10%)
      - Has proper headings (15%)
      - Has adequate slide count (10%)
      - Has substantial body text (20%)
      - Has thumbnail (10%)
      - Has category assigned (10%)
      - Has tags (5%)
    """
    score = 0.0

    # Title quality
    if presentation.title and len(presentation.title) > 5:
        score += 0.10

    # Description
    if presentation.description and len(presentation.description) > 20:
        score += 0.10

    # Author
    if presentation.author:
        score += 0.10

    # Headings
    if extracted.headings:
        heading_ratio = min(1.0, len(extracted.headings) / 5.0)
        score += 0.15 * heading_ratio

    # Slide count
    if presentation.slide_count:
        if presentation.slide_count >= 3:
            score += 0.10
        else:
            score += 0.05  # At least has some slides

    # Body text substance
    if extracted.word_count > 0:
        text_ratio = min(1.0, extracted.word_count / 500.0)
        score += 0.20 * text_ratio

    # Thumbnail
    if presentation.thumbnail_path:
        score += 0.10

    # Category
    if presentation.category_id:
        score += 0.10

    # Tags
    if presentation.tags and len(presentation.tags) >= 3:
        score += 0.05

    return min(1.0, score)


def _compute_freshness(presentation) -> float:
    """Score based on how recently the file was modified.

    Scoring:
      - Modified within 30 days: 1.0
      - Modified within 90 days: 0.8
      - Modified within 180 days: 0.6
      - Modified within 365 days: 0.4
      - Older: 0.2
    """
    ref_date = presentation.file_modified_at or presentation.created_at
    if not ref_date:
        return 0.3  # Unknown freshness

    days_old = (datetime.utcnow() - ref_date).days

    if days_old <= 30:
        return 1.0
    elif days_old <= 90:
        return 0.8
    elif days_old <= 180:
        return 0.6
    elif days_old <= 365:
        return 0.4
    else:
        return 0.2


def _compute_knowledge(presentation, extracted: ExtractedContent) -> float:
    """Score based on content depth and informational value.

    Factors:
      - Keyword density (unique meaningful terms / total words)
      - Heading structure quality
      - Content depth (word count relative to slide count)
      - Speaker notes presence
    """
    score = 0.0

    # Heading structure (max 0.30)
    if extracted.headings:
        heading_score = min(1.0, len(extracted.headings) / 8.0)
        score += 0.30 * heading_score

    # Content depth: words per slide (max 0.30)
    slide_count = presentation.slide_count or 1
    if extracted.word_count > 0:
        words_per_slide = extracted.word_count / max(slide_count, 1)
        # Ideal: 50-150 words per slide
        if words_per_slide >= 50:
            depth_score = min(1.0, words_per_slide / 100.0)
        else:
            depth_score = words_per_slide / 50.0
        score += 0.30 * depth_score

    # Speaker notes presence (max 0.20)
    if extracted.speaker_notes:
        notes_ratio = min(1.0, len(extracted.speaker_notes) / 500.0)
        score += 0.20 * notes_ratio

    # Overall word count (max 0.20)
    if extracted.word_count > 100:
        wc_ratio = min(1.0, extracted.word_count / 2000.0)
        score += 0.20 * wc_ratio

    return min(1.0, score)
