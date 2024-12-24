from flask import Flask, Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import subprocess
import storage

image_routes = Blueprint("image_routes", __name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
FFMPEG_WORKERS = 4
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

file_mapping = storage.get_file_mapping()

# Endpoint to convert image
@image_routes.route('/convert_image', methods=['POST'])
def convert_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
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
