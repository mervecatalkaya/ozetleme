import os

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from services.meeting_graph import run_meeting_analysis
from services.output_models import build_meeting_summary_output
from services.summary_agent import summarize_meeting as summarize_meeting_payload
from services.task_extractor import extract_tasks
from services.transcriber import transcribe_audio
from services.utils import allowed_file, ensure_directories, generate_unique_filename


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "outputs")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.config["ALLOWED_EXTENSIONS"] = {"mp3", "wav", "m4a", "ogg"}

ensure_directories(app.config["UPLOAD_FOLDER"], app.config["OUTPUT_FOLDER"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "audio_file" not in request.files:
        return jsonify({"error": "Dosya secilmedi."}), 400

    file = request.files["audio_file"]

    if file.filename == "":
        return jsonify({"error": "Dosya adi bos."}), 400

    if not allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
        return jsonify(
            {
                "error": "Desteklenmeyen dosya formati. Lutfen mp3, wav, m4a veya ogg dosyasi yukleyin."
            }
        ), 400

    filename = secure_filename(file.filename)
    filename = generate_unique_filename(filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        transcript = transcribe_audio(filepath)

        if not transcript:
            summary = "Anlamli bir transkript olusturulamadi."
            tasks = []
            hierarchical_minutes = {"overview": "", "topics": [], "decisions": []}
            summary_payload = {
                "executiveSummary": "",
                "keyDecisions": [],
                "topics": [],
            }
        else:
            summary_payload = summarize_meeting_payload(transcript=transcript, segments=[])
            summary = summary_payload["executiveSummary"]
            hierarchical_minutes = {
                "overview": summary_payload["executiveSummary"],
                "topics": summary_payload["topics"],
                "decisions": summary_payload["keyDecisions"],
            }
            tasks = extract_tasks(transcript)

        output_model = build_meeting_summary_output(
            executive_summary=summary_payload["executiveSummary"],
            key_decisions=summary_payload["keyDecisions"],
            action_items=tasks,
            topics=summary_payload["topics"],
        )
        output_payload = output_model.model_dump(mode="json")

        return jsonify(
            {
                "success": True,
                "filename": filename,
                "transcript": transcript,
                "summary": summary,
                "executiveSummary": output_payload["executiveSummary"],
                "keyDecisions": output_payload["keyDecisions"],
                "actionItems": output_payload["actionItems"],
                "topics": output_payload["topics"],
                "summaryPayload": output_payload,
                "tasks": tasks,
                "hierarchical_minutes": hierarchical_minutes,
            }
        )

    except Exception as exc:
        return jsonify({"error": f"Islem sirasinda hata olustu: {exc}"}), 500


@app.route("/process_meeting", methods=["POST"])
def process_meeting_endpoint():
    channels = []

    for key, file in request.files.items():
        if not key.startswith("user_audio_"):
            continue

        username = key.replace("user_audio_", "")
        if file and allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
            filename = secure_filename(file.filename)
            filename = generate_unique_filename(filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            channels.append({"username": username, "audio_path": filepath})

    if not channels:
        return jsonify({"error": "Gecerli ses dosyasi bulunamadi."}), 400

    try:
        result = run_meeting_analysis(channels)
        if not result["transcript"]:
            return jsonify({"error": "Anlamli transkript olusturulamadi."}), 400

        summary_output = result["frontend_summary"].model_dump(mode="json")
        return jsonify(
            {
                "success": True,
                "segments": result["segments"],
                "transcript": result["transcript"],
                "summary": result["highlights_summary"],
                "executiveSummary": summary_output["executiveSummary"],
                "keyDecisions": summary_output["keyDecisions"],
                "actionItems": summary_output["actionItems"],
                "topics": summary_output["topics"],
                "summaryPayload": summary_output,
                "hierarchical_minutes": result["hierarchical_minutes"],
                "tasks": result["action_items"],
                "errors": result["errors"],
                "completed": result["completed"],
            }
        )
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Islem sirasinda hata olustu: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
