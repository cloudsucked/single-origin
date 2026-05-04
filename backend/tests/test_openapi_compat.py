"""Unit tests for the OpenAPI 3.1 → 3.0.3 Cloudflare compatibility shim.

These exercise the small recursive transformer in ``app/openapi_compat.py``
directly, isolated from the rest of the FastAPI app, so we can pin the exact
edge cases that matter for Cloudflare API Shield Schema validation:

- The nullable ``anyOf`` collapse FastAPI / Pydantic v2 emit on every
  ``Optional[X]`` field.
- Idempotency, so a converted spec can be safely re-fed through the converter.
- The two ill-formed inputs the converter intentionally tolerates:
  ``anyOf`` with zero non-null entries, and ``type`` as a multi-non-null list
  (Single Origin does not currently emit either, but the production rollout
  agreed to log-and-continue rather than hard-fail).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.openapi_compat import (
    TARGET_OPENAPI_VERSION,
    fix_schema,
    to_cloudflare_compatible,
)


SERVER_URL = "https://api.example.test"


def _minimal_spec(schemas: dict | None = None) -> dict:
    """Build a minimal but real-looking OpenAPI 3.1 document for the converter."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "x", "version": "0"},
        "paths": {},
        "components": {"schemas": schemas or {}},
    }


# ---------------------------------------------------------------------------
# Pattern 1: nullable anyOf collapse
# ---------------------------------------------------------------------------


def test_anyof_with_one_non_null_branch_collapses_to_nullable_field() -> None:
    """The dominant FastAPI pattern: ``Optional[str]`` → anyOf[string, null]."""
    spec = _minimal_spec(
        {
            "Body": {
                "type": "object",
                "properties": {
                    "token": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "title": "Token",
                    },
                },
            }
        }
    )

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)

    token = out["components"]["schemas"]["Body"]["properties"]["token"]
    assert "anyOf" not in token, "anyOf should be flattened away"
    assert token["type"] == "string"
    assert token["nullable"] is True
    assert token["title"] == "Token", "non-anyOf siblings must survive the collapse"


def test_anyof_collapse_parent_annotation_wins_over_branch_annotation() -> None:
    """When a parent and the surviving branch carry the same annotation key,
    the parent's value must win.

    Pydantic v2 sometimes emits ``anyOf`` nodes where the parent and the
    non-null branch both carry ``title`` (the parent inherits from
    ``Field(title=...)``, the branch from the inner type). The parent is the
    authoring surface, so its value is canonical. The branch's value would
    typically be a Pydantic-generated default like the field name, which is
    less informative than what the author wrote.
    """
    spec = _minimal_spec(
        {
            "Body": {
                "properties": {
                    "x": {
                        "anyOf": [
                            {"type": "string", "title": "BranchTitle"},
                            {"type": "null"},
                        ],
                        "title": "ParentTitle",
                        "description": "parent description",
                    }
                }
            }
        }
    )

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)
    prop = out["components"]["schemas"]["Body"]["properties"]["x"]

    # Parent annotation values survived the collapse...
    assert prop["title"] == "ParentTitle"
    assert prop["description"] == "parent description"
    # ...and the branch's type information is still present.
    assert prop["type"] == "string"
    assert prop["nullable"] is True


def test_anyof_collapse_branch_keys_fill_in_what_parent_omits() -> None:
    """If the parent does not define a key, the branch's value survives.

    This is the inverse of the parent-wins case above. Type information
    (``type``, ``$ref``, ``format``) lives on the branch, never on the
    parent, so the merge must let branch keys through whenever the parent
    is silent on a key.
    """
    spec = _minimal_spec(
        {
            "Body": {
                "properties": {
                    "x": {
                        "anyOf": [
                            {"type": "string", "format": "email"},
                            {"type": "null"},
                        ],
                    }
                }
            }
        }
    )

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)
    prop = out["components"]["schemas"]["Body"]["properties"]["x"]

    assert prop["type"] == "string"
    assert prop["format"] == "email"
    assert prop["nullable"] is True


def test_anyof_without_null_keeps_anyof_intact() -> None:
    """Multi-branch anyOf without null is allowed in OAS 3.0 body schemas; leave it alone."""
    spec = _minimal_spec(
        {
            "Loc": {
                "type": "array",
                "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            }
        }
    )

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)

    items = out["components"]["schemas"]["Loc"]["items"]
    assert items == {"anyOf": [{"type": "string"}, {"type": "integer"}]}


def test_anyof_with_multi_non_null_and_null_keeps_anyof_and_marks_nullable() -> None:
    spec = _minimal_spec(
        {
            "Loc": {
                "items": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "integer"},
                        {"type": "null"},
                    ],
                }
            }
        }
    )

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)
    items = out["components"]["schemas"]["Loc"]["items"]
    assert items["anyOf"] == [{"type": "string"}, {"type": "integer"}]
    assert items["nullable"] is True


