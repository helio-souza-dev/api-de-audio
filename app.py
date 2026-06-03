import os
import subprocess
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

import urllib.request
import re

def convert_spotify_url(url):
    if 'spotify.com' in url:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read().decode('utf-8')
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                title = title_match.group(1)
                # Clean up title: "Song Name - song and lyrics by Artist | Spotify" -> "Song Name Artist"
                clean_title = title.replace(' - song and lyrics by ', ' ').replace(' | Spotify', '').strip()
                return f"ytsearch1:{clean_title}"
        except Exception:
            pass
    return url

@app.route('/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter required"}), 400
        
    url = convert_spotify_url(url)
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # extract_info returns a dictionary. If it's a search, entries is a list.
            info = ydl.extract_info(url, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]
                
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

    url = convert_spotify_url(url)

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
