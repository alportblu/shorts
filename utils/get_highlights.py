import openai
import logging
import re

def convert_to_seconds(time_str):
    try:
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except ValueError:
        logging.error(f"Time format error for string '{time_str}'. Expected format 'HH:MM:SS'.")
        return 0

def get_highlights(transcript, api_key):
    """Extrai os highlights do vídeo usando GPT"""
    try:
        openai.api_key = api_key
        max_duration = 59  # Limitar cada destaque ao máximo de 59s
        
        # Converter a lista de dicionários em um texto contínuo
        full_transcript = ""
        for entry in transcript:
            full_transcript += f"{entry['text']} "
            
        logging.info("Requesting highlights from OpenAI...")

        # Prompt detalhado para solicitar análise contextual
        prompt = (
            "Analyze the following video transcript and identify the most interesting moments that would make great short videos. "
            "Each highlight should be a complete thought or idea, and can be any length up to 59 seconds maximum. "
            "Focus on finding natural start and end points that capture the essence of each moment, "
            "rather than trying to fill the maximum time. Short, impactful moments are often better than longer ones.\n\n"
            f"Transcript:\n{full_transcript[:8000]}\n\n"  # Limitando a 8000 caracteres
            "Provide key moments with start and end times in the format 'HH:MM:SS - HH:MM:SS' for each highlight. "
            "Remember: highlights can be any length up to 59 seconds, choose natural break points."
        )

        # Solicitação à API OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Usando gpt-3.5-turbo em vez de gpt-4-turbo
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5
        )

        highlights_text = response['choices'][0]['message']['content']
        logging.info(f"Resposta da OpenAI: {highlights_text}")

        # Extração de intervalos de tempo no formato HH:MM:SS
        highlights = re.findall(r"(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})", highlights_text)

        # Converter para o formato que precisamos
        highlights_in_seconds = []
        for start, end in highlights:
            start_seconds = convert_to_seconds(start)
            end_seconds = convert_to_seconds(end)
            duration = end_seconds - start_seconds

            # Só ajustamos se passar de 59 segundos
            if duration > max_duration:
                end_seconds = start_seconds + max_duration

            # Aceitamos qualquer duração menor que 59 segundos
            highlights_in_seconds.append({
                "start_time": start_seconds,
                "end_time": end_seconds
            })

        # Limitar a 6 highlights
        highlights_in_seconds = highlights_in_seconds[:6]

        # Validação final
        if not highlights_in_seconds:
            logging.error("No valid highlights were found.")
            raise ValueError("No valid highlights found")
        else:
            logging.info(f"Valid highlights: {highlights_in_seconds}")

        return highlights_in_seconds

    except Exception as e:
        logging.error(f"Error getting highlights: {e}")
        raise

