import pytest
from pydantic import ValidationError

from app.schemas.voice import VoiceCommandDraft


def test_incomplete_extraction_keeps_missing_time():
    draft = VoiceCommandDraft(
        intent="create_task",
        source_text="Напомни погулять с Марсом",
        pet_name="Марс",
        title="Прогулка",
        missing_fields=["due_at"],
    )
    assert draft.due_at is None
    assert draft.requires_confirmation is True


@pytest.mark.parametrize(
    "fields",
    [{"requires_confirmation": False}, {"due_at": "2026-11-27T10:00:00"}, {"pet_id": "guessed"}],
)
def test_reject_unconfirmed_write_naive_time_and_guessed_ids(fields):
    with pytest.raises(ValidationError):
        VoiceCommandDraft(intent="create_task", source_text="Прогулка", **fields)
