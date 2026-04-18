import json
from datetime import datetime
from typing import Any

from services.llm_client import GroqLLM, LLMError
from services.meeting_state import MeetingState


VALID_PRIORITIES = {"", "low", "medium", "high", "critical"}
VALID_ACTION_ITEM_TYPES = {"direct", "volunteer", "implicit", "conditional", "group"}


ACTION_ITEM_SYSTEM_PROMPT = """
Sen bir toplanti aksiyon maddesi cikarma ajanisin.
Sadece verilen transcript ve segmentlerde acikca gecen veya guclu bicimde desteklenen gorevleri cikar.
Tum ciktilar Turkce olsun.
Uydurma gorev, kisi, oncelik veya tarih ekleme.
Eger acik gorev yoksa bos liste don.
Her zaman gecerli JSON don.
Tum alanlar her zaman mevcut olsun.

Kurallar:
- Her action item kisa, net ve uygulanabilir olsun.
- Ayni gorevi farkli sekilde tekrar etme.
- assignee sadece transcriptte aciksa yaz; degilse bos string don.
- due_date sadece transcriptte acik ve kesin bir takvim tarihi varsa doldur.
- Goreli tarih ifadelerini takvim tarihine cevirme: yarin, haftaya, cuma, ay sonu gibi ifadelerde due_date bos string olsun.
- meeting_date bilgisinden tarih turetme.
- priority sadece transcriptte net bicimde anlasiliyorsa doldur; aksi halde bos string don.
- Confidence 0.0 ile 1.0 arasinda olsun.
- Confidence 0.65'ten kucukse needs_review true olsun, degilse false olsun.
- Type alani sadece su degerlerden biri olsun: direct, volunteer, implicit, conditional, group.
- direct: gorev bir kisiye dogrudan verildi.
- volunteer: kisi gorevi kendi ustlendi.
- implicit: yapilacak is var ama atama veya talimat dolayli.
- conditional: gorev bir kosula bagli.
- group: gorev ekip ya da grup icin ortak.
- Yorum, tahmin veya baglamdan cikarimla yeni detay ekleme.
- JSON disinda hicbir metin yazma.

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
    return ""


def _normalize_priority(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in VALID_PRIORITIES else ""


def _normalize_action_item_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in VALID_ACTION_ITEM_TYPES:
        return normalized
    return "implicit"


def _normalize_confidence(value: Any) -> float:
    try:
        confidence = float(value or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return round(max(0.0, min(1.0, confidence)), 2)


def _normalize_text(value: Any, max_length: int = 240) -> str:
    text = " ".join(str(value or "").strip().split())
    return text[:max_length].strip(" ,;:-")


def _should_mark_for_review(item: dict[str, Any], confidence: float) -> bool:
    if confidence < 0.65:
        return True
    return bool(item.get("needs_review", False))


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
    seen: set[tuple[str, str, str]] = set()

    for item in result.get("action_items", []):
        if not isinstance(item, dict):
            continue

        confidence = _normalize_confidence(item.get("confidence", 0.0))
        normalized = {
            "task": _normalize_text(item.get("task", "")),
            "assignee": _normalize_text(item.get("assignee", ""), max_length=80),
            "due_date": _normalize_due_date(str(item.get("due_date", "")).strip()),
            "priority": _normalize_priority(item.get("priority", "")),
            "confidence": confidence,
            "type": _normalize_action_item_type(item.get("type", "")),
        }

        if not normalized["task"]:
            continue

        dedupe_key = (
            normalized["task"].casefold(),
            normalized["assignee"].casefold(),
            normalized["due_date"],
        )
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        normalized["needs_review"] = _should_mark_for_review(item, confidence)
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
