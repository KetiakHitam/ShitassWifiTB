import time
import sqlite3
import threading
import subprocess
import re
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_FILE = os.path.join(DB_DIR, "logs.db")

class DisconnectMonitor:
    def __init__(self, check_interval_sec=2):
        self.interval_sec = check_interval_sec
        self.running = False
        self.thread = None
        
        # State tracking
        self.is_connected = True # Assume true on startup to avoid logging a false drop
        self.drop_time = None
        
        # Last known good state
        self.last_signal = None
        self.last_bssid = None
        self.last_channel = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running

    def _loop(self):
        while self.running:
            self._check_connection()
            
            # Fast breaking sleep
            for _ in range(self.interval_sec * 5):
                if not self.running: break
                time.sleep(0.2)

    def _check_connection(self):
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout
            
            state_match = re.search(r"State[\s:]+(\w+)", output)
            curr_state = state_match.group(1).lower() if state_match else "disconnected"
            
            if curr_state == "connected":
                # We are UP
                if not self.is_connected:
                    # We just reconnected after a drop!
                    self._handle_reconnect(output)
                else:
                    # Everything is normal. Just update our last known good state.
                    self._update_last_known_good(output)
                    
                self.is_connected = True
                
            else:
                # We are DOWN
                if self.is_connected:
                    # We JUST dropped!
                    self.is_connected = False
                    self.drop_time = datetime.now()
                    print(f"[DisconnectMonitor] DROP DETECTED at {self.drop_time}")
                    
        except Exception:
            pass

    def _update_last_known_good(self, output):
        sig_match = re.search(r"Signal[\s:]+(\d+)%", output)
        if sig_match:
            self.last_signal = int(sig_match.group(1))
            
        bssid_match = re.search(r"BSSID[\s:]+([0-9a-fA-F\:]+)", output)
        if bssid_match:
            self.last_bssid = bssid_match.group(1)
            
        chan_match = re.search(r"Channel[\s:]+(\d+)", output)
        if chan_match:
            self.last_channel = int(chan_match.group(1))

    def _handle_reconnect(self, output):
        reconnect_time = datetime.now()
        duration = 0.0
        if self.drop_time:
            duration = round((reconnect_time - self.drop_time).total_seconds(), 2)
            
        new_bssid = None
        bssid_match = re.search(r"BSSID[\s:]+([0-9a-fA-F\:]+)", output)
        if bssid_match:
            new_bssid = bssid_match.group(1)
            
        new_channel = None
        chan_match = re.search(r"Channel[\s:]+(\d+)", output)
        if chan_match:
            new_channel = int(chan_match.group(1))
            
        print(f"[DisconnectMonitor] RECONNECTED. Down for {duration} seconds.")
        
        self._write_db(
            drop_time=self.drop_time.strftime("%Y-%m-%d %H:%M:%S") if self.drop_time else None,
            reconnect_time=reconnect_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration_seconds=duration,
            signal_before_drop=self.last_signal,
            previous_bssid=self.last_bssid,
            new_bssid=new_bssid,
            previous_channel=self.last_channel,
            new_channel=new_channel
        )
        self.drop_time = None

    def _write_db(self, drop_time, reconnect_time, duration_seconds, signal_before_drop, 
                  previous_bssid, new_bssid, previous_channel, new_channel):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disconnect_events (
                    drop_time, reconnect_time, duration_seconds, signal_before_drop, 
                    previous_bssid, new_bssid, previous_channel, new_channel
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (drop_time, reconnect_time, duration_seconds, signal_before_drop, 
                  previous_bssid, new_bssid, previous_channel, new_channel))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DisconnectMonitor] DB Error: {e}")
