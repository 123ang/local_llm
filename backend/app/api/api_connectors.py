from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    ensure_company_access,
    ensure_department_access,
    require_knowledge_admin,
    resolve_department_scope,
)
from app.core.security import get_current_user
from app.models.api_connector import APIConnector
from app.models.user import User
from app.schemas.api_connector import APIConnectorCreate, APIConnectorOut, APIConnectorUpdate
from app.services.api_connector_service import APIConnectorError, apply_curl_to_payload, fetch_api_connector, validate_connector_config
from app.services.audit_service import log_action

router = APIRouter(prefix="/api-connectors", tags=["api-connectors"])


@router.get("/{company_id}", response_model=list[APIConnectorOut])
async def list_api_connectors(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    department_ids = await resolve_department_scope(db, current_user, company_id)
    if not department_ids:
        return []
    result = await db.execute(
        select(APIConnector)
        .where(APIConnector.company_id == company_id, APIConnector.department_id.in_(department_ids))
        .order_by(APIConnector.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{company_id}", response_model=APIConnectorOut, status_code=201)
async def create_api_connector(
    company_id: int,
    data: APIConnectorCreate,
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    ensure_company_access(current_user, company_id)
    await ensure_department_access(db, current_user, company_id, data.department_id)
    try:
        apply_curl_to_payload(data)
        validate_connector_config(data.method, data.url)
    except APIConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connector = APIConnector(
        company_id=company_id,
        department_id=data.department_id,
        visibility=data.visibility,
        name=data.name,
        description=data.description,
        method=data.method,
        url=data.url,
        headers=data.headers,
        body=data.body,
        curl_command=data.curl_command,
        created_by=current_user.id,
    )
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    await log_action(
        db,
        action="create_api_connector",
        user_id=current_user.id,
        company_id=company_id,
        resource_type="api_connector",
        resource_id=connector.id,
    )
    return connector


@router.patch("/{company_id}/{connector_id}", response_model=APIConnectorOut)
async def update_api_connector(
    company_id: int,
    connector_id: int,
    data: APIConnectorUpdate,
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    connector = await _get_editable_connector(db, company_id, connector_id, current_user)
    updates = data.model_dump(exclude_unset=True)
    if "department_id" in updates and updates["department_id"] != connector.department_id:
        await ensure_department_access(db, current_user, company_id, updates["department_id"])
    if updates.get("curl_command"):
        try:
            apply_curl_to_payload(data)
            validate_connector_config(data.method, data.url)
        except APIConnectorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        updates.update(
            method=data.method,
            url=data.url,
            headers=data.headers,
            body=data.body,
        )
    elif "method" in updates or "url" in updates:
        try:
            validate_connector_config(updates.get("method") or connector.method, updates.get("url") or connector.url)
        except APIConnectorError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    for key, value in updates.items():
        setattr(connector, key, value)
    await db.commit()
    await db.refresh(connector)
    return connector


@router.post("/{company_id}/{connector_id}/sync", response_model=APIConnectorOut)
async def sync_api_connector(
    company_id: int,
    connector_id: int,
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    connector = await _get_editable_connector(db, company_id, connector_id, current_user)
    try:
        status_code, response_text = await fetch_api_connector(connector)
        connector.last_status_code = status_code
        connector.last_response_text = response_text
        connector.last_error = None
        connector.status = "active"
    except Exception as exc:
        connector.last_error = str(exc)[:1000]
        connector.status = "error"
    connector.last_synced_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(connector)
    await log_action(
        db,
        action="sync_api_connector",
        user_id=current_user.id,
        company_id=company_id,
        resource_type="api_connector",
        resource_id=connector.id,
        details={"status": connector.status, "http_status": connector.last_status_code},
    )
    return connector


@router.delete("/{company_id}/{connector_id}", status_code=204)
async def delete_api_connector(
    company_id: int,
    connector_id: int,
    current_user: User = Depends(require_knowledge_admin),
    db: AsyncSession = Depends(get_db),
):
    connector = await _get_editable_connector(db, company_id, connector_id, current_user)
    await db.delete(connector)
    await db.commit()


async def _get_editable_connector(
    db: AsyncSession,
    company_id: int,
    connector_id: int,
    current_user: User,
) -> APIConnector:
    ensure_company_access(current_user, company_id)
    result = await db.execute(
        select(APIConnector).where(APIConnector.id == connector_id, APIConnector.company_id == company_id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="API connector not found")
    await ensure_department_access(db, current_user, company_id, connector.department_id)
    return connector
