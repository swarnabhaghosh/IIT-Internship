import sqlite3
from datetime import datetime

DB_PATH = "scheduler.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Flights table (with composite ID)
    c.execute("""
    CREATE TABLE IF NOT EXISTS flights (
        id TEXT PRIMARY KEY,
        airline_id TEXT,
        airline TEXT,
        atype TEXT,
        arr TEXT,
        dep TEXT
    )
    """)

    # Bays table
    c.execute("""
    CREATE TABLE IF NOT EXISTS bays (
        bay TEXT PRIMARY KEY
    )
    """)

    # Compatibility table
    c.execute("""
    CREATE TABLE IF NOT EXISTS compatibility (
        atype TEXT,
        bay TEXT,
        compatible INTEGER,
        PRIMARY KEY (atype, bay)
    )
    """)

    # Revenue table
    c.execute("""
    CREATE TABLE IF NOT EXISTS revenue (
        airline TEXT,
        atype TEXT,
        bay TEXT,
        amount REAL,
        PRIMARY KEY (airline, atype, bay)
    )
    """)
    conn.commit()

    # Initialize defaults if empty
    if c.execute("SELECT COUNT(*) FROM bays").fetchone()[0] == 0:
        for b in ["B1", "B2", "B3"]:
            c.execute("INSERT INTO bays (bay) VALUES (?)", (b,))
        conn.commit()

    if c.execute("SELECT COUNT(*) FROM compatibility").fetchone()[0] == 0:
        comp_data = [
            ("A320", "B1", 1), ("A320", "B2", 1), ("A320", "B3", 1),
            ("B737", "B1", 0), ("B737", "B2", 1), ("B737", "B3", 1)
        ]
        c.executemany("INSERT INTO compatibility (atype, bay, compatible) VALUES (?,?,?)", comp_data)
        conn.commit()

    if c.execute("SELECT COUNT(*) FROM revenue").fetchone()[0] == 0:
        rev_data = [
            ("AI", "A320", "B1", 100), ("AI", "A320", "B2", 120), ("AI", "A320", "B3", 130),
            ("BA", "B737", "B2", 150), ("BA", "B737", "B3", 170)
        ]
        c.executemany("INSERT INTO revenue (airline, atype, bay, amount) VALUES (?,?,?,?)", rev_data)
        conn.commit()

    conn.close()

# Flight Operations
def add_flight(fid, airline, atype, arr: datetime, dep: datetime):
    conn = get_conn()
    c = conn.cursor()

    # Composite key
    flight_key = f"{airline}_{fid}"

    exists = c.execute("SELECT 1 FROM flights WHERE id=?", (flight_key,)).fetchone()
    if exists:
        conn.close()
        raise ValueError(f"Flight '{flight_key}' already exists.")

    c.execute(
        "INSERT INTO flights (id, airline_id, airline, atype, arr, dep) VALUES (?,?,?,?,?,?)",
        (flight_key, fid, airline, atype, arr.isoformat(), dep.isoformat())
    )
    conn.commit()
    conn.close()

def get_flights():
    conn = get_conn()
    flights = conn.execute("SELECT * FROM flights").fetchall()
    conn.close()
    return flights

def delete_flight(flight_key):
    conn = get_conn()
    conn.execute("DELETE FROM flights WHERE id=?", (flight_key,))
    conn.commit()
    conn.close()

# Fetch Other Data
def get_bays():
    conn = get_conn()
    bays = [b[0] for b in conn.execute("SELECT bay FROM bays").fetchall()]
    conn.close()
    return bays

def get_compatibility():
    conn = get_conn()
    comp = { (row[0], row[1]): row[2] for row in conn.execute("SELECT atype,bay,compatible FROM compatibility") }
    conn.close()
    return comp

def get_revenue():
    conn = get_conn()
    revenue = { (row[0], row[1], row[2]): row[3] for row in conn.execute("SELECT airline,atype,bay,amount FROM revenue") }
    conn.close()
    return revenue

# Reset System
def reset_system():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM flights")
    c.execute("DELETE FROM bays")
    c.execute("DELETE FROM compatibility")
    c.execute("DELETE FROM revenue")
    conn.commit()
    conn.close()
