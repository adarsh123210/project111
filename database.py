"""
Courier Management System - Database Setup & Connection
"""

import sqlite3
import hashlib
from config import DB_PATH


def get_connection():
    """Get a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables and seed default data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin','staff')) NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Branches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            phone TEXT,
            manager_id INTEGER,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Staff
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
            employee_id TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Couriers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS couriers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle_type TEXT CHECK(vehicle_type IN ('Bike','Van','Truck')) DEFAULT 'Bike',
            branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
            status TEXT CHECK(status IN ('Available','On Delivery','Off Duty')) DEFAULT 'Available',
            is_active INTEGER DEFAULT 1
        )
    """)

    # Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Parcels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parcels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT UNIQUE NOT NULL,
            sender_id INTEGER NOT NULL REFERENCES customers(id),
            receiver_id INTEGER NOT NULL REFERENCES customers(id),
            parcel_type TEXT CHECK(parcel_type IN ('Document','Package','Fragile','Heavy')) NOT NULL,
            weight_kg REAL DEFAULT 0,
            length_cm REAL DEFAULT 0,
            width_cm REAL DEFAULT 0,
            height_cm REAL DEFAULT 0,
            contents_desc TEXT,
            declared_value REAL DEFAULT 0,
            special_instructions TEXT,
            source_branch_id INTEGER NOT NULL REFERENCES branches(id),
            dest_branch_id INTEGER NOT NULL REFERENCES branches(id),
            current_branch_id INTEGER REFERENCES branches(id),
            assigned_courier_id INTEGER REFERENCES couriers(id) ON DELETE SET NULL,
            status TEXT DEFAULT 'Booked',
            total_charge REAL DEFAULT 0,
            booked_by INTEGER REFERENCES users(id),
            booked_at TEXT DEFAULT (datetime('now','localtime')),
            estimated_delivery TEXT,
            delivered_at TEXT
        )
    """)

    # Tracking Events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracking_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id INTEGER NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            location TEXT,
            updated_by INTEGER REFERENCES users(id),
            remarks TEXT,
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Branch Transfers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branch_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id INTEGER NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
            from_branch_id INTEGER NOT NULL REFERENCES branches(id),
            to_branch_id INTEGER NOT NULL REFERENCES branches(id),
            initiated_by INTEGER REFERENCES users(id),
            transfer_status TEXT CHECK(transfer_status IN ('Initiated','In Transit','Received')) DEFAULT 'Initiated',
            initiated_at TEXT DEFAULT (datetime('now','localtime')),
            received_at TEXT
        )
    """)

    # Transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parcel_id INTEGER NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
            amount REAL NOT NULL,
            payment_method TEXT CHECK(payment_method IN ('Cash','Card','UPI','Online')) NOT NULL,
            payment_status TEXT CHECK(payment_status IN ('Paid','Unpaid','Partial')) DEFAULT 'Unpaid',
            recorded_by INTEGER REFERENCES users(id),
            payment_date TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # Delivery Charges Config
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parcel_type TEXT CHECK(parcel_type IN ('Document','Package','Fragile','Heavy')),
            base_charge REAL DEFAULT 0,
            per_kg_rate REAL DEFAULT 0,
            per_km_rate REAL DEFAULT 0,
            express_multiplier REAL DEFAULT 1.0,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Audit Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    conn.commit()
    _seed_default_data(conn)
    conn.close()


def _seed_default_data(conn):
    """Seed initial records for testing and default admin."""
    cursor = conn.cursor()

    # Seed Admin User
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", admin_pass, "admin"),
        )

    # Seed Staff User
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'staff'")
    if cursor.fetchone()[0] == 0:
        staff_pass = hashlib.sha256("staff123".encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("staff", staff_pass, "staff"),
        )

    # Seed Branches
    cursor.execute("SELECT COUNT(*) FROM branches")
    if cursor.fetchone()[0] == 0:
        branches = [
            ("BR-MUM", "Mumbai Central Hub", "123 Marine Drive", "Mumbai", "Maharashtra", "400001", "022-12345678"),
            ("BR-DEL", "Delhi Logistics Hub", "45 Connaught Place", "Delhi", "Delhi", "110001", "011-23456789"),
            ("BR-BLR", "Bangalore Branch", "78 MG Road", "Bangalore", "Karnataka", "560001", "080-34567890"),
            ("BR-PUN", "Pune Distribution Office", "56 FC Road", "Pune", "Maharashtra", "411001", "020-45678901"),
        ]
        cursor.executemany(
            "INSERT INTO branches (branch_code, name, address, city, state, pincode, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
            branches,
        )

    # Link Staff record for sample staff
    cursor.execute("SELECT id FROM users WHERE username = 'staff'")
    staff_user = cursor.fetchone()
    if staff_user:
        cursor.execute("SELECT COUNT(*) FROM staff WHERE user_id = ?", (staff_user["id"],))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO staff (user_id, name, phone, email, branch_id, employee_id) VALUES (?, ?, ?, ?, ?, ?)",
                (staff_user["id"], "Staff Member", "9876543210", "staff@courier.local", 1, "EMP-1001")
            )

    # Seed Default Delivery Charges
    cursor.execute("SELECT COUNT(*) FROM delivery_charges")
    if cursor.fetchone()[0] == 0:
        charges = [
            ("Standard Document", "Document", 30.0, 10.0, 0.3, 1.5),
            ("Standard Package", "Package", 50.0, 15.0, 0.5, 1.5),
            ("Fragile Item", "Fragile", 80.0, 20.0, 0.6, 1.8),
            ("Heavy Cargo", "Heavy", 150.0, 25.0, 0.8, 2.0),
        ]
        cursor.executemany(
            "INSERT INTO delivery_charges (name, parcel_type, base_charge, per_kg_rate, per_km_rate, express_multiplier) VALUES (?, ?, ?, ?, ?, ?)",
            charges,
        )

    # Seed Customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        customers = [
            ("Rahul Sharma", "9823011223", "rahul@example.com", "Flat 12, Sunrise Apts", "Mumbai", "Maharashtra", "400001"),
            ("Anita Desai", "9845011998", "anita@example.com", "Villa 4, Palm Grove", "Pune", "Maharashtra", "411001"),
            ("Vikram Rao", "9899033445", "vikram@example.com", "Plot 105, Ring Road", "Delhi", "Delhi", "110001"),
        ]
        cursor.executemany(
            "INSERT INTO customers (name, phone, email, address, city, state, pincode) VALUES (?, ?, ?, ?, ?, ?, ?)",
            customers,
        )

    conn.commit()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")
