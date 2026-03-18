from utils import Status

def analyze_results(results: dict) -> list[str]:
    """
    Takes a dictionary of diagnostic results and returns a list of actionable,
    plain-English suggestions based on what failed or struggled.
    """
    suggestions = []
    
    # 1. Gateway (Router reachability is the most critical)
    if results.get('gateway', {}).get('status') == Status.BAD:
        suggestions.append("⚠️ [CRITICAL] Your computer cannot reach your router at all. Try restarting your router (unplug it for 30 seconds), or checking if you're actually connected to the right WiFi network.")
        # If we can't reach the router, nothing else matters
        return suggestions
        
    # 2. DNS Health
    if results.get('dns', {}).get('status') in [Status.WARNING, Status.BAD]:
        suggestions.append("🌐 [DNS ISSUE] Your DNS resolution is slow or failing. This makes the internet feel sluggish even if your speed is fine. Try changing your DNS server to Google (8.8.8.8) or Cloudflare (1.1.1.1) in your Windows adapter settings.")
        
    # 3. WiFi Signal & Band
    signal_res = results.get('signal', {})
    if signal_res.get('status') in [Status.WARNING, Status.BAD]:
        suggestions.append(f"📶 [WEAK SIGNAL] Your WiFi signal is weak ({signal_res.get('value')}). Move closer to the router, remove physical obstructions, or consider getting a WiFi extender/mesh system.")
    
    if "2.4 GHz" in signal_res.get('value', ""):
        suggestions.append("ℹ️ [INFO] You are connected to the 2.4 GHz band. It has better range but is slower and more prone to interference (like microwaves). If you are close to the router and gaming, see if your network has a 5 GHz band available and connect to that instead.")
        
    # 4. Channel Congestion
    channel_res = results.get('channel', {})
    if channel_res.get('status') in [Status.WARNING, Status.BAD]:
        suggestions.append(f"📻 [CONGESTION] The WiFi channel you are on is crowded with neighbor networks. Log into your router's admin panel and change your WiFi channel to a less congested one (channels 1, 6, or 11 are best for 2.4 GHz).")
        
    # 5. Gaming Spikes (Ping & Jitter)
    ping_res = results.get('ping', {})
    ping_status = ping_res.get('status')
    if ping_status in [Status.WARNING, Status.BAD]:
        if "packet loss" in ping_res.get('details', "").lower() and "0%" not in ping_res.get('details', ""):
            suggestions.append("🎮 [PACKET LOSS] Your connection is dropping packets. This causes terrible lag and teleporting in games. This is often caused by bad WiFi reception or ISP issues. Try an ethernet cable to see if it fixes it.")
        elif "Jitter" in ping_res.get('value', ""):
             # Extract jitter value to give specific advice
             pass # Jitter is inherently a problem
             suggestions.append("🎮 [JITTER] Your latency is inconsistent (high jitter). This is what causes random lag spikes while gaming at night. This happens when your WiFi channel is congested (see above), your router is overwhelmed, or your ISP is throttling node bandwidth during peak hours.")

    # 6. Overall Speed
    speed_res = results.get('speed', {})
    if speed_res.get('status') == Status.BAD:
         suggestions.append("🐌 [SPEED] Your raw connection speed is very low. If you are paying for faster internet, the bottleneck might be your old router, weak WiFi signal, or background downloads eating your bandwidth.")
         
    # All Good Fallback
    if not suggestions:
        suggestions.append("✅ [ALL GOOD] Your network looks healthy from our end! If you're still lagging in games, the issue might be the game servers themselves, or background apps on your PC updating while you play.")
        
    return suggestions
