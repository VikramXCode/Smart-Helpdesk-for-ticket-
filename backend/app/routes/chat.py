"""
routes/chat.py – AI chatbot endpoint.

Handles conversational AI for the floating helpdesk chatbot.
Can detect ticket creation intent and create tickets inline.
"""
from fastapi import APIRouter

from app.dependencies import CurrentUser, DB
from app.models import Ticket
from app.schemas import ChatRequest, ChatResponse, SimilarArticleOut, TicketCreate, TicketListItem
from app.services.ai import chat_with_ai, classify_ticket, generate_embedding
from app.services.vector import find_similar_articles

router = APIRouter(prefix="/chat", tags=["chat"])

# Keywords that suggest the user wants to create a ticket
TICKET_INTENT_KEYWORDS = [
    "create ticket", "submit ticket", "open ticket", "file ticket",
    "report issue", "report problem", "log issue", "raise ticket",
    "can't", "cannot", "not working", "broken", "error", "failed",
    "issue with", "problem with", "help with",
]


@router.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user: CurrentUser, db: DB):
    """
    Process a chat message and return an AI response.

    Intent detection:
    - If message looks like a ticket creation request, creates the ticket
    - If message looks like a knowledge search, runs vector search
    - Otherwise, returns conversational AI response
    """
    message_lower = payload.message.lower()

    # ── Detect intent ────────────────────────────────────────────────────────
    intent = "general"
    ticket_intent_score = sum(1 for kw in TICKET_INTENT_KEYWORDS if kw in message_lower)

    if ticket_intent_score >= 2:
        intent = "ticket_creation"
    elif any(kw in message_lower for kw in ["how to", "how do", "what is", "guide", "tutorial", "steps"]):
        intent = "knowledge_search"

    # ── Knowledge search ─────────────────────────────────────────────────────
    suggested_articles = []
    if intent == "knowledge_search" and current_user.company_id:
        embedding = await generate_embedding(payload.message)
        similar = await find_similar_articles(db, current_user.company_id, embedding, limit=3)
        suggested_articles = [
            SimilarArticleOut(
                id=article.id,
                title=article.title,
                tag=article.category or "",
                summary=article.content[:120] + "..." if len(article.content) > 120 else article.content,
                similarity=round(sim, 3),
            )
            for article, sim in similar
        ]

    # ── Build context for AI ─────────────────────────────────────────────────
    context = None
    if suggested_articles:
        context = "Relevant knowledge base articles:\n" + "\n".join(
            f"- {a.title}: {a.summary}" for a in suggested_articles
        )

    # ── AI response ──────────────────────────────────────────────────────────
    response_text = await chat_with_ai(
        message=payload.message,
        context=context,
        conversation_history=payload.conversation_history,
    )

    return ChatResponse(
        response=response_text,
        intent=intent,
        ticket_created=None,  # Frontend can use this to show ticket creation confirmation
        suggested_articles=suggested_articles,
    )