def test_anyof_with_zero_non_null_branches_logs_warning_and_passes_through(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Edge case: every branch is ``{"type": "null"}``.

    Production policy is best-effort with a logged warning so we notice
    without breaking the lab. The schema is left intact for a downstream
    validator to reject.
    """
    spec = _minimal_spec(
        {
            "Weird": {
                "properties": {
                    "x": {"anyOf": [{"type": "null"}, {"type": "null"}]},
                }
            }
        }
    )

    with caplog.at_level(logging.WARNING, logger="app.openapi_compat"):
        out = to_cloudflare_compatible(spec, server_url=SERVER_URL)

    assert any("zero non-null entries" in rec.message for rec in caplog.records)
    # anyOf is preserved unchanged so a strict validator still surfaces the error.
    assert out["components"]["schemas"]["Weird"]["properties"]["x"]["anyOf"] == [
        {"type": "null"},
        {"type": "null"},
    ]


# ---------------------------------------------------------------------------
# Pattern 2: type-as-list normalisation
# ---------------------------------------------------------------------------


def test_type_list_with_one_non_null_collapses_with_nullable() -> None:
    spec = _minimal_spec({"X": {"type": ["string", "null"]}})

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)

    schema = out["components"]["schemas"]["X"]
    assert schema["type"] == "string"
    assert schema["nullable"] is True


def test_type_list_with_multiple_non_null_takes_first_and_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    spec = _minimal_spec({"X": {"type": ["string", "integer", "null"]}})

    with caplog.at_level(logging.WARNING, logger="app.openapi_compat"):
        out = to_cloudflare_compatible(spec, server_url=SERVER_URL)

    assert any("multiple non-null types" in rec.message for rec in caplog.records)
    schema = out["components"]["schemas"]["X"]
    assert schema["type"] == "string"
    assert schema["nullable"] is True


# ---------------------------------------------------------------------------
# Document-level transformations
# ---------------------------------------------------------------------------


def test_openapi_version_is_forced_to_3_0_3() -> None:
    spec = _minimal_spec()
    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)
    assert out["openapi"] == TARGET_OPENAPI_VERSION == "3.0.3"


def test_servers_array_is_replaced_with_caller_supplied_url() -> None:
    spec = _minimal_spec()
    spec["servers"] = [{"url": "https://stale.example.test"}]

    out = to_cloudflare_compatible(spec, server_url=SERVER_URL)

    assert out["servers"] == [{"url": SERVER_URL}]


def test_input_is_not_mutated() -> None:
    spec = _minimal_spec(
        {
            "Body": {
                "properties": {
                    "x": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                }
            }
        }
    )

    to_cloudflare_compatible(spec, server_url=SERVER_URL)

    # Input still looks like an OpenAPI 3.1 document with the original anyOf
    # nullable pattern. Callers must rely on the return value, not mutation.
    assert spec["openapi"] == "3.1.0"
    assert spec["components"]["schemas"]["Body"]["properties"]["x"] == {
        "anyOf": [{"type": "string"}, {"type": "null"}]
    }


def test_idempotent() -> None:
    spec = _minimal_spec(
        {
            "Body": {
                "type": "object",
                "properties": {
                    "token": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "count": {"type": ["integer", "null"]},
                },
            }
        }
    )

    once = to_cloudflare_compatible(spec, server_url=SERVER_URL)
    twice = to_cloudflare_compatible(once, server_url=SERVER_URL)

    assert once == twice


def test_missing_openapi_key_raises() -> None:
    with pytest.raises(ValueError, match="OpenAPI document"):
        to_cloudflare_compatible({}, server_url=SERVER_URL)


def test_empty_server_url_raises() -> None:
    with pytest.raises(ValueError, match="absolute URL"):
        to_cloudflare_compatible(_minimal_spec(), server_url="")


# ---------------------------------------------------------------------------
# fix_schema directly (recursion through nested structures)
# ---------------------------------------------------------------------------


def test_fix_schema_walks_deeply_nested_structures() -> None:
    deep = {
        "type": "object",
        "properties": {
            "outer": {
                "type": "object",
                "properties": {
                    "inner": {
                        "type": "array",
                        "items": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                        },
                    }
                },
            }
        },
    }

    out = fix_schema(deep)
    inner_items = out["properties"]["outer"]["properties"]["inner"]["items"]
    assert inner_items == {"type": "string", "nullable": True}


def test_fix_schema_preserves_unrelated_lists() -> None:
    """Lists that are not OpenAPI ``type`` arrays (for example, ``required``,
    ``enum``, parameter ``name`` arrays) must be walked but not rewritten."""
    schema = {
        "type": "object",
        "required": ["a", "b"],
        "properties": {
            "a": {"type": "string", "enum": ["x", "y", "z"]},
            "b": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        },
    }

    out = fix_schema(schema)
    assert out["required"] == ["a", "b"]
    assert out["properties"]["a"]["enum"] == ["x", "y", "z"]
    assert out["properties"]["b"] == {"type": "integer", "nullable": True}
