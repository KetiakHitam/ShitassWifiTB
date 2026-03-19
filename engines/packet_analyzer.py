import threading
import time

try:
    # This requires Npcap on Windows
    from scapy.all import sniff, Dot11Deauth
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class PacketAnalyzer:
    def __init__(self):
        self.running = False
        self.thread = None
        self.deauth_events = []
        self.npcap_missing = not SCAPY_AVAILABLE
        self.monitor_failed = False
        
    def start(self):
        if not self.running and not self.npcap_missing:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        try:
            while self.running:
                # We attempt to sniff 802.11 frames. This requires the adapter to actually
                # pass raw frames up to Npcap, which on Windows usually requires specialized adapters
                # We attempt to sniff 802.11 frames. store=False is CRITICAL to prevent massive memory leaks.
                sniff(prn=self._process_packet, stop_filter=lambda p: not self.running, timeout=2, store=False)
        except Exception as e:
            err = str(e).lower()
            if "npcap" in err or "winpcap" in err or "pcap" in err:
                self.npcap_missing = True
            else:
                self.monitor_failed = True
            self.running = False

    def _process_packet(self, pkt):
        if pkt.haslayer(Dot11Deauth):
            self.deauth_events.insert(0, {
                "time": time.strftime("%H:%M:%S"),
                "sender": str(pkt.addr2),
                "target": str(pkt.addr1)
            })
            if len(self.deauth_events) > 50:
                self.deauth_events.pop()

    def analyze_loss_pattern(self, ping_history):
        # ping_history: list of integers [15, 14, 999, 999, 15...]
        # 999 indicates a dropped packet
        if not ping_history:
            return "Awaiting ping data from Game Mode...", "#a6a8af"
            
        loss_indices = [i for i, p in enumerate(ping_history) if p == 999]
        if not loss_indices:
            return "No packet loss detected in the given timeframe.", "#00E676"
            
        bursts = 0
        for i in range(1, len(loss_indices)):
            if loss_indices[i] == loss_indices[i-1] + 1:
                bursts += 1
                
        if bursts > len(loss_indices) * 0.4:
            return "🚨 BURST LOSS: Multiple packets dropping consecutively. Usually caused by severe physical WiFi interference (microwaves, bluetooth, neighbors) or a completely overloaded ISP node dropping clusters of traffic.", "#FF5252"
            
        intervals = []
        for i in range(1, len(loss_indices)):
            intervals.append(loss_indices[i] - loss_indices[i-1])
            
        if len(intervals) >= 3:
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            if variance < 5.0 and avg_interval > 1: 
                return f"⚠️ PERIODIC LOSS: Packets drop consistently every ~{int(avg_interval)} seconds. This is almost always software-induced: Windows searching for better networks (Roaming), or a background app briefly freezing your network card.", "#FFEA00"
                
        return "⚠️ RANDOM LOSS: Scattered packet drops. Usually caused by general WiFi distance limitations or network congestion.", "#FFEA00"
