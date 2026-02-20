"""
models.py – SQLAlchemy 2.0 async ORM models for the AI Helpdesk SaaS.

All tables (except companies and super_admin users) are scoped by company_id.
pgvector extension is used for storing ticket and article embeddings.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

UserRole = Enum(
    "employee", "it_staff", "company_admin", "super_admin",
    name="user_role"
)

TicketStatus = Enum(
    "new", "assigned", "in_progress", "pending", "resolved", "closed", "auto_resolved",
    name="ticket_status"
)

TicketPriority = Enum(
    "low", "medium", "high", "critical",
    name="ticket_priority"
)

TicketSource = Enum(
    "web", "chat", "email", "mobile", "glpi", "solman",
    name="ticket_source"
)

NotificationEvent = Enum(
    "ticket_created", "ticket_assigned", "ticket_resolved", "ticket_escalated",
    name="notification_event"
)


# ─────────────────────────────────────────────────────────────────────────────
# Companies
# ─────────────────────────────────────────────────────────────────────────────

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Basic"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="company")
    teams: Mapped[List["Team"]] = relationship("Team", back_populates="company")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="company")
    knowledge_articles: Mapped[List["KnowledgeArticle"]] = relationship(
        "KnowledgeArticle", back_populates="company"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(UserRole, nullable=False, default="employee")
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="offline"
    )  # online, away, offline
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("company_id", "email", name="uq_user_company_email"),
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="users")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="members")
    created_tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket", foreign_keys="Ticket.created_by", back_populates="creator"
    )
    assigned_tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket", foreign_keys="Ticket.assigned_to", back_populates="assignee_user"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Teams
# ─────────────────────────────────────────────────────────────────────────────

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_team_company_name"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="teams")
    members: Mapped[List["User"]] = relationship("User", back_populates="team")


# ─────────────────────────────────────────────────────────────────────────────
# Company Team Mappings (category → team)
# ─────────────────────────────────────────────────────────────────────────────

class CompanyTeamMapping(Base):
    __tablename__ = "company_team_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "category", name="uq_mapping_company_category"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tickets
# ─────────────────────────────────────────────────────────────────────────────

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # Human-readable ticket number (INC-XXXX format), auto-assigned via sequence
    ticket_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        TicketStatus, nullable=False, server_default="new"
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(
        TicketPriority, nullable=False, server_default="medium"
    )
    assigned_team: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(
        TicketSource, nullable=False, server_default="web"
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(768), nullable=True
    )
    suggested_article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_articles.id", ondelete="SET NULL"),
        nullable=True,
    )
    ai_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="tickets")
    creator: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_tickets"
    )
    assignee_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assigned_to], back_populates="assigned_tickets"
    )
    suggested_article: Mapped[Optional["KnowledgeArticle"]] = relationship(
        "KnowledgeArticle"
    )
    messages: Mapped[List["TicketMessage"]] = relationship(
        "TicketMessage", back_populates="ticket", order_by="TicketMessage.created_at"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Messages (conversation thread)
# ─────────────────────────────────────────────────────────────────────────────

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # author_type: user | ai | agent
    author_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")
    author: Mapped[Optional["User"]] = relationship("User")


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Articles
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(768), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company", back_populates="knowledge_articles"
    )
    author: Mapped[Optional["User"]] = relationship("User")


# ─────────────────────────────────────────────────────────────────────────────
# Notifications Config
# ─────────────────────────────────────────────────────────────────────────────

class NotificationsConfig(Base):
    __tablename__ = "notifications_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(NotificationEvent, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_recipients: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    sms_recipients: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id", "event_type", name="uq_notif_company_event"
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Audit Logs
# ─────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ─────────────────────────────────────────────────────────────────────────────
# Trend Clusters
# ─────────────────────────────────────────────────────────────────────────────

class TrendCluster(Base):
    __tablename__ = "trend_clusters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    ticket_ids: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticket_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
