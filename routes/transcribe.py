from flask import Flask, Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from transformers import pipeline
import os
import torch
import argostranslate.package 
import argostranslate.translate

transcribe_routes = Blueprint("transcribe_routes", __name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# helper function for transcription
def transcribe_audio(audio_file_path):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3-turbo",
        device=device,
        return_timestamps=True,
    )
    
    result = pipe(audio_file_path)
    
    return result["text"]

# helper function for translation
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

# Endpoint for transcription
@transcribe_routes.route('/transcribe_audio', methods=['POST'])
def transcribe_audio_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        transcribed_text = transcribe_audio(filepath)
        os.remove(filepath)
        return jsonify({'transcribed_text': transcribed_text})
    except Exception as e:
        os.remove(filepath)
        return jsonify({'error': f'Failed to transcribe audio: {str(e)}'}), 500

# Endpoint for translation
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
