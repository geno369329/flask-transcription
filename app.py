from flask import Flask, request, jsonify
import requests
import whisper
import os
import threading

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")

def download_video(video_url, output_file):
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

def send_webhook(webhook_url, payload):
    try:
        webhook_response = requests.post(webhook_url, json=payload)
        app.logger.info(f"Webhook response status code: {webhook_response.status_code}")
    except Exception as e:
        app.logger.error(f"Error sending webhook: {str(e)}")

def transcribe_video(video_url, page_id, format_value):
    video_file = "video.mp4"
    try:
        download_video(video_url, video_file)
    except Exception as e:
        app.logger.error(f"Error during video download: {str(e)}")
        return

    app.logger.info("Starting transcription")
    try:
        result = model.transcribe(video_file, fp16=False)
    except Exception as e:
        app.logger.error(f"Error during transcription: {str(e)}")
        return

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

    app.logger.info("Transcription completed")

    payload = {
        "transcription": transcription_with_timestamps,
        "page_id": page_id
    }

    # Define your webhooks based on format
    webhooks = {
        "Short Form Video": "https://hook.us1.make.com/7mm5hn9lt3uo7cx454melcbnxuiik0jg",
        "Long Form Video": "https://hook.us1.make.com/auddqtllt89eze3bmt1ayoe8qgdvo86f"
    }

    webhook_url = webhooks.get(format_value)
    if webhook_url:
        send_webhook(webhook_url, payload)
    else:
        app.logger.error(f"No webhook URL found for format: {format_value}")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    app.logger.info("Received POST request at /transcribe")
    data = request.json
    video_url = data.get('video_url')
    page_id = data.get('page_id')
    format_value = data.get('format_value')  # Assuming this property is passed in the request
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400
    if not page_id:
        return jsonify({"error": "No page ID provided"}), 400
    if not format_value:
        return jsonify({"error": "No format value provided"}), 400

    threading.Thread(target=transcribe_video, args=(video_url, page_id, format_value)).start()

    return jsonify({"status": "processing", "message": "Transcription is being processed in the background."})

@app.route('/')
def index():
    return "Flask server is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
