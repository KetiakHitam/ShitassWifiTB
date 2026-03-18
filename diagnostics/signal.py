import subprocess
import re
import sys
import os

# Allow importing from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Status, format_result

def get_wifi_signal():
    """
    Parses `netsh wlan show interfaces` to get signal strength, band, and SSID.
    Returns a standardized dictionary.
    """
    try:
        # Run netsh wlan show interfaces
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = result.stdout
        
        # Check if actually connected
        if "State                  : connected" not in output:
            return format_result(Status.ERROR, "Disconnected", "Not connected to any WiFi network.")
            
        # Parse fields with more flexible regex for different Windows versions
        ssid_match = re.search(r"SSID\s*:\s+(.+)$", output, re.MULTILINE)
        signal_match = re.search(r"Signal\s*:\s+(\d+)%", output, re.MULTILINE)
        band_match = re.search(r"Band\s*:\s+(.+)$", output, re.MULTILINE)
        
        ssid = ssid_match.group(1).strip() if ssid_match else "Unknown"
        signal_str = signal_match.group(1) if signal_match else "0"
        band = band_match.group(1).strip() if band_match else "Unknown"
        
        signal = int(signal_str)
        
        # Determine status
        if signal >= 80:
            status = Status.GOOD
        elif signal >= 50:
            status = Status.WARNING
        else:
            status = Status.BAD
            
        details = f"Connected to {ssid} on {band} band."
        value = f"{signal}% ({band})"
        
        return format_result(status, value, details)
        
    except subprocess.CalledProcessError as e:
        return format_result(Status.ERROR, "Error", f"Could not fetch WiFi stats: {e}")
    except Exception as e:
        return format_result(Status.ERROR, "Error", str(e))

if __name__ == "__main__":
    print(get_wifi_signal())
