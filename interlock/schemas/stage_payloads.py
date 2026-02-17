"""Per-stage payload schemas for strict state validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from interlock.fsm import State


class StrictPayloadModel(BaseModel):
    """Base payload model enforcing rigid schema and non-empty strings."""

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def _strip_strings(cls, value):  # type: ignore[no-untyped-def]
        if isinstance(value, str):
            return value.strip()
        return value


class FetchTicketPayload(StrictPayloadModel):
    external_source: str = Field(..., min_length=1)
    external_ticket_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class ExtractRequirementsPayload(StrictPayloadModel):
    acceptance_criteria: list[str] = Field(..., min_length=1)
    constraints: list[str] = Field(..., min_length=1)
    unknowns: list[str] = Field(..., min_length=1)

    @field_validator("acceptance_criteria", "constraints", "unknowns")
    @classmethod
    def _validate_non_empty_items(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            item = item.strip()
            if not item:
                raise ValueError("List items must be non-empty")
            cleaned.append(item)
        return cleaned


class ScopeContextPayload(StrictPayloadModel):
    retrieval_targets: list[str] = Field(..., min_length=1)
    retrieval_justification: str = Field(..., min_length=1)

    @field_validator("retrieval_targets")
    @classmethod
    def _validate_targets(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            item = item.strip()
            if not item:
                raise ValueError("List items must be non-empty")
            cleaned.append(item)
        return cleaned


class EvidenceItem(StrictPayloadModel):
    source_id: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    locator: str = Field(..., min_length=1)
    snippet: str = Field(..., min_length=1)


class GatherEvidencePayload(StrictPayloadModel):
    evidence_items: list[EvidenceItem] = Field(..., min_length=1)


class PlanStep(StrictPayloadModel):
    step_id: str = Field(..., min_length=1)
    intent: str = Field(..., min_length=1)
    requirement_refs: list[str] = Field(..., min_length=1)
    evidence_refs: list[str] = Field(..., min_length=1)

    @field_validator("requirement_refs", "evidence_refs")
    @classmethod
    def _validate_refs(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            item = item.strip()
            if not item:
                raise ValueError("List items must be non-empty")
            cleaned.append(item)
        return cleaned


class ProposePlanPayload(StrictPayloadModel):
    plan_steps: list[PlanStep] = Field(..., min_length=1)


class ActViaToolsPayload(StrictPayloadModel):
    actions_taken: list[str] = Field(..., min_length=1)
    outputs: list[str] = Field(..., min_length=1)
    checkpoints: list[str] = Field(..., min_length=1)

    @field_validator("actions_taken", "outputs", "checkpoints")
    @classmethod
    def _validate_items(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            item = item.strip()
            if not item:
                raise ValueError("List items must be non-empty")
            cleaned.append(item)
        return cleaned


class RecordAndFinalizePayload(StrictPayloadModel):
    artifacts: list[str] = Field(..., min_length=1)
    final_summary: str = Field(..., min_length=1)
    outcome: Literal["success", "partial", "blocked"]

    @field_validator("artifacts")
    @classmethod
    def _validate_artifacts(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            item = item.strip()
            if not item:
                raise ValueError("List items must be non-empty")
            cleaned.append(item)
        return cleaned


STAGE_PAYLOAD_MODELS: dict[State, type[StrictPayloadModel]] = {
    State.FETCH_TICKET: FetchTicketPayload,
    State.EXTRACT_REQUIREMENTS: ExtractRequirementsPayload,
    State.SCOPE_CONTEXT: ScopeContextPayload,
    State.GATHER_EVIDENCE: GatherEvidencePayload,
    State.PROPOSE_PLAN: ProposePlanPayload,
    State.ACT_VIA_TOOLS: ActViaToolsPayload,
    State.RECORD_AND_FINALIZE: RecordAndFinalizePayload,
}

