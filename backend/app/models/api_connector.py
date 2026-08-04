from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIConnector(Base):
    __tablename__ = "api_connectors"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    visibility = Column(String(50), default="department", nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    method = Column(String(20), default="GET", nullable=False)
    url = Column(Text, nullable=False)
    headers = Column(JSON, default=dict, nullable=False)
    body = Column(Text, nullable=True)
    curl_command = Column(Text, nullable=True)

    status = Column(String(50), default="active", nullable=False)
    last_status_code = Column(Integer, nullable=True)
    last_response_text = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company", back_populates="api_connectors")
