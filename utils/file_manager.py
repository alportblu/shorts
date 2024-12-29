import os
import uuid
import time
import threading
import logging
from datetime import datetime, timedelta

class FileManager:
    def __init__(self, base_dir='shorts', cleanup_interval=1800):  # 30 minutos
        self.base_dir = base_dir
        self.cleanup_interval = cleanup_interval
        self.files = {}  # {filename: creation_time}
        
        # Criar diretório se não existir
        os.makedirs(base_dir, exist_ok=True)
        
        # Iniciar thread de limpeza
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def generate_unique_filename(self, original_filename):
        """Gera nome único para o arquivo"""
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extension = os.path.splitext(original_filename)[1]
        return f"short_{timestamp}_{unique_id}{extension}"
    
    def add_file(self, filename):
        """Registra novo arquivo com timestamp"""
        self.files[filename] = time.time()
    
    def get_file_path(self, filename):
        """Retorna caminho completo do arquivo"""
        return os.path.join(self.base_dir, filename)
    
    def _cleanup_loop(self):
        """Loop de limpeza de arquivos antigos"""
        while True:
            try:
                current_time = time.time()
                files_to_remove = []
                
                for filename, creation_time in self.files.items():
                    if current_time - creation_time > self.cleanup_interval:
                        file_path = self.get_file_path(filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            files_to_remove.append(filename)
                            logging.info(f"Removed old file: {filename}")
                
                for filename in files_to_remove:
                    del self.files[filename]
                    
            except Exception as e:
                logging.error(f"Error in cleanup loop: {e}")
                
            time.sleep(300)  # Verificar a cada 5 minutos 