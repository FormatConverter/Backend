from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import atexit
import subprocess

app = Flask(__name__)

CORS(app, origins=["http://localhost:3000"], expose_headers=["Content-Disposition"], supports_credentials=True)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
FFMPEG_WORKERS = 4
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

file_mapping = {} # store orginal file name pair with converted file name

# helper function to check if the file extension is allowed
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
@app.route('/convert_audio', methods=['POST'])
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
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
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

# Endpoint to download converted file
@app.route('/download/<unique_filename>', methods=['GET'])
def download_wav(unique_filename):
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
