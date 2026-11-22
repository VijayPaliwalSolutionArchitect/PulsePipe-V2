"""Deterministic, local event transforms.

Transforms are declared on a pipeline as an ordered list of simple string
keywords.  Each keyword describes one deterministic field operation applied in
order to the event payload.

Supported keywords:
    extract:<field>:<alias>  Copy ``payload[field]`` to ``payload[alias]``.
    drop:<field>             Remove ``payload[field]``.
    tag:<keyword>            Add ``keyword`` to ``payload["tags"]`` (creates list).
    normalize:<field>        Lowercase + strip a string field, if it is a string.
    add:<field>:<literal>    Set ``payload[field] = literal``.
    pluck:<nested.path>      Extract a dotted path to top level (alias = last segment).

Unrecognised keywords are ignored so that adding a typo'd rule never breaks
ingestion — but each applied transform is reported back to the caller.
"""

from __future__ import annotations

import copy
from typing import Any


class AppliedTransform:
    """A single transform that was applied, with a human-readable label."""

    __slots__ = ("keyword", "description")

    def __init__(self, keyword: str, description: str) -> None:
        self.keyword = keyword
        self.description = description

    def as_dict(self) -> dict[str, str]:
        """Return a serializable representation of this transform."""
        return {"keyword": self.keyword, "description": self.description}


def _dig(payload: dict, path: str) -> Any:
    """Walk a dotted path through a nested payload."""
    result: Any = payload
    for part in path.split("."):
        if not isinstance(result, dict) or part not in result:
            raise KeyError(path)
        result = result[part]
    return result


def apply_transforms(
    payload: dict[str, Any], rules: list[str]
) -> tuple[dict[str, Any], list[AppliedTransform]]:
    """Apply an ordered list of transform keywords to a payload.

    Returns ``(new_payload, applied)`` where ``applied`` records which
    keywords actually produced a change.  The input ``payload`` is never
    mutated; a deep copy is operated on instead.
    """
    out: dict[str, Any] = copy.deepcopy(dict(payload))
    applied: list[AppliedTransform] = []

    for rule in rules:
        keyword = (rule or "").strip()
        if not keyword:
            continue

        parts = keyword.split(":")
        op = parts[0].strip().lower()

        try:
            if op == "extract" and len(parts) >= 3:
                field, alias = parts[1], parts[2]
                out[alias] = _dig(payload, field)
                applied.append(
                    AppliedTransform(keyword, f"extracted {field!r} -> {alias!r}")
                )
            elif op == "drop" and len(parts) >= 2:
                field = parts[1]
                if field in out:
                    del out[field]
                    applied.append(AppliedTransform(keyword, f"dropped {field!r}"))
            elif op == "tag" and len(parts) >= 2:
                out.setdefault("tags", [])
                out["tags"].append(parts[1])
                applied.append(AppliedTransform(keyword, f"tagged {parts[1]!r}"))
            elif op == "normalize" and len(parts) >= 2:
                field = parts[1]
                if isinstance(out.get(field), str):
                    out[field] = out[field].strip().lower()
                    applied.append(
                        AppliedTransform(keyword, f"normalized {field!r}")
                    )
            elif op == "add" and len(parts) >= 3:
                field, literal = parts[1], ":".join(parts[2:])
                out[field] = literal
                applied.append(AppliedTransform(keyword, f"added {field!r}={literal!r}"))
            elif op == "pluck" and len(parts) >= 2:
                path = parts[1]
                alias = path.rsplit(".", 1)[-1]
                out[alias] = _dig(payload, path)
                applied.append(
                    AppliedTransform(keyword, f"plucked {path!r} -> {alias!r}")
                )
            # Unknown ops are silently skipped.
        except KeyError:
            # A pluck/extract referenced a missing field: skip transform.
            continue

    return out, applied