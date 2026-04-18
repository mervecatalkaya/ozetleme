from services.groq_client import complete_json


def summarize_meeting(text: str) -> str:
    if not text or len(text.strip()) < 20:
        return ""

    prompt = f"""
Asagidaki toplanti transcriptini analiz et.

Kurallar:
- Turkce yaz
- 3-4 cumlelik kisa bir ozet uret
- Uydurma bilgi ekleme
- Sadece verilen transcriptte gecen bilgilere dayan
- Asagidaki JSON formatinda cevap ver

JSON:
{{
  "highlights_summary": "...",
  "overview": "...",
  "topics": ["..."],
  "decisions": ["..."]
}}

Transcript:
\"\"\"
{text[:12000]}
\"\"\"
"""

    result = complete_json(prompt, temperature=0.2)
    if not isinstance(result, dict):
        return ""

    return str(result.get("highlights_summary", "")).strip()
