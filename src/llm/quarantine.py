import json
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path("logs/quarantine.jsonl")


def quarantine(
    input_text: str,
    raw_output: str,
    error: str,
    prompt_version: str,
) -> None:
    """Append a failed LLM response to the quarantine log."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_text,
        "raw_output": raw_output,
        "error": error,
        "prompt_version": prompt_version,
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")