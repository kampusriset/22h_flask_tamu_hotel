from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.hotel import Tamu, Kamar, Reservasi
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def home():
    if current_user.role == 'admin':
        tamu = Tamu.query.all()
        kamar = Kamar.query.all()
        reservasi = Reservasi.query.all()
        return render_template('admin/home.html',
            tamu=tamu,
            kamar=kamar,
            reservasi=reservasi,
            now=datetime.now()
        )
    else:
        kamar_tersedia = Kamar.query.filter_by(status='tersedia').all()
        return render_template('tamu/home.html', kamar=kamar_tersedia) 