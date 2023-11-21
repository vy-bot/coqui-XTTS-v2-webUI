import os
import time
import hashlib
import torch
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from TTS.api import TTS


app = Flask(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")


script_dir = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(script_dir, "wav"), exist_ok=True)
os.makedirs(os.path.join(script_dir, "voices"), exist_ok=True)

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)


app.config['UPLOAD_FOLDER'] = 'voices'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({'message': 'File uploaded successfully'})

    return jsonify({'error': 'Invalid file type'})

@app.route('/voices')
def list_voices():
    directory = app.config['UPLOAD_FOLDER']
    files = os.listdir(directory)
    wav_files = [file for file in files if file.endswith('.wav')]
    return jsonify(wav_files)

@app.route('/audio/<filename>')
def serve_audio_file(filename):
    return send_from_directory(os.path.join(script_dir, "wav"), secure_filename(filename))

@app.route('/convert', methods=['POST'])
def convert_text():
    text = request.form['text']
    voice_filename = request.form['voice']

    # Find the full path of the selected voice file
    voice_file_path = os.path.join('voices', voice_filename)

    target_voice = script_dir+"/"+voice_file_path

    unique_string = text + str(time.time())  # Combine the text and current time
    filename_hash = hashlib.md5(unique_string.encode()).hexdigest()
    output_filename = f"{filename_hash}.wav"
    output_path = f"{script_dir}/wav/{output_filename}"

    # Save the output to a file
    tts.tts_to_file(text=text, speaker_wav=target_voice, language="en", file_path=output_path)

    return jsonify({'audio_url': f"/audio/{output_filename}"})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
