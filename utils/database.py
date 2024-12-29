import sqlite3
import os
import logging
from datetime import datetime

class Database:
    def __init__(self, db_file='data/shorts.db'):
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        self.db_file = db_file
        self.init_db()
        
    def get_connection(self):
        return sqlite3.connect(self.db_file)
        
    def init_db(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabela de vídeos salvos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS saved_videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        video_path TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        is_deleted BOOLEAN DEFAULT 0
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
            
    def save_video(self, saved_video):
        """Salva um novo vídeo no banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO saved_videos (user_id, video_path, title, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    saved_video.user_id,
                    saved_video.video_path,
                    saved_video.title,
                    saved_video.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ))
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logging.error(f"Error saving video: {e}")
            raise
            
    def get_user_videos(self, user_id):
        """Retorna todos os vídeos salvos de um usuário"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, video_path, title, created_at
                    FROM saved_videos
                    WHERE user_id = ? AND is_deleted = 0
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                videos = []
                for row in cursor.fetchall():
                    videos.append({
                        'id': row[0],
                        'video_path': row[1],
                        'title': row[2],
                        'created_at': datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
                    })
                return videos
                
        except Exception as e:
            logging.error(f"Error getting user videos: {e}")
            return []
            
    def delete_video(self, video_id, user_id):
        """Marca um vídeo como deletado (soft delete)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE saved_videos
                    SET is_deleted = 1
                    WHERE id = ? AND user_id = ?
                ''', (video_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logging.error(f"Error deleting video: {e}")
            return False 