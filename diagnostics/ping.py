import subprocess
import time
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Status, format_result

def run_ping_test(host="8.8.8.8", count=30, timeout_ms=1000):
    """
    Runs a continuous ping test for `count` seconds (approx).
    Calculates average latency, max latency spike, jitter, and packet loss.
    """
    try:
        # Create ping process
        # -n count: number of echoes to send
        # -w timeout: timeout in milliseconds to wait for each reply
        cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), host]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        latencies = []
        lost_packets = 0
        total_packets = 0
        
        # Read output line by line as it comes in
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
                
            if "Reply from" in line:
                total_packets += 1
                # Extract time=XXms
                time_match = re.search(r"time[=<](\d+)ms", line)
                if time_match:
                    latencies.append(int(time_match.group(1)))
                    
            elif "Request timed out" in line or "Destination host unreachable" in line:
                total_packets += 1
                lost_packets += 1
                
        process.wait()
        
        if total_packets == 0:
            return format_result(Status.ERROR, "Ping Failed", f"Could not reach {host}.")
            
        # Calculate stats
        loss_pct = (lost_packets / total_packets) * 100
        
        if not latencies:
            return format_result(Status.ERROR, f"100% Loss", f"All packets to {host} were dropped.")
            
        avg_ping = sum(latencies) / len(latencies)
        max_ping = max(latencies)
        min_ping = min(latencies)
        
        # Calculate jitter (average of absolute differences between consecutive pings)
        jitter = 0
        if len(latencies) > 1:
            differences = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
            jitter = sum(differences) / len(differences)
            
        # Determine status
        if loss_pct > 5 or max_ping >= 150 or jitter >= 30:
            status = Status.BAD
        elif loss_pct > 0 or max_ping >= 100 or jitter >= 15:
            status = Status.WARNING
        else:
            status = Status.GOOD
            
        value = f"Avg: {avg_ping:.0f}ms | Spike: {max_ping}ms | Jitter: {jitter:.0f}ms"
        details = f"Tested {host} x{total_packets}. {loss_pct:.0f}% packet loss."
        
        return format_result(status, value, details)
        
    except Exception as e:
        return format_result(Status.ERROR, "Ping Error", str(e))

if __name__ == "__main__":
    print("Running 10s ping test to 8.8.8.8...")
    print(run_ping_test(count=10))
