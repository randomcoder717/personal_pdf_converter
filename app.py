from flask import Flask, request, jsonify
import pdfplumber
import re
import tempfile
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def parse_questions(text: str):
    question_blocks = re.findall(r'\d+\..*?(?=(?:\n\d+\.|$))', text, re.S)
    questions = []
    for block in question_blocks:
        match = re.match(r'(\d+)\.\s*(.*?)\n', block, re.S)
        if not match:
            continue
        q_number = match.group(1)
        q_text = match.group(2).strip()
        options = re.findall(r'([A-Z])\)\s*(.*?)(?=(?:\n[A-Z]\)|$))', block, re.S)
        option_list = [{"label": opt[0], "text": opt[1].strip().replace("\n", " ")} for opt in options]
        questions.append({"number": q_number, "question": q_text, "options": option_list})
    return questions

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        text = extract_text_from_pdf(tmp_path)
        questions = parse_questions(text)
        return jsonify({"questions": questions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(tmp_path)

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "PDF → Questions API is running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
