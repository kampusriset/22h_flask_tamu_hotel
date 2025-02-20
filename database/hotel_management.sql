-- Hapus dan buat ulang database untuk memastikan data bersih
DROP DATABASE IF EXISTS hotel_management;
CREATE DATABASE hotel_management;
USE hotel_management;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'guest') DEFAULT 'guest',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert admin dan tamu dengan password hash yang benar
INSERT INTO users (username, email, password_hash, role) VALUES 
('admin', 'admin@hotel.com', 'pbkdf2:sha256:1000000$s3WXU67S95qVXOrl$00e29bb952070aea47cebf43a249b910348b04a23600b874bd1e8a105830e22d', 'admin'),
('tamu', 'tamu@hotel.com', 'pbkdf2:sha256:1000000$DBwsPIwfeKV2t1na$45eeb95f7280f795037f3c00d07a0a7fe6450dd0cb35a6d85e6305ea45dd603d', 'guest');

-- Create rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    room_type VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    status ENUM('available', 'occupied', 'maintenance') DEFAULT 'available',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create reservations table
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    room_id INT NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'pending',
    payment_status ENUM('unpaid', 'paid') DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'credit_card', 'transfer') NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
);

-- Insert sample rooms
INSERT INTO rooms (room_number, room_type, price, capacity, description) VALUES
-- Standard Rooms
('101', 'Standard', 500000, 2, 'Standard room with 1 queen bed'),
('102', 'Standard', 500000, 2, 'Standard room with 2 single beds'),
('103', 'Standard', 500000, 2, 'Standard room with city view'),

-- Deluxe Rooms
('201', 'Deluxe', 750000, 2, 'Deluxe room with 1 king bed'),
('202', 'Deluxe', 750000, 3, 'Deluxe room with 1 queen bed and 1 single bed'),
('203', 'Deluxe', 750000, 2, 'Deluxe room with balcony and ocean view'),

-- Suite Rooms
('301', 'Suite', 1200000, 4, 'Suite room with 2 bedrooms'),
('302', 'Suite', 1500000, 4, 'Presidential suite with city view'),
('303', 'Suite', 1300000, 4, 'Family suite with living room and kitchen');

-- Create trigger to update room status when reservation is confirmed
DELIMITER //
CREATE TRIGGER after_reservation_update
AFTER UPDATE ON reservations
FOR EACH ROW
BEGIN
    IF NEW.status = 'cancelled' THEN
        UPDATE rooms SET status = 'available'
        WHERE id = NEW.room_id;
    ELSEIF NEW.status = 'confirmed' THEN
        UPDATE rooms SET status = 'occupied'
        WHERE id = NEW.room_id;
    END IF;
END;//
DELIMITER ;

-- Create view for active reservations
CREATE VIEW active_reservations AS
SELECT 
    r.id,
    u.username,
    rm.room_number,
    rm.room_type,
    r.check_in,
    r.check_out,
    r.total_price,
    r.status,
    r.payment_status
FROM reservations r
JOIN users u ON r.user_id = u.id
JOIN rooms rm ON r.room_id = rm.id
WHERE r.status IN ('pending', 'confirmed'); 