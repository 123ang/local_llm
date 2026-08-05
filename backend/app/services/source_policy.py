from collections.abc import Iterable

DEFAULT_SOURCES = ["documents", "faq"]
PHASE1_SOURCE_SET = set(DEFAULT_SOURCES)


def normalize_allowed_sources(
    sources: list[str] | None,
    allowed_sources: list[str] | None,
) -> list[str]:
    """Clamp chat sources to the SME Phase 1 knowledge scope."""
    allowed = set(allowed_sources or DEFAULT_SOURCES) & PHASE1_SOURCE_SET
    if sources is None:
        return [source for source in DEFAULT_SOURCES if source in allowed]

    requested = set(sources)
    return [source for source in DEFAULT_SOURCES if source in requested and source in allowed]


def source_only_refusal(active_sources: Iterable[str]) -> str:
    selected = ", ".join(source for source in DEFAULT_SOURCES if source in set(active_sources))
    selected = selected or "approved policy documents and FAQ"
    return (
        f"Techpedia AI Assistant could not find that in the selected sources ({selected}).\n\n"
        "Source-only mode is enabled for SME Phase 1, so answers must come from approved policy documents "
        "or published FAQ entries. Please refine the question or upload the approved policy/procedure reference."
    )
