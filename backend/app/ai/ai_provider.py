"""AI Provider abstraction layer — defines the contract for all AI backends.

Supports pluggable providers: rule-based, OpenAI, Claude, Gemini, Ollama.
All providers implement the same interface so they can be swapped without code changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DifficultyLevel(str, Enum):
    """Presentation difficulty classification."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class KeywordType(str, Enum):
    """Classification of extracted keywords."""
    TECHNOLOGY = "technology"
    PRODUCT = "product"
    DEPARTMENT = "department"
    PROCESS = "process"
    TOOL = "tool"
    FRAMEWORK = "framework"
    CONCEPT = "concept"


class SimilarityType(str, Enum):
    """Type of similarity relationship between presentations."""
    CONTENT = "content"
    TOPIC = "topic"
    SUCCESSOR = "successor"
    DUPLICATE = "duplicate"


@dataclass
class ContentPayload:
    """Extracted content passed to AI providers for analysis."""
    title: str
    headings: list[str] = field(default_factory=list)
    body_text: str = ""
    speaker_notes: str = ""
    metadata: dict = field(default_factory=dict)
    slide_texts: list[str] = field(default_factory=list)
    file_name: str = ""
    file_type: str = ""
    word_count: int = 0


@dataclass
class ClassificationResult:
    """Result of AI-based presentation classification."""
    category: str                           # Primary category name
    sub_category: Optional[str] = None      # Sub-category name
    department: Optional[str] = None        # Department name
    business_domain: Optional[str] = None   # Business domain
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    confidence_category: float = 0.0        # 0.0 – 1.0
    confidence_department: float = 0.0      # 0.0 – 1.0
    reasoning: str = ""                     # Explanation of classification


@dataclass
class SummaryResult:
    """AI-generated summaries at multiple detail levels."""
    short_summary: str = ""                 # ~100 words
    medium_summary: str = ""                # ~300 words
    executive_summary: str = ""             # Strategic overview
    learning_objectives: list[str] = field(default_factory=list)
    key_topics: list[str] = field(default_factory=list)


@dataclass
class KeywordResult:
    """A single extracted keyword with classification."""
    keyword: str
    keyword_type: KeywordType = KeywordType.CONCEPT
    relevance_score: float = 0.0            # 0.0 – 1.0


@dataclass
class TagResult:
    """A generated tag for the presentation."""
    name: str
    confidence: float = 0.0                 # 0.0 – 1.0


@dataclass
class SimilarityMatch:
    """A similarity match between two presentations."""
    target_id: str
    score: float = 0.0                      # 0.0 – 1.0
    similarity_type: SimilarityType = SimilarityType.CONTENT


class AIProvider(ABC):
    """Abstract base class for all AI providers.

    Every provider must implement these methods. The classification service
    calls them through this interface, so providers can be swapped via config.
    """

    @abstractmethod
    async def classify(self, content: ContentPayload) -> ClassificationResult:
        """Classify content into category, sub-category, department, and difficulty."""
        ...

    @abstractmethod
    async def generate_tags(self, content: ContentPayload) -> list[TagResult]:
        """Generate 5-20 intelligent tags for the content."""
        ...

    @abstractmethod
    async def generate_summary(self, content: ContentPayload) -> SummaryResult:
        """Generate multi-level summaries of the content."""
        ...

    @abstractmethod
    async def extract_keywords(self, content: ContentPayload) -> list[KeywordResult]:
        """Extract typed keywords (technologies, products, tools, etc.)."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable name of this provider."""
        return self.__class__.__name__
