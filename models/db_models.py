"""Database CRUD model wrappers for users, branches, staff, customers, parcels, and transactions."""

from database import get_connection
from utils.helpers import hash_password, generate_tracking_number


# --- User Model ---
def authenticate_user(username, password, expected_role=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = (
        "SELECT * FROM users WHERE username = ? AND is_active = 1 "
        "AND role IN ('admin', 'staff')"
    )
    params = [username]
    if expected_role:
        query += " AND role = ?"
        params.append(expected_role)
    cursor.execute(query, params)
    user = cursor.fetchone()
    conn.close()
    if user and user["password_hash"] == hash_password(password):
        return dict(user)
    return None


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, role, is_active, created_at FROM users "
        "WHERE role IN ('admin', 'staff') ORDER BY id DESC"
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def create_user(username, password, role):
    if role not in ("admin", "staff"):
        return None, "Only Admin and Staff accounts are supported."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def update_user_status(user_id, is_active):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
    conn.commit()
    conn.close()


def reset_user_password(user_id, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    conn.commit()
    conn.close()


# --- Branch Model ---
def get_all_branches(active_only=False):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM branches"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name ASC"
    cursor.execute(query)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def add_branch(branch_code, name, address, city, state, pincode, phone):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO branches (branch_code, name, address, city, state, pincode, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (branch_code, name, address, city, state, pincode, phone),
        )
        conn.commit()
        return cursor.lastrowid, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def update_branch(branch_id, branch_code, name, address, city, state, pincode, phone, is_active):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE branches 
               SET branch_code=?, name=?, address=?, city=?, state=?, pincode=?, phone=?, is_active=?
               WHERE id=?""",
            (branch_code, name, address, city, state, pincode, phone, is_active, branch_id),
        )
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def delete_branch(branch_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE branches SET is_active = 0 WHERE id = ?", (branch_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# --- Staff Model ---
def get_all_staff():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, b.name as branch_name, u.username, u.role
        FROM staff s
        LEFT JOIN branches b ON s.branch_id = b.id
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def add_staff(name, phone, email, branch_id, employee_id, username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hash_password(password), "staff"),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO staff (user_id, name, phone, email, branch_id, employee_id) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, phone, email, branch_id, employee_id),
        )
        conn.commit()
        return cursor.lastrowid, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()


def update_staff(staff_id, name, phone, email, branch_id, is_active):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE staff SET name=?, phone=?, email=?, branch_id=?, is_active=? WHERE id=?",
            (name, phone, email, branch_id, is_active, staff_id),
        )
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# --- Customers Model ---
def get_all_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY name ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def add_customer(name, phone, email, address, city, state, pincode):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO customers (name, phone, email, address, city, state, pincode) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, email, address, city, state, pincode),
        )
        conn.commit()
        return cursor.lastrowid, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def update_customer(customer_id, name, phone, email, address, city, state, pincode):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE customers 
               SET name=?, phone=?, email=?, address=?, city=?, state=?, pincode=?
               WHERE id=?""",
            (name, phone, email, address, city, state, pincode, customer_id),
        )
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# --- Delivery Charges Model ---
def get_all_charges():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_charges ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def update_charge_rule(rule_id, name, base_charge, per_kg_rate, per_km_rate, express_multiplier):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE delivery_charges 
               SET name=?, base_charge=?, per_kg_rate=?, per_km_rate=?, express_multiplier=?
               WHERE id=?""",
            (name, base_charge, per_kg_rate, per_km_rate, express_multiplier, rule_id),
        )
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# --- Parcel Model ---
def create_parcel(sender_id, receiver_id, parcel_type, weight_kg, length_cm, width_cm,
                  height_cm, contents_desc, declared_value, special_instructions,
                  source_branch_id, dest_branch_id, total_charge, booked_by, payment_method):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        tracking_number = generate_tracking_number()
        # Verify unique tracking
        cursor.execute("SELECT id FROM parcels WHERE tracking_number = ?", (tracking_number,))
        while cursor.fetchone():
            tracking_number = generate_tracking_number()

        cursor.execute("""
            INSERT INTO parcels (
                tracking_number, sender_id, receiver_id, parcel_type, weight_kg,
                length_cm, width_cm, height_cm, contents_desc, declared_value,
                special_instructions, source_branch_id, dest_branch_id, current_branch_id,
                status, total_charge, booked_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Booked', ?, ?)
        """, (
            tracking_number, sender_id, receiver_id, parcel_type, weight_kg,
            length_cm, width_cm, height_cm, contents_desc, declared_value,
            special_instructions, source_branch_id, dest_branch_id, source_branch_id,
            total_charge, booked_by
        ))
        parcel_id = cursor.lastrowid

        # Initial Tracking Event
        cursor.execute("""
            INSERT INTO tracking_events (parcel_id, status, location, updated_by, remarks)
            VALUES (?, 'Booked', (SELECT name FROM branches WHERE id = ?), ?, 'Parcel booked successfully')
        """, (parcel_id, source_branch_id, booked_by))

        # Record Transaction
        cursor.execute("""
            INSERT INTO transactions (parcel_id, amount, payment_method, payment_status, recorded_by)
            VALUES (?, ?, ?, 'Paid', ?)
        """, (parcel_id, total_charge, payment_method, booked_by))

        conn.commit()
        return parcel_id, tracking_number, None
    except Exception as e:
        conn.rollback()
        return None, None, str(e)
    finally:
        conn.close()


def get_all_parcels(branch_id=None, status=None, search_query=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.*, 
               s.name as sender_name, s.phone as sender_phone,
               r.name as receiver_name, r.phone as receiver_phone, r.address as receiver_address,
               b1.name as source_branch_name, b2.name as dest_branch_name,
               t.payment_status, t.payment_method
        FROM parcels p
        JOIN customers s ON p.sender_id = s.id
        JOIN customers r ON p.receiver_id = r.id
        JOIN branches b1 ON p.source_branch_id = b1.id
        JOIN branches b2 ON p.dest_branch_id = b2.id
        LEFT JOIN transactions t ON p.id = t.parcel_id
        WHERE 1=1
    """
    params = []

    if branch_id:
        query += " AND (p.source_branch_id = ? OR p.dest_branch_id = ? OR p.current_branch_id = ?)"
        params.extend([branch_id, branch_id, branch_id])

    if status and status != "All":
        query += " AND p.status = ?"
        params.append(status)

    if search_query:
        query += " AND (p.tracking_number LIKE ? OR s.name LIKE ? OR r.name LIKE ? OR s.phone LIKE ?)"
        like_q = f"%{search_query}%"
        params.extend([like_q, like_q, like_q, like_q])

    query += " ORDER BY p.id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_parcel_by_tracking(tracking_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, 
               s.name as sender_name, s.phone as sender_phone, s.address as sender_address,
               r.name as receiver_name, r.phone as receiver_phone, r.address as receiver_address,
               b1.name as source_branch_name, b2.name as dest_branch_name,
               cur.name as current_branch_name,
               t.payment_status, t.payment_method
        FROM parcels p
        JOIN customers s ON p.sender_id = s.id
        JOIN customers r ON p.receiver_id = r.id
        JOIN branches b1 ON p.source_branch_id = b1.id
        JOIN branches b2 ON p.dest_branch_id = b2.id
        LEFT JOIN branches cur ON p.current_branch_id = cur.id
        LEFT JOIN transactions t ON p.id = t.parcel_id
        WHERE p.tracking_number = ?
    """, (tracking_number.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_parcel_status(parcel_id, status, location, user_id, remarks=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        delivered_at = "datetime('now','localtime')" if status == "Delivered" else "delivered_at"
        cursor.execute(f"""
            UPDATE parcels 
            SET status = ?, delivered_at = CASE WHEN ? = 'Delivered' THEN datetime('now','localtime') ELSE delivered_at END
            WHERE id = ?
        """, (status, status, parcel_id))

        cursor.execute("""
            INSERT INTO tracking_events (parcel_id, status, location, updated_by, remarks)
            VALUES (?, ?, ?, ?, ?)
        """, (parcel_id, status, location, user_id, remarks))

        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def get_tracking_events(parcel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT te.*, u.username 
        FROM tracking_events te
        LEFT JOIN users u ON te.updated_by = u.id
        WHERE te.parcel_id = ?
        ORDER BY te.id ASC
    """, (parcel_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def transfer_parcel_branch(parcel_id, from_branch_id, to_branch_id, user_id, remarks=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO branch_transfers (parcel_id, from_branch_id, to_branch_id, initiated_by, transfer_status)
            VALUES (?, ?, ?, ?, 'In Transit')
        """, (parcel_id, from_branch_id, to_branch_id, user_id))

        cursor.execute("""
            UPDATE parcels 
            SET current_branch_id = ?, status = 'In Transit'
            WHERE id = ?
        """, (to_branch_id, parcel_id))

        cursor.execute("""
            INSERT INTO tracking_events (parcel_id, status, location, updated_by, remarks)
            VALUES (?, 'In Transit', 
                    (SELECT 'Transfer: ' || f.name || ' -> ' || t.name FROM branches f, branches t WHERE f.id = ? AND t.id = ?),
                    ?, ?)
        """, (parcel_id, from_branch_id, to_branch_id, user_id, remarks or "Dispatched between branches"))

        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


# --- Transactions & Dashboard Stats ---
def get_all_transactions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, p.tracking_number, u.username as recorded_by_user
        FROM transactions t
        JOIN parcels p ON t.parcel_id = p.id
        LEFT JOIN users u ON t.recorded_by = u.id
        ORDER BY t.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_transactions_by_date_range(from_date, to_date):
    """Get transactions within a date range (inclusive)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, p.tracking_number, u.username as recorded_by_user,
               s.name as sender_name, r.name as receiver_name, p.parcel_type, p.weight_kg,
               p.source_branch_id, p.dest_branch_id, p.status as parcel_status
        FROM transactions t
        JOIN parcels p ON t.parcel_id = p.id
        JOIN customers s ON p.sender_id = s.id
        JOIN customers r ON p.receiver_id = r.id
        LEFT JOIN users u ON t.recorded_by = u.id
        WHERE date(t.payment_date) BETWEEN date(?) AND date(?)
        ORDER BY t.payment_date DESC
    """, (from_date, to_date))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_parcels_by_date_range(from_date, to_date):
    """Get parcels booked within a date range (inclusive)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, s.name as sender_name, r.name as receiver_name,
               b1.name as source_branch_name, b2.name as dest_branch_name,
               t.payment_status, t.payment_method, t.amount
        FROM parcels p
        JOIN customers s ON p.sender_id = s.id
        JOIN customers r ON p.receiver_id = r.id
        JOIN branches b1 ON p.source_branch_id = b1.id
        JOIN branches b2 ON p.dest_branch_id = b2.id
        LEFT JOIN transactions t ON p.id = t.parcel_id
        WHERE date(p.booked_at) BETWEEN date(?) AND date(?)
        ORDER BY p.booked_at DESC
    """, (from_date, to_date))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_report_summary(from_date, to_date):
    """Get summary statistics for a date range."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total parcels booked
    cursor.execute("""
        SELECT COUNT(*) FROM parcels 
        WHERE date(booked_at) BETWEEN date(?) AND date(?)
    """, (from_date, to_date))
    total_parcels = cursor.fetchone()[0]
    
    # Total revenue (paid transactions)
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM transactions 
        WHERE date(payment_date) BETWEEN date(?) AND date(?)
        AND payment_status = 'Paid'
    """, (from_date, to_date))
    total_revenue = cursor.fetchone()[0]
    
    # Parcels by status
    cursor.execute("""
        SELECT status, COUNT(*) as count FROM parcels 
        WHERE date(booked_at) BETWEEN date(?) AND date(?)
        GROUP BY status
    """, (from_date, to_date))
    status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Parcels by type
    cursor.execute("""
        SELECT parcel_type, COUNT(*) as count FROM parcels 
        WHERE date(booked_at) BETWEEN date(?) AND date(?)
        GROUP BY parcel_type
    """, (from_date, to_date))
    type_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Payment method breakdown
    cursor.execute("""
        SELECT payment_method, COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM transactions 
        WHERE date(payment_date) BETWEEN date(?) AND date(?)
        AND payment_status = 'Paid'
        GROUP BY payment_method
    """, (from_date, to_date))
    payment_breakdown = {row[0]: {"count": row[1], "total": row[2]} for row in cursor.fetchall()}
    
    conn.close()
    return {
        "total_parcels": total_parcels,
        "total_revenue": total_revenue,
        "status_breakdown": status_breakdown,
        "type_breakdown": type_breakdown,
        "payment_breakdown": payment_breakdown,
    }


def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM parcels")
    total_parcels = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM parcels WHERE status IN ('Booked', 'Picked Up', 'At Branch')")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM parcels WHERE status = 'In Transit'")
    in_transit = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM parcels WHERE status = 'Out for Delivery'")
    out_for_delivery = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM parcels WHERE status = 'Delivered'")
    delivered = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM parcels WHERE status = 'Failed'")
    failed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM staff WHERE is_active = 1")
    active_staff = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE payment_status = 'Paid'")
    total_revenue = cursor.fetchone()[0]

    conn.close()
    return {
        "total_parcels": total_parcels,
        "pending": pending,
        "in_transit": in_transit,
        "out_for_delivery": out_for_delivery,
        "delivered": delivered,
        "failed": failed,
        "active_staff": active_staff,
        "total_revenue": total_revenue,
    }
