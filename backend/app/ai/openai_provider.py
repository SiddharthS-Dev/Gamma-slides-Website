"""OpenAI AI provider stub — ready for future integration.

To activate:
  1. pip install openai
  2. Set SLIDEVAULT_AI_PROVIDER=openai
  3. Set SLIDEVAULT_AI_API_KEY=sk-...
  4. Optionally set SLIDEVAULT_AI_MODEL=gpt-4o
"""

import logging

from app.ai.ai_provider import (
    AIProvider, ContentPayload, ClassificationResult, SummaryResult,
    KeywordResult, TagResult,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI-based classification provider.

    Uses structured prompts with JSON mode for reliable extraction.
    Requires the `openai` package and a valid API key.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @property
    def provider_name(self) -> str:
        return f"openai:{self.model}"

    async def classify(self, content: ContentPayload) -> ClassificationResult:
        """Classify using OpenAI chat completion with structured output."""
        raise NotImplementedError(
            "OpenAI provider is not yet implemented. "
            "Install 'openai' package and configure SLIDEVAULT_AI_API_KEY to enable."
        )

    async def generate_tags(self, content: ContentPayload) -> list[TagResult]:
        raise NotImplementedError("OpenAI provider not yet implemented.")

    async def generate_summary(self, content: ContentPayload) -> SummaryResult:
        raise NotImplementedError("OpenAI provider not yet implemented.")

    async def extract_keywords(self, content: ContentPayload) -> list[KeywordResult]:
        raise NotImplementedError("OpenAI provider not yet implemented.")
