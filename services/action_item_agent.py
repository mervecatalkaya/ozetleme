import json
from datetime import datetime
from typing import Any

from services.llm_client import GroqLLM, LLMError
from services.meeting_state import MeetingState


ACTION_ITEM_SYSTEM_PROMPT = """
Sen bir toplanti aksiyon maddesi cikarma ajanisin.
Sadece verilen transcript ve segmentlerde acikca gecen gorevleri cikar.
Uydurma gorev, kisi veya tarih ekleme.
Eger acik gorev yoksa bos liste don.
Tum ciktilar Turkce olsun.
Tarihleri mumkunse ISO 8601 formatina cevir.
Confidence 0.0 ile 1.0 arasinda olsun.
Confidence 0.65'ten kucukse needs_review alanini true olarak ekle.
Type alani sadece su degerlerden biri olsun: direct, volunteer, implicit, conditional, group.
Her zaman gecerli JSON don.

Beklenen JSON:
{
  "action_items": [
    {
      "task": "string",
      "assignee": "string",
      "due_date": "YYYY-MM-DD veya bos string",
      "priority": "low|medium|high|critical veya bos string",
      "confidence": 0.0,
      "type": "direct|volunteer|implicit|conditional|group",
      "needs_review": true
    }
  ]
}
"""


def _normalize_due_date(value: str) -> str:
    if not value:
        return ""

    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def extract_tasks(
    transcript: str,
    segments: list[dict] | None = None,
    meeting_date: str = "",
    llm: GroqLLM | None = None,
) -> list[dict[str, Any]]:
    if not transcript.strip():
        return []

    client = llm or GroqLLM()
    result = client.complete_json(
        system_prompt=ACTION_ITEM_SYSTEM_PROMPT,
        user_prompt=json.dumps(
            {
                "meeting_date": meeting_date,
                "segments": (segments or [])[:120],
                "transcript": transcript[:12000],
            },
            ensure_ascii=False,
            indent=2,
        ),
        temperature=0.1,
    )

    tasks = []
    for item in result.get("action_items", []):
        confidence = float(item.get("confidence", 0.0) or 0.0)
        normalized = {
            "task": str(item.get("task", "")).strip(),
            "assignee": str(item.get("assignee", "")).strip(),
            "due_date": _normalize_due_date(str(item.get("due_date", "")).strip()),
            "priority": str(item.get("priority", "")).strip(),
            "confidence": round(confidence, 2),
            "type": str(item.get("type", "")).strip(),
        }
        if confidence < 0.65:
            normalized["needs_review"] = True
        if normalized["task"]:
            tasks.append(normalized)

    return tasks


def run_action_item_agent(state: MeetingState) -> dict[str, Any]:
    patch = {
        "action_items": [],
        "errors": [],
        "completed": [],
    }

    try:
        patch["action_items"] = extract_tasks(
            transcript=state.get("transcript", ""),
            segments=state.get("segments", []),
            meeting_date=state.get("meeting_date", ""),
        )
        patch["completed"].append("action_item_agent")
    except LLMError as exc:
        patch["errors"].append(f"action_item_agent: {exc}")
    except Exception as exc:  # pragma: no cover
        patch["errors"].append(f"action_item_agent: beklenmeyen hata: {exc}")

    return patch
