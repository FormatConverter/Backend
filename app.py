from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import atexit
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
FFMPEG_WORKERS = 4
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# helper function to check if the file extension is allowed
def allowed_file(filename, allowed_extensions):
    '''
    Check if the file extension is allowed
    '''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Conversion endpoint
@app.route('/convert', methods=['POST'])
def convert_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # get output format from the form and check if it is valid
    output_format = request.form.get('output_format')
    codec = request.form.get('codec')
    bitrate = request.form.get('bitrate')
    sample_rate = request.form.get('sample_rate')
    channels = request.form.get('channels')

    if not output_format or '.' in output_format:
        os.remove(filepath)
        return jsonify({'error': 'Invalid or missing output format. Please specify a valid format like "mp3", "wav", etc.'}), 400
    
    input_extension = filename.rsplit('.', 1)[1].lower()
    valid_extensions = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'webm', 'opus', 'aiff']
    if input_extension not in valid_extensions:
        os.remove(filepath)
        return jsonify({'error': 'Unsupported input file format'}), 400

    output_filename = os.path.splitext(filename)[0] + "." + output_format
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)

    # command = ["ffmpeg", "-i", filepath]
    command = ["ffmpeg", "-i", filepath, "-threads", str(FFMPEG_WORKERS)]

    # Add codec, bitrate, samplerate, channels if specified
    if codec:
        command.extend(["-c:a", codec])

    if bitrate:
        command.extend(["-b:a", bitrate])

    if sample_rate:
        command.extend(["-ar", sample_rate])

    if channels:
        command.extend(["-ac", channels])

    # add output file path
    command.append(output_filepath)

    # run ffmpeg convert the file
    try:
        # command = ["ffmpeg", "-i", filepath, output_filepath]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove(filepath)  # remove the uploaded file
        return jsonify({
            'message': f'File converted to {output_format} successfully',
            'output_file': output_filename
        })
    except subprocess.CalledProcessError as e:
        os.remove(filepath)
        return jsonify({'error': f'FFmpeg failed: {e.stderr.decode()}'}), 500

# Endpoint to download converted WAV
@app.route('/download/<wav_file>', methods=['GET'])
def download_wav(wav_file):
    wav_filepath = os.path.join(OUTPUT_FOLDER, wav_file)
    if os.path.exists(wav_filepath):
        res = send_file(wav_filepath, as_attachment=True)
        os.remove(wav_filepath)
        return res
    return jsonify({'error': 'File not found'}), 404

def cleanup():
    '''
    Clean up uploaded and output folders
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
