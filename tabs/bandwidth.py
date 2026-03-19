import customtkinter as ctk
import threading
from engines.bandwidth_monitor import BandwidthMonitor

class BandwidthTab(ctk.CTkFrame):
    def __init__(self, master, bg_color="#2b2d31", **kwargs):
        super().__init__(master, fg_color=bg_color, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.monitor = BandwidthMonitor()
        self.ui_update_loop = None

        # ========= Header & Controls =========
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.toggle_switch = ctk.CTkSwitch(
            self.header_frame, 
            text="Enable Bandwidth Cop (Live Tracking)", 
            command=self.toggle_monitor,
            progress_color="#cba6f7",
            button_color="#b4befe",
            button_hover_color="#f2f3f5",
            font=ctk.CTkFont(weight="bold")
        )
        self.toggle_switch.pack(side="left")

        # Advisory Note
        note = ctk.CTkLabel(
            self.header_frame, 
            text="Identify what is secretly using the internet.\nNOTE: Kill processes in Task Manager manually.", 
            text_color="#a6a8af", 
            justify="right"
        )
        note.pack(side="right")

        # ========= Speed Dashboard =========
        self.speed_frame = ctk.CTkFrame(self, fg_color="#313338", corner_radius=8)
        self.speed_frame.grid(row=1, column=0, padx=20, pady=15, sticky="ew")
        self.speed_frame.grid_columnconfigure((0, 1), weight=1)

        # Download Stats
        down_container = ctk.CTkFrame(self.speed_frame, fg_color="transparent")
        down_container.grid(row=0, column=0, pady=15)
        ctk.CTkLabel(down_container, text="TOTAL DOWNLOAD", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a6a8af").pack()
        self.down_lbl = ctk.CTkLabel(down_container, text="0.00 Mbps", font=ctk.CTkFont(family="Consolas", size=32, weight="bold"), text_color="#00E676")
        self.down_lbl.pack()

        # Upload Stats
        up_container = ctk.CTkFrame(self.speed_frame, fg_color="transparent")
        up_container.grid(row=0, column=1, pady=15)
        ctk.CTkLabel(up_container, text="TOTAL UPLOAD", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a6a8af").pack()
        self.up_lbl = ctk.CTkLabel(up_container, text="0.00 Mbps", font=ctk.CTkFont(family="Consolas", size=32, weight="bold"), text_color="#00E676")
        self.up_lbl.pack()

        # ========= Process Leaderboard =========
        self.board_frame = ctk.CTkScrollableFrame(
            self, 
            label_text="Active Internet Connections (By Process)", 
            label_font=ctk.CTkFont(weight="bold", size=14),
            label_text_color="#cba6f7",
            fg_color="#313338",
            scrollbar_button_color="#2b2d31",
            scrollbar_button_hover_color="#cba6f7"
        )
        self.board_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Table Headers
        self.board_header = ctk.CTkFrame(self.board_frame, fg_color="#2b2d31")
        self.board_header.pack(fill="x", padx=5, pady=5)
        self.board_header.grid_columnconfigure(0, weight=3) # Name
        self.board_header.grid_columnconfigure(1, weight=1) # PID
        self.board_header.grid_columnconfigure(2, weight=1) # Connections
        
        ctk.CTkLabel(self.board_header, text="PROCESS NAME", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(self.board_header, text="PID", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(self.board_header, text="ACTIVE SOCKETS", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="e", padx=10, pady=5)

        self.process_rows = []

    def toggle_monitor(self):
        if self.toggle_switch.get() == 1:
            self.monitor.start()
            self._update_ui_loop()
        else:
            self.monitor.stop()
            if self.ui_update_loop:
                self.after_cancel(self.ui_update_loop)

    def _update_ui_loop(self):
        if not self.monitor.is_running():
            return

        # 1. Update Speeds
        down_mbps = self.monitor.latest_total["download_mbps"]
        up_mbps = self.monitor.latest_total["upload_mbps"]
        
        # Color coding for high bandwidth (Warning > 10 Mbps, Danger > 50 Mbps)
        down_color = "#FF5252" if down_mbps > 50 else ("#FFEA00" if down_mbps > 10 else "#00E676")
        up_color = "#FF5252" if up_mbps > 20 else ("#FFEA00" if up_mbps > 5 else "#00E676")
        
        self.down_lbl.configure(text=f"{down_mbps:.2f} Mbps", text_color=down_color)
        self.up_lbl.configure(text=f"{up_mbps:.2f} Mbps", text_color=up_color)

        # 2. Update Leaderboard without flickering
        data_len = len(self.monitor.latest_data)
        
        # Ensure we have enough row widgets created in our pool
        while len(self.process_rows) < data_len:
            row_frame = ctk.CTkFrame(self.board_frame, fg_color="transparent")
            row_frame.grid_columnconfigure(0, weight=3)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            
            name_lbl = ctk.CTkLabel(row_frame, text="", font=ctk.CTkFont(family="Consolas"))
            name_lbl.grid(row=0, column=0, sticky="w", padx=10)
            
            pid_lbl = ctk.CTkLabel(row_frame, text="", text_color="#a6a8af")
            pid_lbl.grid(row=0, column=1, sticky="w", padx=10)
            
            conns_lbl = ctk.CTkLabel(row_frame, text="", font=ctk.CTkFont(weight="bold"))
            conns_lbl.grid(row=0, column=2, sticky="e", padx=10)
            
            self.process_rows.append((row_frame, name_lbl, pid_lbl, conns_lbl))

        # Update text on active rows and pack them
        for i, proc in enumerate(self.monitor.latest_data):
            row_frame, name_lbl, pid_lbl, conns_lbl = self.process_rows[i]
            
            conn_count = proc["connections"]
            text_color = "#f2f3f5"
            if conn_count > 50: text_color = "#FF5252"
            elif conn_count > 20: text_color = "#FFEA00"
                
            name_lbl.configure(text=proc["name"], text_color=text_color)
            pid_lbl.configure(text=str(proc["pid"]))
            conns_lbl.configure(text=str(conn_count), text_color=text_color)
            
            if not row_frame.winfo_ismapped():
                row_frame.pack(fill="x", padx=5, pady=2)
                
        # Hide any excess rows we don't need right now
        for i in range(data_len, len(self.process_rows)):
            row_frame, _, _, _ = self.process_rows[i]
            if row_frame.winfo_ismapped():
                row_frame.pack_forget()

        # Schedule next update in 1.5 seconds
        self.ui_update_loop = self.after(1500, self._update_ui_loop)

    def on_closing(self):
        self.monitor.stop()
        if self.ui_update_loop:
            self.after_cancel(self.ui_update_loop)
