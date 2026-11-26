import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.voice import (
    TextSpan,
    VoiceExtractionOutput,
    VoiceInterpretRequest,
    VoiceInterpretResult,
)

DOCS = Path(__file__).resolve().parents[2] / "docs"


@pytest.fixture
def events():
    return json.loads((DOCS / "examples/voice-three-events.json").read_text())


@pytest.fixture
def ambiguous():
    return json.loads((DOCS / "examples/voice-ambiguous.json").read_text())


def test_three_events_preserve_intents_time_and_unambiguous_reference(events):
    result = VoiceInterpretResult.model_validate(events)
    first, second, third = result.drafts
    assert [d.intent for d in result.drafts] == ["log_care", "log_care", "create_task"]
    assert first.pet_id == second.pet_id != third.pet_id
    assert first.occurred_at.hour == 8
    assert second.occurred_at.hour == 9
    assert third.due_at.day == 27 and third.due_at.hour == 10
    assert second.pet_from_draft_id == first.draft_id
    assert second.notices[0].message == "Марс — из предыдущей фразы"
    assert not result.has_blocking_problems
    assert result.requires_confirmation is True
    assert VoiceInterpretResult.model_validate_json(result.model_dump_json()) == result


def test_ambiguous_pet_and_time_stay_unresolved(ambiguous):
    result = VoiceInterpretResult.model_validate(ambiguous)
    draft = result.drafts[0]
    assert draft.pet_id is None and draft.due_at is None
    assert len(draft.pet_candidates) == 2
    assert {c.species for c in draft.pet_candidates} == {"Собака", "Кот"}
    assert {p.field for p in draft.problems} == {"pet", "time"}
    assert result.has_blocking_problems
    assert result.unparsed_fragments[0].text == "И ещё вот это."


@pytest.mark.parametrize("status", ["missing", "ambiguous"])
def test_missing_and_ambiguous_time_need_blocking_reason(events, status):
    draft = events["drafts"][2]
    draft.update(due_at=None, time_status=status, time_spans=[])
    with pytest.raises(ValidationError, match="blocking time problem"):
        VoiceInterpretResult.model_validate(events)
    draft["problems"] = [{"field": "time", "code": status, "message": "Уточните время"}]
    assert VoiceInterpretResult.model_validate(events).drafts[2].time_status == status


def test_explicit_no_deadline_differs_from_missing_time(events):
    draft = deepcopy(events["drafts"][2])
    events["transcript"] = "Дать лекарство Луне без срока"
    draft.update(
        due_at=None,
        time_status="no_deadline",
        event_span={"start": 0, "end": 29, "quote": events["transcript"]},
        action_span={"start": 0, "end": 4, "quote": "Дать"},
        time_spans=[{"start": 20, "end": 29, "quote": "без срока"}],
    )
    events["drafts"] = [draft]
    result = VoiceInterpretResult.model_validate(events)
    assert result.drafts[0].due_at is None and not result.has_blocking_problems
    draft["time_spans"] = []
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(events)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("occurred_at", "2026-11-27T10:00:00+03:00"),
        ("due_at", "2026-11-27T10:00:00"),
        ("due_at", "2026-02-30T10:00:00+03:00"),
        ("time_status", "no_deadline"),
        ("pet_id", "guessed-id"),
    ],
)
def test_reject_invalid_timestamps_intent_combinations_and_ids(events, field, value):
    events["drafts"][2][field] = value
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(events)


def test_care_fact_must_not_be_in_future_relative_to_recording(events):
    events["recording_started_at"] = "2026-11-26T08:30:00+03:00"
    with pytest.raises(ValidationError, match="recording anchor"):
        VoiceInterpretResult.model_validate(events)


@pytest.mark.parametrize("mutation", ["forward", "different_pet", "missing_notice", "duplicate"])
def test_reject_broken_coreference_and_duplicate_draft_ids(events, mutation):
    second = events["drafts"][1]
    if mutation == "forward":
        second["pet_from_draft_id"] = events["drafts"][2]["draft_id"]
    elif mutation == "different_pet":
        second["pet_id"] = events["drafts"][2]["pet_id"]
    elif mutation == "missing_notice":
        second["notices"] = []
    else:
        second["draft_id"] = events["drafts"][0]["draft_id"]
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(events)


def test_ambiguous_pet_cannot_be_selected_silently(ambiguous):
    ambiguous["drafts"][0]["pet_id"] = ambiguous["drafts"][0]["pet_candidates"][0]["pet_id"]
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(ambiguous)


def test_explicit_repeat_is_preserved_and_blocks_unsupported_series(events):
    events["transcript"] += " Каждый день."
    draft = events["drafts"][2]
    draft["recurrence_text"] = "Каждый день"
    with pytest.raises(ValidationError, match="recurrence problem"):
        VoiceInterpretResult.model_validate(events)
    draft["problems"] = [
        {"field": "recurrence", "code": "unsupported", "message": "Серии пока не поддерживаются"}
    ]
    result = VoiceInterpretResult.model_validate(events)
    assert result.drafts[2].recurrence_text == "Каждый день"
    assert result.has_blocking_problems
    draft["recurrence_text"] = "Каждую неделю"
    with pytest.raises(ValidationError, match="unchanged transcript quote"):
        VoiceInterpretResult.model_validate(events)


