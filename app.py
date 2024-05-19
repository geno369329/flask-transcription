from flask import Flask, request, jsonify
import requests
import whisper
import os

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")

def download_video(video_url, output_file):
    if 'www.dropbox.com' in video_url:
        video_url = video_url.replace('www.dropbox.com', 'dl.dropboxusercontent.com')
        video_url = video_url.replace('?dl=0', '')

    app.logger.info(f"Downloading video from URL: {video_url}")

    response = requests.get(video_url, stream=True)
    app.logger.info(f"HTTP status code for video download: {response.status_code}")

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        app.logger.info(f"Video downloaded successfully: {output_file}")
    else:
        app.logger.error(f"Failed to download video. HTTP status code: {response.status_code}")
        raise Exception("Failed to download video")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    app.logger.info("Received POST request at /transcribe")
    data = request.json
    video_url = data.get('video_url')
    page_id = data.get('page_id')
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400
    if not page_id:
        return jsonify({"error": "No page ID provided"}), 400

    video_file = "video.mp4"
    try:
        download_video(video_url, video_file)
    except Exception as e:
        app.logger.error(f"Error during video download: {str(e)}")
        return jsonify({"error": "Failed to download video"}), 500

    result = model.transcribe(video_file, fp16=False)
    transcription = result['text']
    segments = result['segments']

    transcription_with_timestamps = []
    for segment in segments:
        start = segment['start']
        end = segment['end']
        text = segment['text']
        transcription_with_timestamps.append({
            "start": start,
            "end": end,
            "text": text
        })

    webhook_url = "https://hook.us1.make.com/auddqtllt89eze3bmt1ayoe8qgdvo86f"
    payload = {
        "transcription": transcription_with_timestamps,
        "page_id": page_id
    }
    try:
        webhook_response = requests.post(webhook_url, json=payload)
        app.logger.info(f"Webhook response status code: {webhook_response.status_code}")
    except Exception as e:
        app.logger.error(f"Error sending webhook: {str(e)}")

    return jsonify({"status": "completed", "transcription": transcription_with_timestamps})

@app.route('/')
def index():
    return "Flask server is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
