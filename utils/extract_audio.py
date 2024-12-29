import os
import logging

def extract_audio(video_path):
    try:
        logging.info("Extracting audio from video...")
        audio_path = video_path.replace('.mp4', '.mp3')
        
        if not os.path.exists('tmp/'):
            os.makedirs('tmp/')
        
        tmp_audio_path = os.path.join('tmp/', os.path.basename(audio_path))
        
        # Adicione a flag '-y' para substituir automaticamente os arquivos existentes
        os.system(f"ffmpeg -y -i {video_path} -q:a 0 -map a {tmp_audio_path}")

        if not os.path.exists(tmp_audio_path):
            raise Exception("Audio extraction failed. No audio file found.")

        return tmp_audio_path
    except Exception as e:
        raise Exception(f"Failed to extract audio: {e}")