def test_time_correction_can_highlight_both_expressions(events):
    text = "Завтра в восемь, нет, в девять дать Луне лекарство"
    events["transcript"] = text
    draft = deepcopy(events["drafts"][2])

    def span(quote):
        start = text.index(quote)
        return {"start": start, "end": start + len(quote), "quote": quote}

    draft.update(
        due_at="2026-11-27T09:00:00+03:00",
        event_span=span(text),
        action_span=span("дать"),
        time_spans=[span("Завтра в восемь"), span("в девять")],
        notices=[{"code": "time_corrected", "message": "Восемь исправлено на девять"}],
    )
    events["drafts"] = [draft]
    result = VoiceInterpretResult.model_validate(events)
    assert len(result.drafts[0].time_spans) == 2
    assert not result.has_blocking_problems


def test_utf16_offsets_account_for_emoji_and_reject_split_surrogates():
    text = "🐾 Марс"
    TextSpan(start=3, end=7, quote="Марс").check_transcript(text)
    with pytest.raises(ValueError, match="surrogate"):
        TextSpan(start=1, end=2, quote="🐾").check_transcript(text)
    with pytest.raises(ValueError, match="exceeds"):
        TextSpan(start=3, end=8, quote="Марс").check_transcript(text)
    with pytest.raises(ValidationError):
        TextSpan(start=4, end=3, quote="с")


def test_reject_changed_transcript_or_fabricated_quote(events):
    events["transcript"] = "🐾 " + events["transcript"]
    with pytest.raises(ValidationError, match="quote does not match"):
        VoiceInterpretResult.model_validate(events)


def test_unmapped_span_is_problem_not_guessed_offset(events):
    draft = events["drafts"][0]
    draft["action_span"] = None
    with pytest.raises(ValidationError, match="blocking source problem"):
        VoiceInterpretResult.model_validate(events)
    draft["problems"] = [
        {"field": "source", "code": "ambiguous_span", "message": "Диапазон неоднозначен"}
    ]
    assert VoiceInterpretResult.model_validate(events).has_blocking_problems


def test_unparsed_fragment_quote_is_checked(ambiguous):
    ambiguous["unparsed_fragments"][0]["span"]["quote"] = "Несуществующая цитата"
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(ambiguous)


def test_revision_metadata_keeps_anchor_across_midnight_and_reparse(events):
    events["recording_started_at"] = "2026-11-26T23:59:00+03:00"
    original = VoiceInterpretResult.model_validate(events)
    events.update(revision=2, result_id="00000000-0000-4000-8000-000000000099")
    reparsed = VoiceInterpretResult.model_validate(events)
    assert original.recording_started_at == reparsed.recording_started_at
    assert original.timezone == reparsed.timezone
    assert original.transcript_revision == reparsed.transcript_revision
    assert original.drafts[2].due_at == reparsed.drafts[2].due_at
    assert reparsed.result_id == UUID(events["result_id"])


@pytest.mark.parametrize("field", ["revision", "transcript_revision"])
def test_revisions_start_at_one(events, field):
    events[field] = 0
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(events)


def test_unknown_timezone_and_disabled_confirmation_are_rejected(events):
    events["timezone"] = "Mars/Olympus"
    with pytest.raises(ValidationError, match="IANA timezone"):
        VoiceInterpretResult.model_validate(events)
    events["timezone"] = "Europe/Moscow"
    events["requires_confirmation"] = False
    with pytest.raises(ValidationError):
        VoiceInterpretResult.model_validate(events)


def test_model_output_has_no_verified_ids_or_normalized_timestamps():
    raw = json.loads((DOCS / "examples/voice-three-events.model.json").read_text())
    parsed = VoiceExtractionOutput.model_validate(raw)
    assert parsed.drafts[1].pet_reference_item == 0
    raw["drafts"][0]["pet_id"] = "00000000-0000-4000-8000-000000000101"
    with pytest.raises(ValidationError, match="Extra inputs"):
        VoiceExtractionOutput.model_validate(raw)


def test_model_schema_is_required_nullable_and_closed_at_every_object():
    def check(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for child in node.values():
                check(child)
        elif isinstance(node, list):
            for child in node:
                check(child)

    check(VoiceExtractionOutput.model_json_schema())


def test_exported_schemas_match_models():
    for filename, model in [
        ("voice-command.schema.json", VoiceInterpretResult),
        ("voice-extraction.schema.json", VoiceExtractionOutput),
    ]:
        assert json.loads((DOCS / filename).read_text()) == model.model_json_schema()


def test_request_contains_no_user_supplied_authorization_context(events):
    request = {key: events[key] for key in VoiceInterpretRequest.model_fields}
    request["available_pets"] = []
    with pytest.raises(ValidationError):
        VoiceInterpretRequest.model_validate(request)
