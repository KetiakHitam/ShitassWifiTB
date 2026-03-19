import psutil
import time
import threading

class BandwidthMonitor:
    def __init__(self, interval_sec=1):
        self.interval_sec = interval_sec
        self.running = False
        self.thread = None
        self.latest_data = [] # List of dicts mapping PID to active internet connections
        self.latest_total = {"upload_mbps": 0.0, "download_mbps": 0.0}
        
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
        last_io = psutil.net_io_counters()
        last_time = time.time()
        
        while self.running:
            # 1. Total adapter speed
            curr_io = psutil.net_io_counters()
            curr_time = time.time()
            
            elapsed = curr_time - last_time
            if elapsed > 0:
                # Convert bytes/sec to Megabits/sec (Mbps)
                up_speed = ((curr_io.bytes_sent - last_io.bytes_sent) * 8) / (1_000_000 * elapsed)
                down_speed = ((curr_io.bytes_recv - last_io.bytes_recv) * 8) / (1_000_000 * elapsed)
                
                self.latest_total = {
                    "upload_mbps": round(up_speed, 2),
                    "download_mbps": round(down_speed, 2)
                }
            
            last_io = curr_io
            last_time = curr_time
            
            # 2. Per-process active internet connections
            try:
                conns = psutil.net_connections(kind='inet')
                pid_map = {}
                
                for c in conns:
                    # We only care about active outgoing/incoming connections, not listening sockets
                    if c.status == 'ESTABLISHED' and c.pid:
                        # Skip local loopback (localhost)
                        if c.raddr and hasattr(c.raddr, 'ip') and c.raddr.ip.startswith("127."):
                            continue
                            
                        if c.pid not in pid_map:
                            try:
                                proc = psutil.Process(c.pid)
                                pid_map[c.pid] = {
                                    "name": proc.name(),
                                    "pid": c.pid,
                                    "connections": 0
                                }
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                                
                        pid_map[c.pid]["connections"] += 1
                
                # Sort descending by connection count
                sorted_procs = sorted(pid_map.values(), key=lambda x: x["connections"], reverse=True)
                self.latest_data = sorted_procs
                
            except psutil.AccessDenied:
                # Failsafe if not running as admin (though the user usually does)
                self.latest_data = [{"name": "ERROR: Run as Administrator to view processes", "pid": "-", "connections": 0}]
            except Exception:
                pass
                
            # Responsive sleep chunking
            for _ in range(int(self.interval_sec * 5)):
                if not self.running: break
                time.sleep(0.2)
