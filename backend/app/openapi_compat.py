"""
Convert the FastAPI-emitted OpenAPI 3.1 document into a 3.0.3 document that
Cloudflare API Shield Schema validation accepts.

Cloudflare's Schema validation only accepts OpenAPI v3.0.x and rejects three
patterns that FastAPI + Pydantic v2 produces by default:

1. Nullable parameters expressed as ``{"anyOf": [{"type": "X"}, {"type": "null"}]}``.
   Cloudflare rejects these with ``code: 40028, invalid or missing parameter type``
   and does not support ``anyOf`` inside parameter schemas
   (see https://developers.cloudflare.com/api-shield/security/schema-validation/).
2. ``openapi: 3.1.0`` document version. Cloudflare only accepts 3.0.x.
3. Missing root-level ``servers`` array. Without an absolute server URL,
   Cloudflare returns ``code: 50015, failed to construct endpoint URLs``.

This module is the single source of truth for the conversion. ``app.main``
calls :func:`to_cloudflare_compatible` from a custom ``app.openapi()`` so the
Worker's ``/openapi.json`` endpoint and the committed
``docs/openapi/single-origin.openapi.json`` artifact are always in sync with
the Cloudflare contract.

Edge-case handling matches the policy chosen for production rollout: best
effort with a logged warning so the lab does not break if Pydantic ever
emits a pattern we have not seen before. The transformation is deterministic
and idempotent.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Cloudflare API Shield only accepts the 3.0 line. We emit 3.0.3 specifically
# because it is the most permissive 3.0.x patch that the validator accepts.
TARGET_OPENAPI_VERSION = "3.0.3"


def fix_schema(node: Any, *, _path: str = "$") -> Any:
    """Recursively normalise OpenAPI 3.1 nullable patterns into 3.0-compatible ones.

    Two patterns are handled:

    - ``anyOf`` containing a ``{"type": "null"}`` entry → drop the null entry,
      collapse a single remaining branch into the parent, set ``nullable: true``.
    - ``type`` as a list (3.1 style) → take the first non-null type, set
      ``nullable: true`` if ``null`` was in the list. Multi-type lists with
      more than one non-null entry are not representable in OAS 3.0 and are
      logged so an author notices, but the spec is left walkable.

    Other nodes are walked recursively but otherwise untouched. ``_path`` is
    a JSONPath-ish breadcrumb used solely for warnings; callers should leave
    it at the default.
    """
    if isinstance(node, dict):
        # Pattern 1: anyOf with a {"type": "null"} entry.
        if "anyOf" in node and isinstance(node["anyOf"], list):
            non_null = [
                s
                for s in node["anyOf"]
                if not (isinstance(s, dict) and s.get("type") == "null")
            ]
            had_null = len(non_null) < len(node["anyOf"])

            if len(non_null) == 0:
                # Every branch was {"type": "null"}. The schema is meaningless
                # in OAS 3.0; leave anyOf intact so a downstream validator
                # surfaces the error, but warn so we notice.
                logger.warning(
                    "openapi_compat: %s anyOf has zero non-null entries; "
                    "leaving as-is (will likely fail Cloudflare validation)",
                    _path,
                )
            elif len(non_null) == 1:
                # Collapse the single remaining branch into the parent.
                merged = {k: v for k, v in node.items() if k != "anyOf"}
                merged.update(non_null[0])
                if had_null:
                    merged["nullable"] = True
                return fix_schema(merged, _path=_path)
            else:
                # Multiple non-null branches. OAS 3.0 supports anyOf at the
                # schema level (just not inside parameter schemas, but we do
                # not know context here). Drop the null branch and keep anyOf.
                node = {**node, "anyOf": non_null}
                if had_null:
                    node["nullable"] = True

        # Pattern 2: type as a list (e.g. ["string", "null"]).
        if "type" in node and isinstance(node["type"], list):
            non_null_types = [t for t in node["type"] if t != "null"]
            had_null = len(non_null_types) < len(node["type"])
            if len(non_null_types) == 0:
                logger.warning(
                    "openapi_compat: %s type list has zero non-null entries; "
                    "leaving as-is",
                    _path,
                )
            elif len(non_null_types) == 1:
                node = {**node, "type": non_null_types[0]}
                if had_null:
                    node["nullable"] = True
            else:
                # Multi-type lists are an OAS 3.1 feature (e.g. ["string",
                # "integer"]). OAS 3.0 cannot express this directly. Take the
                # first non-null type and warn so authors notice the lossy
                # conversion. Single Origin does not currently emit this
                # pattern.
                logger.warning(
                    "openapi_compat: %s type=%r has multiple non-null types; "
                    "downgrading to %r for OAS 3.0",
                    _path,
                    node["type"],
                    non_null_types[0],
                )
                node = {**node, "type": non_null_types[0]}
                if had_null:
                    node["nullable"] = True

        return {k: fix_schema(v, _path=f"{_path}.{k}") for k, v in node.items()}

    if isinstance(node, list):
        return [fix_schema(item, _path=f"{_path}[{i}]") for i, item in enumerate(node)]

    return node


def to_cloudflare_compatible(spec: dict, server_url: str) -> dict:
    """Apply both Cloudflare-compatibility transformations to an OpenAPI document.

    The transformation is idempotent — running it on an already-converted
    spec produces the same output.

    Parameters
    ----------
    spec:
        The OpenAPI document as produced by ``fastapi.openapi.utils.get_openapi``.
        Must contain an ``openapi`` key.
    server_url:
        Absolute URL to write into the root-level ``servers`` array. Replaces
        any existing ``servers`` entry. Cloudflare requires an absolute URL
        and does not accept relative paths.

    Returns
    -------
    dict
        A new document. The input is not mutated.
    """
    if "openapi" not in spec:
        raise ValueError("input does not look like an OpenAPI document (missing 'openapi' key)")
    if not server_url:
        raise ValueError("server_url is required and must be an absolute URL")

    out = fix_schema(spec)
    out["openapi"] = TARGET_OPENAPI_VERSION
    out["servers"] = [{"url": server_url}]
    return out
