"""
services/ai.py – AI integrations with graceful degradation.

Provides:
- classify_ticket(title, description) → category string
- generate_embedding(text) → list[float] (768-dim)
- chat_response(message, context) → string
- summarize_cluster(titles) → string

When API keys are not configured, falls back to deterministic mock responses
so the application can run and demo without external dependencies.
"""
import hashlib
import random
import re
from typing import List, Optional

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)
_GROQ_TEMP_DISABLED = False


def _can_use_groq() -> bool:
    return settings.use_real_ai and bool(settings.GROQ_API_KEY) and not _GROQ_TEMP_DISABLED


def _disable_groq_for_runtime(reason: str) -> None:
    global _GROQ_TEMP_DISABLED
    _GROQ_TEMP_DISABLED = True
    logger.error("groq_temporarily_disabled", reason=reason)

# Global categories used for classification prompts
GLOBAL_CATEGORIES = [
    "Network Issue",
    "Hardware Problem",
    "Software Bug",
    "Access Request",
    "Security Incident",
    "Email Issue",
    "VPN Problem",
    "Password Reset",
    "Printer Issue",
    "Account Setup",
    "Performance Issue",
    "Data Loss",
    "General IT",
    "HR Policy",
    "Facilities",
]

# Mapping from global categories to frontend display values
CATEGORY_DISPLAY = {
    "Network Issue": "Network",
    "Hardware Problem": "Hardware",
    "Software Bug": "Software",
    "Access Request": "Access",
    "Security Incident": "Security",
    "Email Issue": "Software",
    "VPN Problem": "Network",
    "Password Reset": "Access",
    "Printer Issue": "Hardware",
    "Account Setup": "Access",
    "Performance Issue": "Software",
    "Data Loss": "Software",
    "General IT": "Software",
    "HR Policy": "HR",
    "Facilities": "General",
}


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def map_to_allowed_category(raw_category: Optional[str], allowed_categories: List[str]) -> Optional[str]:
    """Map arbitrary model output to one of allowed categories using generic string similarity."""
    if not raw_category or not allowed_categories:
        return None

    exact_map = {cat.lower(): cat for cat in allowed_categories}
    if raw_category.lower() in exact_map:
        return exact_map[raw_category.lower()]

    normalized_allowed = {_normalize_label(cat): cat for cat in allowed_categories}
    normalized_raw = _normalize_label(raw_category)
    if normalized_raw in normalized_allowed:
        return normalized_allowed[normalized_raw]

    raw_tokens = set(normalized_raw.split())
    best_cat: Optional[str] = None
    best_score = 0.0

    for allowed in allowed_categories:
        normalized_allowed_value = _normalize_label(allowed)
        allowed_tokens = set(normalized_allowed_value.split())

        score = 0.0
        if normalized_allowed_value and (
            normalized_allowed_value in normalized_raw or normalized_raw in normalized_allowed_value
        ):
            score = max(score, 0.8)

        if raw_tokens and allowed_tokens:
            overlap = len(raw_tokens & allowed_tokens)
            if overlap:
                score = max(score, overlap / max(len(allowed_tokens), 1))

        if score > best_score:
            best_score = score
            best_cat = allowed

    if best_score >= 0.3:
        return best_cat
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Mock helpers (used when API keys not set)
# ─────────────────────────────────────────────────────────────────────────────

def _mock_category(title: str, description: str) -> str:
    """Deterministic category based on keywords in the text."""
    text = (title + " " + description).lower()
    if any(kw in text for kw in ["vpn", "network", "wifi", "internet", "connectivity"]):
        return "Network Issue"
    if any(kw in text for kw in ["laptop", "monitor", "keyboard", "mouse", "hardware", "printer"]):
        return "Hardware Problem"
    if any(kw in text for kw in ["password", "reset", "access", "login", "account", "permission"]):
        return "Access Request"
    if any(kw in text for kw in ["software", "app", "install", "license", "crash", "bug"]):
        return "Software Bug"
    if any(kw in text for kw in ["email", "outlook", "mail", "calendar"]):
        return "Email Issue"
    if any(kw in text for kw in ["security", "virus", "malware", "breach"]):
        return "Security Incident"
    return "General IT"


def _mock_embedding(text: str) -> List[float]:
    """Generate a reproducible pseudo-random 768-dim unit vector from text hash."""
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    vec = [rng.gauss(0, 1) for _ in range(768)]
    # Normalize to unit vector
    magnitude = sum(x**2 for x in vec) ** 0.5
    return [x / magnitude for x in vec] if magnitude > 0 else vec


