"""Tests for Interlock ticket.json begin/submit dialog."""

from __future__ import annotations

import pytest

import interlock.server as server
from interlock.schemas.ticket import Ticket
from interlock.storage import ArtifactStore


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Use isolated on-disk storage for each test."""
    monkeypatch.setattr(server, "store", ArtifactStore(tmp_path / "interlock_data"))


def _payload_for_state(state: str) -> dict:
    payloads = {
        "fetch_ticket": {
            "external_source": "jira",
            "external_ticket_id": "PROJ-123",
            "title": "Implement rigid handshake",
            "description": "PoC for deterministic agent/server dialog",
        },
        "extract_requirements": {
            "acceptance_criteria": ["Server returns clean ticket.json in first call"],
            "constraints": ["Use deterministic transitions only"],
            "unknowns": ["None for PoC"],
        },
        "scope_context": {
            "retrieval_targets": ["jira:PROJ-123", "repo:interlock"],
            "retrieval_justification": "Need ticket intent and existing server code context",
        },
        "gather_evidence": {
            "evidence_items": [
                {
                    "source_id": "src_001",
                    "source_type": "repo",
                    "locator": "interlock/server.py:1",
                    "snippet": "server begin/submit workflow implementation",
                }
            ]
        },
        "propose_plan": {
            "plan_steps": [
                {
                    "step_id": "step_001",
                    "intent": "Implement strict ticket schema",
                    "requirement_refs": ["ac_001"],
                    "evidence_refs": ["src_001"],
                }
            ]
        },
        "act_via_tools": {
            "actions_taken": ["Updated FSM and schema code"],
            "outputs": ["Patched interlock modules"],
            "checkpoints": ["checkpoint_001"],
        },
        "record_and_finalize": {
            "artifacts": ["interlock/server.py", "interlock/fsm.py"],
            "final_summary": "Completed deterministic ticket handshake PoC",
            "outcome": "success",
        },
    }
    return payloads[state]


def test_begin_creates_clean_fetch_ticket():
    ticket = server.create_initial_ticket(ticket_id="PROJ-123", run_id="run_test_001")
    assert ticket.state == "fetch_ticket"
    assert ticket.agent_role
    assert ticket.required_fields == [
        "external_source",
        "external_ticket_id",
        "title",
        "description",
    ]
    assert ticket.payload == {}


def test_submit_retry_when_required_fields_missing():
    ticket = server.create_initial_ticket(ticket_id="PROJ-123", run_id="run_test_002")
    ticket = ticket.model_copy(update={"payload": {"external_source": "jira"}})

    response = server.submit_ticket_json(ticket.to_json())

    assert response["continue"] is True
    assert response["next_state"] == "fetch_ticket"
    assert response["gate_result"]["status"] == "retry"
    missing = response["gate_result"]["missing_or_invalid_fields"]
    assert "description" in missing
    assert "external_ticket_id" in missing


def test_submit_advances_state_when_payload_valid():
    ticket = server.create_initial_ticket(ticket_id="PROJ-123", run_id="run_test_003")
    ticket = ticket.model_copy(update={"payload": _payload_for_state("fetch_ticket")})

    response = server.submit_ticket_json(ticket.to_json())

    assert response["continue"] is True
    assert response["next_state"] == "extract_requirements"
    updated = Ticket(**response["updated_ticket"])
    assert updated.state == "extract_requirements"
    assert updated.required_fields == ["acceptance_criteria", "constraints", "unknowns"]
    assert updated.next_stage_fields == ["retrieval_targets", "retrieval_justification"]


def test_submit_fail_closed_on_schema_version_mismatch():
    ticket = server.create_initial_ticket(ticket_id="PROJ-123", run_id="run_test_004")
    ticket = ticket.model_copy(
        update={
            "schema_version": "0.9.0",
            "payload": _payload_for_state("fetch_ticket"),
        }
    )

    response = server.submit_ticket_json(ticket.to_json())

    assert response["continue"] is False
    assert response["next_state"] == "fail_closed"
    assert response["gate_result"]["status"] == "stop"
    assert response["updated_ticket"]["invalidation_report"]["reason_code"] == "schema_version_mismatch"


def test_full_happy_path_reaches_complete():
    ticket = server.create_initial_ticket(ticket_id="PROJ-123", run_id="run_test_005")

    sequence = [
        "fetch_ticket",
        "extract_requirements",
        "scope_context",
        "gather_evidence",
        "propose_plan",
        "act_via_tools",
        "record_and_finalize",
    ]

    for state in sequence:
        assert ticket.state == state
        ticket = ticket.model_copy(update={"payload": _payload_for_state(state)})
        response = server.submit_ticket_json(ticket.to_json())
        ticket = Ticket(**response["updated_ticket"])

    assert ticket.state == "complete"
    assert response["continue"] is False
