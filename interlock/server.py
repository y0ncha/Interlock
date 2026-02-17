"""Interlock MCP server: begin/submit ticket.json lifecycle with rigid FSM + schemas."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastmcp import FastMCP
from pydantic import ValidationError

from interlock.fsm import (
    AGENT_ROLE_BAD_INPUT,
    State,
    get_agent_role,
    get_next_stage_fields,
    get_required_fields,
    is_terminal,
    transition,
)
from interlock.gates import get_gate_for_state
from interlock.schemas.ticket import HistoryEntry, InvalidationReport, Ticket, ValidationIssue, ValidationStatus
from interlock.storage import ArtifactStore

SCHEMA_VERSION = "1.0.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Interlock",
    instructions=(
        "Deterministic MCP server for ticket lifecycle governance. "
        "Use interlock_begin_run once, then submit updated ticket.json via interlock_submit_ticket."
    ),
)
store = ArtifactStore()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _response(
    *,
    updated_ticket: Ticket | None,
    continue_: bool,
    reason: str,
    next_role: str,
    next_state: str | None,
    gate_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard response envelope for MCP tools."""
    return {
        "updated_ticket": updated_ticket.model_dump(mode="json") if updated_ticket else None,
        "ticket_json": updated_ticket.to_json(pretty=True) if updated_ticket else None,
        "continue": continue_,
        "reason": reason,
        "next_role": next_role,
        "next_state": next_state,
        "gate_result": gate_result,
    }


def _append_history(ticket: Ticket, entry: HistoryEntry) -> list[HistoryEntry]:
    return [*ticket.history, entry]


def _ticket_with_server_contract(ticket: Ticket, state: State) -> Ticket:
    """Server is source of truth for role/required/next fields."""
    return ticket.model_copy(
        update={
            "state": state.value,
            "agent_role": get_agent_role(state),
            "required_fields": get_required_fields(state),
            "next_stage_fields": get_next_stage_fields(state),
            "updated_at": _utc_now(),
        }
    )


def create_initial_ticket(ticket_id: str, run_id: str | None = None) -> Ticket:
    """Create a clean ticket.json for the initial FETCH_TICKET state."""
    run_id_value = (run_id or f"run_{uuid4().hex}").strip()
    ticket_id_value = ticket_id.strip()
    if not run_id_value:
        raise ValueError("run_id must not be empty")
    if not ticket_id_value:
        raise ValueError("ticket_id must not be empty")

    state = State.FETCH_TICKET
    ticket = Ticket(
        schema_version=SCHEMA_VERSION,
        run_id=run_id_value,
        ticket_id=ticket_id_value,
        state=state.value,
        agent_role=get_agent_role(state),
        required_fields=get_required_fields(state),
        payload={},
        next_stage_fields=get_next_stage_fields(state),
        validation=ValidationStatus(status="pending", errors=[]),
        invalidation_report=None,
        history=[
            HistoryEntry(
                from_state=None,
                to_state=state.value,
                result="initialized",
                reason="Initial ticket.json issued by server",
            )
        ],
    )
    store.save_ticket(ticket)
    store.save_event(
        run_id=ticket.run_id,
        event_type="begin",
        state=ticket.state,
        details={"ticket_id": ticket.ticket_id},
    )
    return ticket


def _fail_closed(ticket: Ticket, *, reason_code: str, message: str, fields: list[str]) -> Ticket:
    """Move ticket to fail_closed with blocking invalidation report."""
    report = InvalidationReport(
        state=ticket.state,
        reason_code=reason_code,
        fixable=False,
        missing_or_invalid_fields=fields,
        required_next_action=message,
    )
    issue = ValidationIssue(
        field=fields[0] if fields else "payload",
        code=reason_code,
        message=message,
    )
    blocked = ticket.model_copy(
        update={
            "state": State.FAIL_CLOSED.value,
            "agent_role": get_agent_role(State.FAIL_CLOSED),
            "required_fields": [],
            "next_stage_fields": [],
            "validation": ValidationStatus(status="invalid_blocking", errors=[issue]),
            "invalidation_report": report,
            "updated_at": _utc_now(),
        }
    )
    blocked = blocked.model_copy(
        update={
            "history": _append_history(
                blocked,
                HistoryEntry(
                    from_state=ticket.state,
                    to_state=State.FAIL_CLOSED.value,
                    result="blocked",
                    reason=message,
                ),
            )
        }
    )
    store.save_ticket(blocked)
    store.save_event(
        run_id=blocked.run_id,
        event_type="fail_closed",
        state=blocked.state,
        details={"reason_code": reason_code, "fields": fields},
    )
    return blocked


