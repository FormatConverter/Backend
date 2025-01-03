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

def generate_unique_filename(filename):
    """
    Generate a unique filename using uuid to avoid name collisions.
    """
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    return unique_filename

# Updated convert_image endpoint
@image_routes.route('/convert_image', methods=['POST'])
def convert_image():
    '''
    @description: 
        Convert an image file to a different format using ffmpeg, 
        and save the converted file to the outputs folder. 
        Basic image modification also supported: width, height, quality, rotation, and flip.
    @params:
        - Response Params:
            - Files:
                - file: image file to convert
            - Required:
                - output_format: image format to convert to
            - Optional:
                - width: image width to use
                - height: image height to use
                - quality: image quality to use
                - rotate: image rotation angle to use
                - flip: image flip direction to use
    @returns:
        - JSON response with message and output file name if successful
        - JSON response with error message if unsuccessful
    '''
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(filename)
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    width = request.form.get('width')
    height = request.form.get('height')
    quality = request.form.get('quality')
    rotate = request.form.get('rotate')
    flip = request.form.get('flip')

    output_format = request.form.get('output_format')
    
    if not output_format or '.' in output_format:
        os.remove(filepath)
        return jsonify({'error': 'Invalid or missing output format. Please specify a valid format like "jpg", "png", etc.'}), 400

    input_extension = filename.rsplit('.', 1)[1].lower()
    valid_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'webp']
    if input_extension not in valid_extensions:
        os.remove(filepath)
        return jsonify({'error': 'Unsupported input file format'}), 400

    output_filename = generate_unique_filename(f"output.{output_format}")
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)

    command = ["ffmpeg", "-i", filepath, "-threads", str(FFMPEG_WORKERS)]

    # Apply width and height if provided
    if width and height:
        try:
            width = int(width)
            height = int(height)
            command.extend(["-vf", f"scale={width}:{height}"])
        except ValueError:
            os.remove(filepath)
            return jsonify({'error': 'Invalid width or height values. They must be integers.'}), 400

    # Apply quality if provided
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

    # Apply rotation if provided
    if rotate:
        try:
            rotate_angle = int(rotate)
            if rotate_angle not in [90, 180, 270]:
                raise ValueError
            if rotate_angle == 90:
                command.extend(["-vf", "transpose=1"])
            elif rotate_angle == 180:
                command.extend(["-vf", "transpose=2,transpose=2"])
            elif rotate_angle == 270:
                command.extend(["-vf", "transpose=2"])
        except ValueError:
            os.remove(filepath)
            return jsonify({'error': 'Invalid rotation value. Only 90, 180, and 270 degrees are supported.'}), 400
    
    # First conversion step: Apply width, height, quality, rotation
    temp_filename = generate_unique_filename(f"temp_output.{output_format}")
    temp_filepath = os.path.join(OUTPUT_FOLDER, temp_filename)
    command.append(temp_filepath)

    # run ffmpeg to convert the file
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        os.remove(filepath)
        return jsonify({'error': f'FFmpeg failed during the first conversion: {e.stderr.decode()}'}), 500

    # flip cannot work with the first conversion step, so we need to apply it separately
    if flip:
        flip_command = ["ffmpeg", "-i", temp_filepath, "-threads", str(FFMPEG_WORKERS)]

        # Apply flip if provided
        if flip.lower() == 'h':
            flip_command.extend(["-vf", "hflip"])
        elif flip.lower() == 'v':
            flip_command.extend(["-vf", "vflip"])
        elif flip.lower() == 'hv' or flip.lower() == 'vh':
            flip_command.extend(["-vf", "hflip,vflip"])
        else:
            os.remove(filepath)
            os.remove(temp_filepath)
            return jsonify({'error': 'Invalid flip direction. Please use "horizontal" or "vertical".'}), 400

        # final output file after flip
        flip_command.append(output_filepath)

        # run ffmpeg to convert the file
        try:
            subprocess.run(flip_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            os.remove(filepath)
            os.remove(temp_filepath)
            return jsonify({'error': f'FFmpeg failed during flip conversion: {e.stderr.decode()}'}), 500

    # Clean up the temporary file if flip is not applied
    if not flip:
        os.rename(temp_filepath, output_filepath)

    # Remove the original file and temporary file if flip was applied
    os.remove(filepath)
    if flip:
        os.remove(temp_filepath)

    return jsonify({
        'message': f'File converted to {output_format} successfully',
        'output_file': output_filename
    })
