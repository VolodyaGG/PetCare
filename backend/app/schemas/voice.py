"""Voice contracts only: extraction does not execute commands or persist domain data."""

from typing import Literal, Self
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class VoiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextSpan(VoiceModel):
    """UTF-16 code-unit offsets [start, end) into the envelope's transcript revision."""

    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    quote: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Text span must have start < end")
        return self

    def check_transcript(self, transcript: str) -> None:
        encoded = transcript.encode("utf-16-le")
        if self.end * 2 > len(encoded):
            raise ValueError("Text span exceeds transcript")
        try:
            quoted = encoded[self.start * 2 : self.end * 2].decode("utf-16-le")
        except UnicodeDecodeError as exc:
            raise ValueError("Text span splits a UTF-16 surrogate pair") from exc
        if quoted != self.quote:
            raise ValueError("Text span quote does not match unchanged transcript")


class PetCandidate(VoiceModel):
    """Server-supplied, access-checked candidate; never trusted just because LLM returned it."""

    pet_id: UUID
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=1, max_length=100)
    subtitle: str | None = None


class VoiceNotice(VoiceModel):
    code: Literal["pet_from_context", "time_corrected"]
    message: str = Field(min_length=1)


class VoiceProblem(VoiceModel):
    field: Literal["pet", "title", "time", "source", "recurrence", "intent"]
    code: Literal[
        "missing", "ambiguous", "not_found", "invalid_time", "ambiguous_span", "unsupported"
    ]
    message: str = Field(min_length=1)