# ─────────────────────────────────────────────────────────────────────────────
# Groq – Classification
# ─────────────────────────────────────────────────────────────────────────────

async def classify_ticket(title: str, description: str) -> str:
    """
    Classify a ticket into one of GLOBAL_CATEGORIES using Groq LLM.
    Falls back to keyword-based mock if GROQ_API_KEY is not set.
    """
    if not _can_use_groq():
        logger.info("groq_api_key_missing", action="using_mock_classification")
        return _mock_category(title, description)

    categories_str = "\n".join(f"- {c}" for c in GLOBAL_CATEGORIES)
    prompt = (
        f"You are an IT helpdesk classification engine. "
        f"Classify the following support ticket into exactly ONE category from this list:\n"
        f"{categories_str}\n\n"
        f"Ticket Title: {title}\n"
        f"Ticket Description: {description}\n\n"
        f"Respond with ONLY the category name, nothing else."
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You classify IT support tickets. Respond only with the category name."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0,
                    "max_tokens": 50,
                },
            )
            response.raise_for_status()
            data = response.json()
            category = data["choices"][0]["message"]["content"].strip()
            # Validate it's in our list
            if category in GLOBAL_CATEGORIES:
                return category
            # Fuzzy match
            for cat in GLOBAL_CATEGORIES:
                if cat.lower() in category.lower() or category.lower() in cat.lower():
                    return cat
            logger.warning("groq_unknown_category", returned=category)
            return _mock_category(title, description)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            _disable_groq_for_runtime("unauthorized_or_forbidden")
        logger.error("groq_classification_failed", error=str(e), status_code=e.response.status_code)
        return _mock_category(title, description)
    except Exception as e:
        logger.error("groq_classification_failed", error=str(e))
        return _mock_category(title, description)


async def classify_ticket_to_allowed_category(
    title: str,
    description: str,
    allowed_categories: List[str],
) -> Optional[str]:
    """Classify a ticket into one category from tenant-provided allowed categories."""
    if not allowed_categories:
        return None

    if _can_use_groq():
        categories_str = "\n".join(f"- {c}" for c in allowed_categories)
        prompt = (
            "You are an IT helpdesk routing engine. "
            "Choose exactly ONE category from the allowed categories list below.\n"
            f"Allowed categories:\n{categories_str}\n\n"
            f"Ticket Title: {title}\n"
            f"Ticket Description: {description}\n\n"
            "Return only the category name exactly as written in the list."
        )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You classify tickets into provided categories. Return only one allowed category.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0,
                        "max_tokens": 50,
                    },
                )
                response.raise_for_status()
                category = response.json()["choices"][0]["message"]["content"].strip()
                mapped = map_to_allowed_category(category, allowed_categories)
                if mapped:
                    return mapped
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                _disable_groq_for_runtime("unauthorized_or_forbidden")
            logger.error("groq_allowed_category_classification_failed", error=str(e), status_code=e.response.status_code)
        except Exception as e:
            logger.error("groq_allowed_category_classification_failed", error=str(e))

    generic_category = await classify_ticket(title, description)
    return map_to_allowed_category(generic_category, allowed_categories)


# ─────────────────────────────────────────────────────────────────────────────
# Groq – Chat / Conversational AI
# ─────────────────────────────────────────────────────────────────────────────

async def chat_with_ai(
    message: str,
    context: Optional[str] = None,
    conversation_history: Optional[List[dict]] = None,
) -> str:
    """
    Chat with the Groq LLM for general IT helpdesk queries.
    Falls back to a canned response if API key not set.
    """
    if not _can_use_groq():
        return (
            "I'm your AI assistant. I can help you troubleshoot IT issues, "
            "find knowledge base articles, or create support tickets. "
            "What can I help you with today?"
        )

    system_prompt = (
        "You are HelpDesk AI, an intelligent IT support assistant. "
        "Help users troubleshoot issues, guide them to self-service solutions, "
        "and collect information to create support tickets when needed. "
        "Be concise, friendly, and technical when appropriate."
    )
    if context:
        system_prompt += f"\n\nContext: {context}"

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history[-10:])  # Last 10 turns
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            _disable_groq_for_runtime("unauthorized_or_forbidden")
        logger.error("groq_chat_failed", error=str(e), status_code=e.response.status_code)
        return "I'm currently running in fallback mode due to AI auth configuration. I can still help and create a ticket for you."
    except Exception as e:
        logger.error("groq_chat_failed", error=str(e))
        return "I'm having trouble connecting right now. Please try again or create a support ticket for urgent issues."


