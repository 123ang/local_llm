from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CompanyAISettings(Base):
    __tablename__ = "company_ai_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Default is strict/source-bound for enterprise trust.
    default_source_only = Column(Boolean, default=True, nullable=False)
    ai_insights_allowed = Column(Boolean, default=True, nullable=False)
    allowed_sources = Column(JSON, default=lambda: ["database", "documents", "faq"], nullable=False)
    min_document_relevance = Column(Float, default=0.60, nullable=False)
    require_citations = Column(Boolean, default=True, nullable=False)
    sql_visible_to_admins_only = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company", back_populates="ai_settings")
