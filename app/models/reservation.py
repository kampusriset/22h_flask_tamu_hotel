from app import get_db
from datetime import datetime

class Reservation:
    def __init__(self, id, user_id, room_id, check_in, check_out, total_price, status, payment_status):
        self.id = id
        self.user_id = user_id
        self.room_id = room_id
        self.check_in = check_in
        self.check_out = check_out
        self.total_price = total_price
        self.status = status
        self.payment_status = payment_status

    @staticmethod
    def create_reservation(user_id, room_id, check_in, check_out):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO reservations (user_id, room_id, check_in, check_out, status)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, room_id, check_in, check_out, 'pending'))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def update_status(id, status):
        conn = get_db()
        cur = conn.cursor()
        try:
            # Update status reservasi
            cur.execute('''
                UPDATE reservations 
                SET status = %s
                WHERE id = %s
            ''', (status, id))
            
            # Update status kamar sesuai status reservasi
            if status == 'confirmed':
                cur.execute('''
                    UPDATE rooms r
                    JOIN reservations res ON r.id = res.room_id
                    SET r.status = 'occupied'
                    WHERE res.id = %s
                ''', (id,))
            elif status in ['cancelled', 'completed']:
                cur.execute('''
                    UPDATE rooms r
                    JOIN reservations res ON r.id = res.room_id
                    SET r.status = 'available'
                    WHERE res.id = %s
                ''', (id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating reservation status: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_user_reservations(user_id):
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT r.*, rm.room_number, rm.room_type 
            FROM reservations r
            JOIN rooms rm ON r.room_id = rm.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        ''', (user_id,))
        reservations = cur.fetchall()
        cur.close()
        conn.close()
        return reservations

    @staticmethod
    def get_all_reservations():
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute('''
            SELECT r.*, u.username, rm.room_number 
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            JOIN rooms rm ON r.room_id = rm.id
            ORDER BY r.created_at DESC
        ''')
        reservations = cur.fetchall()
        cur.close()
        conn.close()
        return reservations 