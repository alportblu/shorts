import subprocess
import logging
import os
import json
import openai  # Importação antiga

def generate_srt_from_audio(video_path, output_srt_path, api_key=None):
    try:
        # Verificar se o arquivo de vídeo existe
        if not os.path.exists(video_path):
            logging.error(f"Video file not found at {video_path}")
            return

        # Extrair áudio em formato WAV temporário
        temp_audio = video_path.replace('.mp4', '_temp.wav')
        logging.info(f"Extracting audio to {temp_audio}")
        
        ffmpeg_extract = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM format
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            temp_audio
        ]
        
        subprocess.run(ffmpeg_extract, check=True)

        # Configurar API key
        openai.api_key = api_key
        
        # Processar áudio e gerar legendas
        with open(temp_audio, 'rb') as audio_file:
            logging.info("Transcribing audio with OpenAI Whisper API")
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="srt"
            )
            
            # Salvar as legendas
            with open(output_srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(response)

        # Limpar arquivo temporário
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        logging.info(f"Subtitles saved to {output_srt_path}")

    except Exception as e:
        logging.error(f"Failed to generate subtitles: {e}")
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        raise

