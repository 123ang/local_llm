from collections import defaultdict
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import AuditLog
from app.models.api_connector import APIConnector
from app.models.chat import ChatSession
from app.models.company import Company
from app.models.company_ai_settings import CompanyAISettings
from app.models.dataset import Dataset
from app.models.department import Department
from app.models.document import Document
from app.models.evaluation import EvaluationQuestion
from app.models.faq import FAQItem
from app.models.user import User


RESOURCE_KIND_LABELS = {
    "api_connector": "API Connector",
    "chat": "Chat Session",
    "company": "Organization",
    "company_ai_settings": "Organization AI Settings",
    "dataset": "Dataset",
    "department": "Department",
    "document": "Document",
    "evaluation_question": "Evaluation Question",
    "faq": "FAQ",
    "organization": "Organization",
    "user": "User",
}


def _shorten(value: str | None, limit: int = 80) -> str | None:
    if not value:
        return None
    compact = " ".join(value.split())
    return compact if len(compact) <= limit else f"{compact[: limit - 1]}..."


def _resource_kind_label(resource_type: str | None) -> str | None:
    if not resource_type:
        return None
    return RESOURCE_KIND_LABELS.get(resource_type, resource_type.replace("_", " ").title())


def _user_label(user: object | None) -> str | None:
    if not user:
        return None
    name = getattr(user, "full_name", None)
    email = getattr(user, "email", None)
    if name and email:
        return f"{name} ({email})"
    return name or email


def _unavailable_resource_label(resource_type: str | None, resource_id: int | None) -> str | None:
    kind = _resource_kind_label(resource_type)
    if not kind:
        return None
    if resource_id is None:
        return kind
    return f"Unavailable {kind.lower()} (ID {resource_id})"


def serialize_audit_log(
    entry: AuditLog,
    *,
    users: dict[int, User],
    companies: dict[int, Company],
    resource_labels: dict[tuple[str, int], str],
) -> dict:
    user = users.get(entry.user_id) if entry.user_id is not None else None
    company = companies.get(entry.company_id) if entry.company_id is not None else None
    if company is None and entry.resource_type in ("company", "organization") and entry.resource_id is not None:
        company = companies.get(entry.resource_id)
    resource_label = None
    if entry.resource_type and entry.resource_id is not None:
        resource_label = resource_labels.get((entry.resource_type, entry.resource_id))

    return {
        "id": entry.id,
        "company_id": entry.company_id,
        "company_name": company.name if company else None,
        "organization_name": company.name if company else None,
        "user_id": entry.user_id,
        "user_name": getattr(user, "full_name", None) if user else None,
        "user_email": getattr(user, "email", None) if user else None,
        "actor_label": _user_label(user) or "System",
        "action": entry.action,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id,
        "resource_kind_label": _resource_kind_label(entry.resource_type),
        "resource_label": resource_label or _unavailable_resource_label(entry.resource_type, entry.resource_id),
        "details": entry.details,
        "ip_address": entry.ip_address,
        "created_at": entry.created_at,
    }


async def _load_by_ids(db: AsyncSession, model: type, ids: set[int]) -> dict[int, object]:
    clean_ids = {int(item) for item in ids if item is not None}
    if not clean_ids:
        return {}
    result = await db.execute(select(model).where(model.id.in_(clean_ids)))
    return {item.id: item for item in result.scalars().all()}


def _add_resource_labels(
    labels: dict[tuple[str, int], str],
    resource_type: str,
    items: dict[int, object],
    formatter: Callable[[object], str | None],
) -> None:
    for item_id, item in items.items():
        label = formatter(item)
        if label:
            labels[(resource_type, item_id)] = label


async def _build_audit_display_maps(
    db: AsyncSession,
    entries: list[AuditLog],
) -> tuple[dict[int, User], dict[int, Company], dict[tuple[str, int], str]]:
    resource_ids: dict[str, set[int]] = defaultdict(set)
    user_ids = {entry.user_id for entry in entries if entry.user_id is not None}
    company_ids = {entry.company_id for entry in entries if entry.company_id is not None}

    for entry in entries:
        if entry.resource_type and entry.resource_id is not None:
            resource_ids[entry.resource_type].add(entry.resource_id)

    user_ids.update(resource_ids.get("user", set()))
    company_ids.update(resource_ids.get("company", set()))
    company_ids.update(resource_ids.get("organization", set()))

    users = await _load_by_ids(db, User, user_ids)
    companies = await _load_by_ids(db, Company, company_ids)
    resource_labels: dict[tuple[str, int], str] = {}

    _add_resource_labels(resource_labels, "user", users, _user_label)
    _add_resource_labels(resource_labels, "company", companies, lambda company: getattr(company, "name", None))
    _add_resource_labels(resource_labels, "organization", companies, lambda company: getattr(company, "name", None))

    departments = await _load_by_ids(db, Department, resource_ids.get("department", set()))
    documents = await _load_by_ids(db, Document, resource_ids.get("document", set()))
    faqs = await _load_by_ids(db, FAQItem, resource_ids.get("faq", set()))
    datasets = await _load_by_ids(db, Dataset, resource_ids.get("dataset", set()))
    api_connectors = await _load_by_ids(db, APIConnector, resource_ids.get("api_connector", set()))
    evaluation_questions = await _load_by_ids(db, EvaluationQuestion, resource_ids.get("evaluation_question", set()))
    chat_sessions = await _load_by_ids(db, ChatSession, resource_ids.get("chat", set()))
    company_ai_settings = await _load_by_ids(db, CompanyAISettings, resource_ids.get("company_ai_settings", set()))

    _add_resource_labels(resource_labels, "department", departments, lambda dept: getattr(dept, "name", None))
    _add_resource_labels(resource_labels, "document", documents, lambda doc: getattr(doc, "original_name", None))
    _add_resource_labels(resource_labels, "faq", faqs, lambda faq: _shorten(getattr(faq, "question", None)))
    _add_resource_labels(resource_labels, "dataset", datasets, lambda dataset: getattr(dataset, "display_name", None))
    _add_resource_labels(resource_labels, "api_connector", api_connectors, lambda connector: getattr(connector, "name", None))
    _add_resource_labels(
        resource_labels,
        "evaluation_question",
        evaluation_questions,
        lambda question: _shorten(getattr(question, "question", None)),
    )
    _add_resource_labels(resource_labels, "chat", chat_sessions, lambda session: getattr(session, "title", None) or "Chat session")
    _add_resource_labels(resource_labels, "company_ai_settings", company_ai_settings, lambda _: "Organization AI settings")

    return users, companies, resource_labels

async def log_action(db: AsyncSession, action: str, user_id: int | None = None, company_id: int | None = None,
                     resource_type: str | None = None, resource_id: int | None = None,
                     details: dict | None = None, ip_address: str | None = None):
    entry = AuditLog(
        action=action, user_id=user_id, company_id=company_id,
        resource_type=resource_type, resource_id=resource_id,
        details=details, ip_address=ip_address,
    )
    db.add(entry)
    await db.commit()

async def get_audit_logs(db: AsyncSession, company_id: int | None = None, limit: int = 100, offset: int = 0) -> list:
    query = select(AuditLog)
    if company_id:
        query = query.where(AuditLog.company_id == company_id)
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    entries = list(result.scalars().all())
    users, companies, resource_labels = await _build_audit_display_maps(db, entries)
    return [
        serialize_audit_log(entry, users=users, companies=companies, resource_labels=resource_labels)
        for entry in entries
    ]
