import sqlite3
from datetime import datetime

DB_NAME = "hotel.db"

def init_db():
    conn = connect()
    cur = conn.cursor()
    with open("database.sql", "r") as f:
        cur.executescript(f.read())

    conn.commit()
    conn.close()

def connect():
    return sqlite3.connect(DB_NAME)

# –––––––– SIGN UP ––––––––

def sign_up(name, last_name, national_id, contact, password):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO Customers (name, last_name, national_id, contact_number, password)
        VALUES (?, ?, ?, ?, ?)
        """, (name, last_name, national_id, contact, password))
        conn.commit()
        return True, "Sign up successful"
    except sqlite3.IntegrityError:
        return False, "This national ID is already registered"
    finally:
        conn.close()

# –––––––– LOGIN ––––––––

def login(national_id, password):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT customer_id FROM Customers
        WHERE national_id=? AND password=?
    """, (national_id, password))

    user = cur.fetchone()
    conn.close()

    if user:
        return True, user[0], "Login successful"
    return False, None, "Invalid credentials"

# –––––––– LIST ROOMS ––––––––

def list_rooms(enter_date, exit_date, capacity):
    conn = connect()
    cur = conn.cursor()
    query = """
    SELECT r.room_number, r.capacity, r.price_per_night, r.status, r.info
    FROM Rooms r
    WHERE r.capacity >= ?
    """
    cur.execute(query, (capacity,))
    rooms = cur.fetchall()

    available = []
    unavailable = []

    for room in rooms:
        room_number = room[0]

        cur.execute("""
        SELECT * FROM Reservations
        WHERE room_number=?
        AND NOT (exit_date <= ? OR enter_date >= ?)
        """, (room_number, enter_date, exit_date))

        overlap = cur.fetchone()

        if overlap or room[3] == "out_of_service":
            unavailable.append(room)
        else:
            available.append(room)

    conn.close()
    return available, unavailable

# –––––––– BOOK ––––––––

def book(customer_id, room_number, enter_date, exit_date):
    conn = connect()
    cur = conn.cursor()
    nights = (datetime.strptime(exit_date, "%Y-%m-%d") -
            datetime.strptime(enter_date, "%Y-%m-%d")).days

    # bug fix #5: reject zero or negative night stays
    if nights < 1:
        conn.close()
        return False, None, "Check-out date must be after check-in date"

    # get room (price + status)
    cur.execute("SELECT price_per_night, status FROM Rooms WHERE room_number=?", (room_number,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, None, "Room not found"

    price, status = row

    # bug fix #1 & #2: verify the room is actually bookable before inserting
    if status == "out_of_service":
        conn.close()
        return False, None, "This room is out of service"

    cur.execute("""
        SELECT 1 FROM Reservations
        WHERE room_number=?
        AND NOT (exit_date <= ? OR enter_date >= ?)
    """, (room_number, enter_date, exit_date))

    if cur.fetchone():
        conn.close()
        return False, None, "This room is already booked for the selected dates"

    total = price * nights

    # insert reservation
    cur.execute("""
        INSERT INTO Reservations (customer_id, room_number, enter_date, exit_date, stay_nights)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, room_number, enter_date, exit_date, nights))

    reservation_id = cur.lastrowid

    # insert payment
    cur.execute("""
        INSERT INTO Payments (reservation_id, amount)
        VALUES (?, ?)
    """, (reservation_id, total))

    conn.commit()
    conn.close()

    receipt = {
        "Reservation ID": reservation_id,
        "Room": room_number,
        "Price Paid": total,
        "Check-in": enter_date,
        "Check-out": exit_date
    }

    return True, receipt, "Reservation completed successfully"

# –––––––– CANCEL ––––––––

def cancel_reservation(reservation_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM Payments WHERE reservation_id=?", (reservation_id,))
    cur.execute("DELETE FROM Reservations WHERE reservation_id=?", (reservation_id,))
    deleted = cur.rowcount

    conn.commit()
    conn.close()

    # bug fix #3: report failure when no reservation matches the given id
    if deleted == 0:
        return False, "No reservation found with that ID"
    return True, "Reservation cancelled"

# –––––––– ADMIN ––––––––
def add_room(room_number, capacity, price, status, info):
    conn = connect()
    cur = conn.cursor()
    # bug fix #2: handle duplicate room numbers gracefully
    try:
        cur.execute("""
            INSERT INTO Rooms VALUES (?, ?, ?, ?, ?)
        """, (room_number, capacity, price, status, info))
        conn.commit()
        return True, "Room added"
    except sqlite3.IntegrityError:
        return False, "A room with this number already exists"
    finally:
        conn.close()

def get_user(customer_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, last_name, national_id, contact_number FROM Customers WHERE customer_id=?",
        (customer_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row

def get_all_reservations():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Reservations")
    data = cur.fetchall()
    conn.close()
    return data