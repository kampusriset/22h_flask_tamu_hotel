from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import get_db, login_manager

class User(UserMixin):
    def __init__(self, id, username, email, role, password_hash=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.password_hash = password_hash

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return User(user[0], user[1], user[2], user[4], user[3])
        return None

    @staticmethod
    def get_by_email(email):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return User(user[0], user[1], user[2], user[4], user[3])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return User(user[0], user[1], user[2], user[4], user[3])
        return None

    @staticmethod
    def create_user(username, email, password, role='guest'):
        conn = get_db()
        cur = conn.cursor()
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        cur.execute('INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)',
                   (username, email, password_hash, role))
        conn.commit()
        cur.close()
        conn.close()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id) 