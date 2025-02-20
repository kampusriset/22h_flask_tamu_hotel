@app.route('/rooms')
def rooms():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get all rooms grouped by type
    cur.execute('SELECT * FROM rooms ORDER BY room_type, room_number')
    all_rooms = cur.fetchall()
    
    # Group rooms by type
    rooms_by_type = {}
    for room in all_rooms:
        if room['room_type'] not in rooms_by_type:
            rooms_by_type[room['room_type']] = []
        rooms_by_type[room['room_type']].append(room)
    
    cur.close()
    conn.close()
    
    return render_template('rooms.html', rooms_by_type=rooms_by_type)

@app.route('/facilities')
def facilities():
    return render_template('facilities.html') 