def submit_ticket_json(ticket_json: str) -> dict[str, Any]:
    """Validate + transition ticket.json according to rigid state contract."""
    try:
        ticket = Ticket.from_json(ticket_json)
    except json.JSONDecodeError as exc:
        return _response(
            updated_ticket=None,
            continue_=False,
            reason=f"Invalid JSON: {exc}",
            next_role=AGENT_ROLE_BAD_INPUT,
            next_state=None,
            gate_result={
                "status": "retry",
                "reasons": ["ticket_json must be valid JSON"],
                "fixes": ["Serialize ticket.json as valid JSON before submitting"],
                "missing_or_invalid_fields": ["ticket_json"],
                "issues": [{"field": "ticket_json", "message": str(exc), "code": "json_decode_error"}],
            },
        )
    except ValidationError as exc:
        return _response(
            updated_ticket=None,
            continue_=False,
            reason="Ticket schema validation failed",
            next_role=AGENT_ROLE_BAD_INPUT,
            next_state=None,
            gate_result={
                "status": "retry",
                "reasons": ["ticket_json does not match required envelope schema"],
                "fixes": ["Ensure all required ticket envelope fields are present and non-empty"],
                "missing_or_invalid_fields": sorted(
                    {".".join(str(p) for p in err.get("loc", ())) for err in exc.errors()}
                ),
                "issues": [
                    {
                        "field": ".".join(str(p) for p in err.get("loc", ())) or "ticket_json",
                        "message": err.get("msg", "invalid value"),
                        "code": err.get("type", "value_error"),
                    }
                    for err in exc.errors()
                ],
            },
        )

    store.save_ticket(ticket)
    store.save_event(
        run_id=ticket.run_id,
        event_type="submit",
        state=ticket.state,
        details={"ticket_id": ticket.ticket_id},
    )

    state = State(ticket.state)

    if ticket.schema_version != SCHEMA_VERSION:
        blocked = _fail_closed(
            ticket,
            reason_code="schema_version_mismatch",
            message=f"Expected schema_version '{SCHEMA_VERSION}'",
            fields=["schema_version"],
        )
        return _response(
            updated_ticket=blocked,
            continue_=False,
            reason="Blocking validation failure: schema version mismatch",
            next_role=blocked.agent_role,
            next_state=blocked.state,
            gate_result={
                "status": "stop",
                "reasons": ["schema_version mismatch"],
                "fixes": [f"Use schema_version '{SCHEMA_VERSION}' and restart run"],
                "missing_or_invalid_fields": ["schema_version"],
                "issues": [issue.model_dump(mode="json") for issue in blocked.validation.errors],
            },
        )

    if is_terminal(state):
        terminal = _ticket_with_server_contract(ticket, state)
        store.save_ticket(terminal)
        return _response(
            updated_ticket=terminal,
            continue_=False,
            reason=f"Run is already in terminal state '{state.value}'",
            next_role=terminal.agent_role,
            next_state=terminal.state,
            gate_result={"status": "stop", "reasons": [f"State '{state.value}' is terminal"]},
        )

    gate = get_gate_for_state(ticket.state)
    gate_result = gate.validate(ticket)
    gate_payload = gate_result.model_dump(mode="json")

    if gate_result.status == "retry":
        fixed = ticket.model_copy(
            update={
                "agent_role": get_agent_role(state),
                "required_fields": get_required_fields(state),
                "next_stage_fields": get_next_stage_fields(state),
                "validation": ValidationStatus(status="invalid_fixable", errors=gate_result.issues),
                "invalidation_report": None,
                "history": _append_history(
                    ticket,
                    HistoryEntry(
                        from_state=state.value,
                        to_state=state.value,
                        result="retry",
                        reason="Fixable validation errors in payload",
                    ),
                ),
                "updated_at": _utc_now(),
            }
        )
        store.save_ticket(fixed)
        store.save_event(
            run_id=fixed.run_id,
            event_type="retry",
            state=fixed.state,
            details={"fields": gate_result.missing_or_invalid_fields},
        )
        return _response(
            updated_ticket=fixed,
            continue_=True,
            reason="Fixable validation errors. Update required fields and resubmit ticket.json.",
            next_role=fixed.agent_role,
            next_state=fixed.state,
            gate_result=gate_payload,
        )

    if gate_result.status == "stop":
        blocked = _fail_closed(
            ticket,
            reason_code="blocking_gate_failure",
            message="Blocking gate failure. Cannot proceed.",
            fields=gate_result.missing_or_invalid_fields,
        )
        return _response(
            updated_ticket=blocked,
            continue_=False,
            reason="Blocking validation failure",
            next_role=blocked.agent_role,
            next_state=blocked.state,
            gate_result=gate_payload,
        )

    transition_result = transition(state)
    if transition_result.status == "stop" or transition_result.next_state is None:
        terminal = _ticket_with_server_contract(ticket, state)
        terminal = terminal.model_copy(
            update={
                "validation": ValidationStatus(status="valid", errors=[]),
                "history": _append_history(
                    terminal,
                    HistoryEntry(
                        from_state=state.value,
                        to_state=state.value,
                        result="completed" if state == State.COMPLETE else "advanced",
                        reason=transition_result.reason,
                    ),
                ),
            }
        )
        store.save_ticket(terminal)
        return _response(
            updated_ticket=terminal,
            continue_=False,
            reason=transition_result.reason,
            next_role=terminal.agent_role,
            next_state=terminal.state,
            gate_result=gate_payload,
        )

    next_state = transition_result.next_state
    is_complete = next_state == State.COMPLETE
    updated = ticket.model_copy(
        update={
            "state": next_state.value,
            "agent_role": get_agent_role(next_state),
            "required_fields": get_required_fields(next_state),
            "payload": {},
            "next_stage_fields": get_next_stage_fields(next_state),
            "validation": ValidationStatus(status="valid", errors=[]),
            "invalidation_report": None,
            "history": _append_history(
                ticket,
                HistoryEntry(
                    from_state=state.value,
                    to_state=next_state.value,
                    result="completed" if is_complete else "advanced",
                    reason=transition_result.reason,
                ),
            ),
            "updated_at": _utc_now(),
        }
    )
    store.save_ticket(updated)
    store.save_event(
        run_id=updated.run_id,
        event_type="transition",
        state=updated.state,
        details={"from_state": state.value, "to_state": next_state.value},
    )
    return _response(
        updated_ticket=updated,
        continue_=not is_complete,
        reason=transition_result.reason,
        next_role=updated.agent_role,
        next_state=updated.state,
        gate_result=gate_payload,
    )


