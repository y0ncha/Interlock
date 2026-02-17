"""Response models for Interlock gates."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from interlock.schemas.ticket import ValidationIssue


class GateResult(BaseModel):
    """Result of a stage validation gate."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["pass", "retry", "stop"] = Field(..., description="Gate validation status")
    reasons: list[str] = Field(default_factory=list, description="Reasons for the status")
    fixes: list[str] | None = Field(None, description="Suggested fixes")
    missing_or_invalid_fields: list[str] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)
