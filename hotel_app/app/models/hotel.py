from app import db
from datetime import datetime

class Tamu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    no_kamar = db.Column(db.String(10), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    no_telp = db.Column(db.String(15))
    status = db.Column(db.String(20), default='reservasi')  # reservasi/menginap

class Kamar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(10), unique=True, nullable=False)
    tipe = db.Column(db.String(50), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='tersedia')
    gambar = db.Column(db.String(200))

class Reservasi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kamar_id = db.Column(db.Integer, db.ForeignKey('kamar.id'), nullable=False)
    nama_tamu = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    no_telp = db.Column(db.String(20))
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reservasi')
    kamar = db.relationship('Kamar', backref='reservasi')
    pembayaran = db.relationship('Pembayaran', backref='reservasi', cascade='all, delete-orphan')

class Pembayaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservasi_id = db.Column(db.Integer, db.ForeignKey('reservasi.id'), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    metode = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 