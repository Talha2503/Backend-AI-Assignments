import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError, APIStatusError


load_dotenv()


PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "support-v1.md"
)

PROMPT_VERSION = "support-v1"

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]


def load_system_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_client():
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=0,
    )


def _should_retry(exc):
    if isinstance(exc, APITimeoutError):
        return True

    if isinstance(exc, APIConnectionError):
        return True

    if isinstance(exc, APIStatusError):
        status_code = exc.status_code

        if status_code == 429:
            return True

        if 500 <= status_code <= 599:
            return True

    return False


def _retry_after(exc):
    if isinstance(exc, APIStatusError) and exc.status_code == 429:
        headers = getattr(exc.response, "headers", {})

        value = headers.get("retry-after")

        if value:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass

    return None


def _call_model(
    text: str,
    messages: list,
    is_repair: bool = False,
):
    client = get_client()
    model = os.environ["LLM_MODEL"]

    attempt = 0

    while True:
        attempt += 1
        started = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )

            duration_ms = round(
                (time.perf_counter() - started) * 1000
            )

            usage = response.usage

            prompt_tokens = (
                usage.prompt_tokens
                if usage
                else 0
            )

            completion_tokens = (
                usage.completion_tokens
                if usage
                else 0
            )

            print(
                {
                    "event": "llm_call",
                    "prompt_version": PROMPT_VERSION,
                    "model": model,
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                    "duration_ms": duration_ms,
                    "repair": is_repair,
                    "attempt": attempt,
                }
            )

            return response.choices[0].message.content

        except Exception as exc:
            duration_ms = round(
                (time.perf_counter() - started) * 1000
            )

            print(
                {
                    "event": "llm_call_failed",
                    "prompt_version": PROMPT_VERSION,
                    "model": model,
                    "duration_ms": duration_ms,
                    "repair": is_repair,
                    "attempt": attempt,
                    "error": type(exc).__name__,
                }
            )

            if not _should_retry(exc):
                raise

            if attempt > MAX_RETRIES:
                raise

            retry_after = _retry_after(exc)

            if retry_after is not None:
                delay = retry_after
            else:
                delay = BACKOFF_SECONDS[attempt - 1]

                delay += random.uniform(0, 0.25)

            time.sleep(delay)


def classify_with_llm(text: str):
    system_prompt = load_system_prompt()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    return _call_model(
        text=text,
        messages=messages,
        is_repair=False,
    )


def repair_with_llm(
    text: str,
    broken_output: str,
    validation_error: str,
):
    system_prompt = load_system_prompt()

    repair_message = f"""
Your previous answer was rejected for this reason:

{validation_error}

Your previous answer was:

{broken_output}

Return only corrected JSON matching the schema.

The original support message is:

{text}
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": repair_message,
        },
    ]

    return _call_model(
        text=text,
        messages=messages,
        is_repair=True,
    )