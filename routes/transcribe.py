# import subprocess
# import os
# import torch
# import argostranslate.package
# import argostranslate.translate
# from flask import Blueprint, request, jsonify
# from werkzeug.utils import secure_filename
# from transformers import pipeline
# from fpdf import FPDF
# from docx import Document
# from flask import send_file
# from io import BytesIO
# import json
# from reportlab.pdfgen import canvas

# # Initialize Blueprint
# transcribe_routes = Blueprint("transcribe_routes", __name__)

# # Directories for uploaded and output files
# UPLOAD_FOLDER = 'uploads'
# OUTPUT_FOLDER = 'outputs'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# FFMPEG_WORKERS = 4

# # helper function for transcription
# def transcribe_audio(audio_file_path):
#     device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
#     pipe = pipeline(
#         "automatic-speech-recognition",
#         model="openai/whisper-large-v3-turbo",
#         device=device,
#         return_timestamps=True,
#     )
    
#     result = pipe(audio_file_path)
    
#     return result["text"]

# # helper function for translation
# def translate_text(text, from_code, to_code):
#     argostranslate.package.update_package_index()
#     available_packages = argostranslate.package.get_available_packages()
#     package_to_install = next(
#         filter(
#             lambda x: x.from_code == from_code and x.to_code == to_code,
#             available_packages
#         )
#     )
#     argostranslate.package.install_from_path(package_to_install.download())
    
#     translated = argostranslate.translate.translate(text, from_code, to_code)
#     return translated

# # helper function for extracting audio from video using ffmpeg with multithreading
# def extract_audio_from_video(video_file_path, audio_output_path):
#     # FFmpeg command to extract audio
#     cmd = [
#         'ffmpeg', 
#         '-i', video_file_path,  # input video file
#         '-vn',                  # disable video recording
#         '-acodec', 'pcm_s16le', # audio codec
#         '-ar', '16000',         # sample rate
#         '-ac', '1',             # number of audio channels (mono)
#         '-threads', str(FFMPEG_WORKERS),  # number of threads/workers
#         audio_output_path       # output audio file path
#     ]
    
#     # Run the command using subprocess to extract audio
#     subprocess.run(cmd, check=True)

# # helper function for saving transcription to different formats
# def generate_transcription_file(transcribed_text, save_format):
#     if save_format == "txt":
#         file_stream = BytesIO()
#         file_stream.write(transcribed_text.encode('utf-8'))
#         file_stream.seek(0)
#         return file_stream, "transcription.txt", "text/plain"
    
#     elif save_format == "docx":
#         file_stream = BytesIO()
#         doc = Document()
#         doc.add_paragraph(transcribed_text)
#         doc.save(file_stream)
#         file_stream.seek(0)
#         return file_stream, "transcription.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
#     elif save_format == "json":
#         file_stream = BytesIO()
#         json_data = json.dumps({"transcribed_text": transcribed_text}).encode('utf-8')
#         file_stream.write(json_data)
#         file_stream.seek(0)
#         return file_stream, "transcription.json", "application/json"
    
#     elif save_format == "pdf":
#         file_stream = BytesIO()
#         pdf_canvas = canvas.Canvas(file_stream)
#         pdf_canvas.setFont("Helvetica", 12)
        
#         # Define margins and page width
#         page_width, page_height = pdf_canvas._pagesize
#         margin = 40
#         text_width = page_width - 2 * margin
#         y_position = page_height - margin
        
#         # Split the text into lines that fit within the page width
#         lines = []
#         for line in transcribed_text.splitlines():
#             words = line.split(' ')
#             current_line = ""
#             for word in words:
#                 if pdf_canvas.stringWidth(current_line + word) <= text_width:
#                     current_line += word + " "
#                 else:
#                     lines.append(current_line.strip())
#                     current_line = word + " "
#             lines.append(current_line.strip())
        
#         # Add lines to the PDF
#         for line in lines:
#             if y_position < margin:  # Start a new page if out of space
#                 pdf_canvas.showPage()
#                 y_position = page_height - margin
#             pdf_canvas.drawString(margin, y_position, line)
#             y_position -= 15  # Line spacing
        
#         pdf_canvas.save()
#         file_stream.seek(0)
#         return file_stream, "transcription.pdf", "application/pdf"
    
#     raise ValueError("Unsupported format")

# # Endpoint for transcription
# @transcribe_routes.route('/transcribe_audio', methods=['POST'])
# def transcribe_audio_endpoint():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part in the request'}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected for upload'}), 400

#     filename = secure_filename(file.filename)
#     filepath = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(filepath)

#     try:
#         transcribed_text = transcribe_audio(filepath)
#         os.remove(filepath)
#         return jsonify({'transcribed_text': transcribed_text})
#     except Exception as e:
#         os.remove(filepath)
#         return jsonify({'error': f'Failed to transcribe audio: {str(e)}'}), 500
# # Endpoint for video transcription
# @transcribe_routes.route('/transcribe_video', methods=['POST'])
# def transcribe_video_endpoint():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part in the request'}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected for upload'}), 400

#     filename = secure_filename(file.filename)
#     video_filepath = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(video_filepath)

#     try:
#         # Extract audio from video using ffmpeg
#         audio_filepath = os.path.join(UPLOAD_FOLDER, "audio.wav")
#         extract_audio_from_video(video_filepath, audio_filepath)

#         # Transcribe the extracted audio
#         transcribed_text = transcribe_audio(audio_filepath)
#         os.remove(video_filepath)  # Clean up the uploaded video file
#         os.remove(audio_filepath)  # Clean up the extracted audio file
#         return jsonify({'transcribed_text': transcribed_text})

#     except Exception as e:
#         os.remove(video_filepath)
#         return jsonify({'error': f'Failed to transcribe video: {str(e)}'}), 500

# # Endpoint for saving transcription in various formats
# @transcribe_routes.route('/save_transcription', methods=['POST'])
# def save_transcription_endpoint():
#     data = request.get_json()
#     if not data or 'text' not in data or 'format' not in data:
#         return jsonify({'error': 'Missing required fields (text, format)'}), 400

#     text = data['text']
#     save_format = data['format']
#     print(text, save_format)

#     if save_format not in ["txt", "docx", "json", "pdf"]:
#         return jsonify({'error': 'Invalid format. Valid options are txt, docx, json, pdf.'}), 400

#     try:
#         file_stream, filename, mime_type = generate_transcription_file(text, save_format)
#         return send_file(
#             file_stream,
#             download_name=filename,
#             mimetype=mime_type,
#             as_attachment=True
#         )
#     except Exception as e:
#         return jsonify({'error': f'Failed to generate transcription: {str(e)}'}), 500

# # Endpoint for translation
# @transcribe_routes.route('/translate_text', methods=['POST'])
# def translate_text_endpoint():
#     data = request.get_json()
#     if not data or 'text' not in data or 'from_code' not in data or 'to_code' not in data:
#         return jsonify({'error': 'Missing required fields (text, from_code, to_code)'}), 400

#     text = data['text']
#     from_code = data['from_code']
#     to_code = data['to_code']

#     try:
#         translated_text = translate_text(text, from_code, to_code)
#         return jsonify({'translated_text': translated_text})
#     except Exception as e:
#         return jsonify({'error': f'Failed to translate text: {str(e)}'}), 500
