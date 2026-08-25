import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "support-v1.md"


def load_system_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def classify_with_llm(text: str):
    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )

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