# ─────────────────────────────────────────────────────────────────────────────
# Groq – Ticket suggestion for ticket detail view
# ─────────────────────────────────────────────────────────────────────────────

async def generate_ticket_suggestion(
    title: str,
    description: str,
    category: Optional[str],
    similar_titles: Optional[List[str]] = None,
) -> tuple[str, int]:
    """
    Generate an AI suggestion/insight for a ticket.
    Returns (suggestion_text, confidence_percentage).
    """
    if not _can_use_groq():
        confidence = 75
        similar_str = ""
        if similar_titles:
            confidence = 85
            similar_str = f" Similar tickets like '{similar_titles[0]}' were resolved by resetting credentials or checking network configuration."
        return (
            f"This {category or 'IT'} issue matches common patterns in our knowledge base.{similar_str} "
            f"Recommend checking the knowledge base for self-service resolution steps.",
            confidence,
        )

    similar_context = ""
    if similar_titles:
        similar_context = f"\nSimilar resolved tickets: {', '.join(similar_titles[:3])}"

    prompt = (
        f"Analyze this IT support ticket and provide a brief insight (2-3 sentences) "
        f"about likely causes and recommended resolution approach.\n\n"
        f"Title: {title}\nDescription: {description}\nCategory: {category}{similar_context}\n\n"
        f"Also estimate resolution confidence as a percentage (0-100).\n"
        f"Format: INSIGHT: <text> | CONFIDENCE: <number>"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()
            # Parse response
            insight = text
            confidence = 75
            if "INSIGHT:" in text and "CONFIDENCE:" in text:
                parts = text.split("|")
                insight = parts[0].replace("INSIGHT:", "").strip()
                conf_str = parts[1].replace("CONFIDENCE:", "").strip()
                try:
                    confidence = int("".join(c for c in conf_str if c.isdigit())[:3])
                    confidence = max(0, min(100, confidence))
                except ValueError:
                    pass
            return insight, confidence
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            _disable_groq_for_runtime("unauthorized_or_forbidden")
        logger.error("groq_suggestion_failed", error=str(e), status_code=e.response.status_code)
        return "AI analysis unavailable. Please review the ticket manually.", 0
    except Exception as e:
        logger.error("groq_suggestion_failed", error=str(e))
        return "AI analysis unavailable. Please review the ticket manually.", 0


# ─────────────────────────────────────────────────────────────────────────────
# Groq – Trend Cluster Summarization
# ─────────────────────────────────────────────────────────────────────────────

async def summarize_trend_cluster(ticket_titles: List[str]) -> str:
    """
    Summarize a cluster of related tickets using Groq.
    Falls back to a template if API key not set.
    """
    if not _can_use_groq() or not ticket_titles:
        return f"Cluster of {len(ticket_titles)} related tickets detected. Common theme: {ticket_titles[0] if ticket_titles else 'Unknown'}."

    titles_str = "\n".join(f"- {t}" for t in ticket_titles[:20])
    prompt = (
        f"The following IT support tickets appear to be related. "
        f"Write a 1-2 sentence summary of the common issue:\n{titles_str}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 150,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            _disable_groq_for_runtime("unauthorized_or_forbidden")
        logger.error("groq_summarize_failed", error=str(e), status_code=e.response.status_code)
        return f"Multiple related tickets detected: {ticket_titles[0]}."
    except Exception as e:
        logger.error("groq_summarize_failed", error=str(e))
        return f"Multiple related tickets detected: {ticket_titles[0]}."


# ─────────────────────────────────────────────────────────────────────────────
# Jina AI – Embeddings
# ─────────────────────────────────────────────────────────────────────────────

async def generate_embedding(text: str) -> List[float]:
    """
    Generate a 768-dim embedding vector using Jina AI.
    Falls back to a deterministic mock vector if JINA_API_KEY is not set.
    """
    if not settings.use_real_ai or not settings.JINA_API_KEY:
        logger.info("jina_api_key_missing", action="using_mock_embedding")
        return _mock_embedding(text)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.jina.ai/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.JINA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.JINA_MODEL,
                    "input": [text[:8000]],  # Max token limit
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception as e:
        logger.error("jina_embedding_failed", error=str(e))
        return _mock_embedding(text)
