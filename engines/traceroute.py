import subprocess
import threading
import re
from utils import Status

class TracerouteEngine:
    def __init__(self):
        self.running = False
        self.proc = None

    def start_trace(self, target, on_hop_callback, on_complete_callback):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run, args=(target, on_hop_callback, on_complete_callback), daemon=True).start()

    def stop(self):
        self.running = False
        if self.proc:
            try:
                self.proc.terminate()
            except: pass

    def _run(self, target, on_hop_callback, on_complete_callback):
        hops_data = []
        
        # -d: Do not resolve addresses to hostnames (makes traceroute exponentially faster)
        # -w 1000: 1 second timeout per hop
        self.proc = subprocess.Popen(
            ["tracert", "-d", "-w", "1000", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        for line in self.proc.stdout:
            if not self.running:
                break
                
            line = line.strip()
            if not line or line.startswith("Tracing") or line.startswith("Over") or line.startswith("Trace complete"):
                continue
            
            parts = [p for p in line.split(" ") if p]
            if not parts or not parts[0].isdigit():
                continue
                
            hop_num = int(parts[0])
            
            ms_matches = re.findall(r"(<?\d+\s?ms|\*)", line)
            pings = []
            for m in ms_matches:
                if "*" in m:
                    pings.append(999) # Timeout code
                else:
                    val = re.sub(r"[^\d]", "", m)
                    pings.append(int(val) if val else 999)
                    
            ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
            ip = ip_match.group(0) if ip_match else "Unknown/Timeout"
            
            valid_pings = [p for p in pings[:3] if p != 999]
            avg_ping = sum(valid_pings) // len(valid_pings) if valid_pings else 999
            
            hop_info = {
                "hop": hop_num,
                "pings": pings[:3],
                "avg_ping": avg_ping,
                "ip": ip
            }
            
            hops_data.append(hop_info)
            if on_hop_callback:
                on_hop_callback(hop_info)
                
        self.running = False
        
        if self.proc:
            try: self.proc.terminate()
            except: pass
            
        blame_report = self._analyze_blame(hops_data)
        if on_complete_callback:
            on_complete_callback(hops_data, blame_report)

    def _analyze_blame(self, hops):
        if not hops:
            return {"verdict": "ERROR", "text": "Traceroute failed to run. Ensure the target host is reachable.", "status": Status.ERROR}
            
        hop1 = hops[0]
        if hop1["avg_ping"] > 50 and hop1["avg_ping"] != 999:
            return {"verdict": "YOUR WIFI ROUTER", "text": f"Your connection to the WiFi router is unstable ({hop1['avg_ping']}ms). The issue is inside your house. Move closer to the router, switch from 2.4GHz to 5GHz, or use an Ethernet cable.", "status": Status.BAD}
            
        isp_hops = [h for h in hops if h["hop"] in (2, 3)]
        for h in isp_hops:
            if h["avg_ping"] > 80 and h["avg_ping"] != 999:
                return {"verdict": "YOUR ISP", "text": f"The lag spike starts exactly at Hop {h['hop']} (IP: {h['ip']} at {h['avg_ping']}ms). This is your Internet Service Provider's network node. They are dropping or delaying your packets before they even reach the internet infrastructure.", "status": Status.BAD}

        last_hop = hops[-1]
        
        if last_hop["avg_ping"] > 120 and last_hop["avg_ping"] != 999:
            return {"verdict": "GAME SERVER / ROUTING", "text": f"Your local WiFi and ISP are fine, but the connection degrades deeper into the internet. The server is either physically very far away, or the routing path to it is inefficient. Try using a VPN like Exitlag.", "status": Status.WARNING}
            
        if last_hop["avg_ping"] == 999:
            # Check if previous hops are fine
            if len(hops) > 3 and hops[-2]["avg_ping"] < 80:
                return {"verdict": "SERVER FIREWALL", "text": "The target server is blocking Ping requests (Timed out), but your local network and ISP hops look perfectly healthy. Your connection is likely fine.", "status": Status.GOOD}
            return {"verdict": "INCONCLUSIVE", "text": "The trace timed out before reaching the destination.", "status": Status.WARNING}
            
        return {"verdict": "NETWORK HEALTHY", "text": f"Network path is completely clear. End-to-end latency is an optimal {last_hop['avg_ping']}ms. No network issues detected on this route.", "status": Status.GOOD}
