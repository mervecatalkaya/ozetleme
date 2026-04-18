"""
Task Extractor Service - Görev Çıkarma
========================================
Transkript metninden görev cümlelerini çıkaran
servis modülü. Performans odaklı yazılmıştır.
"""

import re

# ─── Görev Anahtar Kelimeleri ──────────────────────────────────────────────────
TASK_KEYWORDS = [
    "yapılacak",
    "yapılması gerekiyor",
    "görev",
    "sorumlu",
    "kontrol edilecek",
    "planlandı",
    "karar verildi",
    "yapılmalı",
    "takip edilecek",
    "hazırlanacak"
]


def extract_tasks(text: str) -> list:
    """
    Metinden görev cümlelerini yüksek performansla çıkarır.
    Ağır işlemleri kısıtlar ve çok uzun metinlerde kesme yapar.
    
    Args:
        text (str): Görev çıkarılacak transkript metni.
        
    Returns:
        list: Bulunan görevlerin listesi. Boş ise [] döner.
    """

    # 1. Hızlı Güvenlik Kontrolü
    if not text or len(text.strip()) < 15:
        return []

    # 3. Yüksek Boyutlu Metin Kesimi (Sadece ilk 5000 karakteri analiz et)
    if len(text) > 5000:
        text = text[:5000]

    text_lower = text.lower()

    # 2. Hızlı Ön Kontrol (FAST FILTER)
    if not any(keyword in text_lower for keyword in TASK_KEYWORDS):
        return []

    # 5. Basit Regex ile Cümlelere Bölme (Ağır kütüphaneler yerine)
    # Nokta, ünlem veya soru işaretinden sonra gelen boşluklardan cümleleri ayırır.
    raw_sentences = re.split(r'[.!?]+\s+', text)
    
    tasks = []
    seen = set()

    # 6. Sadece ilgili cümleleri al
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if len(sentence) < 5:
            continue
            
        sentence_lower = sentence.lower()

        # Cümle içinde keyword geçiyorsa task olarak ekle
        if any(keyword in sentence_lower for keyword in TASK_KEYWORDS):
            normalized = " ".join(sentence_lower.split()) # Fazla boşlukları yoksay
            
            # 7. Tekrarlı görevleri filtrele
            if normalized not in seen:
                seen.add(normalized)
                tasks.append(sentence)

    # 8. Görev yoksa boş liste döndür (string mesaj yerine)
    if not tasks:
        return []

    print(f"[Task Extractor] Hızlı analiz ile {len(tasks)} görev çıkarıldı.")
    return tasks