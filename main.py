from flask import Flask, request, jsonify
import yt_dlp
import os
import tempfile
import threading

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "yt-dlp API is running", "version": "1.0"})

@app.route('/get-url', methods=['POST'])
def get_download_url():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400
    
    video_url = data['url']
    quality = data.get('quality', '1080')
    
    ydl_opts = {
        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if not info:
                return jsonify({"error": "Could not extract video info"}), 400
            
            # Get the best format URL
            formats = info.get('formats', [])
            
            # Try to find a merged/direct MP4 URL
            direct_url = None
            filename = f"{info.get('title', 'video')}.mp4"
            
            # Look for best direct video URL
            for f in reversed(formats):
                if f.get('ext') == 'mp4' and f.get('url'):
                    height = f.get('height', 0)
                    if height and height <= int(quality):
                        direct_url = f['url']
                        break
            
            # Fallback to any available URL
            if not direct_url:
                if info.get('url'):
                    direct_url = info['url']
                elif formats:
                    direct_url = formats[-1].get('url')
            
            if not direct_url:
                return jsonify({"error": "No downloadable URL found"}), 400
            
            return jsonify({
                "status": "success",
                "url": direct_url,
                "filename": filename,
                "title": info.get('title', 'video'),
                "duration": info.get('duration'),
                "height": info.get('height'),
                "ext": "mp4"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400
    
    video_url = data['url']
    
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "title": info.get('title'),
                "duration": info.get('duration'),
                "formats": len(info.get('formats', [])),
                "uploader": info.get('uploader'),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
