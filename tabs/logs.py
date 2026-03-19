import customtkinter as ctk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
from engines.night_logger import NightLogger
from engines.disconnect_monitor import DisconnectMonitor

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_FILE = os.path.join(DB_DIR, "logs.db")

class LogsTab(ctk.CTkFrame):
    def __init__(self, master, bg_color="#2b2d31", **kwargs):
        super().__init__(master, fg_color=bg_color, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        # Give bottom row less weight so chart takes up more space
        self.grid_rowconfigure(1, weight=3) # Chart
        self.grid_rowconfigure(2, weight=1) # Disconnects log
        
        # Engine instances
        self.night_logger = NightLogger()
        self.disconnect_monitor = DisconnectMonitor()
        
        # ========= Top Controls =========
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        # Switches
        self.switches_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.switches_frame.pack(side="left")
        
        self.toggle_night = ctk.CTkSwitch(
            self.switches_frame, 
            text="Night Logger (Ping/Signal)", 
            command=self.toggle_engines,
            progress_color="#cba6f7",
            button_color="#b4befe",
            button_hover_color="#f2f3f5"
        )
        self.toggle_night.pack(anchor="w", pady=(0, 5))
        
        self.toggle_disc = ctk.CTkSwitch(
            self.switches_frame, 
            text="Disconnect Detective (Real-time drops)", 
            command=self.toggle_engines,
            progress_color="#cba6f7",
            button_color="#b4befe",
            button_hover_color="#f2f3f5"
        )
        self.toggle_disc.pack(anchor="w")
        
        # Buttons
        self.refresh_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Refresh Data", 
            command=self.load_data,
            fg_color="#cba6f7",
            hover_color="#b4befe",
            text_color="#313338",
            font=ctk.CTkFont(weight="bold")
        )
        self.refresh_btn.pack(side="right", padx=(10, 0))
        
        self.export_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Export to CSV", 
            command=self.export_csv,
            fg_color="#313338",
            hover_color="#2b2d31",
            text_color="#f2f3f5",
            border_color="#cba6f7",
            border_width=1
        )
        self.export_btn.pack(side="right")
        
        # ========= Chart Frame =========
        self.chart_frame = ctk.CTkFrame(self, fg_color="#313338")
        self.chart_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        
        self.fig, self.ax = plt.subplots(figsize=(8, 3), facecolor="#313338")
        self.ax.set_facecolor("#313338")
        self.ax.tick_params(colors="#f2f3f5")
        for spine in self.ax.spines.values():
            spine.set_color("#6c6f78")
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # ========= Disconnect Log Frame =========
        self.disc_frame = ctk.CTkFrame(self, fg_color="#313338")
        self.disc_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        lbl = ctk.CTkLabel(self.disc_frame, text="Recent Disconnect Events", font=ctk.CTkFont(weight="bold", size=14), text_color="#cba6f7")
        lbl.pack(anchor="w", padx=10, pady=(5, 0))
        
        self.disc_textbox = ctk.CTkTextbox(self.disc_frame, height=100, wrap="word", fg_color="#2b2d31", text_color="#f2f3f5")
        self.disc_textbox.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.disc_textbox.configure(state="disabled")
        
        # Load initial data
        self.load_data()

    def toggle_engines(self):
        if self.toggle_night.get() == 1: self.night_logger.start()
        else: self.night_logger.stop()
            
        if self.toggle_disc.get() == 1: self.disconnect_monitor.start()
        else: self.disconnect_monitor.stop()

    def load_data(self):
        self.load_chart()
        self.load_disconnects()

    def load_chart(self):
        self.ax.clear()
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Use Python's local time string explicitly instead of SQLite's UTC 'now'
            threshold_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT timestamp, ping_ms FROM periodic_logs WHERE timestamp >= ? ORDER BY timestamp ASC", (threshold_time,))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                self.ax.text(0.5, 0.5, "No ping data collected yet.\nEnable Night Logger.", 
                             horizontalalignment='center', verticalalignment='center',
                             color="#f2f3f5", transform=self.ax.transAxes)
            else:
                timestamps = []
                pings = []
                for row in rows:
                    try:
                        timestamps.append(datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"))
                        pings.append(row[1] if row[1] is not None else 0)
                    except ValueError: pass
                
                self.ax.plot(timestamps, pings, color="#cba6f7", linewidth=2)
                self.ax.set_title("Latency (ms) over last 24 hours", color="#f2f3f5", pad=10)
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                
                threshold = 80
                self.ax.axhline(y=threshold, color="#ff5252", linestyle="--", alpha=0.5)
                self.ax.fill_between(timestamps, pings, threshold, 
                                     where=([p >= threshold for p in pings]), 
                                     color="#ff5252", alpha=0.3)
                self.fig.autofmt_xdate()
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Error loading ping data: {e}", color="#ff5252", transform=self.ax.transAxes)
            
        self.canvas.draw()

    def load_disconnects(self):
        self.disc_textbox.configure(state="normal")
        self.disc_textbox.delete("0.0", "end")
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # Get last 10 drops
            cursor.execute("SELECT drop_time, duration_seconds, signal_before_drop, previous_channel, new_channel FROM disconnect_events ORDER BY drop_time DESC LIMIT 10")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                self.disc_textbox.insert("end", "No disconnect events recorded yet. Enable Disconnect Detective.")
            else:
                text_content = ""
                for row in rows:
                    drop, dur, sig, old_ch, new_ch = row
                    chan_info = ""
                    if old_ch and new_ch and old_ch != new_ch:
                        chan_info = f"[Channel Switch: {old_ch} -> {new_ch}]"
                    elif old_ch:
                        chan_info = f"[Channel {old_ch}]"
                        
                    sig_info = f"{sig}%" if sig else "Unknown"
                    text_content += f"[{drop}] DROPPED for {dur}s — Signal before drop: {sig_info} {chan_info}\n"
                
                self.disc_textbox.insert("end", text_content)
                
        except Exception as e:
            self.disc_textbox.insert("end", f"Error loading disconnects: {e}")
            
        self.disc_textbox.configure(state="disabled")

    def export_csv(self):
        import tkinter.filedialog as fd
        import csv
        file_path = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Logs"
        )
        if file_path:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                # Write multiple tables to the same csv or separate? Let's write periodic logs.
                # In the future they might want both, but for now Night Logs is the main export.
                cursor.execute("SELECT * FROM periodic_logs ORDER BY timestamp DESC")
                with open(file_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([d[0] for d in cursor.description])
                    writer.writerows(cursor.fetchall())
                conn.close()
            except Exception as e:
                print(f"Export error: {e}")

    def on_closing(self):
        # Stop gracefully
        self.night_logger.stop()
        self.disconnect_monitor.stop()
