from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from werkzeug.security import generate_password_hash
from app import get_db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, langsung ke homepage
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            # Setelah login sukses, arahkan sesuai role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('guest.dashboard'))
        
        flash('Username atau password salah', 'danger')
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validasi input
        if not all([username, email, password, confirm_password]):
            flash('Please fill all fields', 'danger')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
            
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        try:
            # Cek apakah email sudah terdaftar
            cur.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cur.fetchone():
                flash('Email already registered', 'danger')
                return redirect(url_for('auth.register'))
            
            # Cek apakah username sudah digunakan
            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                flash('Username already taken', 'danger')
                return redirect(url_for('auth.register'))
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            # Insert user baru
            cur.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, 'guest')
            ''', (username, email, password_hash))
            
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            conn.rollback()
            flash('Registration failed. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
            
        finally:
            cur.close()
            conn.close()
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index')) 