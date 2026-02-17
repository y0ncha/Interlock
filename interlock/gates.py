"""Validation gates for strict stage-by-stage ticket submission."""

from __future__ import annotations

from pydantic import ValidationError

from interlock.fsm import State
from interlock.schemas.responses import GateResult
from interlock.schemas.stage_payloads import STAGE_PAYLOAD_MODELS
from interlock.schemas.ticket import Ticket, ValidationIssue


class Gate:
    """Base interface for stage validators."""

    def validate(self, ticket: Ticket) -> GateResult:  # pragma: no cover - interface
        raise NotImplementedError


def _issues_from_validation_error(exc: ValidationError) -> list[ValidationIssue]:
    """Normalize pydantic errors into deterministic issue ordering."""
    issues: list[ValidationIssue] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()))
        issues.append(
            ValidationIssue(
                field=loc or "payload",
                message=err.get("msg", "Invalid value"),
                code=err.get("type", "value_error"),
            )
        )
    issues.sort(key=lambda issue: (issue.field, issue.code, issue.message))
    return issues


class StagePayloadGate(Gate):
    """Validate ticket.payload against the rigid schema for current state."""

    def validate(self, ticket: Ticket) -> GateResult:
        state = State(ticket.state)

        if state in {State.COMPLETE, State.FAIL_CLOSED}:
            return GateResult(
                status="stop",
                reasons=[f"State '{state.value}' is terminal"],
            )

        payload_model = STAGE_PAYLOAD_MODELS.get(state)
        if payload_model is None:
            return GateResult(
                status="stop",
                reasons=[f"No payload schema is registered for state '{state.value}'"],
            )

        try:
            payload_model(**ticket.payload)
        except ValidationError as exc:
            issues = _issues_from_validation_error(exc)
            fields = sorted({issue.field for issue in issues})
            return GateResult(
                status="retry",
                reasons=[f"Payload validation failed for state '{state.value}'"],
                fixes=["Populate all required fields with non-empty values and resubmit ticket.json"],
                missing_or_invalid_fields=fields,
                issues=issues,
            )

        return GateResult(
            status="pass",
            reasons=[f"Payload schema validation passed for '{state.value}'"],
        )


def get_gate_for_state(state: str) -> Gate:
    """Return gate for a state. Current PoC uses one rigid gate for all stages."""
    # Gate behavior depends on ticket.state internally and terminal handling is explicit.
    _ = state
    return StagePayloadGate()
