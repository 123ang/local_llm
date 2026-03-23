from __future__ import annotations

import re

# Common internet scanner targets and upload probe paths.
_PROBE_PATTERNS = [
    r"/\.env(?:$|[/?])",
    r"/\.git(?:$|[/?])",
    r"/config\.php(?:$|[/?])",
    r"/actuator/(?:env|health|info)(?:$|[/?])",
    r"/api/info(?:$|[/?])",
    r"/api/env(?:$|[/?])",
    r"/api/session/properties(?:$|[/?])",
    r"/api/(?:v1/)?totp/",
    r"\.\./\.\./",
    # Generic upload/media/avatar probing endpoints that this app does not expose.
    r"/api/(?:v1/)?(?:upwload|uploads|files/upload|files|media(?:/upload)?|images(?:/upload)?|photos|gallery/upload|attachments|content/upload|assets(?:/upload)?|products/(?:images|upload)|catalog/images|resources/upload|storage(?:/upload)?|blob(?:/upload)?)",
    r"/api/(?:v1/)?users/avatar(?:$|[/?])",
    r"/api/profile/(?:avatar|photo)(?:$|[/?])",
    r"/api/account/avatar(?:$|[/?])",
    r"/api/(?:v1/)?documents(?:/upload)?(?:$|[/?])",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _PROBE_PATTERNS]


def is_suspicious_probe_path(path: str) -> bool:
    target = path or ""
    return any(p.search(target) for p in _COMPILED)
