import logging
import os
import shutil
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from faster_whisper import WhisperModel
import time

def generate_fancy_subtitles(input_path, output_path):
    """Gera legendas usando Faster Whisper"""
    try:
        if os.path.exists(output_path):
            logging.warning(f"Output file {output_path} already exists, skipping...")
            return
            
        with VideoFileClip(input_path) as video:
            audio = video.audio
            audio_path = f"temp_audio_{int(time.time())}.wav"
            clips = []
            
            try:
                # Extrair áudio
                audio.write_audiofile(audio_path, codec='pcm_s16le')
                
                # Gerar legendas
                logging.info("Loading model...")
                model = WhisperModel("base", device="cpu", compute_type="int8")
                
                logging.info("Transcribing audio...")
                transcription = model.transcribe(audio_path)
                segments = transcription.segments
                
                # Processar texto em chunks menores
                def chunk_text(text, max_words=4):
                    words = text.split()
                    chunks = []
                    current_chunk = []
                    
                    for word in words:
                        current_chunk.append(word)
                        if len(current_chunk) >= max_words:
                            chunks.append(' '.join(current_chunk))
                            current_chunk = []
                    
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                    return chunks
                
                for segment in segments:
                    if not segment.text or not segment.text.strip():
                        continue
                        
                    chunks = chunk_text(segment.text.strip())
                    if not chunks:
                        continue
                        
                    chunk_duration = (segment.end - segment.start) / len(chunks)
                    if chunk_duration <= 0:
                        continue
                    
                    for i, chunk in enumerate(chunks):
                        start_time = segment.start + (i * chunk_duration)
                        
                        try:
                            txt_clip = (TextClip(
                                chunk,
                                fontsize=80,
                                color='yellow',
                                font='Arial'
                            )
                            .set_position(('center', 'bottom', 150))
                            .set_duration(chunk_duration)
                            .set_start(start_time))
                            
                            clips.append(txt_clip)
                            
                        except Exception as e:
                            logging.error(f"Error creating text clip: {e}")
                            continue
                
                if clips:
                    logging.info("Adding subtitles to video...")
                    final = CompositeVideoClip([video] + clips)
                    
                    logging.info("Saving video...")
                    final.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True
                    )
                else:
                    shutil.copy(input_path, output_path)
                
            finally:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                for clip in clips:
                    try:
                        clip.close()
                    except:
                        pass
                    
    except Exception as e:
        logging.error(f"Error generating subtitles: {e}")
        if os.path.exists(input_path) and not os.path.exists(output_path):
            shutil.copy(input_path, output_path) 