from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.hotel import Reservasi, Kamar, Tamu, Pembayaran
from app import db
from datetime import datetime
from flask_paginate import Pagination, get_page_parameter

reservasi_bp = Blueprint('reservasi', __name__, url_prefix='/reservasi')

@reservasi_bp.route('/')
@login_required
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 4
    
    # Query reservasi untuk user yang login
    pagination = Reservasi.query.filter_by(user_id=current_user.id)\
        .order_by(Reservasi.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Query kamar yang tersedia
    kamar_tersedia = Kamar.query.filter_by(status='tersedia').all()
    
    return render_template('reservasi/index.html',
        reservasi=pagination.items,
        pagination=pagination,
        kamar=kamar_tersedia
    )

@reservasi_bp.route('/tambah', methods=['POST'])
@login_required
def tambah():
    if request.method == 'POST':
        kamar_id = request.form['kamar_id']
        nama_tamu = request.form['nama_tamu']
        email = request.form['email']
        no_telp = request.form['no_telp']
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
        
        # Validasi tanggal - hanya cek apakah check_in tidak lebih besar dari check_out
        if check_in > check_out:
            flash('Tanggal check-in tidak boleh lebih besar dari check-out!')
            return redirect(url_for('reservasi.index'))
        
        # Buat reservasi baru
        reservasi_baru = Reservasi(
            user_id=current_user.id,
            kamar_id=kamar_id,
            nama_tamu=nama_tamu,
            email=email,
            no_telp=no_telp,
            check_in=check_in,
            check_out=check_out
        )
        
        # Tambahkan ke tabel Tamu
        kamar = Kamar.query.get(kamar_id)
        tamu_baru = Tamu(
            nama=nama_tamu,
            no_kamar=kamar.nomor,
            check_in=check_in,
            check_out=check_out,
            no_telp=no_telp
        )
        
        db.session.add(reservasi_baru)
        db.session.add(tamu_baru)
        db.session.commit()
        
        flash('Reservasi berhasil dibuat!')
        return redirect(url_for('reservasi.index'))

@reservasi_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    reservasi = Reservasi.query.get_or_404(id)
    if reservasi.user_id != current_user.id:
        flash('Anda tidak memiliki akses untuk mengedit reservasi ini!')
        return redirect(url_for('reservasi.index'))
    
    reservasi.nama_tamu = request.form['nama_tamu']
    reservasi.email = request.form['email']
    reservasi.no_telp = request.form['no_telp']
    reservasi.check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
    reservasi.check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
    
    db.session.commit()
    flash('Reservasi berhasil diupdate!')
    return redirect(url_for('reservasi.index'))

@reservasi_bp.route('/hapus/<int:id>')
@login_required
def hapus(id):
    reservasi = Reservasi.query.get_or_404(id)
    if reservasi.user_id != current_user.id:
        flash('Anda tidak memiliki akses untuk menghapus reservasi ini!')
        return redirect(url_for('reservasi.index'))
    
    # Hapus data pembayaran terlebih dahulu jika ada
    if reservasi.pembayaran:
        for pembayaran in reservasi.pembayaran:
            db.session.delete(pembayaran)
    
    # Hapus data tamu yang sesuai
    tamu = Tamu.query.filter_by(
        nama=reservasi.nama_tamu,
        no_kamar=reservasi.kamar.nomor,
        check_in=reservasi.check_in,
        check_out=reservasi.check_out
    ).first()
    
    if tamu:
        db.session.delete(tamu)
    
    # Update status kamar menjadi tersedia jika reservasi confirmed
    if reservasi.status == 'confirmed':
        kamar = reservasi.kamar
        kamar.status = 'tersedia'
    
    # Hapus reservasi
    db.session.delete(reservasi)
    db.session.commit()
    
    flash('Reservasi berhasil dihapus!')
    return redirect(url_for('reservasi.index'))

@reservasi_bp.route('/pembayaran/<int:reservasi_id>')
@login_required
def pembayaran(reservasi_id):
    reservasi = Reservasi.query.get_or_404(reservasi_id)
    if reservasi.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke pembayaran ini!')
        return redirect(url_for('reservasi.index'))
    
    durasi = (reservasi.check_out - reservasi.check_in).days
    total_harga = durasi * reservasi.kamar.harga
    
    return render_template('reservasi/pembayaran.html', 
        reservasi=reservasi, 
        total_harga=total_harga
    )

@reservasi_bp.route('/proses_pembayaran/<int:reservasi_id>', methods=['POST'])
@login_required
def proses_pembayaran(reservasi_id):
    reservasi = Reservasi.query.get_or_404(reservasi_id)
    if reservasi.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke pembayaran ini!')
        return redirect(url_for('reservasi.index'))
    
    metode = request.form['metode_pembayaran']
    durasi = (reservasi.check_out - reservasi.check_in).days
    total_harga = durasi * reservasi.kamar.harga
    
    pembayaran = Pembayaran(
        reservasi_id=reservasi.id,
        jumlah=total_harga,
        metode=metode,
        status='success'
    )
    
    reservasi.status = 'confirmed'
    kamar = reservasi.kamar
    kamar.status = 'terisi'
    
    db.session.add(pembayaran)
    db.session.commit()
    
    return redirect(url_for('reservasi.struk', pembayaran_id=pembayaran.id))

@reservasi_bp.route('/struk/<int:pembayaran_id>')
@login_required
def struk(pembayaran_id):
    pembayaran = Pembayaran.query.get_or_404(pembayaran_id)
    reservasi = pembayaran.reservasi
    
    if reservasi.user_id != current_user.id and current_user.role != 'admin':
        flash('Anda tidak memiliki akses ke struk ini!')
        return redirect(url_for('reservasi.index'))
    
    return render_template('reservasi/struk.html', 
        pembayaran=pembayaran, 
        reservasi=reservasi
    ) 