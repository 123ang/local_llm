from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from app.core.database import Base


class EvaluationQuestion(Base):
    __tablename__ = "evaluation_questions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_keywords = Column(JSON, default=list, nullable=False)
    expected_source = Column(String(255), nullable=True)
    sources = Column(JSON, default=lambda: ["database", "documents", "faq"], nullable=False)
    ai_insights = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("evaluation_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    answer = Column(Text, nullable=False)
    sources_used = Column(JSON, nullable=True)
    missing_keywords = Column(JSON, default=list, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    model_tier = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
