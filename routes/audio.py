from flask import Flask, Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import atexit
import subprocess

audio_routes = Blueprint("audio_routes", __name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
FFMPEG_WORKERS = 4
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

file_mapping = {}

def allowed_file(filename, allowed_extensions):
    '''
    Check if the file extension is allowed
    '''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(filename):
    """
    Generate a unique filename using uuid to avoid name collisions.
    """
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{extension}"  # generate unique file name with original extension
    return unique_filename

# Audio conversion endpoint
@audio_routes.route('/convert_audio', methods=['POST'])
def convert_audio():
    print("Audio Converting...")
    print(request)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(filename)
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    # get output format from the form and check if it is valid
    output_format = request.form.get('output_format')
    codec = request.form.get('codec')
    bitrate = request.form.get('bitrate')
    sample_rate = request.form.get('sample_rate')
    channels = request.form.get('channels')
    volume = request.form.get('volume')

    if not output_format or '.' in output_format:
        os.remove(filepath)
        return jsonify({'error': 'Invalid or missing output format. Please specify a valid format like "mp3", "wav", etc.'}), 400
    
    input_extension = filename.rsplit('.', 1)[1].lower()
    valid_extensions = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'webm', 'opus', 'aiff']
    if input_extension not in valid_extensions:
        os.remove(filepath)
        return jsonify({'error': 'Unsupported input file format'}), 400

    # generate output file path, and store the mapping between original and converted file names
    output_filename = f"{uuid.uuid4().hex}.{output_format}"
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
    file_mapping[output_filename] = filename.split('.')[0] + '.' + output_format
    
    command = ["ffmpeg", "-i", filepath, "-threads", str(FFMPEG_WORKERS)]

    # Add codec, bitrate, samplerate, channels, volume if specified
    if codec:
        command.extend(["-c:a", codec])

    if bitrate:
        command.extend(["-b:a", bitrate])

    if sample_rate:
        command.extend(["-ar", sample_rate])

    if channels:
        command.extend(["-ac", channels])
    
    if volume:
        try:
            float(volume) # check if the volume is a valid number
            command.extend(["-filter:a", f"volume={volume}"])
        except ValueError:
            os.remove(filepath)
            return jsonify({'error': 'Invalid volume value. Please provide a numeric value.'}), 400


    # add output file path
    command.append(output_filepath)
    print(command)

    # run ffmpeg convert the file
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({
            'message': f'File converted to {output_format} successfully',
            'output_file': output_filename
        })
    except subprocess.CalledProcessError as e:
        os.remove(filepath)
        return jsonify({'error': f'FFmpeg failed: {e.stderr.decode()}'}), 500

