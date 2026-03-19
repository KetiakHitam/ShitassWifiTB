import customtkinter as ctk
from engines.traceroute import TracerouteEngine
from utils import Status

class TracerouteTab(ctk.CTkFrame):
    def __init__(self, master, bg_color="#2b2d31", **kwargs):
        super().__init__(master, fg_color=bg_color, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.engine = TracerouteEngine()

        # ========= Header & Controls =========
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        ctk.CTkLabel(self.header_frame, text="Target Host / Server IP:", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        
        self.target_entry = ctk.CTkEntry(
            self.header_frame, 
            placeholder_text="e.g. 8.8.8.8 or unifi.com.my", 
            width=250,
            fg_color="#313338",
            border_color="#cba6f7",
            text_color="#f2f3f5"
        )
        self.target_entry.insert(0, "8.8.8.8")
        self.target_entry.pack(side="left")
        
        self.run_btn = ctk.CTkButton(
            self.header_frame, 
            text="Start Trace", 
            command=self.start_trace,
            fg_color="#cba6f7",
            hover_color="#b4befe",
            text_color="#313338",
            font=ctk.CTkFont(weight="bold"),
            width=120
        )
        self.run_btn.pack(side="left", padx=15)

        self.status_lbl = ctk.CTkLabel(self.header_frame, text="Ready.", text_color="#a6a8af")
        self.status_lbl.pack(side="left", padx=10)
        
        self.auto_rerun_var = ctk.StringVar(value="off")
        self.auto_rerun_chk = ctk.CTkCheckBox(
            self.header_frame, 
            text="Auto Re-run",
            variable=self.auto_rerun_var,
            onvalue="on",
            offvalue="off",
            fg_color="#cba6f7",
            hover_color="#b4befe"
        )
        self.auto_rerun_chk.pack(side="right")

        # ========= Hops List =========
        self.hops_frame = ctk.CTkScrollableFrame(
            self, 
            label_text="Network Path (Hop-by-Hop Latency)", 
            label_font=ctk.CTkFont(weight="bold", size=14),
            label_text_color="#f2f3f5",
            fg_color="#313338",
            scrollbar_button_color="#2b2d31",
            scrollbar_button_hover_color="#cba6f7"
        )
        self.hops_frame.grid(row=1, column=0, padx=20, pady=(15, 10), sticky="nsew")

        # Hops headers
        header_row = ctk.CTkFrame(self.hops_frame, fg_color="#2b2d31", corner_radius=0)
        header_row.pack(fill="x", pady=(0, 5))
        header_row.grid_columnconfigure((0,1,2,3), weight=1)
        
        ctk.CTkLabel(header_row, text="HOP", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(header_row, text="IP ADDRESS", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(header_row, text="AVG PING", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="e", padx=10, pady=5)
        ctk.CTkLabel(header_row, text="RAW PINGS", text_color="#a6a8af", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, sticky="e", padx=10, pady=5)

        self.hops_container = ctk.CTkFrame(self.hops_frame, fg_color="transparent")
        self.hops_container.pack(fill="both", expand=True)

        self.hop_widgets = []

        # ========= Blame Card =========
        self.blame_frame = ctk.CTkFrame(self, fg_color="#313338", corner_radius=8)
        self.blame_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.blame_title = ctk.CTkLabel(self.blame_frame, text="Awaiting trace...", font=ctk.CTkFont(weight="bold", size=16), text_color="#a6a8af")
        self.blame_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.blame_desc = ctk.CTkLabel(self.blame_frame, text="Run a trace to identify the exact router causing your lag.", text_color="#f2f3f5", justify="left", wraplength=700)
        self.blame_desc.pack(anchor="w", padx=15, pady=(0, 15))

    def start_trace(self):
        target = self.target_entry.get().strip()
        if not target: return
        
        self.run_btn.configure(state="disabled", text="Tracing...")
        self.status_lbl.configure(text=f"Tracing path to {target} (Max 30 hops)...")
        
        for w in self.hop_widgets: w.destroy()
        self.hop_widgets.clear()
        
        self.blame_title.configure(text="Analyzing path...", text_color="#a6a8af")
        self.blame_desc.configure(text="Please wait until the end-to-end trace is complete.")
        
        self.engine.start_trace(target, self.on_hop, self.on_complete)

    def on_hop(self, hop_info):
        self.winfo_toplevel().after(0, self._render_hop, hop_info)

    def _render_hop(self, h):
        row = len(self.hop_widgets)
        
        frame = ctk.CTkFrame(self.hops_container, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=0, pady=2)
        frame.grid_columnconfigure((0,1,2,3), weight=1)
        self.hop_widgets.append(frame)
        
        ctk.CTkLabel(frame, text=f"Hop {h['hop']}", font=ctk.CTkFont(family="Consolas")).grid(row=0, column=0, sticky="w", padx=10)
        
        ctk.CTkLabel(frame, text=h["ip"], text_color="#a6a8af", font=ctk.CTkFont(family="Consolas")).grid(row=0, column=1, sticky="w", padx=10)
        
        ping = h["avg_ping"]
        ping_str = f"{ping} ms" if ping != 999 else "TIMEOUT"
        color = "#00E676" if ping < 50 else ("#FFEA00" if ping < 100 else "#FF5252")
        
        ctk.CTkLabel(frame, text=ping_str, text_color=color, font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="e", padx=10)
        
        raw_strs = [f"{p}ms" if p != 999 else "T/O" for p in h["pings"]]
        raw_text = " | ".join(raw_strs)
        ctk.CTkLabel(frame, text=raw_text, text_color="#6c6f78", font=ctk.CTkFont(size=11)).grid(row=0, column=3, sticky="e", padx=10)
        
        self.hops_frame._parent_canvas.yview_moveto(1.0)

    def on_complete(self, hops_data, blame_report):
        self.winfo_toplevel().after(0, self._render_complete, blame_report)

    def _render_complete(self, report):
        self.run_btn.configure(state="normal", text="Start Trace")
        self.status_lbl.configure(text="Trace complete.")
        
        colors = {
            Status.GOOD: "#00E676",
            Status.WARNING: "#FFEA00",
            Status.BAD: "#FF5252",
            Status.ERROR: "#D50000"
        }
        
        self.blame_title.configure(text=f"GUILTY HOP: {report['verdict']}", text_color=colors.get(report['status'], "#f2f3f5"))
        self.blame_desc.configure(text=report['text'])
        
        if self.auto_rerun_var.get() == "on":
            self.status_lbl.configure(text="Auto re-run enabled. Waiting 3s...")
            self.after(3000, self._auto_restart)

    def _auto_restart(self):
        if self.auto_rerun_var.get() == "on":
            self.start_trace()

    def on_closing(self):
        self.engine.stop()

#testing