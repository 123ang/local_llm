import re
import uuid


CORRELATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def correlation_id_from_request(request) -> str:
    state = getattr(request, "state", None)
    existing = getattr(state, "correlation_id", None) if state else None
    if existing and CORRELATION_ID_RE.fullmatch(str(existing)):
        return str(existing)

    correlation_id = str(uuid.uuid4())
    if state is not None:
        state.correlation_id = correlation_id
    return correlation_id


def public_error_detail(request, message: str, error: Exception | None = None) -> dict[str, str]:
    return {
        "message": message,
        "correlation_id": correlation_id_from_request(request),
    }
