import json
import os
from models.user import User

class UserManager:
    def __init__(self):
        self.users = {}
        self.users_file = 'data/users.json'
        self.load_users()
        
    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                for username, user_data in data.items():
                    user = User(username, user_data['email'])
                    user.password_hash = user_data['password_hash']
                    self.users[username] = user
                    
    def save_users(self):
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w') as f:
            data = {
                username: {
                    'email': user.email,
                    'password_hash': user.password_hash
                }
                for username, user in self.users.items()
            }
            json.dump(data, f)
            
    def add_user(self, username, email, password):
        if username in self.users:
            raise ValueError("Username already exists")
            
        user = User(username, email)
        user.set_password(password)
        self.users[username] = user
        self.save_users()
        
    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user.check_password(password):
            return user
        return None 