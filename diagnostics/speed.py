import speedtest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Status, format_result

def run_speed_test():
    """
    Runs a speed test using speedtest-cli.
    Returns download, upload, and ping stats.
    """
    try:
        st = speedtest.Speedtest()
        
        # Get best server
        st.get_best_server()
        
        # Run tests
        download_bps = st.download()
        upload_bps = st.upload()
        ping_ms = st.results.ping
        
        # Convert to Mbps
        download_mbps = download_bps / 1_000_000
        upload_mbps = upload_bps / 1_000_000
        
        # Determine status based on arbitrary but reasonable thresholds
        if download_mbps >= 50 and ping_ms <= 50:
            status = Status.GOOD
        elif download_mbps >= 15 and ping_ms <= 100:
            status = Status.WARNING
        else:
            status = Status.BAD
            
        value = f"{download_mbps:.1f} Mbps ▼ / {upload_mbps:.1f} Mbps ▲"
        details = f"Ping: {ping_ms:.0f}ms to test server"
        
        # Store raw metrics in details for the UI to parse if needed
        raw_data = {"download": download_mbps, "upload": upload_mbps, "ping": ping_ms}
        
        return format_result(status, value, details)
        
    except Exception as e:
        return format_result(Status.ERROR, "Speed Test Failed", str(e))

if __name__ == "__main__":
    print("Running speed test (this takes a moment)...")
    print(run_speed_test())
