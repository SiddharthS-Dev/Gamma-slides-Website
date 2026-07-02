"""Rule-based AI provider — offline classifier using keyword dictionaries and TF-IDF.

This is the default provider that requires no API keys. It uses keyword matching,
TF-IDF scoring, and heuristic rules to classify presentations, generate tags,
extract keywords, and produce summaries.
"""

import logging
import re
from collections import Counter
from math import log

from app.ai.ai_provider import (
    AIProvider, ContentPayload, ClassificationResult, SummaryResult,
    KeywordResult, TagResult, DifficultyLevel, KeywordType,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# TAXONOMY: Category → Sub-categories + associated keywords
# ═══════════════════════════════════════════════════════════════

CATEGORY_TAXONOMY: dict[str, dict] = {
    "Engineering": {
        "sub_categories": {
            "Architecture": ["architecture", "system design", "microservices", "monolith", "api design",
                             "scalability", "distributed", "design patterns", "ddd", "event-driven"],
            "Backend": ["backend", "fastapi", "django", "flask", "rest api", "graphql", "database",
                        "postgresql", "redis", "celery", "queue", "server", "orm", "sqlalchemy"],
            "Frontend": ["frontend", "react", "vue", "angular", "typescript", "javascript", "css",
                         "html", "ui", "ux", "component", "webpack", "vite", "tailwind"],
            "DevOps": ["devops", "docker", "kubernetes", "k8s", "ci/cd", "pipeline", "jenkins",
                       "github actions", "terraform", "ansible", "helm", "deployment", "monitoring",
                       "prometheus", "grafana", "infrastructure"],
            "AI": ["machine learning", "deep learning", "neural network", "nlp", "computer vision",
                   "tensorflow", "pytorch", "model training", "ai", "llm", "gpt", "transformer",
                   "classification", "regression", "clustering"],
            "Data Engineering": ["data pipeline", "etl", "data warehouse", "spark", "airflow",
                                 "data lake", "bigquery", "snowflake", "dbt", "kafka", "streaming",
                                 "batch processing", "data ingestion"],
        },
        "keywords": ["engineering", "code", "software", "development", "programming", "technical",
                     "implementation", "refactoring", "codebase", "repository", "git"],
    },
    "Product": {
        "sub_categories": {
            "FleetExplorer": ["fleetexplorer", "fleet explorer", "fleet", "vehicle tracking",
                              "telemetry", "gps tracking", "fleet management"],
            "PDLC": ["pdlc", "product development lifecycle", "product lifecycle"],
            "ESG Wallet": ["esg wallet", "esg", "sustainability wallet", "carbon credit"],
            "Product Documentation": ["product documentation", "user guide", "feature spec",
                                      "product spec", "requirements", "prd"],
        },
        "keywords": ["product", "feature", "roadmap", "backlog", "user story", "sprint",
                     "release", "mvp", "launch", "stakeholder", "customer feedback"],
    },
    "Operations": {
        "sub_categories": {
            "Fleet Operations": ["fleet operations", "vehicle maintenance", "dispatch", "routing"],
            "Supply Chain": ["supply chain", "logistics", "inventory", "procurement", "warehouse"],
            "Process Improvement": ["process improvement", "lean", "six sigma", "automation",
                                    "optimization", "sop", "standard operating procedure"],
        },
        "keywords": ["operations", "operational", "efficiency", "workflow", "process",
                     "logistics", "supply", "maintenance"],
    },
    "Human Resources": {
        "sub_categories": {
            "Discipline Engine": ["discipline engine", "disciplinary", "misconduct", "warning"],
            "Leave Management": ["leave management", "leave policy", "pto", "vacation",
                                 "sick leave", "absence"],
            "Employee Onboarding": ["onboarding", "new hire", "orientation", "induction"],
            "Policies": ["hr policy", "employee handbook", "code of conduct", "workplace policy"],
        },
        "keywords": ["hr", "human resources", "employee", "talent", "recruitment", "hiring",
                     "performance review", "appraisal", "compensation", "benefits", "payroll"],
    },
    "ESG": {
        "sub_categories": {
            "Environmental": ["environmental", "carbon footprint", "emissions", "green energy",
                              "sustainability", "climate"],
            "Social": ["social responsibility", "community", "diversity", "inclusion", "dei"],
            "Governance": ["corporate governance", "board", "transparency", "ethics"],
        },
        "keywords": ["esg", "sustainability", "environmental", "social", "governance",
                     "csr", "carbon", "green"],
    },
    "Finance": {
        "sub_categories": {
            "Budgeting": ["budget", "budgeting", "forecast", "financial planning"],
            "Reporting": ["financial report", "quarterly report", "annual report", "p&l",
                          "balance sheet", "income statement"],
            "Audit": ["audit", "internal audit", "external audit", "compliance audit"],
        },
        "keywords": ["finance", "financial", "revenue", "cost", "profit", "expense",
                     "accounting", "invoice", "billing", "tax"],
    },
    "Compliance": {
        "sub_categories": {
            "Regulatory": ["regulatory", "regulation", "gdpr", "hipaa", "sox", "pci"],
            "Risk Management": ["risk management", "risk assessment", "mitigation"],
            "Legal": ["legal", "contract", "agreement", "liability", "litigation"],
        },
        "keywords": ["compliance", "compliant", "regulatory", "regulation", "policy",
                     "standard", "certification", "iso"],
    },
    "Administration": {
        "sub_categories": {
            "Office Management": ["office management", "facilities", "workspace"],
            "Vendor Management": ["vendor", "procurement", "contract management"],
            "Asset Management": ["asset management", "inventory", "equipment"],
        },
        "keywords": ["administration", "admin", "office", "facilities", "procurement"],
    },
    "Training": {
        "sub_categories": {
            "Technical Training": ["technical training", "workshop", "coding bootcamp",
                                    "lab", "hands-on"],
            "Soft Skills": ["soft skills", "leadership", "communication", "teamwork",
                            "presentation skills"],
            "Onboarding Training": ["onboarding training", "new employee training",
                                     "orientation program"],
        },
        "keywords": ["training", "learning", "development", "course", "tutorial",
                     "workshop", "certification", "skill", "education"],
    },
    "Customer Success": {
        "sub_categories": {
            "Support": ["customer support", "help desk", "ticketing", "sla"],
            "Account Management": ["account management", "client relationship", "retention"],
            "Feedback": ["customer feedback", "nps", "satisfaction", "survey"],
        },
        "keywords": ["customer success", "customer", "client", "support", "satisfaction",
                     "retention", "churn"],
    },
    "Sales": {
        "sub_categories": {
            "Strategy": ["sales strategy", "go-to-market", "gtm", "pipeline"],
            "Enablement": ["sales enablement", "pitch deck", "battle card", "objection handling"],
            "CRM": ["crm", "salesforce", "hubspot", "lead management"],
        },
        "keywords": ["sales", "revenue", "deal", "prospect", "lead", "pipeline", "quota",
                     "closing", "commission"],
    },
    "Marketing": {
        "sub_categories": {
            "Digital Marketing": ["digital marketing", "seo", "sem", "ppc", "social media",
                                   "content marketing"],
            "Brand": ["brand", "branding", "brand identity", "brand strategy"],
            "Events": ["event", "conference", "webinar", "trade show"],
        },
        "keywords": ["marketing", "campaign", "brand", "content", "social media",
                     "advertising", "promotion", "awareness"],
    },
    "IT Infrastructure": {
        "sub_categories": {
            "Network": ["network", "networking", "firewall", "vpn", "dns", "load balancer"],
            "Cloud": ["cloud", "aws", "azure", "gcp", "saas", "paas", "iaas"],
            "Systems": ["server", "storage", "backup", "disaster recovery", "uptime"],
        },
        "keywords": ["infrastructure", "it", "network", "server", "cloud", "hardware",
                     "datacenter", "sysadmin"],
    },
    "Security": {
        "sub_categories": {
            "Cybersecurity": ["cybersecurity", "penetration testing", "vulnerability",
                               "threat", "incident response"],
            "Access Control": ["access control", "iam", "authentication", "authorization",
                                "sso", "mfa", "oauth"],
            "Data Security": ["data security", "encryption", "data loss prevention",
                               "backup", "privacy"],
        },
        "keywords": ["security", "secure", "vulnerability", "threat", "hack", "breach",
                     "encryption", "firewall", "authentication"],
    },
    "Governance": {
        "sub_categories": {
            "Corporate": ["corporate governance", "board meeting", "shareholder"],
            "IT Governance": ["it governance", "itil", "cobit", "change management"],
            "Data Governance": ["data governance", "data quality", "master data", "metadata"],
        },
        "keywords": ["governance", "policy", "framework", "standard", "oversight",
                     "accountability"],
    },
}

# ═══════════════════════════════════════════════════════════════
# KNOWN ENTITY DICTIONARIES for keyword extraction
# ═══════════════════════════════════════════════════════════════

KNOWN_TECHNOLOGIES = {
    "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
    "react", "vue", "angular", "svelte", "nextjs", "nuxt", "fastapi", "django",
    "flask", "spring", "express", "nestjs", "postgresql", "mysql", "mongodb",
    "redis", "elasticsearch", "kafka", "rabbitmq", "docker", "kubernetes",
    "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
    "aws", "azure", "gcp", "firebase", "vercel", "netlify",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "graphql", "rest", "grpc", "websocket", "oauth", "jwt",
}

KNOWN_TOOLS = {
    "jira", "confluence", "slack", "teams", "zoom", "figma", "miro",
    "notion", "trello", "asana", "linear", "github", "gitlab", "bitbucket",
    "postman", "swagger", "grafana", "prometheus", "datadog", "sentry",
    "salesforce", "hubspot", "zendesk", "intercom", "tableau", "power bi",
    "excel", "powerpoint", "word", "outlook",
}

KNOWN_FRAMEWORKS = {
    "agile", "scrum", "kanban", "lean", "six sigma", "itil", "cobit",
    "togaf", "safe", "devops", "devsecops", "ci/cd", "tdd", "bdd",
    "ddd", "microservices", "event-driven", "cqrs", "solid",
}

KNOWN_PRODUCTS = {
    "fleetexplorer", "fleet explorer", "esg wallet", "pdlc",
    "discipline engine", "leave management",
}

# Common English stop words for TF-IDF
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "dare",
    "not", "no", "nor", "so", "yet", "both", "each", "few", "more",
    "most", "other", "some", "such", "than", "too", "very", "just",
    "about", "above", "after", "again", "all", "also", "any", "because",
    "before", "below", "between", "during", "here", "how", "into", "its",
    "let", "like", "make", "many", "much", "must", "new", "now", "off",
    "old", "only", "our", "out", "over", "own", "same", "she", "then",
    "them", "there", "these", "they", "this", "those", "through", "under",
    "until", "upon", "what", "when", "where", "which", "while", "who",
    "whom", "why", "you", "your", "i", "me", "my", "we", "us", "he",
    "him", "his", "her", "it", "that", "as", "if", "up", "one", "two",
    "slide", "page", "click", "next", "previous", "presentation",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words, stripping punctuation."""
    return re.findall(r'\b[a-z][a-z0-9+#./-]{1,40}\b', text.lower())


def _compute_tf(words: list[str]) -> dict[str, float]:
    """Compute term frequency (TF) for a word list."""
    counter = Counter(words)
    total = len(words) if words else 1
    return {word: count / total for word, count in counter.items()}


def _compute_tfidf_tags(text: str, max_tags: int = 20) -> list[tuple[str, float]]:
    """Simple TF-IDF-like scoring for tag extraction.

    Since we don't have a corpus of documents, we approximate IDF
    by penalizing very common words (stop words) and boosting
    rare/domain-specific terms.
    """
    words = _tokenize(text)
    words = [w for w in words if w not in STOP_WORDS and len(w) > 2]

    tf = _compute_tf(words)

    # Boost known domain terms
    scored = {}
    for word, freq in tf.items():
        score = freq
        # Boost known entities
        if word in KNOWN_TECHNOLOGIES:
            score *= 3.0
        elif word in KNOWN_TOOLS:
            score *= 2.5
        elif word in KNOWN_FRAMEWORKS:
            score *= 2.5
        elif word in KNOWN_PRODUCTS:
            score *= 4.0
        # Penalize very short generic words
        if len(word) <= 3:
            score *= 0.5
        scored[word] = score

    # Sort by score descending
    sorted_tags = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    return sorted_tags[:max_tags]


def _score_category(text: str, category_name: str, category_data: dict) -> tuple[float, str | None]:
    """Score how well text matches a category. Returns (score, best_sub_category)."""
    text_lower = text.lower()
    score = 0.0
    best_sub = None
    best_sub_score = 0.0

    # Score against top-level keywords
    for keyword in category_data.get("keywords", []):
        occurrences = text_lower.count(keyword)
        if occurrences > 0:
            # Weight by keyword length (longer = more specific = more valuable)
            weight = len(keyword.split()) * 1.5
            score += occurrences * weight

    # Score against sub-category keywords
    for sub_name, sub_keywords in category_data.get("sub_categories", {}).items():
        sub_score = 0.0
        for keyword in sub_keywords:
            occurrences = text_lower.count(keyword)
            if occurrences > 0:
                weight = len(keyword.split()) * 2.0  # Sub-category keywords are more specific
                sub_score += occurrences * weight

        score += sub_score
        if sub_score > best_sub_score:
            best_sub_score = sub_score
            best_sub = sub_name

    return score, best_sub


def _estimate_difficulty(content: ContentPayload) -> DifficultyLevel:
    """Estimate presentation difficulty from content characteristics."""
    text = (content.body_text or "").lower()
    words = _tokenize(text)
    total_words = len(words)

    if total_words == 0:
        return DifficultyLevel.INTERMEDIATE

    # Count technical/advanced terms
    advanced_terms = {
        "architecture", "microservices", "distributed", "scalability",
        "algorithm", "optimization", "concurrency", "parallelism",
        "encryption", "authentication", "authorization", "compliance",
        "regression", "classification", "neural", "transformer",
        "kubernetes", "terraform", "infrastructure",
    }
    intermediate_terms = {
        "api", "database", "deployment", "testing", "integration",
        "configuration", "monitoring", "pipeline", "automation",
        "dashboard", "analytics", "reporting", "workflow",
    }
    beginner_terms = {
        "introduction", "overview", "getting started", "basics",
        "tutorial", "guide", "101", "beginner", "fundamentals",
        "onboarding", "orientation", "welcome",
    }

    advanced_count = sum(1 for w in words if w in advanced_terms)
    intermediate_count = sum(1 for w in words if w in intermediate_terms)
    beginner_count = sum(1 for w in words if w in beginner_terms)

    # Check for beginner signals in title/headings
    title_lower = (content.title or "").lower()
    for term in beginner_terms:
        if term in title_lower:
            beginner_count += 10

    # Average word length as complexity proxy
    avg_word_len = sum(len(w) for w in words) / total_words if total_words else 5

    # Scoring
    if beginner_count > advanced_count and beginner_count > intermediate_count:
        return DifficultyLevel.BEGINNER
    elif advanced_count > 15 or avg_word_len > 7:
        return DifficultyLevel.EXPERT
    elif advanced_count > 5:
        return DifficultyLevel.ADVANCED
    elif intermediate_count > 3:
        return DifficultyLevel.INTERMEDIATE
    else:
        return DifficultyLevel.BEGINNER


def _extract_sentences(text: str, max_sentences: int = 5) -> list[str]:
    """Extract the first N meaningful sentences from text."""
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out very short or noise sentences
    meaningful = [
        s.strip() for s in sentences
        if len(s.strip()) > 20 and not s.strip().startswith(('•', '-', '*', '●'))
    ]
    return meaningful[:max_sentences]


class RuleBasedProvider(AIProvider):
    """Offline AI provider using keyword matching and TF-IDF scoring.

    No external API calls required. Suitable as default/fallback provider.
    """

    @property
    def provider_name(self) -> str:
        return "rule_based"

    async def classify(self, content: ContentPayload) -> ClassificationResult:
        """Classify content using keyword-to-category scoring matrix."""
        # Build analysis text from all available content
        analysis_text = " ".join([
            content.title or "",
            " ".join(content.headings),
            content.body_text,
            content.speaker_notes,
            content.file_name,
        ])

        if not analysis_text.strip():
            return ClassificationResult(
                category="Administration",
                confidence_category=0.1,
                reasoning="No content available for classification",
            )

        # Score each category
        scores: list[tuple[str, float, str | None]] = []
        for cat_name, cat_data in CATEGORY_TAXONOMY.items():
            score, best_sub = _score_category(analysis_text, cat_name, cat_data)
            if score > 0:
                scores.append((cat_name, score, best_sub))

        if not scores:
            return ClassificationResult(
                category="Administration",
                confidence_category=0.2,
                reasoning="No strong keyword matches found; defaulting to Administration",
            )

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        best_cat, best_score, best_sub = scores[0]

        # Normalize confidence (sigmoid-like scaling)
        max_possible = max(best_score, 1.0)
        confidence = min(1.0, best_score / (best_score + 10.0))  # Sigmoid normalization

        # If the gap between #1 and #2 is small, lower confidence
        if len(scores) > 1:
            gap_ratio = scores[0][1] / max(scores[1][1], 0.1)
            if gap_ratio < 1.5:
                confidence *= 0.8  # Not very decisive

        # Determine department (often same as category for enterprise context)
        department = best_cat
        dept_confidence = confidence * 0.9  # Slightly less confident about department

        # Determine business domain
        domain_map = {
            "Engineering": "Technology",
            "Product": "Product Management",
            "Operations": "Operations",
            "Human Resources": "People & Culture",
            "ESG": "Sustainability",
            "Finance": "Finance & Accounting",
            "Compliance": "Legal & Compliance",
            "Administration": "Administration",
            "Training": "Learning & Development",
            "Customer Success": "Customer Experience",
            "Sales": "Revenue",
            "Marketing": "Marketing & Growth",
            "IT Infrastructure": "Technology",
            "Security": "Information Security",
            "Governance": "Corporate Governance",
        }

        difficulty = _estimate_difficulty(content)

        top_matches = ", ".join(f"{name}({score:.1f})" for name, score, _ in scores[:3])

        return ClassificationResult(
            category=best_cat,
            sub_category=best_sub,
            department=department,
            business_domain=domain_map.get(best_cat, best_cat),
            difficulty_level=difficulty,
            confidence_category=round(confidence, 3),
            confidence_department=round(dept_confidence, 3),
            reasoning=f"Top matches: {top_matches}",
        )

    async def generate_tags(self, content: ContentPayload) -> list[TagResult]:
        """Generate intelligent tags using TF-IDF on extracted text."""
        analysis_text = " ".join([
            content.title or "",
            " ".join(content.headings),
            content.body_text,
        ])

        if not analysis_text.strip():
            return []

        tfidf_tags = _compute_tfidf_tags(analysis_text, max_tags=20)

        # Also include 2-word phrases from headings (bigrams)
        heading_text = " ".join(content.headings).lower()
        bigrams = []
        heading_words = _tokenize(heading_text)
        for i in range(len(heading_words) - 1):
            bigram = f"{heading_words[i]} {heading_words[i+1]}"
            if heading_words[i] not in STOP_WORDS and heading_words[i+1] not in STOP_WORDS:
                bigrams.append(bigram)

        # Combine unigrams from TF-IDF + heading bigrams
        tags: list[TagResult] = []
        seen = set()

        # Add bigrams first (they're usually more meaningful)
        for bigram in bigrams[:5]:
            if bigram not in seen:
                seen.add(bigram)
                tags.append(TagResult(name=bigram, confidence=0.85))

        # Then TF-IDF unigrams
        max_score = tfidf_tags[0][1] if tfidf_tags else 1.0
        for word, score in tfidf_tags:
            if word not in seen and len(tags) < 20:
                seen.add(word)
                normalized = min(1.0, score / max_score) if max_score > 0 else 0.5
                tags.append(TagResult(name=word, confidence=round(normalized, 3)))

        # Ensure minimum of 5 tags by adding from title words if needed
        if len(tags) < 5:
            title_words = _tokenize(content.title)
            for w in title_words:
                if w not in seen and w not in STOP_WORDS and len(w) > 2:
                    seen.add(w)
                    tags.append(TagResult(name=w, confidence=0.5))
                if len(tags) >= 5:
                    break

        return tags[:20]

    async def generate_summary(self, content: ContentPayload) -> SummaryResult:
        """Generate summaries via sentence extraction."""
        full_text = content.body_text or ""
        headings = content.headings or []
        title = content.title or ""

        # Short summary: title + first 2 sentences
        first_sentences = _extract_sentences(full_text, 3)
        short = f"{title}. " + " ".join(first_sentences) if first_sentences else title
        # Truncate to ~100 words
        short_words = short.split()[:100]
        short_summary = " ".join(short_words)
        if len(short.split()) > 100:
            short_summary += "..."

        # Medium summary: title + headings + first sentences
        medium_parts = [title + "."]
        if headings:
            medium_parts.append("Key sections: " + ", ".join(headings[:10]) + ".")
        medium_parts.extend(_extract_sentences(full_text, 8))
        medium = " ".join(medium_parts)
        medium_words = medium.split()[:300]
        medium_summary = " ".join(medium_words)
        if len(medium.split()) > 300:
            medium_summary += "..."

        # Executive summary
        exec_parts = [f"This presentation on \"{title}\" covers the following areas:"]
        if headings:
            for h in headings[:8]:
                exec_parts.append(f"• {h}")
        exec_parts.extend(_extract_sentences(full_text, 4))
        executive_summary = " ".join(exec_parts)

        # Learning objectives from headings
        learning_objectives = []
        for h in headings[:6]:
            h_clean = h.strip().rstrip(".:;")
            if h_clean and len(h_clean) > 3:
                learning_objectives.append(f"Understand {h_clean}")

        # Key topics from headings + high-frequency terms
        key_topics = headings[:10] if headings else []
        if not key_topics:
            tfidf = _compute_tfidf_tags(full_text, max_tags=10)
            key_topics = [word for word, _ in tfidf]

        return SummaryResult(
            short_summary=short_summary,
            medium_summary=medium_summary,
            executive_summary=executive_summary,
            learning_objectives=learning_objectives,
            key_topics=key_topics,
        )

    async def extract_keywords(self, content: ContentPayload) -> list[KeywordResult]:
        """Extract typed keywords by matching against known entity dictionaries."""
        analysis_text = " ".join([
            content.title or "",
            " ".join(content.headings),
            content.body_text,
        ]).lower()

        words = set(_tokenize(analysis_text))
        keywords: list[KeywordResult] = []

        # Technologies
        for tech in KNOWN_TECHNOLOGIES:
            if tech in analysis_text:
                occurrences = analysis_text.count(tech)
                score = min(1.0, occurrences / 5.0)
                keywords.append(KeywordResult(
                    keyword=tech, keyword_type=KeywordType.TECHNOLOGY,
                    relevance_score=round(score, 3),
                ))

        # Tools
        for tool in KNOWN_TOOLS:
            if tool in analysis_text:
                occurrences = analysis_text.count(tool)
                score = min(1.0, occurrences / 5.0)
                keywords.append(KeywordResult(
                    keyword=tool, keyword_type=KeywordType.TOOL,
                    relevance_score=round(score, 3),
                ))

        # Frameworks
        for fw in KNOWN_FRAMEWORKS:
            if fw in analysis_text:
                occurrences = analysis_text.count(fw)
                score = min(1.0, occurrences / 5.0)
                keywords.append(KeywordResult(
                    keyword=fw, keyword_type=KeywordType.FRAMEWORK,
                    relevance_score=round(score, 3),
                ))

        # Products
        for product in KNOWN_PRODUCTS:
            if product in analysis_text:
                occurrences = analysis_text.count(product)
                score = min(1.0, occurrences / 3.0)
                keywords.append(KeywordResult(
                    keyword=product, keyword_type=KeywordType.PRODUCT,
                    relevance_score=round(score, 3),
                ))

        # Sort by relevance
        keywords.sort(key=lambda k: k.relevance_score, reverse=True)
        return keywords
