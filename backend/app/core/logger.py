import logging
import sys
import re
from pathlib import Path

from app.core.probe_detection import is_suspicious_probe_path

logger = logging.getLogger("askai")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)


security_logger = logging.getLogger("askai.security")
security_logger.setLevel(logging.INFO)

if not security_logger.handlers:
    # Separate destination for probe/security events.
    security_log_path = Path("storage/security_events.log")
    security_log_path.parent.mkdir(parents=True, exist_ok=True)

    security_stream = logging.StreamHandler(sys.stdout)
    security_stream.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    security_logger.addHandler(security_stream)

    security_file = logging.FileHandler(security_log_path, encoding="utf-8")
    security_file.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    security_logger.addHandler(security_file)


class ProbeAccessFilter(logging.Filter):
    _pattern = re.compile(r'"[A-Z]+\s+([^ ]+)\s+HTTP/\d\.\d"\s+(\d{3})')
    _suppress_codes = {"401", "404", "405"}

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        match = self._pattern.search(message)
        if not match:
            return True
        path, status = match.group(1), match.group(2)
        if status in self._suppress_codes and is_suspicious_probe_path(path):
            return False
        return True


def install_access_log_probe_filter() -> None:
    access_logger = logging.getLogger("uvicorn.access")
    # Avoid duplicate filters when autoreload/import happens.
    if any(isinstance(f, ProbeAccessFilter) for f in access_logger.filters):
        return
    access_logger.addFilter(ProbeAccessFilter())
