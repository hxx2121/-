from __future__ import annotations

from typing import Any


def render_template(text: str, variables: dict[str, Any]) -> str:
    out = text or ""
    for k, v in (variables or {}).items():
        out = out.replace("{{" + str(k) + "}}", "" if v is None else str(v))
    return out

