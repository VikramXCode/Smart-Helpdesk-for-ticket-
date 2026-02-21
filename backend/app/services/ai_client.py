"""
AI Service Client - Handles communication with the FastAPI AI service
"""
import httpx
from typing import Any, Dict, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

AI_SERVICE_URL = settings.AI_SERVICE_URL
AI_SERVICE_TIMEOUT = settings.AI_SERVICE_TIMEOUT


class AIServiceClient:
    """Client for communicating with the AI model service"""

    def __init__(self, base_url: str = AI_SERVICE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=AI_SERVICE_TIMEOUT)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """
        Check if AI service is healthy and responsive

        Returns:
            bool: True if service is healthy
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return False

    async def analyze_ticket(
        self,
        subject: str,
        description: str,
        tenant_id: Optional[str] = None,
        allowed_categories: Optional[list[str]] = None,
        category_team_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Send ticket to AI service for analysis

        Args:
            subject: Ticket subject/title
            description: Ticket description
            tenant_id: Optional company/tenant identifier

        Returns:
            Dict containing:
                - success: bool
                - ai_response: str (human-readable English response)
                - confidence: float
                - category: str
                - priority: str
                - is_duplicate: bool
                - similar_tickets: list
                - should_resolve: bool
                - full_analysis: dict (complete AI analysis)

        Raises:
            Exception: If AI service is unavailable or returns error
        """
        if settings.mock_mode:
            selected_category = (allowed_categories[0] if allowed_categories else "General")
            selected_team = None
            if category_team_map:
                selected_team = category_team_map.get(selected_category)
            return {
                "success": True,
                "ai_response": "Mock mode enabled. Ticket has been routed based on configured team mappings.",
                "confidence": 0.75,
                "category": selected_category,
                "priority": "medium",
                "assigned_team": selected_team,
                "is_duplicate": False,
                "similar_tickets": [],
                "should_resolve": False,
                "full_analysis": {"mode": "mock"},
            }

        try:
            payload = {
                "subject": subject,
                "description": description,
            }
            if tenant_id:
                payload["tenant_id"] = tenant_id
            if allowed_categories is not None:
                payload["allowed_categories"] = allowed_categories
            if category_team_map is not None:
                payload["category_team_map"] = category_team_map

            logger.info(f"Sending ticket to AI service: {subject[:50]}...")

            response = await self.client.post(
                f"{self.base_url}/analyze",
                json=payload
            )

            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"AI service returned error: {error_detail}")
                raise Exception(f"AI service error: {error_detail}")

            result = response.json()
            logger.info(f"AI analysis complete - Category: {result.get('category')}, "
                       f"Confidence: {result.get('confidence', 0):.2%}")

            return result

        except httpx.TimeoutException:
            logger.error("AI service request timed out")
            raise Exception("AI service timeout - please try again")
        except httpx.ConnectError:
            logger.error("Could not connect to AI service")
            raise Exception("AI service unavailable - please ensure service is running")
        except Exception as e:
            logger.error(f"AI service request failed: {e}")
            raise


# Global AI service client instance
_ai_client: Optional[AIServiceClient] = None


def get_ai_client() -> AIServiceClient:
    """Get or create AI service client instance"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIServiceClient()
    return _ai_client


async def analyze_ticket_with_ai(
    subject: str,
    description: str,
    company_id: Optional[str] = None,
    allowed_categories: Optional[list[str]] = None,
    category_team_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to analyze ticket with AI

    Args:
        subject: Ticket subject
        description: Ticket description
        company_id: Optional company identifier

    Returns:
        AI analysis result dictionary
    """
    client = get_ai_client()
    return await client.analyze_ticket(
        subject,
        description,
        tenant_id=company_id,
        allowed_categories=allowed_categories,
        category_team_map=category_team_map,
    )
