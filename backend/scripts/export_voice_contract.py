"""Run from backend/: python -m scripts.export_voice_contract [--check]."""

import argparse
import json
from pathlib import Path

from app.schemas.voice import VoiceExtractionOutput, VoiceInterpretResult


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    docs = Path(__file__).resolve().parents[2] / "docs"
    schemas = {
        "voice-command.schema.json": VoiceInterpretResult.model_json_schema(),
        "voice-extraction.schema.json": VoiceExtractionOutput.model_json_schema(),
    }
    for filename, schema in schemas.items():
        path = docs / filename
        rendered = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != rendered:
                parser.exit(1, f"Stale schema: {path}\n")
        else:
            path.write_text(rendered)


if __name__ == "__main__":
    main()
