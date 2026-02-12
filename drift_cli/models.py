"""Pydantic models for Drift CLI."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk levels for commands."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Command(BaseModel):
    """A single command to execute."""

    command: str = Field(..., description="The shell command to execute")
    description: str = Field(..., description="What this command does")
    dry_run: Optional[str] = Field(None, description="Dry-run version if applicable")


class ClarificationQuestion(BaseModel):
    """A question to ask the user for clarification."""

    question: str = Field(..., description="The question to ask")
    options: Optional[List[str]] = Field(None, description="Suggested options if applicable")


class Plan(BaseModel):
    """A plan for executing user intent."""

    summary: str = Field(..., description="Brief summary of what will be done")
    risk: RiskLevel = Field(..., description="Risk level of the operation")
    commands: List[Command] = Field(..., description="Commands to execute")
    explanation: str = Field(..., description="Detailed explanation of the approach")
    affected_files: Optional[List[str]] = Field(None, description="Files that may be affected")
    clarification_needed: Optional[List[ClarificationQuestion]] = Field(
        None, description="Questions to ask before proceeding"
    )


class HistoryEntry(BaseModel):
    """A single entry in the Drift history."""

    timestamp: str
    query: str
    plan: Plan
    executed: bool
    exit_code: Optional[int] = None
    snapshot_id: Optional[str] = None
