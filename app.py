import os
import subprocess
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter required"}), 400
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title', 'Unknown'),
                "author": info.get('uploader', 'Unknown'),
                "duration": info.get('duration', 0)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream')
def stream_audio():
    url = request.args.get('url')
    if not url:
        return "URL parameter required", 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info['url']
    except Exception as e:
        return str(e), 500

    # Use ffmpeg to stream and convert to mp3 on the fly
    command = [
        'ffmpeg',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',
        '-i', stream_url,
        '-f', 'mp3',
        '-vn', # no video
        '-ar', '44100', # sample rate
        '-ac', '2', # channels
        '-b:a', '128k', # bitrate
        'pipe:1'
    ]

    def generate():
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while True:
                data = process.stdout.read(4096)
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(generate(), mimetype='audio/mpeg')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port)
