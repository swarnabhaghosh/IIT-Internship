import sqlite3
from datetime import datetime

DB_PATH = "scheduler.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

#initialize database
def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Flights table
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

    # Initialize defaults if tables are empty
    if c.execute("SELECT COUNT(*) FROM bays").fetchone()[0] == 0:
        bays_to_create = [f"B{i}" for i in range(1, 11)]
        for b in bays_to_create:
            c.execute("INSERT INTO bays (bay) VALUES (?)", (b,))
        conn.commit()

    if c.execute("SELECT COUNT(*) FROM compatibility").fetchone()[0] == 0:
        comp_data = []
        all_bays = [f"B{i}" for i in range(1, 11)]
        
        # Combined loop for efficiency
        for bay in all_bays:
            # Rule: A320 is compatible with all 10 bays
            comp_data.append(("A320", bay, 1))
            
            # Rule: B737 is not compatible with B1, but is with the other 9
            is_compatible = 1 if bay != "B1" else 0
            comp_data.append(("B737", bay, is_compatible))
            
        c.executemany("INSERT INTO compatibility (atype, bay, compatible) VALUES (?,?,?)", comp_data)
        conn.commit()

    if c.execute("SELECT COUNT(*) FROM revenue").fetchone()[0] == 0:
        rev_data = []
        all_bays = [f"B{i}" for i in range(1, 11)]

        # Rule: AI A320 revenue starts at 100 and increases by 5 for each bay
        for i, bay in enumerate(all_bays):
            rev_data.append(("AI", "A320", bay, 100 + i * 5))
            
        # Rule: BA B737 revenue (for compatible bays B2-B10) starts at 150
        for i, bay in enumerate(all_bays):
            if bay != "B1":
                rev_data.append(("BA", "B737", bay, 150 + (i - 1) * 5))
                
        c.executemany("INSERT INTO revenue (airline, atype, bay, amount) VALUES (?,?,?,?)", rev_data)
        conn.commit()

    conn.close()

# Flight Operations
def add_flight(fid, airline, atype, arr: datetime, dep: datetime):
    airline = airline.strip().upper()
    atype = atype.strip().upper()
    fid = fid.strip()

    if not all([fid, airline, atype]):
        raise ValueError("Flight ID, Airline, and Aircraft Type cannot be empty.")

    conn = get_conn()
    c = conn.cursor()
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
    comp = {(row[0], row[1]): row[2] for row in conn.execute("SELECT atype,bay,compatible FROM compatibility")}
    conn.close()
    return comp

def get_revenue():
    conn = get_conn()
    revenue = {(row[0], row[1], row[2]): row[3] for row in conn.execute("SELECT airline,atype,bay,amount FROM revenue")}
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