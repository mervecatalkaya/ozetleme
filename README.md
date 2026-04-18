# Meeting Assistant - Toplantı Asistanı

Toplantı ses dosyalarını yükleyip otomatik olarak **transkript**, **özet** ve **görev listesi** oluşturan Flask tabanlı web uygulaması.

## Özellikler

- 🎙️ Ses dosyası yükleme (MP3, WAV, M4A)
- 📝 OpenAI Whisper ile otomatik transkript
- 📋 Extractive summarization ile özetleme
- ✅ Rule-based görev çıkarma
- 🎨 Modern, responsive web arayüzü

## Proje Yapısı

```
meeting-assistant/
│
├── app.py                    # Flask ana uygulama
├── requirements.txt          # Python bağımlılıkları
├── README.md                 # Proje dokümantasyonu
├── .gitignore
├── uploads/                  # Yüklenen ses dosyaları
├── outputs/                  # İşlenmiş çıktılar
├── static/
│   ├── css/style.css         # Stil dosyası
│   └── js/script.js          # Frontend JavaScript
├── templates/
│   └── index.html            # Ana sayfa şablonu
└── services/
    ├── __init__.py
    ├── transcriber.py         # Whisper transkripsiyon servisi
    ├── summarizer.py          # Metin özetleme servisi
    ├── task_extractor.py      # Görev çıkarma servisi
    └── utils.py               # Yardımcı fonksiyonlar
```

## Kurulum

### 1. Sanal ortam oluşturun

```bash
python -m venv venv
```

### 2. Sanal ortamı aktifleştirin

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Bağımlılıkları yükleyin

```bash
pip install flask openai-whisper
```

> **Not:** Whisper, PyTorch gerektirir. GPU kullanmak için uygun CUDA sürümüyle PyTorch kurulumu yapın.

### 4. Uygulamayı çalıştırın

```bash
python app.py
```

Uygulama varsayılan olarak `http://localhost:5000` adresinde çalışır.

## Kullanım

1. Tarayıcınızda `http://localhost:5000` adresine gidin
2. Ses dosyanızı sürükleyip bırakın veya tıklayarak seçin
3. "Yükle ve İşle" butonuna tıklayın
4. Sonuçları Transkript, Özet ve Görevler sekmelerinden inceleyin

## Teknolojiler

| Teknoloji | Kullanım Alanı |
|-----------|---------------|
| Flask | Web framework |
| OpenAI Whisper | Speech-to-text |
| Vanilla JS | Frontend etkileşim |
| CSS3 | Modern UI tasarım |

## Lisans

Bu proje bir bitirme projesidir.
