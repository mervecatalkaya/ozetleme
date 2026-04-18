from concurrent.futures import ThreadPoolExecutor
from services.transcriber import transcribe_audio_segments
from services.summarizer import summarize_meeting
from services.task_extractor import extract_tasks
from services.utils import format_timestamp


def _process_user(p, language):
    username = p.get("username", "Bilinmeyen")
    filepath = p.get("audio_path")

    segments = []

    if not filepath:
        return segments

    print(f"[MeetingProcessor] Kullanıcı işleniyor: {username}")

    try:
        user_segments = transcribe_audio_segments(filepath, language)
    except Exception as e:
        print(f"[MeetingProcessor] HATA ({username}): {e}")
        return segments

    if not user_segments:
        print(f"[MeetingProcessor] {username} için segment bulunamadı.")
        return segments

    for seg in user_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        segments.append({
            "speaker": username,
            "start": seg.get("start", 0),
            "end": seg.get("end", 0),
            "text": text
        })

    return segments


def process_meeting(participants, language="tr"):
    if not participants:
        return {
            "segments": [],
            "transcript": "",
            "summary": "",
            "tasks": []
        }

    all_segments = []

    print(f"[MeetingProcessor] {len(participants)} katılımcı işleniyor...")

    max_workers = min(4, len(participants))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(lambda p: _process_user(p, language), participants)

    for res in results:
        all_segments.extend(res)

    all_segments.sort(key=lambda x: x.get("start", 0))

    transcript_lines = []

    for seg in all_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        s = format_timestamp(seg.get("start", 0))
        e = format_timestamp(seg.get("end", 0))
        speaker = seg.get("speaker", "Bilinmeyen")

        transcript_lines.append(f"[{speaker} | {s} - {e}]\n{text}\n")

    combined_transcript = "\n".join(transcript_lines).strip()

    print(f"[MeetingProcessor] {len(all_segments)} segment üretildi.")

    # NLP işlemleri için daha sade metin
    plain_text = " ".join(
        seg.get("text", "").strip()
        for seg in all_segments
        if seg.get("text", "").strip()
    )

    summary = ""
    tasks = []

    if plain_text:
        short_text = plain_text[:5000]

        print("[MeetingProcessor] Özetleme başlıyor...")
        summary = summarize_meeting(short_text)

        print("[MeetingProcessor] Görev çıkarma başlıyor...")
        tasks = extract_tasks(short_text)
    else:
        print("[MeetingProcessor] UYARI: Transcript boş.")

    return {
        "segments": all_segments,
        "transcript": combined_transcript,
        "summary": summary,
        "tasks": tasks
    }