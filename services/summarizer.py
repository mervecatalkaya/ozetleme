"""
Summarizer Service - Metin Özetleme
=====================================
Extractive summarization yöntemiyle metni özetleyen
servis modülü. Cümle skorlama ve sıralama ile
en önemli cümleleri seçer.
"""

import re
from collections import Counter
from services.utils import split_sentences


# ─── Stop Words (modül seviyesinde tek sefer oluşturulur) ──────────────────────
# Türkçe ve İngilizce yaygın kelimeler — özetleme skorlamasında göz ardı edilir.
STOP_WORDS = {
    # Türkçe
    "bir", "ve", "bu", "da", "de", "ile", "için", "olan",
    "ben", "sen", "biz", "siz", "onlar", "şey", "gibi",
    "daha", "çok", "var", "yok", "ne", "nasıl", "ama",
    "fakat", "ancak", "ise", "ya", "hem", "her", "hiç",
    "kadar", "sonra", "önce", "şimdi", "zaman", "olarak",
    "ki", "mi", "mu", "mı", "mü", "bile", "sadece",
    "evet", "hayır", "tamam", "işte", "şu", "aslında",
    # İngilizce
    "the", "is", "at", "which", "on", "a", "an", "and",
    "or", "but", "in", "with", "to", "for", "of", "that",
    "this", "it", "from", "by", "are", "was", "were", "be",
    "have", "has", "had", "not", "they", "we", "you", "he",
    "she", "will", "would", "can", "could", "should", "do",
}


def _score_sentence(sentence: str, word_frequencies: dict) -> float:
    """
    Bir cümlenin önem skorunu hesapla.
    
    Kelime frekanslarına dayalı basit skorlama yöntemi.
    
    Args:
        sentence: Skorlanacak cümle
        word_frequencies: Kelime frekans sözlüğü
    
    Returns:
        Cümle skoru (float)
    """
    words = re.findall(r'\b\w+\b', sentence.lower())
    if not words:
        return 0.0
    
    score = sum(word_frequencies.get(w, 0) for w in words)
    # Uzunluğa göre normalize et (çok uzun cümleleri cezalandır)
    return score / len(words)


def summarize_text(text: str, ratio: float = 0.3) -> str:
    """
    Metni extractive yöntemle özetle.
    
    İşlem adımları:
    1. Metni cümlelere ayır (Whisper uyumlu, noktalama yoksa fallback)
    2. Kelime frekanslarını hesapla
    3. Her cümleyi skorla
    4. En yüksek skorlu cümleleri seç
    5. Orijinal sıralarına göre birleştir
    
    Args:
        text: Özetlenecek metin
        ratio: Seçilecek cümle oranı (0.0 - 1.0, varsayılan %30)
    
    Returns:
        Özet metni
    """
    if not text or len(text.strip()) < 50:
        return text  # Çok kısa metinleri olduğu gibi döndür
    
    # ── 1. Cümlelere Ayır (utils'den ortak fonksiyon) ──
    sentences = split_sentences(text)
    
    if len(sentences) <= 2:
        return text  # 2 veya daha az cümle varsa özetlemeye gerek yok
    
    # ── 2. Kelime Frekanslarını Hesapla ──
    all_words = re.findall(r'\b\w+\b', text.lower())
    # Stop words'ları çıkar
    filtered_words = [w for w in all_words if w not in STOP_WORDS and len(w) > 2]
    word_freq = Counter(filtered_words)
    
    # Frekansları normalize et
    if word_freq:
        max_freq = max(word_freq.values())
        word_freq = {w: f / max_freq for w, f in word_freq.items()}
    
    # ── 3. Cümleleri Skorla ──
    scored = [(i, s, _score_sentence(s, word_freq)) for i, s in enumerate(sentences)]
    
    # ── 4. En İyi Cümleleri Seç ──
    num_sentences = max(1, int(len(sentences) * ratio))
    top_sentences = sorted(scored, key=lambda x: x[2], reverse=True)[:num_sentences]
    
    # ── 5. Orijinal Sıraya Göre Birleştir ──
    top_sentences.sort(key=lambda x: x[0])
    summary = " ".join(s[1] for s in top_sentences)
    
    print(f"[Summarizer] {len(sentences)} cümleden {num_sentences} cümle seçildi.")
    
    return summary
