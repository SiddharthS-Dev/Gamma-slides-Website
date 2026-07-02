"""AI provider package — pluggable AI backend for classification, tagging, and summarization.

Usage:
    from app.ai import get_ai_provider

    provider = get_ai_provider()
    result = await provider.classify(content)
"""

import logging
from functools import lru_cache

from app.ai.ai_provider import (
    AIProvider, ContentPayload, ClassificationResult, SummaryResult,
    KeywordResult, TagResult, KeywordType, DifficultyLevel,
    SimilarityType, SimilarityMatch,
)
from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_ai_provider() -> AIProvider:
    """Factory function — returns the configured AI provider instance.

    Reads SLIDEVAULT_AI_PROVIDER from settings and instantiates
    the appropriate provider. Defaults to rule_based.
    """
    settings = get_settings()
    provider_name = settings.ai_provider.lower()

    if provider_name == "openai":
        from app.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.ai_api_key,
            model=settings.ai_model or "gpt-4o",
            base_url=settings.ai_base_url or None,
        )
    elif provider_name == "ollama":
        from app.ai.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=settings.ai_base_url or "http://localhost:11434",
            model=settings.ai_model or "llama3",
        )
    elif provider_name == "rule_based":
        from app.ai.rule_based import RuleBasedProvider
        return RuleBasedProvider()
    else:
        logger.warning(f"Unknown AI provider '{provider_name}', falling back to rule_based")
        from app.ai.rule_based import RuleBasedProvider
        return RuleBasedProvider()


__all__ = [
    "get_ai_provider",
    "AIProvider",
    "ContentPayload",
    "ClassificationResult",
    "SummaryResult",
    "KeywordResult",
    "TagResult",
    "KeywordType",
    "DifficultyLevel",
    "SimilarityType",
    "SimilarityMatch",
]
