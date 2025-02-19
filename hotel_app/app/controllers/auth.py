from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            login_user(user)
            flash(f'Selamat datang, {username}!')
            return redirect(url_for('main.home'))
        else:
            flash('Username atau password salah!')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nama = request.form['nama']
        email = request.form['email']
        no_hp = request.form['no_hp']
        role = 'tamu'
        
        if User.query.filter_by(username=username).first():
            flash('Username sudah ada!')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!')
            return redirect(url_for('auth.register'))
            
        user = User(
            username=username, 
            password=password, 
            nama=nama,
            email=email,
            no_hp=no_hp,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Tambahkan route lupa password
@auth_bp.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username tidak ditemukan!')
            return redirect(url_for('auth.lupa_password'))
            
        if password != confirm_password:
            flash('Password tidak cocok!')
            return redirect(url_for('auth.lupa_password'))
        
        # Update password
        user.password = password
        db.session.commit()
        
        flash('Password berhasil direset! Silakan login.')
        return redirect(url_for('auth.login'))
            
    return render_template('auth/lupa_password.html') 