import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_FILE = os.path.join(DB_DIR, "logs.db")

def init_db():
    """Initializes the SQLite database with the required tables for Phase 2 logging."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Table for periodic night logging (ping, jitter, signal strength over time)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS periodic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ping_ms REAL,
            jitter_ms REAL,
            packet_loss_pct REAL,
            signal_strength_pct INTEGER
        )
    """)
    
    # Table for disconnect detective (recording exact moments when the adapter drops)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disconnect_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drop_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            reconnect_time DATETIME,
            duration_seconds REAL,
            signal_before_drop INTEGER,
            previous_bssid TEXT,
            new_bssid TEXT,
            previous_channel INTEGER,
            new_channel INTEGER
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_FILE}")
