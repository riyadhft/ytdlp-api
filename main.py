from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "yt-dlp API is running", "version": "2.0"})

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
        'socket_timeout': 120,
        'retries': 10,
        'fragment_retries': 10,
        'extractor_retries': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,*/*',
            'Referer': video_url,
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            if not info:
                return jsonify({"error": "Could not extract video info"}), 400

            formats = info.get('formats', [])
            direct_url = None
            filename = f"{info.get('title', 'video')}.mp4"

            # Clean filename - remove special characters
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
            if not filename or filename == '.mp4':
                filename = 'soccer_video.mp4'

            # Find best MP4 URL
            for f in reversed(formats):
                if f.get('ext') == 'mp4' and f.get('url'):
                    height = f.get('height', 0)
                    if height and height <= int(quality):
                        direct_url = f['url']
                        break

            # Fallback
            if not direct_url:
                if info.get('url'):
                    direct_url = info['url']
                elif formats:
                    for f in reversed(formats):
                        if f.get('url'):
                            direct_url = f['url']
                            break

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

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": f"yt-dlp error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/info', methods=['POST'])
def get_video_info():
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400

    video_url = data['url']

    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'socket_timeout': 60,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        }
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
