"""
Transcriber Service - Ses Dosyasını Metne Dönüştürme
====================================================

faster-whisper kütüphanesini kullanarak ses dosyalarını
daha güvenilir ve hızlı şekilde metne dönüştüren servis modülü.

Özellikler:
- faster-whisper kullanır
- VAD (Voice Activity Detection) filtresi aktiftir
- Sessizlik/gürültü kaynaklı halüsinasyonları azaltır
- Tek dosya için düz transcript üretebilir
- Meeting processor için segment bazlı çıktı üretebilir
"""

import os
import re
import subprocess
import tempfile
from typing import List

from faster_whisper import WhisperModel


# ─── Yapılandırma ──────────────────────────────────────────────────────────────

MODEL_NAME = "medium"
DEFAULT_LANGUAGE = "tr"
BEAM_SIZE = 5

# Segment filtreleme eşikleri
MIN_SEGMENT_CHARS = 3
MIN_SEGMENT_WORDS = 2
MAX_NO_SPEECH_PROB = 0.50
MIN_AVG_LOGPROB = -1.0


# ─── Model Yükleme (Singleton) ────────────────────────────────────────────────

_model = None


def _get_model() -> WhisperModel:
    """
    faster-whisper modelini yükle veya önbellekten al.
    """
    global _model
    if _model is None:
        print(f"[Transcriber] faster-whisper '{MODEL_NAME}' modeli yükleniyor...")
        print("[Transcriber] İlk çalıştırmada model indirilebileceği için biraz sürebilir.")
        _model = WhisperModel(
            MODEL_NAME,
            device="auto",
            compute_type="default"
        )
        print("[Transcriber] Model başarıyla yüklendi.")
    return _model


# ─── Audio Ön İşleme ───────────────────────────────────────────────────────────

def _preprocess_audio(input_path: str) -> str:
    """
    Ses dosyasını model için optimize eder:
    - mono kanal
    - 16kHz sample rate
    - wav formatı
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Ses dosyası bulunamadı: {input_path}")

    temp_dir = os.path.dirname(input_path) or "."
    temp_fd, temp_path = tempfile.mkstemp(suffix=".wav", dir=temp_dir)
    os.close(temp_fd)

    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-y",
        temp_path
    ]

    print("[Transcriber] Audio ön işleme başlatılıyor...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(
                f"FFmpeg işlemi başarısız oldu (kod: {result.returncode}).\n"
                f"Hata: {result.stderr[:500]}"
            )

        print(f"[Transcriber] Audio ön işleme tamamlandı: {temp_path}")
        return temp_path

    except FileNotFoundError:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print("[Transcriber] UYARI: FFmpeg bulunamadı. Ön işleme atlanıyor.")
        return input_path

    except subprocess.TimeoutExpired:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise RuntimeError("FFmpeg işlemi zaman aşımına uğradı (120 saniye).")


# ─── Yardımcı Temizlik ve Filtreleme ───────────────────────────────────────────

def _clean_transcript(text: str) -> str:
    """
    Genel transcript temizliği yapar.
    """
    if not text:
        return ""

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_segment_meaningful(text: str) -> bool:
    """
    Segment metni temel kalite kontrollerinden geçiyor mu?
    Çok kısa, anlamsız veya bozuk görünümlü segmentleri eler.
    """
    if not text:
        return False

    text = text.strip()
    if len(text) < MIN_SEGMENT_CHARS:
        return False

    words = text.split()
    if len(words) < MIN_SEGMENT_WORDS:
        return False

    alpha_count = sum(1 for ch in text if ch.isalpha())
    if alpha_count < 2:
        return False

    short_word_count = sum(
        1 for w in words
        if len(re.sub(r"[^\wçğıöşüÇĞIİÖŞÜ]", "", w)) <= 1
    )
    if words and (short_word_count / len(words)) > 0.6:
        return False

    return True


# ─── Ana Transkripsiyon Yardımcısı ─────────────────────────────────────────────

def _run_transcription(audio_path: str, language: str):
    """
    faster-whisper ile VAD aktif transkripsiyon çalıştırır.
    """
    model = _get_model()

    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=BEAM_SIZE,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=300,
            speech_pad_ms=100
        )
    )

    return segments


# ─── Tek Dosya -> Düz Transcript ───────────────────────────────────────────────

def transcribe_audio(filepath: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Ses dosyasını düz metne dönüştürür.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ses dosyası bulunamadı: {filepath}")

    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"[Transcriber] İşleniyor: {filepath} ({file_size_mb:.1f} MB) - faster-whisper (VAD aktif)")

    processed_path = _preprocess_audio(filepath)
    is_temp_file = (processed_path != filepath)

    try:
        segments = _run_transcription(processed_path, language)
        kept_texts: List[str] = []

        for segment in segments:
            text = _clean_transcript((getattr(segment, "text", "") or "").strip())
            no_speech_prob = getattr(segment, "no_speech_prob", 0.0)
            avg_logprob = getattr(segment, "avg_logprob", -999.0)

            if not _is_segment_meaningful(text):
                continue
            if no_speech_prob > MAX_NO_SPEECH_PROB:
                continue
            if avg_logprob < MIN_AVG_LOGPROB:
                continue

            kept_texts.append(text)

        transcript = _clean_transcript(" ".join(kept_texts))

        if not transcript:
            print("[Transcriber] Anlamlı transkript üretilemedi veya tamamen sessizdi.")
            return ""

        print(f"[Transcriber] Transkript tamamlandı. ({len(transcript)} karakter)")
        return transcript

    finally:
        if is_temp_file and os.path.exists(processed_path):
            os.remove(processed_path)
            print(f"[Transcriber] Geçici dosya silindi: {processed_path}")


# ─── Tek Dosya -> Segment Listesi ──────────────────────────────────────────────

def transcribe_audio_segments(filepath: str, language: str = DEFAULT_LANGUAGE) -> List[dict]:
    """
    Ses dosyasını segment bazlı transkript eder.

    Returns:
        [
            {"start": float, "end": float, "text": str},
            ...
        ]
    """
    if not os.path.exists(filepath):
        print(f"[Transcriber] UYARI: Ses dosyası bulunamadı: {filepath}")
        return []

    print(f"[Transcriber] Segment bazlı transkripsiyon başlatıldı: {filepath}")

    processed_path = _preprocess_audio(filepath)
    is_temp_file = (processed_path != filepath)

    segments_data: List[dict] = []

    try:
        segments = _run_transcription(processed_path, language)

        for segment in segments:
            text = _clean_transcript((getattr(segment, "text", "") or "").strip())
            no_speech_prob = getattr(segment, "no_speech_prob", 0.0)
            avg_logprob = getattr(segment, "avg_logprob", -999.0)

            if not _is_segment_meaningful(text):
                continue
            if no_speech_prob > MAX_NO_SPEECH_PROB:
                continue
            if avg_logprob < MIN_AVG_LOGPROB:
                continue

            segments_data.append({
                "start": float(getattr(segment, "start", 0.0)),
                "end": float(getattr(segment, "end", 0.0)),
                "text": text
            })

        print(f"[Transcriber] {len(segments_data)} anlamlı segment çıkarıldı.")
        return segments_data

    finally:
        if is_temp_file and os.path.exists(processed_path):
            os.remove(processed_path)
            print(f"[Transcriber] Geçici dosya silindi: {processed_path}")