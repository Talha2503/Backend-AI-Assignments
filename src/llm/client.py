import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "support-v1.md"


def load_system_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_client():
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )


def classify_with_llm(text: str):
    client = get_client()

    system_prompt = load_system_prompt()

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


def repair_with_llm(
    text: str,
    broken_output: str,
    validation_error: str,
):
    client = get_client()

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

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": repair_message,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content