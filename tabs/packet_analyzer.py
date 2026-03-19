import customtkinter as ctk
from engines.packet_analyzer import PacketAnalyzer

class PacketAnalyzerTab(ctk.CTkFrame):
    def __init__(self, master, bg_color="#2b2d31", **kwargs):
        super().__init__(master, fg_color=bg_color, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((1,2), weight=1)
        
        self.engine = PacketAnalyzer()
        self.ui_update_loop = None

        # ========= Header =========
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        ctk.CTkLabel(self.header_frame, text="Advanced Packet Analysis", font=ctk.CTkFont(weight="bold", size=18), text_color="#cba6f7").pack(side="left")

        # ========= Deauth Scanner (Scapy) =========
        self.deauth_frame = ctk.CTkFrame(self, fg_color="#313338", corner_radius=8)
        self.deauth_frame.grid(row=1, column=0, padx=20, pady=(15, 10), sticky="nsew")
        
        ctk.CTkLabel(self.deauth_frame, text="802.11 Deauthentication Frame Sniffer", font=ctk.CTkFont(weight="bold", size=14), text_color="#f2f3f5").pack(anchor="w", padx=15, pady=(15, 5))
        
        if self.engine.npcap_missing:
            ctk.CTkLabel(self.deauth_frame, text="ERROR: Npcap driver is not installed, or not installed with 'Raw 802.11 support'.\nScapy cannot sniff raw WiFi frames on standard Windows without Npcap in Monitor Mode.", text_color="#FF5252", justify="left").pack(anchor="w", padx=15, pady=5)
        else:
            self.deauth_toggle = ctk.CTkSwitch(
                self.deauth_frame, 
                text="Enable Raw WiFi Packet Cap (Requires Monitor Mode adapter)", 
                command=self.toggle_scanner,
                progress_color="#FF5252",
                button_color="#b4befe"
            )
            self.deauth_toggle.pack(anchor="w", padx=15, pady=10)
            
            self.deauth_status = ctk.CTkLabel(self.deauth_frame, text="Sniffer is offline.", text_color="#a6a8af")
            self.deauth_status.pack(anchor="w", padx=15)
            
            self.deauth_list = ctk.CTkTextbox(self.deauth_frame, height=100, fg_color="#2b2d31", text_color="#f2f3f5")
            self.deauth_list.pack(fill="both", expand=True, padx=15, pady=15)
            self.deauth_list.insert("0.0", "Awaiting capture...")
            self.deauth_list.configure(state="disabled")

        # ========= ICMP Loss Pattern Algorithm =========
        self.pattern_frame = ctk.CTkFrame(self, fg_color="#313338", corner_radius=8)
        self.pattern_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        ctk.CTkLabel(self.pattern_frame, text="Lag Spikes Mathematical Analyzer", font=ctk.CTkFont(weight="bold", size=14), text_color="#f2f3f5").pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(self.pattern_frame, text="Analyzes your Game Mode ping history to mathematically classify what type of interference is hitting your PC.", text_color="#a6a8af", justify="left").pack(anchor="w", padx=15)
        
        self.analyze_btn = ctk.CTkButton(
            self.pattern_frame, 
            text="Analyze Game Mode History", 
            command=self.run_pattern_analysis,
            fg_color="#cba6f7",
            hover_color="#b4befe",
            text_color="#313338",
            font=ctk.CTkFont(weight="bold")
        )
        self.analyze_btn.pack(anchor="w", padx=15, pady=15)
        
        self.pattern_result_lbl = ctk.CTkLabel(self.pattern_frame, text="Run an analysis to see results.", font=ctk.CTkFont(weight="bold", size=14), text_color="#f2f3f5", justify="left", wraplength=700)
        self.pattern_result_lbl.pack(anchor="w", padx=15, pady=(0, 15))

    def toggle_scanner(self):
        if self.deauth_toggle.get() == 1:
            self.engine.start()
            if self.engine.monitor_failed:
                self.deauth_status.configure(text="ERROR: Adapter rejected capture. It likely does not support Monitor Mode on Windows.", text_color="#FF5252")
                self.deauth_toggle.deselect()
            else:
                self.deauth_status.configure(text="Sniffing locally... (Searching for malicious Deauth storms)", text_color="#00E676")
                self._update_deauth_loop()
        else:
            self.engine.stop()
            self.deauth_status.configure(text="Sniffer is offline.", text_color="#a6a8af")
            if self.ui_update_loop:
                self.after_cancel(self.ui_update_loop)

    def _update_deauth_loop(self):
        if not self.engine.running: return
        
        if self.engine.monitor_failed:
            self.deauth_status.configure(text="ERROR: Adapter rejected raw capture. It likely does not support Monitor Mode natively.", text_color="#FF5252")
            self.deauth_toggle.deselect()
            return
            
        events = self.engine.deauth_events
        self.deauth_list.configure(state="normal")
        self.deauth_list.delete("0.0", "end")
        if not events:
            self.deauth_list.insert("0.0", "No Deauthentication frames detected (You are safe).")
        else:
            for ev in events:
                self.deauth_list.insert("end", f"[{ev['time']}] DEAUTH ATTACK from {ev['sender']} targeting {ev['target']}\n")
        self.deauth_list.configure(state="disabled")
        
        # UI refresh cycle
        self.ui_update_loop = self.after(2000, self._update_deauth_loop)

    def run_pattern_analysis(self):
        try:
            # Safely grab history from the main app's GameMode tab
            app_instance = self.winfo_toplevel()
            game_history = app_instance.game_mode_tab.pinger.history
            pings = [h[1] for h in game_history]
            
            text, color = self.engine.analyze_loss_pattern(pings)
            self.pattern_result_lbl.configure(text=text, text_color=color)
        except Exception as e:
            self.pattern_result_lbl.configure(text=f"Failed to read Game Mode data. Ensure Game Mode has been running continuously to generate a trace. Error: {e}", text_color="#FF5252")

    def on_closing(self):
        self.engine.stop()
        if self.ui_update_loop:
            self.after_cancel(self.ui_update_loop)
