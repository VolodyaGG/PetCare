"""Extraction contract for Egor's prototype; not a command execution endpoint."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class VoiceCommandDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    intent: Literal["create_task", "log_care", "unknown"]
    source_text: str = Field(min_length=1, max_length=4000)
    pet_name: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    due_at: AwareDatetime | None = None
    recurrence: Literal["none", "daily", "weekly", "monthly"] | None = None
    missing_fields: list[Literal["pet", "title", "due_at", "intent"]] = Field(default_factory=list)
    requires_confirmation: Literal[True] = True
