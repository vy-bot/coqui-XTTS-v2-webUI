import torch
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

import pyaudio
import wave

import hashlib
import os
import time


from TTS.api import TTS  # Make sure to import your TTS library correctly


app = Flask(__name__)



device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

import os
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
    return send_from_directory(os.path.join(script_dir, "wav"), filename)

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


    def find_device_index(p, partial_name):
        """Find the first device that matches the partial name."""
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if partial_name in dev['name']:
                return i
        return None

    # Create an instance of PyAudio
    p = pyaudio.PyAudio()


    partial_device_name = 'VoiceMeeter Inp'

    # Find the device index
    device_index = find_device_index(p, partial_device_name)
    if device_index is None:
        print(f"No device found with partial name '{partial_device_name}'")
        p.terminate()
        exit()


    # Open the WAV file
    wf = wave.open(output_voice, 'rb')

    # Create an instance of PyAudio
    p = pyaudio.PyAudio()

    # Open a Stream with the correct settings
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=device_index)

    # Read data in chunks
    data = wf.readframes(1024)

    # Play the audio file by writing to the stream
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Close PyAudio
    p.terminate()



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
