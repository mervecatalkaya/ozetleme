import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

SYSTEM_PROMPT = "Sen bir toplanti analiz asistanisin"
MODEL_NAME = "llama-3.3-70b-versatile"


class GroqClient:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY tanimli degil.")

        self.client = Groq(api_key=api_key)

    def complete(self, prompt: str, temperature: float = 0.3) -> str:
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            temperature=temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    def complete_json(self, prompt: str, temperature: float = 0.2) -> dict | list | None:
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"{SYSTEM_PROMPT}. Yalnizca gecerli JSON dondur.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = (response.choices[0].message.content or "").strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None


_client: GroqClient | None = None


def _get_client() -> GroqClient:
    global _client
    if _client is None:
        _client = GroqClient()
    return _client


def complete(prompt: str, temperature: float = 0.3) -> str:
    return _get_client().complete(prompt=prompt, temperature=temperature)


def complete_json(prompt: str, temperature: float = 0.2) -> dict[str, Any] | list[Any] | None:
    return _get_client().complete_json(prompt=prompt, temperature=temperature)
