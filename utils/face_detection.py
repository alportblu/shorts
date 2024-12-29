import cv2

def detect_face(frame):
    # Carregar o modelo de detecção de rosto
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Converter o frame para escala de cinza
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detectar rostos
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
    
    if len(faces) > 0:
        # Pegar o primeiro rosto detectado
        (x, y, w, h) = faces[0]
        return (x, y, w, h)
    else:
        return None
