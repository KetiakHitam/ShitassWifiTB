import subprocess
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Status, format_result

def analyze_channels():
    """
    Parses `netsh wlan show networks mode=bssid` to find nearby networks.
    Determines if the current channel is congested.
    """
    try:
        # First get our current channel
        ifaces_result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        channel_match = re.search(r"^\s+Channel\s+:\s+(\d+)$", ifaces_result.stdout, re.MULTILINE)
        if not channel_match:
            return format_result(Status.ERROR, "Unknown", "Could not determine current WiFi channel.")
            
        current_channel = int(channel_match.group(1))
        
        # Now get all nearby networks to see who else is on this channel
        networks_result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = networks_result.stdout
        
        # Count occurrences of our channel
        networks_on_our_channel = 0
        total_nearby_networks = 0
        
        # We need to find all "Channel : X" lines
        for match in re.finditer(r"^\s+Channel\s+:\s+(\d+)$", output, re.MULTILINE):
            total_nearby_networks += 1
            found_chan = int(match.group(1))
            if found_chan == current_channel:
                networks_on_our_channel += 1
                
        # Subtract 1 because OUR network will show up in the list
        networks_on_our_channel = max(0, networks_on_our_channel - 1)
        
        if networks_on_our_channel >= 4:
            status = Status.BAD
            details = f"Extremely congested. {networks_on_our_channel} other networks are using your channel."
        elif networks_on_our_channel >= 2:
            status = Status.WARNING
            details = f"Slightly crowded. {networks_on_our_channel} other networks are sharing this channel."
        else:
            status = Status.GOOD
            details = f"Clear channel. Only {networks_on_our_channel} other networks sharing it."
            
        value = f"Channel {current_channel}"
        
        return format_result(status, value, details)
        
    except Exception as e:
        return format_result(Status.ERROR, "Channel Check Error", str(e))

if __name__ == "__main__":
    print(analyze_channels())
