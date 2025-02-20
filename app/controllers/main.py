from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user
from app import get_db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Jika belum login, tampilkan homepage
    if not current_user.is_authenticated:
        return render_template('home.html')
    # Jika sudah login, tampilkan dashboard
    return render_template('home.html')

@main.route('/rooms')
def rooms():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get filter parameters
    room_type = request.args.get('type')
    capacity = request.args.get('capacity')
    price_range = request.args.get('price')
    
    # Base query
    query = '''
        SELECT * FROM rooms 
        WHERE 1=1
    '''
    params = []
    
    # Add filters if specified
    if room_type:
        query += ' AND room_type = %s'
        params.append(room_type)
    
    if capacity:
        query += ' AND capacity >= %s'
        params.append(int(capacity))
    
    if price_range:
        price = int(price_range)
        if price == 500000:
            query += ' AND price < 500000'
        elif price == 1000000:
            query += ' AND price BETWEEN 500000 AND 1000000'
        else:
            query += ' AND price > 1000000'
    
    # Add ordering
    query += ' ORDER BY room_type, room_number'
    
    # Execute query
    cur.execute(query, tuple(params))
    all_rooms = cur.fetchall()
    
    # Group rooms by type
    rooms_by_type = {}
    for room in all_rooms:
        if room['room_type'] not in rooms_by_type:
            rooms_by_type[room['room_type']] = []
        rooms_by_type[room['room_type']].append(room)
    
    cur.close()
    conn.close()
    
    # Get current filter values for form
    current_filters = {
        'type': room_type,
        'capacity': capacity,
        'price': price_range
    }
    
    return render_template('rooms.html', 
                         rooms_by_type=rooms_by_type,
                         current_filters=current_filters)

@main.route('/facilities')
def facilities():
    return render_template('facilities.html')

# Hapus route /dashboard karena tidak digunakan 