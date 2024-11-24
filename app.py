from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename, allowed_extensions):
    '''
    Check if the file extension is allowed
    '''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Endpoint to convert MP3 to WAV using FFmpeg
@app.route('/mp3_to_wav', methods=['POST'])
def convert_mp3_to_wav():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    allowed_extensions = {'mp3'}

    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Convert MP3 to WAV using FFmpeg
        try:
            wav_filename = os.path.splitext(filename)[0] + ".wav"
            wav_filepath = os.path.join(OUTPUT_FOLDER, wav_filename)
            command = ["ffmpeg", "-i", filepath, wav_filepath]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.remove(filepath) # remove the uploaded MP3 file
            return jsonify({
                'message': 'File converted successfully',
                'wav_file': wav_filename
            })
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'FFmpeg failed: {e.stderr.decode()}'}), 500

    return jsonify({'error': 'Unsupported file type'}), 400

# Endpoint to convert WAV to MP3 using FFmpeg
@app.route('/wav_to_mp3', methods=['POST'])
def convert_wav_to_mp3():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    if allowed_file(filename, {'wav'}):
        mp3_filename = os.path.splitext(filename)[0] + ".mp3"
        mp3_filepath = os.path.join(OUTPUT_FOLDER, mp3_filename)
        try:
            command = ["ffmpeg", "-i", filepath, mp3_filepath]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.remove(filepath)  # remove the uploaded WAV file
            return jsonify({
                'message': 'WAV converted to MP3 successfully',
                'mp3_file': mp3_filename
            })
        except subprocess.CalledProcessError as e:
            os.remove(filepath)
            return jsonify({'error': f'FFmpeg failed: {e.stderr.decode()}'}), 500

    else:
        os.remove(filepath)
        return jsonify({'error': 'Unsupported file type'}), 400



# Endpoint to download converted WAV
@app.route('/download/<wav_file>', methods=['GET'])
def download_wav(wav_file):
    wav_filepath = os.path.join(OUTPUT_FOLDER, wav_file)
    if os.path.exists(wav_filepath):
        res = send_file(wav_filepath, as_attachment=True)
        os.remove(wav_filepath)
        return res
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