class VoiceCommandDraft(VoiceModel):
    draft_id: UUID
    intent: Literal["create_task", "log_care"]
    title: str | None = Field(default=None, min_length=1, max_length=120)
    pet_name: str | None = Field(default=None, min_length=1, max_length=100)
    pet_id: UUID | None = None
    pet_resolution: Literal["explicit", "context", "unresolved"]
    pet_from_draft_id: UUID | None = None
    pet_candidates: list[PetCandidate] = Field(default_factory=list)
    due_at: AwareDatetime | None = None
    occurred_at: AwareDatetime | None = None
    time_status: Literal["resolved", "no_deadline", "missing", "ambiguous"]
    event_span: TextSpan | None = None
    action_span: TextSpan | None = None
    time_spans: list[TextSpan] = Field(default_factory=list)
    recurrence_text: str | None = Field(default=None, min_length=1)
    notices: list[VoiceNotice] = Field(default_factory=list)
    problems: list[VoiceProblem] = Field(default_factory=list)

    @property
    def has_blocking_problems(self) -> bool:
        return bool(self.problems)

    @model_validator(mode="after")
    def consistent_draft(self) -> Self:
        fields = {problem.field for problem in self.problems}
        if self.title is None and "title" not in fields:
            raise ValueError("Missing title needs a blocking problem")
        if self.pet_resolution == "unresolved":
            if self.pet_id is not None or self.pet_from_draft_id is not None or "pet" not in fields:
                raise ValueError("Unresolved pet needs null IDs and a blocking pet problem")
        elif self.pet_id is None:
            raise ValueError("Resolved pet needs a verified pet_id")
        if "pet" in fields and self.pet_resolution != "unresolved":
            raise ValueError("Blocking pet problem must leave pet unresolved")
        if self.pet_resolution == "explicit" and self.pet_name is None:
            raise ValueError("Explicit pet resolution needs the recognized name")
        if self.pet_resolution == "context":
            if self.pet_from_draft_id is None or not any(
                notice.code == "pet_from_context" for notice in self.notices
            ):
                raise ValueError("Context resolution needs a reference and an informational notice")
        elif self.pet_from_draft_id is not None:
            raise ValueError("Only context resolution can reference another draft")
        candidate_ids = [candidate.pet_id for candidate in self.pet_candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("Duplicate pet candidates")
        if self.intent == "create_task" and self.occurred_at is not None:
            raise ValueError("A task cannot have occurred_at")
        if self.intent == "log_care" and self.due_at is not None:
            raise ValueError("A care fact cannot have due_at")
        timestamp = self.due_at if self.intent == "create_task" else self.occurred_at
        if self.time_status == "resolved":
            if timestamp is None:
                raise ValueError("Resolved time needs the intent-specific timestamp")
        elif self.due_at is not None or self.occurred_at is not None:
            raise ValueError("Unresolved/no-deadline time must not contain a timestamp")
        if self.time_status == "no_deadline":
            if self.intent != "create_task" or not self.time_spans:
                raise ValueError("No deadline requires a task and explicit source evidence")
            if not any("без срока" in span.quote.casefold() for span in self.time_spans):
                raise ValueError("No deadline requires explicit 'без срока' evidence")
        if self.time_status in {"missing", "ambiguous"} and "time" not in fields:
            raise ValueError("Missing/ambiguous time needs a blocking time problem")
        if (self.event_span is None or self.action_span is None) and "source" not in fields:
            raise ValueError("Unmapped event/action span needs a blocking source problem")
        if self.event_span and self.action_span:
            if not (
                self.event_span.start <= self.action_span.start
                and self.action_span.end <= self.event_span.end
            ):
                raise ValueError("Action span must be inside its event")
        if self.time_status == "resolved" and not self.time_spans and "source" not in fields:
            raise ValueError("Resolved time needs source evidence or a mapping problem")
        if self.recurrence_text is not None and not any(
            problem.field == "recurrence" and problem.code == "unsupported"
            for problem in self.problems
        ):
            raise ValueError("Explicit recurrence must retain an unsupported recurrence problem")
        return self


class UnparsedFragment(VoiceModel):
    span: TextSpan | None
    text: str = Field(min_length=1)
    reason: Literal["unknown_intent", "ambiguous_meaning", "ambiguous_span", "unsupported"]


class VoiceInterpretRequest(VoiceModel):
    recording_id: UUID
    revision: int = Field(ge=1, strict=True)
    transcript_revision: int = Field(ge=1, strict=True)
    transcript: str = Field(min_length=1, max_length=4000)
    recording_started_at: AwareDatetime
    timezone: str

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class VoiceInterpretResult(VoiceInterpretRequest):
    schema_version: Literal[2] = 2
    result_id: UUID
    drafts: list[VoiceCommandDraft]
    unparsed_fragments: list[UnparsedFragment]
    requires_confirmation: Literal[True] = True

    @property
    def has_blocking_problems(self) -> bool:
        return bool(self.unparsed_fragments) or any(d.has_blocking_problems for d in self.drafts)

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        previous: dict[UUID, VoiceCommandDraft] = {}
        for draft in self.drafts:
            if draft.draft_id in previous:
                raise ValueError("Duplicate draft_id")
            if draft.pet_from_draft_id is not None:
                target = previous.get(draft.pet_from_draft_id)
                if target is None or target.pet_id is None or target.pet_id != draft.pet_id:
                    raise ValueError("Pet reference must resolve to a preceding resolved draft")
            if draft.occurred_at is not None and draft.occurred_at > self.recording_started_at:
                raise ValueError("A care fact cannot occur after the recording anchor")
            if draft.pet_name is not None and draft.pet_name not in self.transcript:
                raise ValueError("Recognized pet name must be an unchanged transcript quote")
            spans = [draft.event_span, draft.action_span, *draft.time_spans]
            for span in spans:
                if span is not None:
                    span.check_transcript(self.transcript)
            if draft.recurrence_text is not None and draft.recurrence_text not in self.transcript:
                raise ValueError("Recurrence text must be an unchanged transcript quote")
            previous[draft.draft_id] = draft
        for fragment in self.unparsed_fragments:
            if fragment.span is not None:
                fragment.span.check_transcript(self.transcript)
                if fragment.text != fragment.span.quote:
                    raise ValueError("Unparsed text must match its span")
            elif fragment.reason != "ambiguous_span" or fragment.text not in self.transcript:
                raise ValueError("Unmapped fragment needs an exact quote and ambiguous_span reason")
        return self


# Separate extraction DTOs: all fields required, nullable values explicit, closed objects.
# No trusted IDs, resolved dates, client notices, offsets or validation outcomes from the LLM.
class VoiceExtractedDraft(VoiceModel):
    intent: Literal["create_task", "log_care"]
    title: str | None
    pet_name: str | None
    pet_reference_item: int | None
    time_kind: Literal["explicit", "no_deadline", "missing", "ambiguous"]
    event_quote: str
    action_quote: str | None
    time_quotes: list[str]
    recurrence_text: str | None


class VoiceExtractionOutput(VoiceModel):
    drafts: list[VoiceExtractedDraft]
    unparsed_quotes: list[str]
