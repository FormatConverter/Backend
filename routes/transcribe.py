from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
from docx import Document
from io import BytesIO
import json
from reportlab.pdfgen import canvas
from pywhispercpp.model import Model
import os
import subprocess
import argostranslate.package
import argostranslate.translate

transcribe_routes = Blueprint("transcribe_routes", __name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

FFMPEG_WORKERS = 4

SUPPORTED_LANGUAGES = [
    'ar', 'az', 'zh', 'nl', 'en', 'fi', 'fr', 'de', 'hi', 'hu', 'id', 'ga', 'it', 'ja', 'ko', 'pl', 'pt', 'ru', 'es', 'sv', 'tr', 'uk', 'vi'
]

def transcribe_audio(audio_file_path, language=None):
    try:
        model = Model(f'base-q5_1', n_threads=12)
        if language:
            segments = model.transcribe(audio_file_path, language=language)
        else:
            segments = model.transcribe(audio_file_path)
        
        output = " ".join([segment.text for segment in segments])
        return output
    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {str(e)}")

def extract_audio_from_video(video_file_path, audio_output_path):
    cmd = [
        'ffmpeg',
        '-i', video_file_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-threads', str(FFMPEG_WORKERS),
        audio_output_path
    ]
    subprocess.run(cmd, check=True)

def generate_transcription_file(transcribed_text, save_format):
    if save_format == "txt":
        file_stream = BytesIO()
        file_stream.write(transcribed_text.encode('utf-8'))
        file_stream.seek(0)
        return file_stream, "transcription.txt", "text/plain"
    
    elif save_format == "docx":
        file_stream = BytesIO()
        doc = Document()
        doc.add_paragraph(transcribed_text)
        doc.save(file_stream)
        file_stream.seek(0)
        return file_stream, "transcription.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    elif save_format == "json":
        file_stream = BytesIO()
        json_data = json.dumps({"transcribed_text": transcribed_text}).encode('utf-8')
        file_stream.write(json_data)
        file_stream.seek(0)
        return file_stream, "transcription.json", "application/json"
    
    elif save_format == "pdf":
        file_stream = BytesIO()
        pdf_canvas = canvas.Canvas(file_stream)
        pdf_canvas.setFont("Helvetica", 12)
        
        page_width, page_height = pdf_canvas._pagesize
        margin = 40
        text_width = page_width - 2 * margin
        y_position = page_height - margin
        
        lines = []
        for line in transcribed_text.splitlines():
            words = line.split(' ')
            current_line = ""
            for word in words:
                if pdf_canvas.stringWidth(current_line + word) <= text_width:
                    current_line += word + " "
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())
        
        for line in lines:
            if y_position < margin:
                pdf_canvas.showPage()
                y_position = page_height - margin
            pdf_canvas.drawString(margin, y_position, line)
            y_position -= 15
        
        pdf_canvas.save()
        file_stream.seek(0)
        return file_stream, "transcription.pdf", "application/pdf"
    
    raise ValueError("Unsupported format")

def translate_text(text, from_code, to_code):
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code,
            available_packages
        )
    )
    argostranslate.package.install_from_path(package_to_install.download())
    
    translated = argostranslate.translate.translate(text, from_code, to_code)
    return translated

def validate_language(language):
    if language not in SUPPORTED_LANGUAGES:
        return jsonify({'error': 'Unsupported language. Please choose from the following: ' + ', '.join(SUPPORTED_LANGUAGES)}), 400
    return None

@transcribe_routes.route('/transcribe_audio', methods=['POST'])
def transcribe_audio_endpoint():
    input_language = request.form.get('input_language', None)
    output_language = request.form.get('output_language', 'en')
    save_file = request.form.get('save_file', False)
    save_format = request.form.get('save_format', 'txt')
    if input_language:
        validation_error = validate_language(input_language)
        if validation_error:
            return validation_error
    
    validation_error = validate_language(output_language)
    if validation_error:
        return validation_error

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    # print("save file is", save_file, "and format is", save_format)
    try:
        transcribed_text = transcribe_audio(filepath, input_language)
        os.remove(filepath)

        if not (input_language == 'en' and output_language == 'en'):
            transcribed_text = translate_text(transcribed_text, input_language or 'en', output_language)

        if save_file and save_format in ['txt', 'docx', 'pdf', 'json']:
            file_stream, filename, mime_type = generate_transcription_file(transcribed_text, save_format)
            return send_file(file_stream, download_name=filename, mimetype=mime_type, as_attachment=True)

        return jsonify({'transcribed_text': transcribed_text})

    except Exception as e:
        os.remove(filepath)
        return jsonify({'error': f'Failed to transcribe audio: {str(e)}'}), 500

@transcribe_routes.route('/transcribe_video', methods=['POST'])
def transcribe_video_endpoint():
    input_language = request.form.get('input_language', None)
    output_language = request.form.get('output_language', 'en')
    save_file = request.form.get('save_file', False)
    save_format = request.form.get('save_format', 'txt')
    if input_language:
        validation_error = validate_language(input_language)
        if validation_error:
            return validation_error
    
    validation_error = validate_language(output_language)
    if validation_error:
        return validation_error

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    video_filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(video_filepath)

    try:
        audio_filepath = os.path.join(UPLOAD_FOLDER, "audio.wav")
        extract_audio_from_video(video_filepath, audio_filepath)
        transcribed_text = transcribe_audio(audio_filepath, input_language)
        os.remove(video_filepath)
        os.remove(audio_filepath)

        if not (input_language == 'en' and output_language == 'en'):
            transcribed_text = translate_text(transcribed_text, input_language or 'en', output_language)

        if save_file and save_format in ['txt', 'docx', 'pdf', 'json']:
            file_stream, filename, mime_type = generate_transcription_file(transcribed_text, save_format)
            return send_file(file_stream, download_name=filename, mimetype=mime_type, as_attachment=True)

        return jsonify({'transcribed_text': transcribed_text})

    except Exception as e:
        os.remove(video_filepath)
        return jsonify({'error': f'Failed to transcribe video: {str(e)}'}), 500

@transcribe_routes.route('/save_transcription', methods=['POST'])
def save_transcription_endpoint():
    data = request.get_json()
    if not data or 'text' not in data or 'format' not in data:
        return jsonify({'error': 'Missing required fields (text, format)'}), 400

    text = data['text']
    save_format = data['format']

    if save_format not in ["txt", "docx", "json", "pdf"]:
        return jsonify({'error': 'Invalid format. Valid options are txt, docx, json, pdf.'}), 400

    try:
        file_stream, filename, mime_type = generate_transcription_file(text, save_format)
        return send_file(
            file_stream,
            download_name=filename,
            mimetype=mime_type,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': f'Failed to generate transcription: {str(e)}'}), 500

@transcribe_routes.route('/translate_text', methods=['POST'])
def translate_text_endpoint():
    data = request.get_json()
    if not data or 'text' not in data or 'from_code' not in data or 'to_code' not in data:
        return jsonify({'error': 'Missing required fields (text, from_code, to_code)'}), 400

    text = data['text']
    from_code = data['from_code']
    to_code = data['to_code']

    try:
        translated_text = translate_text(text, from_code, to_code)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': f'Failed to translate text: {str(e)}'}), 500
