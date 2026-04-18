"""
Utils - Yardımcı Fonksiyonlar
==============================
Proje genelinde kullanılan yardımcı fonksiyonlar.
Dosya doğrulama, klasör oluşturma, metin işleme vb.
"""

import os
import re
import time


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Dosya uzantısının desteklenip desteklenmediğini kontrol et.
    
    Args:
        filename: Kontrol edilecek dosya adı
        allowed_extensions: İzin verilen uzantılar kümesi (örn: {"mp3", "wav", "m4a"})
    
    Returns:
        True ise dosya uzantısı destekleniyor
    """
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in allowed_extensions


def ensure_directories(*dirs: str) -> None:
    """
    Verilen klasörlerin var olduğundan emin ol, yoksa oluştur.
    
    Args:
        *dirs: Oluşturulacak klasör yolları
    """
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"[Utils] Klasör hazır: {directory}")


def generate_unique_filename(original_filename: str) -> str:
    """
    Dosya adı çakışmasını önlemek için benzersiz dosya adı oluştur.
    
    Orijinal dosya adının başına Unix timestamp ekler.
    Örnek: "toplanti.mp3" → "1713222744_toplanti.mp3"
    
    Args:
        original_filename: Orijinal dosya adı (secure_filename uygulanmış)
    
    Returns:
        Benzersiz dosya adı
    """
    return f"{int(time.time())}_{original_filename}"


def split_sentences(text: str, min_length: int = 10) -> list:
    """
    Metni cümlelere ayır.
    
    Whisper çıktısı Türkçe'de genellikle noktalama işareti koymaz.
    Bu yüzden önce noktalamaya göre denenir, başarısız olursa
    kelime sayısına göre parçalara bölünür.
    
    Strateji:
    1. Noktalama işaretlerine göre böl (.!?)
    2. Eğer noktalama yoksa veya tek parça kaldıysa → kelime gruplarına böl
    3. Boş/kısa cümleleri filtrele
    
    Args:
        text: Bölünecek metin
        min_length: Minimum cümle karakter uzunluğu
    
    Returns:
        Cümle listesi
    """
    if not text or not text.strip():
        return []

    # ── 1. Noktalamaya göre böl ──
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Kısa parçaları filtrele
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > min_length]

    # ── 2. Noktalama yoksa veya tek parçaysa → kelime gruplarına böl ──
    if len(sentences) <= 1:
        words = text.split()
        if len(words) <= 5:
            # Metin çok kısa, bölmeye gerek yok
            return [text.strip()] if len(text.strip()) > min_length else []

        chunk_size = 20  # Her ~20 kelimede bir parçala
        sentences = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip() and len(chunk.strip()) > min_length:
                sentences.append(chunk.strip())

    return sentences


def get_file_extension(filename: str) -> str:
    """
    Dosya uzantısını döndür.
    
    Args:
        filename: Dosya adı
    
    Returns:
        Dosya uzantısı (küçük harf, nokta olmadan)
    """
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def format_file_size(size_bytes: int) -> str:
    """
    Byte cinsinden dosya boyutunu okunabilir formata çevir.
    
    Args:
        size_bytes: Dosya boyutu (byte)
    
    Returns:
        Formatlanmış boyut (örn: "2.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_timestamp(seconds: float) -> str:
    """
    Saniye cinsinden zamanı saat:dakika:saniye formatına çevirir.
    
    Örnek: 125.4 -> "00:02:05"
    
    Args:
        seconds: Saniye
        
    Returns:
        Formatlanmış zaman metni
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

