import re

SECTION_RE = re.compile(
    r"^\s*((?:section\s+)?(?:\d+(?:\.\d+)*|[A-Z])[\).:\s-]+[A-Z][^\n]{3,140})\s*$",
    re.IGNORECASE,
)


def extract_section_title(content: str | None) -> str | None:
    """Extract a likely policy/procedure section heading from chunk text."""
    if not content:
        return None

    for raw_line in content.splitlines()[:12]:
        line = re.sub(r"\s+", " ", raw_line).strip(" -\t")
        if not line or len(line) > 160:
            continue
        match = SECTION_RE.match(line)
        if match:
            return match.group(1).strip()
    return None
