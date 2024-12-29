import yt_dlp
import logging
import os

def download_video(youtube_url, output_path):
    """Download video from YouTube"""
    try:
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            
        if not os.path.exists(output_path):
            raise Exception("Download failed")
            
        return output_path
        
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        raise
