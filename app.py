from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import atexit
import subprocess
from transformers import pipeline
import torch
import argostranslate.package 
import argostranslate.translate

from routes.audio import audio_routes

app = Flask(__name__)
app.register_blueprint(audio_routes, url_prefix='/audio')
CORS(app, origins=["http://localhost:3000"], expose_headers=["Content-Disposition"], supports_credentials=True)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


# Endpoint to convert image
@app.route('/convert_image', methods=['POST'])
def convert_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # get image conversion parameters from the form
    width = request.form.get('width')
    height = request.form.get('height')
    quality = request.form.get('quality')

    # get output format from the form and check if it is valid
    output_format = request.form.get('output_format')
    if not output_format or '.' in output_format:
        os.remove(filepath)
        return jsonify({'error': 'Invalid or missing output format. Please specify a valid format like "jpg", "png", etc.'}), 400

    input_extension = filename.rsplit('.', 1)[1].lower()
    valid_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'webp']
    if input_extension not in valid_extensions:
        os.remove(filepath)
        return jsonify({'error': 'Unsupported input file format'}), 400

    output_filename = os.path.splitext(filename)[0] + "." + output_format
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)

    command = ["ffmpeg", "-i", filepath, "-threads", str(FFMPEG_WORKERS)]

    if width and height:
        try:
            width = int(width)
            height = int(height)
            command.extend(["-vf", f"scale={width}:{height}"])
        except ValueError:
            os.remove(filepath)
            return jsonify({'error': 'Invalid width or height values. They must be integers.'}), 400

    if quality:
        try:
            quality = int(quality)
            if quality < 1 or quality > 31:
                os.remove(filepath)
                return jsonify({'error': 'Quality must be between 1 and 31.'}), 400
            command.extend(["-q:v", str(quality)])
        except ValueError:
            os.remove(filepath)
            return jsonify({'error': 'Invalid quality value. It must be an integer between 1 and 31.'}), 400

    command.append(output_filepath)
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove(filepath)  # remove the uploaded file
        return jsonify({
            'message': f'File converted to {output_format} successfully',
            'output_file': output_filename
        })
    except subprocess.CalledProcessError as e:
        os.remove(filepath)
        return jsonify({'error': f'FFmpeg failed: {e.stderr.decode()}'}), 500

# Endpoint for transcription
@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        transcribed_text = transcribe_audio(filepath)
        os.remove(filepath)
        return jsonify({'transcribed_text': transcribed_text})
    except Exception as e:
        os.remove(filepath)
        return jsonify({'error': f'Failed to transcribe audio: {str(e)}'}), 500

# Endpoint for translation
@app.route('/translate_text', methods=['POST'])
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

# Endpoint to download converted file
@app.route('/download/<unique_filename>', methods=['GET'])
def download_file(unique_filename):
    print("Downloading...")
    original_filename = file_mapping.get(unique_filename)
    print(original_filename)
    if not original_filename:
        return jsonify({'error': 'File not found'}), 404
    
    download_filepath = os.path.join(OUTPUT_FOLDER, unique_filename)
    if os.path.exists(download_filepath):
        try:
            res = send_file(download_filepath, download_name=original_filename, as_attachment=True)
            # os.remove(download_filepath) # remove the downloaded file
            return res
        except Exception as e:
            return jsonify({'error': f'Failed to download file: {str(e)}'}), 500
    
    return jsonify({'error': 'File not found'}), 404


def cleanup():
    '''
    Clean up uploaded and output folders when the server is shutting down
    '''
    print("Server shutting down. Cleaning up...")
    if os.path.exists(UPLOAD_FOLDER):
        subprocess.run(['rm', '-rf', UPLOAD_FOLDER], check=True)

    if os.path.exists(OUTPUT_FOLDER):
        subprocess.run(['rm', '-rf', OUTPUT_FOLDER], check=True)
    
    print(f"Cleaned up {UPLOAD_FOLDER} and {OUTPUT_FOLDER}")

atexit.register(cleanup)

if __name__ == '__main__':
    app.run(debug=True)
