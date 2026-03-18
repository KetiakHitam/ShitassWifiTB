import socket
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Status, format_result

def check_dns(domains=None):
    """
    Checks DNS resolution times for a list of common domains.
    Helps identify if the internet is 'slow' because DNS is struggling.
    """
    if domains is None:
        domains = ["google.com", "cloudflare.com", "microsoft.com", "amazon.com"]
        
    times = []
    failed = 0
    
    for domain in domains:
        try:
            start_time = time.time()
            # Resolve the domain to an IP
            socket.gethostbyname(domain)
            end_time = time.time()
            
            # Convert to ms
            resolve_time = (end_time - start_time) * 1000
            times.append(resolve_time)
            
        except socket.gaierror:
            failed += 1
            
    if failed == len(domains):
        return format_result(Status.ERROR, "DNS Failed", "Could not resolve any tested domains.")
        
    avg_time = sum(times) / len(times)
    
    if failed > 0:
        status = Status.BAD
        details = f"{failed}/{len(domains)} domains failed to resolve."
    elif avg_time > 100:
        status = Status.WARNING
        details = "DNS resolution is noticeably slow."
    else:
        status = Status.GOOD
        details = "DNS is healthy and resolving quickly."
        
    value = f"Avg: {avg_time:.0f}ms"
    
    return format_result(status, value, details)

if __name__ == "__main__":
    print(check_dns())
