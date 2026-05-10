from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_ai_settings import CompanyAISettings

DEFAULT_SOURCES = ["database", "documents", "faq"]


async def get_or_create_company_ai_settings(db: AsyncSession, company_id: int) -> CompanyAISettings:
    result = await db.execute(select(CompanyAISettings).where(CompanyAISettings.company_id == company_id))
    settings = result.scalar_one_or_none()
    if settings:
        return settings

    settings = CompanyAISettings(
        company_id=company_id,
        default_source_only=True,
        ai_insights_allowed=True,
        allowed_sources=DEFAULT_SOURCES,
        min_document_relevance=0.60,
        require_citations=True,
        sql_visible_to_admins_only=True,
    )
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings


def normalize_allowed_sources(sources: list[str] | None, allowed_sources: list[str] | None) -> list[str]:
    allowed = set(allowed_sources or DEFAULT_SOURCES)
    requested = set(sources) if sources is not None else allowed
    active = sorted(requested & allowed & set(DEFAULT_SOURCES))
    return active
