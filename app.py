from flask import Flask, request, jsonify
import requests
import whisper
import os
from threading import Thread
import time
import uuid

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")
jobs = {}

def download_video(video_url, output_file):
    # Download the video file
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        raise Exception("Failed to download video")

def transcribe_video(job_id, video_url):
    video_file = f"{job_id}.mp4"
    download_video(video_url, video_file)

    # Transcribe the video file
    result = model.transcribe(video_file)
    jobs[job_id] = {"status": "completed", "transcription": result['text']}

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.json
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing"}
    thread = Thread(target=transcribe_video, args=(job_id, video_url))
    thread.start()

    return jsonify({"job_id": job_id})

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Invalid job ID"}), 404

    return jsonify(job)

@app.route('/')
def index():
    return "Flask server is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
