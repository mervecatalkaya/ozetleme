import re
from datetime import datetime

from services.groq_client import complete_json


def has_explicit_date(text: str) -> bool:
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",
        r"\b\d{1,2}\s+(ocak|subat|mart|nisan|mayis|haziran|temmuz|agustos|eylul|ekim|kasim|aralik)\b",
        r"\b\d{1,2}\s+(şubat|mayıs|ağustos|eylül|kasım|aralık)\b",
    ]
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


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


def extract_tasks(text: str) -> list:
    if not text or len(text.strip()) < 20:
        return []

    prompt = f"""
Asagidaki toplanti transcriptinden yalnizca acik veya makul derecede belirgin gorevleri cikar.

Kurallar:
- Turkce uret
- Gorev yoksa bos liste don
- Uydurma gorev ekleme
- Confidence dusukse yine don ama degeri dusuk olsun
- Uydurma bilgi ekleme
- Transcriptte olmayan tarih uretme
- due_date icin yalnizca transcriptte acik ve net bicimde gecen tarihi kullan
- Eger tarih net degilse due_date alanini bos string "" yap
- Gun adlarindan, baglamdan, bugunun tarihinden veya meeting_date bilgisinden tarih cikarma
- "cuma", "persembe", "yarin", "haftaya" gibi ifadeleri transcriptte acik bir takvim tarihi yoksa ISO tarihe cevirme
- Sadece transcriptte kesin tarih varsa due_date yaz
- JSON disinda aciklama yazma
- Yalnizca JSON liste don

Beklenen format:
[
  {{
    "task": "string",
    "assignee": "string",
    "due_date": "string",
    "priority": "string",
    "confidence": 0.0,
    "type": "string"
  }}
]

Transcript:
\"\"\"
{text[:12000]}
\"\"\"
"""

    result = complete_json(prompt, temperature=0.1)
    if result is None:
        return []

    if isinstance(result, dict):
        if isinstance(result.get("tasks"), list):
            raw_tasks = result["tasks"]
        elif isinstance(result.get("action_items"), list):
            raw_tasks = result["action_items"]
        else:
            return []
    elif isinstance(result, list):
        raw_tasks = result
    else:
        return []

    tasks = []
    explicit_date_exists = has_explicit_date(text)

    for item in raw_tasks:
        if not isinstance(item, dict):
            continue

        confidence = item.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        task = {
            "task": str(item.get("task", "")).strip(),
            "assignee": str(item.get("assignee", "")).strip(),
            "due_date": _normalize_due_date(str(item.get("due_date", "")).strip()),
            "priority": str(item.get("priority", "")).strip(),
            "confidence": round(confidence, 2),
            "type": str(item.get("type", "")).strip(),
        }

        if task["task"]:
            if not explicit_date_exists:
                task["due_date"] = ""
            tasks.append(task)

    return tasks
