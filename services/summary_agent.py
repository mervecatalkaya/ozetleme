import json
from typing import Any

from services.llm_client import GroqLLM, LLMError
from services.meeting_state import MeetingState


SUMMARY_SYSTEM_PROMPT = """
Sen bir toplanti ozetleme ajanisin.
Sadece verilen transcript ve segmentlere dayan.
Uydurma bilgi, yorum veya transcriptte gecmeyen karar ekleme.
Tum ciktilar Turkce olsun.
Her zaman gecerli JSON don.

Beklenen JSON:
{
  "highlights_summary": "3-4 cumlelik ozet",
  "hierarchical_minutes": {
    "overview": "kisa genel ozet",
    "topics": ["konu 1", "konu 2"],
    "decisions": ["karar 1", "karar 2"]
  }
}
"""


def summarize_meeting(
    transcript: str,
    segments: list[dict] | None = None,
    llm: GroqLLM | None = None,
) -> dict[str, Any]:
    if not transcript.strip():
        return {
            "highlights_summary": "",
            "hierarchical_minutes": {
                "overview": "",
                "topics": [],
                "decisions": [],
            },
        }

    client = llm or GroqLLM()
    result = client.complete_json(
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        user_prompt=json.dumps(
            {
                "segments": (segments or [])[:120],
                "transcript": transcript[:12000],
            },
            ensure_ascii=False,
            indent=2,
        ),
        temperature=0.2,
    )

    minutes = result.get("hierarchical_minutes") or {}
    return {
        "highlights_summary": str(result.get("highlights_summary", "")).strip(),
        "hierarchical_minutes": {
            "overview": str(minutes.get("overview", "")).strip(),
            "topics": [str(item).strip() for item in minutes.get("topics", []) if str(item).strip()],
            "decisions": [str(item).strip() for item in minutes.get("decisions", []) if str(item).strip()],
        },
    }


def run_summary_agent(state: MeetingState) -> dict[str, Any]:
    patch = {
        "highlights_summary": "",
        "hierarchical_minutes": {
            "overview": "",
            "topics": [],
            "decisions": [],
        },
        "errors": [],
        "completed": [],
    }

    try:
        result = summarize_meeting(
            transcript=state.get("transcript", ""),
            segments=state.get("segments", []),
        )
        patch["highlights_summary"] = result["highlights_summary"]
        patch["hierarchical_minutes"] = result["hierarchical_minutes"]
        patch["completed"].append("summary_agent")
    except LLMError as exc:
        patch["errors"].append(f"summary_agent: {exc}")
    except Exception as exc:  # pragma: no cover
        patch["errors"].append(f"summary_agent: beklenmeyen hata: {exc}")

    return patch
