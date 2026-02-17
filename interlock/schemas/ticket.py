"""Canonical ticket.json contract for Interlock agent/server dialog."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from interlock.fsm import State


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ValidationIssue(BaseModel):
    """Structured validation error entry."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)

    @field_validator("field", "message", "code")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value


class ValidationStatus(BaseModel):
    """Validation summary attached to each response ticket."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "valid", "invalid_fixable", "invalid_blocking"] = "pending"
    errors: list[ValidationIssue] = Field(default_factory=list)


class InvalidationReport(BaseModel):
    """Blocking failure report (fail-closed branch)."""

    model_config = ConfigDict(extra="forbid")

    state: str = Field(..., min_length=1)
    reason_code: str = Field(..., min_length=1)
    fixable: bool
    missing_or_invalid_fields: list[str] = Field(default_factory=list)
    required_next_action: str = Field(..., min_length=1)

    @field_validator("state", "reason_code", "required_next_action")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("missing_or_invalid_fields", mode="before")
    @classmethod
    def _normalize_field_list(cls, values: Any) -> Any:
        if values is None:
            return []
        return values


class HistoryEntry(BaseModel):
    """State transition or validation event persisted in ticket history."""

    model_config = ConfigDict(extra="forbid")

    ts: datetime = Field(default_factory=_utc_now)
    from_state: str | None = None
    to_state: str
    result: Literal["initialized", "advanced", "retry", "blocked", "completed"]
    reason: str = Field(..., min_length=1)

    @field_validator("to_state", "reason")
    @classmethod
    def _required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value


class Ticket(BaseModel):
    """Strict ticket.json envelope used in every agent/server round-trip."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0.0", min_length=1)
    run_id: str = Field(..., min_length=1)
    ticket_id: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    agent_role: str = Field(..., min_length=1)
    required_fields: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    next_stage_fields: list[str] = Field(default_factory=list)
    validation: ValidationStatus = Field(default_factory=ValidationStatus)
    invalidation_report: InvalidationReport | None = None
    history: list[HistoryEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @field_validator("run_id", "ticket_id", "state", "agent_role", "schema_version")
    @classmethod
    def _validate_required_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty or whitespace only")
        return value

    @field_validator("required_fields", "next_stage_fields")
    @classmethod
    def _validate_field_names(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            item = item.strip()
            if not item:
                raise ValueError("Field names cannot be empty")
            cleaned.append(item)
        return cleaned

    @field_validator("state")
    @classmethod
    def _validate_state(cls, value: str) -> str:
        valid_states = {state.value for state in State}
        if value not in valid_states:
            raise ValueError(f"Invalid state: {value}. Must be one of {sorted(valid_states)}")
        return value

    def to_json(self, *, pretty: bool = False) -> str:
        """Serialize ticket to JSON for exchange over MCP."""
        if pretty:
            return json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2)
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Ticket":
        """Parse and validate ticket JSON string."""
        data = json.loads(json_str)
        return cls(**data)
