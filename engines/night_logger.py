import time
import sqlite3
import threading
import subprocess
import re
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_FILE = os.path.join(DB_DIR, "logs.db")

class NightLogger:
    def __init__(self, target_host="8.8.8.8", interval_sec=30):
        self.target_host = target_host
        self.interval_sec = interval_sec
        self.running = False
        self.thread = None

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
            self._log_snapshot()
            
            # Sleep in small chunks so we can stop quickly without waiting 30 seconds
            for _ in range(self.interval_sec):
                if not self.running:
                    break
                time.sleep(1)

    def _log_snapshot(self):
        # 1. Get quick ping stats (4 packets takes ~4 seconds)
        ping_ms, jitter_ms, loss_pct = self._get_ping_stats()
        
        # 2. Get quick signal strength
        signal_pct = self._get_signal_strength()
        
        # 3. Write to DB
        self._write_db(ping_ms, jitter_ms, loss_pct, signal_pct)

    def _get_ping_stats(self):
        try:
            # -n 4 sends 4 packets, -w 1000 waits max 1000ms per reply
            # CREATE_NO_WINDOW prevents command prompt windows popping up every 30s
            result = subprocess.run(
                ["ping", "-n", "4", "-w", "1000", self.target_host],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout
            
            # Parse packet loss
            loss_match = re.search(r"\((\d+)% loss\)", output)
            loss_pct = float(loss_match.group(1)) if loss_match else 100.0
            
            # Parse round trip times
            if loss_pct < 100.0:
                times = re.findall(r"time[=<](\d+)ms", output)
                times = [int(t) for t in times]
                
                if times:
                    ping_ms = sum(times) / len(times)
                    jitter_ms = max(times) - min(times) if len(times) > 1 else 0.0
                else:
                    ping_ms = None
                    jitter_ms = None
            else:
                ping_ms = None
                jitter_ms = None
                
            return ping_ms, jitter_ms, loss_pct
            
        except Exception:
            return None, None, 100.0

    def _get_signal_strength(self):
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            match = re.search(r"Signal[\s:]+(\d+)%", result.stdout)
            if match:
                return int(match.group(1))
            return None
        except Exception:
            return None

    def _write_db(self, ping_ms, jitter_ms, loss_pct, signal_pct):
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO periodic_logs (timestamp, ping_ms, jitter_ms, packet_loss_pct, signal_strength_pct)
                VALUES (?, ?, ?, ?, ?)
            """, (local_time, ping_ms, jitter_ms, loss_pct, signal_pct))
            conn.commit()
            conn.close()
        except Exception as e:
            # Silently fail if DB is locked or unavailable, to avoid crashing the background thread
            print(f"[NightLogger] DB Error: {e}")
