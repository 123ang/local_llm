from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_ai_settings import CompanyAISettings
from app.services.source_policy import DEFAULT_SOURCES, normalize_allowed_sources


async def get_or_create_company_ai_settings(db: AsyncSession, company_id: int) -> CompanyAISettings:
    result = await db.execute(select(CompanyAISettings).where(CompanyAISettings.company_id == company_id))
    settings = result.scalar_one_or_none()
    if settings:
        normalized_sources = normalize_allowed_sources(None, settings.allowed_sources)
        changed = False
        if settings.allowed_sources != normalized_sources:
            settings.allowed_sources = normalized_sources
            changed = True
        if not settings.default_source_only:
            settings.default_source_only = True
            changed = True
        if settings.ai_insights_allowed:
            settings.ai_insights_allowed = False
            changed = True
        if changed:
            await db.commit()
            await db.refresh(settings)
        return settings

    settings = CompanyAISettings(
        company_id=company_id,
        default_source_only=True,
        ai_insights_allowed=False,
        allowed_sources=DEFAULT_SOURCES,
        min_document_relevance=0.60,
        require_citations=True,
        sql_visible_to_admins_only=True,
    )
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings
