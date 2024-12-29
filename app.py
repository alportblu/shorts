import os
import time
import json
from flask import Flask, request, render_template, send_from_directory, jsonify, session, redirect, url_for
from utils.download_video import download_video
from utils.extract_audio import extract_audio
from utils.generate_transcript import generate_transcript
from utils.get_highlights import get_highlights
from utils.cut_video import cut_video_with_smart_frame  # Importando a função com frame fixo
from dotenv import load_dotenv
import threading
import logging
import moviepy.editor as mp
from utils.file_manager import FileManager
from threading import Lock
import uuid
from utils.user_manager import UserManager
from functools import wraps
from datetime import datetime
from models.saved_video import SavedVideo
from utils.database import Database

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Dicionário para armazenar múltiplos processos
process_statuses = {}
process_lock = Lock()

# Inicializar gerenciador de arquivos (ainda precisamos disso)
file_manager = FileManager()

# Inicializar gerenciador de usuários
user_manager = UserManager()

# Chave secreta para sessões
app.secret_key = os.environ.get('SECRET_KEY', 'dev')

# Inicializar banco de dados
db = Database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            user_manager.add_user(username, email, password)
            session['username'] = username
            return redirect(url_for('index'))
        except ValueError as e:
            return render_template('register.html', error=str(e))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_manager.authenticate(username, password)
        if user:
            session['username'] = username
            return redirect(url_for('index'))
            
        return render_template('login.html', error="Invalid username or password")
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    """Página inicial"""
    return render_template("index.html")

