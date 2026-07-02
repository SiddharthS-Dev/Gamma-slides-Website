"""Ollama local LLM provider stub — ready for future integration.

To activate:
  1. Install Ollama: https://ollama.ai
  2. Pull a model: ollama pull llama3
  3. Set SLIDEVAULT_AI_PROVIDER=ollama
  4. Set SLIDEVAULT_AI_BASE_URL=http://localhost:11434
  5. Set SLIDEVAULT_AI_MODEL=llama3
"""

import logging

from app.ai.ai_provider import (
    AIProvider, ContentPayload, ClassificationResult, SummaryResult,
    KeywordResult, TagResult,
)

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Local LLM provider via Ollama REST API.

    Runs models locally — no data leaves the network.
    Requires Ollama running on the configured base URL.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def provider_name(self) -> str:
        return f"ollama:{self.model}"

    async def classify(self, content: ContentPayload) -> ClassificationResult:
        """Classify using local LLM via Ollama API."""
        raise NotImplementedError(
            "Ollama provider is not yet implemented. "
            "Install Ollama and configure SLIDEVAULT_AI_BASE_URL to enable."
        )

    async def generate_tags(self, content: ContentPayload) -> list[TagResult]:
        raise NotImplementedError("Ollama provider not yet implemented.")

    async def generate_summary(self, content: ContentPayload) -> SummaryResult:
        raise NotImplementedError("Ollama provider not yet implemented.")

    async def extract_keywords(self, content: ContentPayload) -> list[KeywordResult]:
        raise NotImplementedError("Ollama provider not yet implemented.")
