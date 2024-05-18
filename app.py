from flask import Flask, request, jsonify
import requests
import whisper
import os

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")

# Replace with your Make webhook URL
MAKE_WEBHOOK_URL = "YOUR_MAKE_WEBHOOK_URL"

def download_video(video_url, output_file):
    # Convert Dropbox link to direct download link
    if 'www.dropbox.com' in video_url:
        video_url = video_url.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
        video_url = video_url.replace('?dl=0', '')

    # Download the video file
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        raise Exception("Failed to download video")

def trigger_make_webhook(data):
    response = requests.post(MAKE_WEBHOOK_URL, json=data)
    if response.status_code != 200:
        raise Exception("Failed to trigger Make webhook")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    print("Received POST request at /transcribe")
    data = request.json
    video_url = data.get('video_url')
    page_id = data.get('page_id')  # Get the page ID from the request
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    video_file = "video.mp4"
    download_video(video_url, video_file)

    # Transcribe the video file with timestamps
    result = model.transcribe(video_file, fp16=False, language='en', timestamps=True)

    # Extract text and timestamps
    segments = result.get('segments')
    transcription = []
    for segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']
        transcription.append({
            "start_time": start_time,
            "end_time": end_time,
            "text": text
        })

    # Trigger Make webhook with transcription data and page ID
    trigger_make_webhook({"transcription": transcription, "page_id": page_id})

    return jsonify({"transcription": transcription})

@app.route('/')
def index():
    return "Flask server is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
