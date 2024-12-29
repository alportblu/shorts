import logging
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def generate_transcript(youtube_url, api_key=None):  # api_key é opcional
    try:
        # Extrair o ID do vídeo do URL, considerando URLs completos e encurtados
        video_id = None
        if "v=" in youtube_url:
            video_id = youtube_url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in youtube_url:
            video_id = youtube_url.split("youtu.be/")[-1].split("?")[0]
        else:
            raise ValueError("Invalid YouTube URL format")

        # Tentar buscar a transcrição
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'pt'])
        
        # Garantir que o transcript seja uma lista de dicionários
        if not isinstance(transcript, list):
            raise ValueError("Transcrição não está no formato de lista esperado.")

        # Verificar se os dicionários têm as chaves corretas
        for entry in transcript:
            if not all(key in entry for key in ['start', 'duration', 'text']):
                raise ValueError("Cada entrada na transcrição deve conter as chaves 'start', 'duration' e 'text'.")

        # Ajustar os dicionários para conter 'end' em vez de 'duration'
        adjusted_transcript = []
        for entry in transcript:
            start_time = entry['start']
            end_time = start_time + entry['duration']
            adjusted_transcript.append({
                'start': start_time,
                'end': end_time,
                'text': entry['text']
            })

        logging.info("Transcrição gerada com sucesso.")
        return adjusted_transcript

    except TranscriptsDisabled:
        logging.error("Transcrições estão desativadas para este vídeo.")
        return []
    except NoTranscriptFound:
        logging.error("Nenhuma transcrição encontrada para este vídeo.")
        return []
    except Exception as e:
        logging.error(f"Erro ao gerar transcrição: {e}")
        return []
