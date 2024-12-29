import cv2
import numpy as np
from collections import deque
import logging

class PersonTracker:
    def __init__(self):
        # Carregar apenas o detector de faces (mais confiável que o de corpo)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.history = deque(maxlen=15)  # Reduzido para 15 frames
        self.last_valid_box = None
        
    def detect_person(self, frame):
        """Detecta a pessoa principal no frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # Pegar a maior face
                face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = face
                
                # Expandir área para incluir corpo
                body_height = int(h * 3)
                body_y = max(0, y - h)
                
                self.last_valid_box = {
                    'x': x, 
                    'y': body_y, 
                    'w': w, 
                    'h': body_height
                }
                return self.last_valid_box
                
            # Se não encontrou face, usar última posição válida
            return self.last_valid_box
            
        except Exception as e:
            logging.error(f"Error detecting person: {e}")
            return self.last_valid_box
            
    def get_crop_area(self, frame, box, target_ratio):
        """Calcula área de corte com suavização"""
        h, w = frame.shape[:2]
        
        # Se não tiver detecção, centralizar
        if not box:
            return {'x': (w - int(h * target_ratio)) // 2, 'y': 0, 
                   'w': int(h * target_ratio), 'h': h}
        
        # Centro da pessoa detectada
        person_center_x = box['x'] + box['w'] // 2
        
        # Calcular largura do corte
        crop_width = int(h * target_ratio)
        
        # Calcular posição x do corte
        crop_x = person_center_x - (crop_width // 2)
        
        # Suavização
        if self.history:
            prev_crops = [hist['x'] for hist in self.history]
            crop_x = int(np.mean([crop_x] + prev_crops))
        
        # Garantir que está dentro dos limites
        crop_x = max(0, min(crop_x, w - crop_width))
        
        crop_area = {'x': crop_x, 'y': 0, 'w': crop_width, 'h': h}
        self.history.append(crop_area)
        
        return crop_area 