from concurrent.futures import ThreadPoolExecutor
from typing import Any

from services.meeting_state import MeetingState
from services.transcriber import transcribe_audio_segments
from services.utils import format_timestamp


def _process_user(participant: dict[str, Any], language: str) -> list[dict]:
    username = participant.get("username", "Bilinmeyen")
    filepath = participant.get("audio_path")

    if not filepath:
        return []

    print(f"[MeetingProcessor] Kullanici isleniyor: {username}")

    try:
        user_segments = transcribe_audio_segments(filepath, language)
    except Exception as exc:
        print(f"[MeetingProcessor] HATA ({username}): {exc}")
        return []

    segments = []
    for seg in user_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        segments.append(
            {
                "speaker": username,
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": text,
            }
        )

    return segments


def build_transcript(segments: list[dict]) -> str:
    transcript_lines = []

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start_value = format_timestamp(seg.get("start", 0))
        end_value = format_timestamp(seg.get("end", 0))
        speaker = seg.get("speaker", "Bilinmeyen")
        transcript_lines.append(f"[{speaker} | {start_value} - {end_value}]\n{text}\n")

    return "\n".join(transcript_lines).strip()


def transcribe_participants(participants: list[dict], language: str = "tr") -> tuple[list[dict], str]:
    if not participants:
        return [], ""

    all_segments = []

    print(f"[MeetingProcessor] {len(participants)} katilimci isleniyor...")

    max_workers = min(4, len(participants))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(lambda item: _process_user(item, language), participants)

    for result in results:
        all_segments.extend(result)

    all_segments.sort(key=lambda item: item.get("start", 0))
    transcript = build_transcript(all_segments)

    print(f"[MeetingProcessor] {len(all_segments)} segment uretildi.")
    return all_segments, transcript


def run_transcription_agent(state: MeetingState) -> dict[str, Any]:
    patch = {
        "segments": [],
        "transcript": "",
        "errors": [],
        "completed": [],
    }

    try:
        participants = state.get("participants", [])
        language = state.get("language", "tr")
        segments, transcript = transcribe_participants(participants, language)

        patch["segments"] = segments
        patch["transcript"] = transcript
        patch["completed"].append("transcription_agent")

        if not transcript.strip():
            patch["errors"].append("transcription_agent: transcript bos.")
    except Exception as exc:  # pragma: no cover
        patch["errors"].append(f"transcription_agent: beklenmeyen hata: {exc}")

    return patch
