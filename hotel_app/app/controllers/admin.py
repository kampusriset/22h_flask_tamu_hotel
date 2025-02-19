from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.hotel import Tamu, Kamar, Reservasi
from app import db
from datetime import datetime
from flask_paginate import Pagination, get_page_parameter
from functools import wraps
from app.models.user import User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Anda tidak memiliki akses ke halaman ini!')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/tamu')
@login_required
@admin_required
def tamu():
    today = datetime.now().date()
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 4
    
    # Get search parameters
    search = request.args.get('search', '')
    tanggal = request.args.get('tanggal', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Tamu.query
    
    # Apply filters
    if search:
        query = query.filter(Tamu.nama.ilike(f'%{search}%'))
    
    if tanggal:
        tanggal_obj = datetime.strptime(tanggal, '%Y-%m-%d').date()
        query = query.filter(
            db.func.date(Tamu.check_in) <= tanggal_obj,
            db.func.date(Tamu.check_out) >= tanggal_obj
        )
    
    if status:
        query = query.filter(Tamu.status == status)
    
    # Paginate results
    daftar_tamu = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Update status tamu berdasarkan pembayaran
    for tamu in daftar_tamu.items:
        reservasi = Reservasi.query.filter_by(
            nama_tamu=tamu.nama,
            check_in=tamu.check_in,
            check_out=tamu.check_out
        ).join(Kamar).filter(Kamar.nomor == tamu.no_kamar).first()
        
        if reservasi and reservasi.pembayaran:
            for pembayaran in reservasi.pembayaran:
                if pembayaran.status == 'success':
                    tamu.status = 'menginap'
                    break
        else:
            tamu.status = 'reservasi'
    
    db.session.commit()
    
    check_in_today = Tamu.query.filter(
        db.func.date(Tamu.check_in) == today
    ).all()
    
    check_out_today = Tamu.query.filter(
        db.func.date(Tamu.check_out) == today
    ).all()
    
    return render_template('admin/tamu.html', 
        tamu=daftar_tamu.items, 
        check_in_today=check_in_today,
        check_out_today=check_out_today,
        pagination=daftar_tamu,
        now=datetime.now()
    )

@admin_bp.route('/tambah_tamu', methods=['POST'])
@login_required
@admin_required
def tambah_tamu():
    if request.method == 'POST':
        nama = request.form['nama']
        no_kamar = request.form['no_kamar']
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
        no_telp = request.form['no_telp']
        
        # Validasi tanggal - hanya cek apakah check_in tidak lebih besar dari check_out
        if check_in > check_out:
            flash('Tanggal check-in tidak boleh lebih besar dari check-out!')
            return redirect(url_for('admin.tamu'))
        
        # Cari kamar berdasarkan nomor
        kamar = Kamar.query.filter_by(nomor=no_kamar).first()
        if not kamar:
            flash('Kamar tidak ditemukan!')
            return redirect(url_for('admin.tamu'))
            
        # Cek status kamar
        if kamar.status != 'tersedia':
            flash('Kamar sudah terisi!')
            return redirect(url_for('admin.tamu'))
        
        # Buat tamu baru
        tamu_baru = Tamu(
            nama=nama,
            no_kamar=no_kamar,
            check_in=check_in,
            check_out=check_out,
            no_telp=no_telp,
            status='reservasi'
        )
        
        # Buat reservasi dengan admin sebagai user
        reservasi_baru = Reservasi(
            user_id=current_user.id,
            kamar_id=kamar.id,
            nama_tamu=nama,
            no_telp=no_telp,
            check_in=check_in,
            check_out=check_out,
            status='pending'
        )
        
        # Update status kamar
        kamar.status = 'terisi'
        
        db.session.add(tamu_baru)
        db.session.add(reservasi_baru)
        db.session.commit()
        
        flash('Data tamu berhasil ditambahkan!')
        return redirect(url_for('admin.tamu'))

@admin_bp.route('/edit_tamu/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_tamu(id):
    tamu = Tamu.query.get_or_404(id)
    
    # Validasi tanggal
    check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
    check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
    if check_in >= check_out:
        flash('Tanggal check-in/check-out tidak valid!')
        return redirect(url_for('admin.tamu'))
    
    # Update tamu
    tamu.nama = request.form['nama']
    tamu.no_kamar = request.form['no_kamar']
    tamu.check_in = check_in
    tamu.check_out = check_out
    tamu.no_telp = request.form['no_telp']
    
    # Update reservasi terkait
    reservasi = Reservasi.query.filter_by(
        nama_tamu=tamu.nama,
        check_in=tamu.check_in,
        check_out=tamu.check_out
    ).join(Kamar).filter(Kamar.nomor == tamu.no_kamar).first()
    
    if reservasi:
        reservasi.nama_tamu = tamu.nama
        reservasi.no_telp = tamu.no_telp
        reservasi.check_in = check_in
        reservasi.check_out = check_out
    
    db.session.commit()
    flash('Data tamu berhasil diupdate!')
    return redirect(url_for('admin.tamu'))

@admin_bp.route('/tamu/hapus/<int:id>')
@login_required
@admin_required
def hapus_tamu(id):
    tamu = Tamu.query.get_or_404(id)
    
    # Cari reservasi yang terkait dengan tamu ini
    reservasi = Reservasi.query.filter_by(
        nama_tamu=tamu.nama,
        check_in=tamu.check_in,
        check_out=tamu.check_out
    ).join(Kamar).filter(Kamar.nomor == tamu.no_kamar).first()
    
    if reservasi:
        # Hapus pembayaran terkait jika ada
        if reservasi.pembayaran:
            for pembayaran in reservasi.pembayaran:
                db.session.delete(pembayaran)
        
        # Update status kamar jika reservasi confirmed
        if reservasi.status == 'confirmed':
            kamar = reservasi.kamar
            kamar.status = 'tersedia'
        
        # Hapus reservasi
        db.session.delete(reservasi)
    
    # Hapus data tamu
    db.session.delete(tamu)
    db.session.commit()
    
    flash('Data tamu dan reservasi terkait berhasil dihapus!')
    return redirect(url_for('admin.tamu')) 