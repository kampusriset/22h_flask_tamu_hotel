from app import create_app, db
from app.models.user import User
from app.models.hotel import Kamar

app = create_app()

def init_db():
    with app.app_context():
        db.create_all()
        
        # Buat user admin default
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password='admin123',
                nama='Administrator',
                email='admin@hotel.com',
                no_hp='081234567890',
                role='admin'
            )
            db.session.add(admin)
            
        # Buat beberapa akun tamu default
        default_tamu = [
            {
                'username': 'tamu1',
                'password': 'tamu123',
                'nama': 'Tamu Satu',
                'email': 'tamu1@example.com',
                'no_hp': '081234567891',
                'role': 'tamu'
            }
        ]
        
        for tamu in default_tamu:
            if not User.query.filter_by(username=tamu['username']).first():
                new_tamu = User(
                    username=tamu['username'],
                    password=tamu['password'],
                    nama=tamu['nama'],
                    email=tamu['email'],
                    no_hp=tamu['no_hp'],
                    role=tamu['role']
                )
                db.session.add(new_tamu)
        
        # Tambahkan 9 kamar hotel
        kamar_list = [
            # Kamar Standard (3 kamar)
            Kamar(nomor='101', tipe='Standard', harga=500000, status='tersedia'),
            Kamar(nomor='102', tipe='Standard', harga=500000, status='tersedia'),
            Kamar(nomor='103', tipe='Standard', harga=500000, status='tersedia'),
            
            # Kamar Deluxe (3 kamar)
            Kamar(nomor='201', tipe='Deluxe', harga=800000, status='tersedia'),
            Kamar(nomor='202', tipe='Deluxe', harga=800000, status='tersedia'),
            Kamar(nomor='203', tipe='Deluxe', harga=800000, status='tersedia'),
            
            # Kamar Suite (3 kamar)
            Kamar(nomor='301', tipe='Suite', harga=1200000, status='tersedia'),
            Kamar(nomor='302', tipe='Suite', harga=1200000, status='tersedia'),
            Kamar(nomor='303', tipe='Suite', harga=1200000, status='tersedia'),
        ]

        # Cek apakah kamar sudah ada
        existing_kamar = Kamar.query.all()
        if not existing_kamar:
            for kamar in kamar_list:
                db.session.add(kamar)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 