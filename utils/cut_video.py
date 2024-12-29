import moviepy.editor as mp
import logging
import os
from utils.subtitle_generator import generate_fancy_subtitles
import time
from utils.person_tracker import PersonTracker
import numpy as np

def cut_video_with_smart_frame(video_path, highlights, output_dir):
    """Corta o vídeo em shorts usando frame fixo e tracking suave"""
    try:
        if not highlights or not isinstance(highlights, list):
            raise ValueError("No valid highlights provided")
            
        logging.info(f"Starting to process {len(highlights)} highlights...")
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        timestamp = int(time.time())
        target_width, target_height = 1080, 1920
        
        with mp.VideoFileClip(video_path) as main_video:
            video_duration = main_video.duration
            
            for idx, highlight in enumerate(highlights, 1):
                try:
                    output_filename = f"short_{timestamp}_{idx}.mp4"
                    output_path = os.path.join(output_dir, output_filename)
                    temp_path = output_path.replace('.mp4', '_temp.mp4')
                    
                    if os.path.exists(output_path):
                        generated_files.append(output_filename)
                        continue
                    
                    logging.info(f"Processing highlight {idx}/{len(highlights)}")
                    start_time = float(highlight['start_time'])
                    end_time = min(float(highlight['end_time']), video_duration)
                    
                    if start_time >= video_duration or end_time - start_time < 1:
                        continue
                    
                    # Extrair o clipe com áudio
                    short = main_video.subclip(start_time, end_time)
                    audio = short.audio
                    
                    # Processar frames
                    tracker = PersonTracker()
                    frames = []
                    
                    # Processar apenas 1 frame a cada 2 para melhor performance
                    for t in np.arange(0, short.duration, 1/15):
                        frame = short.get_frame(t)
                        box = tracker.detect_person(frame)
                        if box:
                            crop_area = tracker.get_crop_area(frame, box, target_width/target_height)
                            cropped = frame[crop_area['y']:crop_area['y']+crop_area['h'], 
                                         crop_area['x']:crop_area['x']+crop_area['w']]
                            frames.append(cropped)
                        else:
                            # Se não detectou, usar frame inteiro
                            frames.append(frame)
                    
                    # Criar clip final
                    tracked_clip = mp.ImageSequenceClip(frames, fps=30)
                    final_clip = tracked_clip.resize((target_width, target_height))
                    final_clip = final_clip.set_audio(audio)
                    
                    # Salvar
                    logging.info(f"Saving temp video: {temp_path}")
                    final_clip.write_videofile(
                        temp_path,
                        codec="libx264",
                        audio_codec="aac",
                        fps=30,
                        threads=4,
                        logger=None
                    )
                    
                    # Adicionar legendas
                    generate_fancy_subtitles(temp_path, output_path)
                    
                    # Limpar
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    generated_files.append(output_filename)
                    
                except Exception as e:
                    logging.error(f"Error processing highlight {idx}: {e}")
                    continue
                    
        return generated_files
        
    except Exception as e:
        logging.error(f"Failed to process video: {str(e)}")
        raise

