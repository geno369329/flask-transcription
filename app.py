from flask import Flask, request, jsonify
import requests
import whisper
import os

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")

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

@app.route('/transcribe', methods=['POST'])
def transcribe():
    print("Received POST request at /transcribe")
    data = request.json
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400

    video_file = "video.mp4"
    download_video(video_url, video_file)

    # Transcribe the video file
    result = model.transcribe(video_file)
    return jsonify({"transcription": result['text']})

@app.route('/')
def index():
    return "Flask server is running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
