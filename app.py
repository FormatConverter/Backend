from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from routes.audio import audio_routes
from routes.image import image_routes
from routes.transcribe import transcribe_routes
import os
import atexit
import subprocess
import storage

app = Flask(__name__)
app.register_blueprint(audio_routes, url_prefix='/audio')
app.register_blueprint(image_routes, url_prefix='/image')
app.register_blueprint(transcribe_routes, url_prefix='/transcribe')
CORS(app, origins=["http://localhost:3000"], expose_headers=["Content-Disposition"], supports_credentials=True)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Endpoint to download converted file
@app.route('/download/<unique_filename>', methods=['GET'])
def download_file(unique_filename):
    print("Downloading...")
    original_filename = storage.get_file_mapping.get(unique_filename)
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
