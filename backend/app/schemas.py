"""
schemas.py – Pydantic v2 request/response schemas.

Field names match the frontend's expected data shapes exactly.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Common
# ─────────────────────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    company_id: Optional[uuid.UUID] = None
    company_name: Optional[str] = None
    company_slug: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    avatar_url: Optional[str] = None
    status: str = "offline"
    department: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Companies
# ─────────────────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    plan_tier: str = Field(default="Basic")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_name: str = Field(..., min_length=2)


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan_tier: str
    status: str
    created_at: datetime
    # Computed stats (populated separately)
    total_users: Optional[int] = 0
    total_tickets: Optional[int] = 0
    admin_email: Optional[str] = None

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    companies: List[CompanyOut]
    total: int
    page: int
    limit: int


# ─────────────────────────────────────────────────────────────────────────────
# Teams
# ─────────────────────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    email: Optional[EmailStr] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    email: Optional[EmailStr] = None


class TeamOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    member_count: Optional[int] = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamAssignAgentRequest(BaseModel):
    agent_id: uuid.UUID


class TeamRemoveAgentRequest(BaseModel):
    agent_id: uuid.UUID


# ─────────────────────────────────────────────────────────────────────────────
# Category Mappings
# ─────────────────────────────────────────────────────────────────────────────

class MappingItem(BaseModel):
    category: str
    team_name: str


class MappingBulkSave(BaseModel):
    mappings: List[MappingItem]


class MappingOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    category: str
    team_name: str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Tickets
# ─────────────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10)
    priority: str = Field(default="medium")
    source: str = Field(default="web")
    department: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        # Map "urgent" → "critical" for frontend compatibility
        mapping = {"urgent": "critical", "low": "low", "medium": "medium", "high": "high", "critical": "critical"}
        return mapping.get(v.lower(), "medium")


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_team: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None


class TicketAssign(BaseModel):
    assigned_team: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None


class AuthorOut(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    avatar_url: Optional[str] = None
    type: str = "user"  # user | ai | agent
    badge: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    author: AuthorOut
    content: str
    is_internal: bool
    created_at: datetime
    timestamp: str = ""  # human-readable, populated in route

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class SimilarArticleOut(BaseModel):
    id: uuid.UUID
    title: str
    tag: str = ""
    summary: str = ""
    similarity: Optional[float] = None

    model_config = {"from_attributes": True}


class AssignedTeamOut(BaseModel):
    name: str
    tier: str = "Tier 1 Support"


class AISuggestionOut(BaseModel):
    text: str
    confidence: int = 0


class TicketOut(BaseModel):
    """Full ticket detail — used by GET /tickets/:id"""
    id: uuid.UUID
    ticket_number: Optional[str] = None
    title: str
    description: str
    status: str
    priority: str
    category: Optional[str] = None
    source: str
    department: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    reported_at: str = ""  # human-readable relative time

    # People
    reporter: Optional[AuthorOut] = None
    assignee: Optional[AuthorOut] = None
    assigned_team: Optional[str] = None
    assigned_team_detail: Optional[AssignedTeamOut] = None

    # AI
    ai_response: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_predicted_category: Optional[str] = None
    ai_suggested_priority: Optional[str] = None
    is_ai_duplicate: Optional[bool] = None
    ai_suggestion: Optional[AISuggestionOut] = None

    # Nested
    messages: List[MessageOut] = []
    similar_articles: List[SimilarArticleOut] = []

    model_config = {"from_attributes": True}


class TicketListItem(BaseModel):
    """Compact ticket — used by list endpoints"""
    id: uuid.UUID
    ticket_number: Optional[str] = None
    title: str
    description: str
    status: str
    priority: str
    category: Optional[str] = None
    source: str
    department: Optional[str] = None
    assigned_team: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    assignee_name: Optional[str] = None
    created_by: uuid.UUID
    creator_name: Optional[str] = None
    has_ai_insight: bool = False
    ai_confidence: Optional[float] = None
    ai_predicted_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reported_at: str = ""

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    tickets: List[TicketListItem]
    total: int
    page: int
    limit: int


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Articles
# ─────────────────────────────────────────────────────────────────────────────

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    content: str = Field(..., min_length=10)
    category: Optional[str] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    content: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = None


class ArticleAuthorOut(BaseModel):
    name: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    content: str
    category: Optional[str] = None
    view_count: int
    author: Optional[ArticleAuthorOut] = None
    updated_at: datetime
    created_at: datetime
    updated_label: str = ""  # e.g. "Updated 2d ago"

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    articles: List[ArticleOut]
    total: int
    page: int
    limit: int


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

class AnalyticsOverview(BaseModel):
    total_tickets_7d: int
    total_tickets_change: str
    avg_resolution_time: str
    avg_resolution_change: str
    sla_compliance: float
    sla_compliance_change: str
    active_tickets: int
    active_tickets_change: str
    user_satisfaction: float
    user_satisfaction_change: str
    ai_resolution_rate: float


class VolumeDataPoint(BaseModel):
    date: str
    count: int


class VolumeResponse(BaseModel):
    labels: List[str]
    values: List[int]
    period: str


class CategoryDataPoint(BaseModel):
    label: str
    count: int
    percentage: float


class CategoryResponse(BaseModel):
    total: int
    categories: List[CategoryDataPoint]


class TeamPerformanceItem(BaseModel):
    team_name: str
    avg_resolution_hours: float
    total_tickets: int
    resolved_tickets: int


class TrendOut(BaseModel):
    id: uuid.UUID
    summary: Optional[str] = None
    category: Optional[str] = None
    ticket_count: int
    ticket_ids: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Super Admin Analytics
# ─────────────────────────────────────────────────────────────────────────────

class SuperAdminStats(BaseModel):
    total_companies: int
    total_companies_change: str
    total_users: int
    total_users_change: str
    processed_tickets: int
    processed_tickets_change: str
    ai_resolution_rate: float


class CompanyVolumeItem(BaseModel):
    company_name: str
    color: str
    values: List[int]


class SuperAdminVolumeResponse(BaseModel):
    period: str
    labels: List[str]
    companies: List[CompanyVolumeItem]


# ─────────────────────────────────────────────────────────────────────────────
# Notifications Config
# ─────────────────────────────────────────────────────────────────────────────

class NotificationsConfigOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    event_type: str
    email_enabled: bool
    sms_enabled: bool
    email_recipients: List[str]
    sms_recipients: List[str]

    model_config = {"from_attributes": True}


class NotificationsConfigUpdate(BaseModel):
    event_type: str
    email_enabled: bool = True
    sms_enabled: bool = False
    email_recipients: List[str] = []
    sms_recipients: List[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Agents (IT staff users managed by company admin)
# ─────────────────────────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=8)
    role: str = Field(default="it_staff")
    team_id: Optional[uuid.UUID] = None
    department: Optional[str] = None


class AgentUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    department: Optional[str] = None


class AgentOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    avatar_url: Optional[str] = None
    role: str
    status: str
    assigned_tickets: int = 0
    performance: int = 0
    team_id: Optional[uuid.UUID] = None
    team_name: Optional[str] = None

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: List[AgentOut]
    total: int
    page: int
    limit: int


# ─────────────────────────────────────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    ticket_id: Optional[uuid.UUID] = None
    conversation_history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None  # "ticket_creation" | "knowledge_search" | "general"
    ticket_created: Optional[TicketListItem] = None
    suggested_articles: List[SimilarArticleOut] = []


# ─────────────────────────────────────────────────────────────────────────────
# Employee Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeStats(BaseModel):
    open_tickets: int
    resolved: int
    avg_response_time: str
    avg_response_change: str


# ─────────────────────────────────────────────────────────────────────────────
# IT Staff Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class ITStaffStats(BaseModel):
    open: int
    pending: int
    urgent: int
    resolved: int