@mcp.tool()
def interlock_begin_run(ticket_id: str, run_id: str | None = None) -> dict[str, Any]:
    """Create a clean initial ticket.json with state=fetch_ticket."""
    try:
        ticket = create_initial_ticket(ticket_id=ticket_id, run_id=run_id)
    except ValueError as exc:
        return _response(
            updated_ticket=None,
            continue_=False,
            reason=str(exc),
            next_role=AGENT_ROLE_BAD_INPUT,
            next_state=None,
            gate_result={
                "status": "retry",
                "reasons": [str(exc)],
                "fixes": ["Provide non-empty ticket_id (and run_id if provided)"],
            },
        )
    return _response(
        updated_ticket=ticket,
        continue_=True,
        reason=(
            "Initialized ticket.json at fetch_ticket. Save this file to your repo, fill required_fields "
            "via external MCP tools, and submit it back."
        ),
        next_role=ticket.agent_role,
        next_state=ticket.state,
    )


@mcp.tool()
def interlock_submit_ticket(ticket_json: str) -> dict[str, Any]:
    """Validate submitted ticket.json and deterministically advance or fail."""
    return submit_ticket_json(ticket_json)


@mcp.tool()
def interlock_next_step(ticket_json: str) -> dict[str, Any]:
    """Backward-compatible alias for interlock_submit_ticket."""
    return submit_ticket_json(ticket_json)


if __name__ == "__main__":
    mcp.run()
