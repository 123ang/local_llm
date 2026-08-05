from typing import Any


def build_chat_audit_details(
    *,
    session_id: int,
    question: str,
    answer: str,
    sources: dict[str, Any] | None,
    response_time_ms: int,
    model_tier: str | None,
) -> dict[str, Any]:
    source_payload = sources or {}
    meta = source_payload.get("_meta") if isinstance(source_payload.get("_meta"), dict) else {}
    return {
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "sources": source_payload,
        "response_time_ms": response_time_ms,
        "model_tier": model_tier,
        "source_mode": "source_only",
        "used_general_knowledge": False,
        "refused": "could not find" in (answer or "").lower()
        or "couldn't find" in (answer or "").lower(),
        "meta": meta,
    }
