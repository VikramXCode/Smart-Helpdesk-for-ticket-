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
from typing import List, Optional

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

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
    if not settings.GROQ_API_KEY:
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
    except Exception as e:
        logger.error("groq_classification_failed", error=str(e))
        return _mock_category(title, description)


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
    if not settings.GROQ_API_KEY:
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
    if not settings.GROQ_API_KEY:
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
    if not settings.GROQ_API_KEY or not ticket_titles:
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
    if not settings.JINA_API_KEY:
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
