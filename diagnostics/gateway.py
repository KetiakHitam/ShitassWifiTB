import subprocess
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Status, format_result

def check_gateway():
    """
    Finds the default gateway IP and pings it.
    If you can't reach the gateway, your connection to the router is broken.
    """
    try:
        # Get default gateway IP using ipconfig
        ipconfig_result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Look for Default Gateway line under Wi-Fi adapter
        gateway_ip = None
        in_wifi_section = False
        
        for line in ipconfig_result.stdout.split('\n'):
            line = line.strip()
            if "Wi-Fi" in line or "Wireless LAN" in line:
                in_wifi_section = True
            elif line == "":
                # Empty line usually denotes end of interface block, but we'll loosely parse
                pass
            elif "Default Gateway" in line and in_wifi_section:
                # Need to find the IPv4 address (ignore IPv6 fe80 stuff if on same line)
                # Usually: Default Gateway . . . . . . . . . : 192.168.1.1 or fe80::...
                match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                if match:
                    gateway_ip = match.group(1)
                    break
        
        # Sometimes ipconfig puts the IPv4 gateway on the NEXT line
        if not gateway_ip and in_wifi_section:
            # Let's do a more robust raw text search for the gateway
            # Find the block for Wi-Fi, then find the first IPv4 address after Default Gateway
            wifi_block = ipconfig_result.stdout[ipconfig_result.stdout.find("Wi-Fi"):]
            gw_idx = wifi_block.find("Default Gateway")
            if gw_idx != -1:
                gw_block = wifi_block[gw_idx:]
                match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", gw_block)
                if match:
                    gateway_ip = match.group(1)
                    
        if not gateway_ip:
            return format_result(Status.ERROR, "Unknown Gateway", "Could not find a default gateway IP (router not detected).")
            
        # Ping the gateway
        ping_result = subprocess.run(
            ["ping", "-n", "4", "-w", "1000", gateway_ip],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = ping_result.stdout
        
        # Analyze ping results
        if "Destination host unreachable" in output or "Request timed out" in output:
            # Check if total failure
             loss_match = re.search(r"Lost = (\d+)", output)
             loss = int(loss_match.group(1)) if loss_match else 4
             
             if loss == 4:
                 return format_result(Status.BAD, "Unreachable", f"Cannot reach router at {gateway_ip}.")
             else:
                 return format_result(Status.WARNING, "Unstable", f"Packet loss ({loss}/4) communicating with router at {gateway_ip}.")
                 
        else:
            time_match = re.search(r"Average = (\d+)ms", output)
            avg_time = int(time_match.group(1)) if time_match else 0
            
            if avg_time > 20:
                status = Status.WARNING
                details = f"Router response is surprisingly slow ({avg_time}ms) for a local connection."
            else:
                status = Status.GOOD
                details = f"Reachable. Fast connection to router ({avg_time}ms)."
                
            return format_result(status, f"Reachable ({gateway_ip})", details)
            
    except Exception as e:
        return format_result(Status.ERROR, "Error", str(e))

if __name__ == "__main__":
    print(check_gateway())