@app.route("/process", methods=["POST"])
@login_required
def process():
    try:
        username = session['username']
        youtube_url = request.form.get("youtube_url")
        api_key = request.form.get("api_key")
        
        if not youtube_url or not api_key:
            raise ValueError("Missing required parameters")
        
        # Verificar se já existe um processo em andamento
        with process_lock:
            for status in process_statuses.values():
                if status.get('is_processing'):
                    return jsonify({"error": "Another process is already running"}), 400
        
        # Gerar ID único para este processo
        process_id = str(uuid.uuid4())
        
        # Associar processo ao usuário
        with process_lock:
            if username not in process_statuses:
                process_statuses[username] = {}
            process_statuses[username][process_id] = {
                "step": "Starting",
                "progress": 0,
                "error": None,
                "shorts_paths": [],
                "is_processing": True,
                "currentShort": 0,
                "totalShorts": 0
            }
        
        # Iniciar processamento em thread separada
        thread = threading.Thread(
            target=process_video,
            args=(youtube_url, api_key, process_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({"message": "Processing started", "process_id": process_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<process_id>")
def status(process_id):
    """Retorna o status de um processo específico"""
    try:
        with process_lock:
            status = process_statuses.get(process_id)
            if not status:
                return jsonify({"error": "Process not found"}), 404
            return jsonify(status)
    except Exception as e:
        logging.error(f"Error getting status: {e}")
        return jsonify({"error": "Failed to get status"}), 500

@app.route('/shorts/<filename>')
def download_short(filename):
    """Endpoint para download dos shorts"""
    try:
        return send_from_directory(file_manager.base_dir, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return jsonify({"error": "File not found"}), 404

@app.route('/download/<session_id>')
def download_page(session_id):
    """Página de download dos shorts"""
    try:
        # Verificar se o processo existe
        status = process_statuses.get(session_id)
        if not status:
            return render_template("error.html", 
                                error="Sessão não encontrada ou expirada"), 404
            
        # Verificar se o processo terminou
        if not status.get("is_processing") and status.get("step") == "Process completed":
            shorts = status.get("shorts_paths", [])
            if not shorts:
                return render_template("error.html", 
                                    error="Nenhum short encontrado"), 404
                                    
            return render_template("download.html", 
                                shorts=shorts, 
                                session_id=session_id)
        else:
            return render_template("error.html", 
                                error="Processo ainda em andamento"), 400
                                
    except Exception as e:
        logging.error(f"Error loading download page: {e}")
        return render_template("error.html", 
                            error="Erro ao carregar página de download"), 500

@app.route('/delete-short/<filename>', methods=['DELETE'])
def delete_short(filename):
    """Deleta um short específico"""
    try:
        file_path = os.path.join(file_manager.base_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def process_video(youtube_url, api_key, process_id):
    try:
        with process_lock:
            if process_id not in process_statuses:
                process_statuses[process_id] = {
                    "step": "Starting",
                    "progress": 0,
                    "error": None,
                    "shorts_paths": [],
                    "is_processing": True
                }
            status = process_statuses[process_id]
        
        # Criar diretório único para este processo
        process_dir = os.path.join('videos', process_id)
        os.makedirs(process_dir, exist_ok=True)
        
        # Etapa 1: Download do vídeo
        status.update({
            "step": "Downloading video...",
            "progress": 10
        })
        
        video_path = os.path.join(process_dir, "downloaded_video.mp4")
        download_video(youtube_url, video_path)
        
        # Carregar o vídeo para obter a duração
        video = mp.VideoFileClip(video_path)
        video_duration = video.duration
        video.close()  # Importante: fechar o vídeo após usar

        # Etapa 2: Extração do áudio
        status.update({
            "step": "Extracting audio...",
            "progress": 30
        })
        audio_path = extract_audio(video_path)

        # Etapa 3: Geração da transcrição
        status.update({
            "step": "Generating transcript...",
            "progress": 50
        })
        transcript = generate_transcript(youtube_url, api_key)

        # Etapa 4: Identificação dos destaques
        status.update({
            "step": "Identifying highlights...",
            "progress": 70
        })
        highlights = get_highlights(transcript, api_key)

        # Etapa 5: Corte do vídeo
        status.update({
            "step": "Cutting video into shorts...",
            "progress": 90
        })
        
        # Limpar shorts antigos
        output_dir = "shorts"
        os.makedirs(output_dir, exist_ok=True)
        for f in os.listdir(output_dir):
            if f.endswith('.mp4'):
                try:
                    os.remove(os.path.join(output_dir, f))
                except Exception as e:
                    logging.error(f"Error removing old file {f}: {e}")
        
        # Processar vídeo
        output_files = cut_video_with_smart_frame(
            video_path, 
            highlights, 
            file_manager.base_dir
        )
        
        # Garantir que não há duplicatas
        output_files = list(dict.fromkeys(output_files))
        
        # Registrar arquivos
        for filename in output_files:
            file_manager.add_file(filename)
        
        # Atualizar status final
        with process_lock:
            status.update({
                "step": "Process completed",
                "progress": 100,
                "shorts_paths": output_files,
                "is_processing": False
            })

    except Exception as e:
        logging.error(f"Error processing video: {e}")
        with process_lock:
            status.update({
                "step": "Error",
                "progress": 100,
                "error": str(e),
                "is_processing": False
            })

    finally:
        # Cleanup após 30 minutos
        def cleanup():
            time.sleep(1800)
            try:
                if os.path.exists(process_dir):
                    shutil.rmtree(process_dir)
                with process_lock:
                    if process_id in process_statuses:
                        del process_statuses[process_id]
            except Exception as e:
                logging.error(f"Error cleaning up: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()

# Rota para limpar erros e resetar status
@app.route("/reset", methods=["POST"])
def reset():
    """Limpa todos os processos (útil para desenvolvimento)"""
    with process_lock:
        process_statuses.clear()
    return jsonify({"message": "All processes reset successfully"})

# Novas rotas para gerenciar vídeos salvos
@app.route("/save-video", methods=["POST"])
@login_required
def save_video():
    video_path = request.form.get("video_path")
    title = request.form.get("title")
    user_id = session['user_id']
    
    saved_video = SavedVideo(user_id, video_path, title, datetime.now())
    db.save_video(saved_video)
    
    return jsonify({"success": True})

@app.route("/my-videos")
@login_required
def my_videos():
    user_id = session['user_id']
    saved_videos = db.get_user_videos(user_id)
    return render_template("my_videos.html", videos=saved_videos)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

