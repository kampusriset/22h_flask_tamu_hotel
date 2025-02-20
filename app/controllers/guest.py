from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.reservation import Reservation
from app import get_db
from functools import wraps
from datetime import date, datetime

guest = Blueprint('guest', __name__)

def guest_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'guest':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@guest.route('/dashboard')
@login_required
@guest_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 4
    offset = (page - 1) * per_page
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get total reservations for pagination
    cur.execute('''
        SELECT COUNT(*) as total 
        FROM reservations 
        WHERE user_id = %s AND status IN ('pending', 'confirmed')
    ''', (current_user.id,))
    total_records = cur.fetchone()['total']
    total_pages = (total_records + per_page - 1) // per_page
    
    # Get paginated upcoming reservations
    cur.execute('''
        SELECT r.*, rm.room_number, rm.room_type, rm.price
        FROM reservations r 
        JOIN rooms rm ON r.room_id = rm.id 
        WHERE r.user_id = %s AND r.status IN ('pending', 'confirmed')
        ORDER BY r.check_in ASC
        LIMIT %s OFFSET %s
    ''', (current_user.id, per_page, offset))
    upcoming_reservations = cur.fetchall()
    
    # Get other dashboard data
    cur.execute('''
        SELECT COUNT(*) as active 
        FROM reservations 
        WHERE user_id = %s AND status IN ('pending', 'confirmed')
    ''', (current_user.id,))
    active_reservations = cur.fetchone()['active']
    
    cur.execute('''
        SELECT COUNT(*) as total 
        FROM reservations 
        WHERE user_id = %s
    ''', (current_user.id,))
    total_reservations = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as available FROM rooms WHERE status = 'available'")
    available_rooms = cur.fetchone()['available']
    
    cur.close()
    conn.close()
    
    return render_template('guest/dashboard.html',
                         active_reservations=active_reservations,
                         total_reservations=total_reservations,
                         available_rooms=available_rooms,
                         upcoming_reservations=upcoming_reservations,
                         current_page=page,
                         total_pages=total_pages)

@guest.route('/reservation/new', methods=['GET', 'POST'])
@login_required
@guest_required
def new_reservation():
    if request.method == 'POST':
        room_id = request.form.get('room_id')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        
        # Validasi input
        if not all([room_id, check_in, check_out]):
            flash('Please fill all fields', 'danger')
            return redirect(url_for('guest.new_reservation'))
        
        try:
            # Hitung total harga
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            
            # Ambil harga kamar
            cur.execute('SELECT price FROM rooms WHERE id = %s', (room_id,))
            room = cur.fetchone()
            
            # Hitung jumlah hari
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
            days = (check_out_date - check_in_date).days
            
            # Hitung total
            total_price = room['price'] * days
            
            # Buat reservasi
            cur.execute('''
                INSERT INTO reservations 
                (user_id, room_id, check_in, check_out, total_price, status, payment_status)
                VALUES (%s, %s, %s, %s, %s, 'pending', 'unpaid')
            ''', (current_user.id, room_id, check_in, check_out, total_price))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Reservation created successfully!', 'success')
            return redirect(url_for('guest.dashboard'))
            
        except Exception as e:
            flash('Error creating reservation. Please try again.', 'danger')
            return redirect(url_for('guest.new_reservation'))
    
    # GET request - tampilkan form
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Ambil daftar kamar yang tersedia
    cur.execute('''
        SELECT id, room_number, room_type, price, capacity 
        FROM rooms 
        WHERE status = 'available'
        ORDER BY room_type, room_number
    ''')
    available_rooms = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('guest/reservation_form.html',
                         available_rooms=available_rooms,
                         today=date.today().isoformat())

@guest.route('/reservation/<int:reservation_id>/payment', methods=['GET', 'POST'])
@login_required
@guest_required
def make_payment(reservation_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get reservation details
    cur.execute('''
        SELECT r.*, rm.room_number, rm.room_type 
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.id = %s AND r.user_id = %s
    ''', (reservation_id, current_user.id))
    reservation = cur.fetchone()
    
    if not reservation:
        flash('Reservation not found', 'danger')
        return redirect(url_for('guest.dashboard'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        try:
            # Create payment record
            cur.execute('''
                INSERT INTO payments 
                (reservation_id, amount, payment_method, status)
                VALUES (%s, %s, %s, 'completed')
            ''', (reservation_id, reservation['total_price'], payment_method))
            
            # Update reservation payment status
            cur.execute('''
                UPDATE reservations 
                SET payment_status = 'paid'
                WHERE id = %s
            ''', (reservation_id,))
            
            conn.commit()
            flash('Payment successful!', 'success')
            return redirect(url_for('guest.dashboard'))
            
        except Exception as e:
            flash('Payment failed. Please try again.', 'danger')
    
    cur.close()
    conn.close()
    
    return render_template('guest/payment_form.html', reservation=reservation)

@guest.route('/guest/reservation/<int:id>/cancel', methods=['POST'])
@login_required
@guest_required
def cancel_reservation(id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    try:
        # Cek apakah reservasi milik user yang sedang login
        cur.execute('''
            SELECT r.*, rm.status as room_status, r.room_id 
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.id = %s AND r.user_id = %s
        ''', (id, current_user.id))
        reservation = cur.fetchone()
        
        if not reservation:
            flash('Reservation not found', 'danger')
            return redirect(url_for('guest.dashboard'))
            
        # Hanya bisa cancel jika status masih pending
        if reservation['status'] != 'pending':
            flash('Cannot cancel this reservation', 'danger')
            return redirect(url_for('guest.dashboard'))
        
        # Update status reservasi
        cur.execute('''
            UPDATE reservations 
            SET status = 'cancelled'
            WHERE id = %s AND user_id = %s
        ''', (id, current_user.id))
        
        # Update status kamar menjadi available
        cur.execute('''
            UPDATE rooms 
            SET status = 'available'
            WHERE id = %s
        ''', (reservation['room_id'],))
        
        conn.commit()
        flash('Reservation cancelled successfully', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Error: {str(e)}")
        flash('Failed to cancel reservation', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('guest.dashboard'))

@guest.route('/reservation/<int:reservation_id>/invoice')
@login_required
@guest_required
def view_invoice(reservation_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get reservation with payment details
    cur.execute('''
        SELECT r.*, u.username, u.email, 
               rm.room_number, rm.room_type, rm.price,
               p.id as payment_id, p.payment_method, p.payment_date
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN rooms rm ON r.room_id = rm.id
        JOIN payments p ON r.id = p.reservation_id
        WHERE r.id = %s AND r.user_id = %s AND r.payment_status = 'paid'
    ''', (reservation_id, current_user.id))
    
    data = cur.fetchone()
    cur.close()
    conn.close()
    
    if not data:
        flash('Invoice not found or payment not completed', 'danger')
        return redirect(url_for('guest.dashboard'))
    
    # Calculate number of nights
    check_in = datetime.strptime(str(data['check_in']), '%Y-%m-%d')
    check_out = datetime.strptime(str(data['check_out']), '%Y-%m-%d')
    nights = (check_out - check_in).days
    
    # Create payment object
    payment = {
        'id': data['payment_id'],
        'payment_method': data['payment_method'],
        'payment_date': datetime.strptime(str(data['payment_date']), '%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('guest/invoice.html',
                         reservation=data,
                         payment=payment,
                         nights=nights,
                         rate_per_night=data['price']) 