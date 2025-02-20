from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.reservation import Reservation
from functools import wraps
from app import get_db
from datetime import date

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get statistics
    cur.execute('SELECT COUNT(*) as total FROM rooms')
    total_rooms = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as available FROM rooms WHERE status = 'available'")
    available_rooms_count = cur.fetchone()['available']
    
    cur.execute("SELECT COUNT(*) as pending FROM reservations WHERE status = 'pending'")
    pending_reservations = cur.fetchone()['pending']
    
    cur.execute("SELECT COUNT(*) as total FROM users WHERE role = 'guest'")
    total_guests = cur.fetchone()['total']
    
    # Get all rooms
    cur.execute('SELECT * FROM rooms ORDER BY room_number')
    rooms = cur.fetchall()
    
    # Get available rooms untuk form reservasi
    cur.execute("SELECT * FROM rooms WHERE status = 'available' ORDER BY room_type, room_number")
    available_rooms = cur.fetchall()
    
    # Get all rooms untuk form edit
    cur.execute('SELECT * FROM rooms')
    all_rooms = cur.fetchall()
    
    # Get recent reservations
    cur.execute('''
        SELECT r.*, u.username, rm.room_number 
        FROM reservations r 
        JOIN users u ON r.user_id = u.id 
        JOIN rooms rm ON r.room_id = rm.id 
        ORDER BY r.created_at DESC 
        LIMIT 10
    ''')
    reservations = cur.fetchall()
    
    # Get all guests
    cur.execute('SELECT id, username, email FROM users WHERE role = "guest"')
    guests = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin/dashboard.html',
                         total_rooms=total_rooms,
                         available_rooms=available_rooms_count,
                         pending_reservations=pending_reservations,
                         total_guests=total_guests,
                         rooms=rooms,
                         reservations=reservations,
                         guests=guests,
                         available_rooms_list=available_rooms,
                         all_rooms=all_rooms)

@admin.route('/admin/reservation/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_reservation(id):
    status = request.form.get('status')
    Reservation.update_status(id, status)
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/room/add', methods=['POST'])
@login_required
@admin_required
def add_room():
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    price = request.form.get('price')
    capacity = request.form.get('capacity')
    description = request.form.get('description')
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO rooms (room_number, room_type, price, capacity, description)
            VALUES (%s, %s, %s, %s, %s)
        ''', (room_number, room_type, price, capacity, description))
        conn.commit()
        flash('Room added successfully', 'success')
    except Exception as e:
        flash('Failed to add room', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/room/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_room(id):
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    price = request.form.get('price')
    capacity = request.form.get('capacity')
    description = request.form.get('description')
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE rooms 
            SET room_number = %s, room_type = %s, price = %s, 
                capacity = %s, description = %s
            WHERE id = %s
        ''', (room_number, room_type, price, capacity, description, id))
        conn.commit()
        flash('Room updated successfully', 'success')
    except Exception as e:
        flash('Failed to update room', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/room/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_room(id):
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Check if room has active reservations
        cur.execute('''
            SELECT COUNT(*) FROM reservations 
            WHERE room_id = %s AND status IN ('pending', 'confirmed')
        ''', (id,))
        if cur.fetchone()[0] > 0:
            flash('Cannot delete room with active reservations', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        cur.execute('DELETE FROM rooms WHERE id = %s', (id,))
        conn.commit()
        flash('Room deleted successfully', 'success')
    except Exception as e:
        flash('Failed to delete room', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/reservation/add', methods=['POST'])
@login_required
@admin_required
def add_reservation():
    user_id = request.form.get('user_id')
    room_id = request.form.get('room_id')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Hitung total harga
        cur.execute('SELECT price FROM rooms WHERE id = %s', (room_id,))
        room = cur.fetchone()
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        days = (check_out_date - check_in_date).days
        total_price = room[0] * days
        
        # Buat reservasi
        cur.execute('''
            INSERT INTO reservations 
            (user_id, room_id, check_in, check_out, total_price, status, payment_status)
            VALUES (%s, %s, %s, %s, %s, 'pending', 'unpaid')
        ''', (user_id, room_id, check_in, check_out, total_price))
        
        conn.commit()
        flash('Reservation added successfully', 'success')
    except Exception as e:
        flash('Failed to add reservation', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/reservation/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_reservation(id):
    user_id = request.form.get('user_id')
    room_id = request.form.get('room_id')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Hitung total harga
        cur.execute('SELECT price FROM rooms WHERE id = %s', (room_id,))
        room = cur.fetchone()
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        days = (check_out_date - check_in_date).days
        total_price = room[0] * days
        
        # Update reservasi
        cur.execute('''
            UPDATE reservations 
            SET user_id = %s, room_id = %s, check_in = %s, check_out = %s, total_price = %s
            WHERE id = %s
        ''', (user_id, room_id, check_in, check_out, total_price, id))
        
        conn.commit()
        flash('Reservation updated successfully', 'success')
    except Exception as e:
        flash('Failed to update reservation', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/reservation/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_reservation(id):
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM reservations WHERE id = %s', (id,))
        conn.commit()
        flash('Reservation deleted successfully', 'success')
    except Exception as e:
        flash('Failed to delete reservation', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin.dashboard')) 