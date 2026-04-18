"""
Meeting Assistant - Ana Uygulama Dosyası
=========================================
Flask tabanlı toplantı asistanı uygulaması.
Ses dosyası yükleme, transkript oluşturma,
özetleme ve görev çıkarma işlemlerini yönetir.
"""

import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Servis modüllerini içe aktar
from services.transcriber import transcribe_audio, process_meeting
from services.summarizer import summarize_text
from services.task_extractor import extract_tasks
from services.utils import allowed_file, ensure_directories, generate_unique_filename

# ─── Flask Uygulaması Yapılandırması ───────────────────────────────────────────

app = Flask(__name__)

# Yükleme ve çıktı klasörleri
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "outputs")

# Maksimum dosya boyutu: 50 MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# Desteklenen ses formatları
app.config["ALLOWED_EXTENSIONS"] = {"mp3", "wav", "m4a", "ogg"}

# Gerekli klasörlerin var olduğundan emin ol
ensure_directories(app.config["UPLOAD_FOLDER"], app.config["OUTPUT_FOLDER"])


# ─── Route Tanımları ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Ana sayfa - dosya yükleme arayüzü."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Ses dosyasını yükle ve işle.
    
    İşlem sırası:
    1. Dosya doğrulama (varlık, uzantı kontrolü)
    2. Dosyayı uploads/ klasörüne kaydet
    3. Whisper ile transkript oluştur
    4. Metni özetle
    5. Görevleri çıkar
    6. Sonuçları JSON olarak döndür
    """
    # ── 1. Dosya Doğrulama ──
    if "audio_file" not in request.files:
        return jsonify({"error": "Dosya seçilmedi."}), 400

    file = request.files["audio_file"]

    if file.filename == "":
        return jsonify({"error": "Dosya adı boş."}), 400

    if not allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
        return jsonify({
            "error": "Desteklenmeyen dosya formatı. Lütfen mp3, wav, m4a veya ogg dosyası yükleyin."
        }), 400

    # ── 2. Dosyayı Kaydet ──
    filename = secure_filename(file.filename)
    filename = generate_unique_filename(filename)  # Çakışmayı önle
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        # ── 3. Transkript Oluştur ──
        transcript = transcribe_audio(filepath)

        if not transcript:
            summary = "Anlamlı bir transkript oluşturulamadı."
            tasks = ["Metinde görev bulunamadı"]
        else:
            # ── 4. Özetleme ──
            summary = summarize_text(transcript)

            # ── 5. Görev Çıkarma ──
            tasks = extract_tasks(transcript)

        # ── 6. Sonuçları Döndür ──
        return jsonify({
            "success": True,
            "filename": filename,
            "transcript": transcript,
            "summary": summary,
            "tasks": tasks
        })

    except Exception as e:
        return jsonify({"error": f"İşlem sırasında hata oluştu: {str(e)}"}), 500


@app.route("/process_meeting", methods=["POST"])
def process_meeting_endpoint():
    """
    Örnek Kullanım: Çok Kullanıcılı Toplantı İşleme
    
    Bu endpoint, farklı kullanıcılara ait farklı ses dosyalarını aynı anda alır,
    transkriptleri çıkarır, sıraya dizer ve birleşik bir metin oluşturur.
    
    Örnek İstek (form-data):
    - user_audio_Merve: (Merve'nin ses dosyası)
    - user_audio_Ahmet: (Ahmet'in ses dosyası)
    """
    channels = []
    
    # ── 1. Gelen Dosyaları Topla ──
    for key, file in request.files.items():
        if key.startswith("user_audio_"):
            # Örnek key: "user_audio_Merve" -> username: "Merve"
            username = key.replace("user_audio_", "")
            
            if file and allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
                filename = secure_filename(file.filename)
                filename = generate_unique_filename(filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                
                channels.append({
                    "username": username,
                    "audio_path": filepath
                })
    
    if not channels:
        return jsonify({"error": "Geçerli ses dosyası bulunamadı."}), 400

    try:
        # ── 2. Toplantıyı İşle (Transkripsiyon & Birleştirme) ──
        result = process_meeting(channels)
        
        combined_transcript = result["transcript"]
        segments = result["segments"]
        
        if not combined_transcript:
            return jsonify({"error": "Anlamlı transkript oluşturulamadı."}), 400

        # ── 3. Özetleme ve Görev Çıkarma (Birleşik Metin Üzerinden) ──
        summary = summarize_text(combined_transcript)
        tasks = extract_tasks(combined_transcript)

        # ── 4. Sonuçları Döndür ──
        return jsonify({
            "success": True,
            "segments": segments,            # Makine okuyabilir yapı
            "transcript": combined_transcript, # İnsan okuyabilir birleşik metin
            "summary": summary,
            "tasks": tasks
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"İşlem sırasında hata oluştu: {str(e)}"}), 500

# ─── Uygulama Başlatma ────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
