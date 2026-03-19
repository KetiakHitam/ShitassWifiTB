import subprocess
import threading
import time
import re

class GamePinger:
    def __init__(self, target_host="8.8.8.8"):
        self.target_host = target_host
        self.running = False
        self.thread = None
        self.history = [] # list of (timestamp, ping_ms)
        self.max_history = 300 # 5 minutes of 1-second pings
        self.proc = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.proc:
            try:
                self.proc.terminate()
            except: pass

    def change_target(self, new_host):
        self.stop()
        self.target_host = new_host
        # Clear history when switching targets
        self.history.clear()
        # Small delay to ensure old proc dies
        time.sleep(0.5)
        self.start()

    def _loop(self):
        # We use a single continuous ping process natively to minimize Python CPU overhead
        self.proc = subprocess.Popen(
            ["ping", "-t", self.target_host],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        while self.running and self.proc.poll() is None:
            line = self.proc.stdout.readline()
            if not line:
                break
                
            if "Reply from" in line:
                match = re.search(r"time[=<](\d+)ms", line)
                ping_ms = int(match.group(1)) if match else None
                if ping_ms is not None:
                    self.history.append((time.time(), ping_ms))
            elif "Request timed out" in line or "unreachable" in line.lower() or "failure" in line.lower():
                self.history.append((time.time(), 999)) # 999 indicates a true packet timeout/loss
                
            if len(self.history) > self.max_history:
                self.history.pop(0)

        # Cleanup if loop breaks manually or ping dies
        try:
            self.proc.terminate()
        except: pass
        self.running = False
