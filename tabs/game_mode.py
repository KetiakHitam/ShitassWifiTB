import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from engines.game_pinger import GamePinger

class GameModeTab(ctk.CTkFrame):
    def __init__(self, master, bg_color="#2b2d31", **kwargs):
        super().__init__(master, fg_color=bg_color, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.pinger = GamePinger()
        self.ui_update_loop = None

        # ========= Header & Controls =========
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.toggle_switch = ctk.CTkSwitch(
            self.controls_frame, 
            text="Enable Game Mode (Live Continuous Ping)", 
            command=self.toggle_pinger,
            progress_color="#cba6f7",
            button_color="#b4befe",
            button_hover_color="#f2f3f5",
            font=ctk.CTkFont(weight="bold")
        )
        self.toggle_switch.pack(side="left")
        
        ctk.CTkLabel(self.controls_frame, text="Target Host:", text_color="#a6a8af").pack(side="left", padx=(20, 5))
        self.target_dropdown = ctk.CTkComboBox(
            self.controls_frame, 
            values=["8.8.8.8 (Google DNS)", "1.1.1.1 (Cloudflare)", "192.168.1.1 (Local Router)"],
            command=self.change_target,
            fg_color="#313338",
            border_color="#cba6f7",
            button_color="#cba6f7"
        )
        self.target_dropdown.set("8.8.8.8 (Google DNS)")
        self.target_dropdown.pack(side="left")

        # ========= Live Stats Overlay =========
        self.stats_frame = ctk.CTkFrame(self.controls_frame, fg_color="#313338", corner_radius=8)
        self.stats_frame.pack(side="right")
        
        ctk.CTkLabel(self.stats_frame, text="LATENCY", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a6a8af").grid(row=0, column=0, padx=15, pady=(5,0))
        self.ping_lbl = ctk.CTkLabel(self.stats_frame, text="-- ms", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="#f2f3f5")
        self.ping_lbl.grid(row=1, column=0, padx=15, pady=(0,5))

        ctk.CTkLabel(self.stats_frame, text="PACKET LOSS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a6a8af").grid(row=0, column=1, padx=15, pady=(5,0))
        self.loss_lbl = ctk.CTkLabel(self.stats_frame, text="0.0%", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="#f2f3f5")
        self.loss_lbl.grid(row=1, column=1, padx=15, pady=(0,5))

        # ========= Chart Frame =========
        self.chart_frame = ctk.CTkFrame(self, fg_color="#313338")
        self.chart_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Setup Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 4), facecolor="#313338")
        self.ax.set_facecolor("#313338")
        self.ax.tick_params(colors="#f2f3f5")
        for spine in self.ax.spines.values():
            spine.set_color("#6c6f78")
            
        self.ax.set_ylabel("Ping (ms)", color="#f2f3f5")
        self.ax.set_xlabel("Seconds Ago", color="#a6a8af")
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        self._init_chart()

    def _init_chart(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, "Game Mode Offline.\nEnable toggle to start tracing ping latency.", 
                     horizontalalignment='center', verticalalignment='center', color="#f2f3f5", transform=self.ax.transAxes)
        self.canvas.draw()

    def toggle_pinger(self):
        if self.toggle_switch.get() == 1:
            target = self.target_dropdown.get().split(" ")[0]
            self.pinger.target_host = target
            self.pinger.start()
            self._update_ui_loop()
        else:
            self.pinger.stop()
            if self.ui_update_loop:
                self.after_cancel(self.ui_update_loop)
            self._init_chart()
            self.ping_lbl.configure(text="-- ms", text_color="#f2f3f5")
            self.loss_lbl.configure(text="0.0%", text_color="#f2f3f5")

    def change_target(self, choice):
        if self.toggle_switch.get() == 1:
            target = choice.split(" ")[0]
            self.pinger.change_target(target)

    def _update_ui_loop(self):
        if not self.pinger.running: return

        # Shallow copy for thread safety while iterating
        history = list(self.pinger.history) 
        
        if history:
            current_ping = history[-1][1]
            
            # --- Text UI Updates ---
            color = "#00E676" if current_ping < 60 else ("#FFEA00" if current_ping < 120 else "#FF5252")
            if current_ping == 999:
                self.ping_lbl.configure(text="TIMEOUT", text_color="#FF5252")
            else:
                self.ping_lbl.configure(text=f"{current_ping} ms", text_color=color)
                
            # Calculate rolling packet loss (last 50 packets is roughly 50 seconds)
            recent = history[-50:]
            loss_count = sum(1 for _, p in recent if p == 999)
            loss_pct = (loss_count / len(recent)) * 100 if len(recent) > 0 else 0
            
            loss_color = "#00E676" if loss_pct == 0 else ("#FFEA00" if loss_pct < 5 else "#FF5252")
            self.loss_lbl.configure(text=f"{loss_pct:.1f}%", text_color=loss_color)

            # --- Chart Updates ---
            self.ax.clear()
            
            now = time.time()
            x = [t - now for t, _ in history]
            y = [p for _, p in history]
            
            self.ax.plot(x, y, color="#cba6f7", linewidth=2)
            
            # Maintain a reasonable Y scale but allow it to grow for spikes
            max_y = max(100, max(y)) if y else 100
            self.ax.set_ylim(bottom=0, top=max_y + 10)
            
            # X limits: -300s (5 min) to 0s
            self.ax.set_xlim(left=-300, right=0)
            
            # Fill bad zones (> 80ms is lag limit)
            self.ax.axhline(y=80, color="#FF5252", linestyle="--", alpha=0.5)
            self.ax.fill_between(x, y, 80, where=([val >= 80 for val in y]), color="#FF5252", alpha=0.3)
            
            self.ax.set_xlabel("Seconds ago", color="#a6a8af")
            self.ax.set_ylabel("Ping (ms)", color="#f2f3f5")
            self.canvas.draw()

        self.ui_update_loop = self.after(1000, self._update_ui_loop)

    def on_closing(self):
        self.pinger.stop()
        if self.ui_update_loop:
            self.after_cancel(self.ui_update_loop)
