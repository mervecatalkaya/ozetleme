import json
import os
from typing import Any

import requests


class LLMError(Exception):
    pass


def _load_dotenv_if_needed() -> None:
    if os.getenv("GROQ_API_KEY"):
        return

    project_root = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(project_root, ".env")

    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


class GroqLLM:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1/chat/completions",
        timeout: int = 60,
    ) -> None:
        _load_dotenv_if_needed()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

        if not self.api_key:
            raise LLMError("GROQ_API_KEY tanimli degil.")

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        data = self._post(payload)
        content = self._extract_content(data)

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM gecerli JSON donmedi: {exc}") from exc

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise LLMError(f"Groq istegi basarisiz: {exc}") from exc

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise LLMError("Groq yanitinda choices alani bos.")

        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if not content:
            raise LLMError("Groq yanitinda content alani bos.")
        return content
