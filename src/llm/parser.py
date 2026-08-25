import json
import re

from pydantic import ValidationError

from src.llm.schema import SupportClassification


def extract_json_object(raw_text: str) -> str:
    """
    Extract a JSON object from raw model output.

    Handles:
    - plain JSON
    - ```json ... ``` code fences
    - explanatory text before/after the JSON object
    """
    text = raw_text.strip()

    # Remove markdown code fences if present.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Find the first JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    return text[start:end + 1]


def parse_and_validate(raw_text: str) -> SupportClassification:
    """
    Parse raw model output and validate it against the support schema.

    Raises:
        ValueError: if the output is not valid JSON.
        ValidationError: if the JSON does not match the schema.
    """
    json_text = extract_json_object(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON returned by model: {exc.msg}"
        ) from exc

    return SupportClassification.model_validate(data)