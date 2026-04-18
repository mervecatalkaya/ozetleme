import json
from typing import Any

from services.llm_client import GroqLLM, LLMError
from services.meeting_state import MeetingState


MAX_TOPICS = 5
MAX_DECISIONS = 5


SUMMARY_SYSTEM_PROMPT = """
Sen bir toplanti ozetleme ajanisin.
Sadece verilen transcript ve segmentlere dayan.
Tum ciktilar Turkce olsun.
Uydurma bilgi, yorum veya transcriptte gecmeyen karar ekleme.
Her zaman gecerli JSON don.
Tum alanlar her zaman mevcut olsun.

Kurallar:
- Sadece transcriptte acikca gecen bilgiye dayan.
- executiveSummary 2 ila 4 cumle olsun; kisa, yogun ve yonetici seviyesi bir ozet yaz.
- executiveSummary icine yeni karar, gorev veya tarih uydurma.
- keyDecisions yalnizca toplantida acikca alinmis kararlar icersin.
- Acik karar yoksa keyDecisions bos liste olsun.
- topics sadece ana konulari icersin; kisa basliklar kullan.
- topics en fazla 5 madde olsun.
- Tekrar eden veya anlami ayni olan maddeleri birlestir.
- Belirsiz, varsayimsal veya yoruma dayali madde ekleme.
- JSON disinda hicbir metin yazma.

Beklenen JSON:
{
  "executiveSummary": "2-4 cumlelik yonetici ozeti",
  "keyDecisions": ["karar 1", "karar 2"],
  "topics": ["konu 1", "konu 2"]
}
"""


def _normalize_string_list(
    items: Any,
    *,
    limit: int,
    max_item_length: int = 120,
) -> list[str]:
    if not isinstance(items, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for item in items:
        text = " ".join(str(item).strip().split())
        if not text:
            continue

        text = text[:max_item_length].strip(" ,;:-")
        if not text:
            continue

        key = text.casefold()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(text)
        if len(normalized) >= limit:
            break

    return normalized


def _normalize_summary_text(value: Any, max_length: int = 1000) -> str:
    text = " ".join(str(value or "").strip().split())
    return text[:max_length].strip()


def summarize_meeting(
    transcript: str,
    segments: list[dict] | None = None,
    llm: GroqLLM | None = None,
) -> dict[str, Any]:
    if not transcript.strip():
        return {
            "executiveSummary": "",
            "keyDecisions": [],
            "topics": [],
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
        temperature=0.1,
    )

    executive_summary = str(
        result.get("executiveSummary")
        or result.get("highlights_summary")
        or ""
    ).strip()

    key_decisions = result.get("keyDecisions")
    if not isinstance(key_decisions, list):
        minutes = result.get("hierarchical_minutes") or {}
        key_decisions = minutes.get("decisions", [])

    topics = result.get("topics")
    if not isinstance(topics, list):
        minutes = result.get("hierarchical_minutes") or {}
        topics = minutes.get("topics", [])

    return {
        "executiveSummary": _normalize_summary_text(executive_summary),
        "keyDecisions": _normalize_string_list(
            key_decisions,
            limit=MAX_DECISIONS,
        ),
        "topics": _normalize_string_list(
            topics,
            limit=MAX_TOPICS,
            max_item_length=80,
        ),
    }


def run_summary_agent(state: MeetingState) -> dict[str, Any]:
    patch = {
        "highlights_summary": "",
        "hierarchical_minutes": {
            "overview": "",
            "topics": [],
            "decisions": [],
        },
        "executive_summary": "",
        "key_decisions": [],
        "topics": [],
        "errors": [],
        "completed": [],
    }

    try:
        result = summarize_meeting(
            transcript=state.get("transcript", ""),
            segments=state.get("segments", []),
        )
        patch["executive_summary"] = result["executiveSummary"]
        patch["key_decisions"] = result["keyDecisions"]
        patch["topics"] = result["topics"]
        patch["highlights_summary"] = result["executiveSummary"]
        patch["hierarchical_minutes"] = {
            "overview": result["executiveSummary"],
            "topics": result["topics"],
            "decisions": result["keyDecisions"],
        }
        patch["completed"].append("summary_agent")
    except LLMError as exc:
        patch["errors"].append(f"summary_agent: {exc}")
    except Exception as exc:  # pragma: no cover
        patch["errors"].append(f"summary_agent: beklenmeyen hata: {exc}")

    return patch
