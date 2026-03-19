import customtkinter as ctk
import threading
from diagnostics.signal import get_wifi_signal
from diagnostics.speed import run_speed_test
from diagnostics.ping import run_ping_test
from diagnostics.dns import check_dns
from diagnostics.gateway import check_gateway
from diagnostics.channel import analyze_channels
from troubleshooter import analyze_results
from utils import Status

class DashboardTab(ctk.CTkFrame):
    def __init__(self, master, update_status_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.update_status_callback = update_status_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Controls
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        self.run_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Run Full Diagnostics", 
            command=self.run_diagnostics,
            fg_color="#cba6f7",
            hover_color="#b4befe",
            text_color="#313338",
            font=ctk.CTkFont(weight="bold")
        )
        self.run_btn.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.controls_frame, 
            mode="indeterminate",
            progress_color="#cba6f7"
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(20, 0))
        self.progress_bar.set(0)

        # Results Panel
        self.results_frame = ctk.CTkScrollableFrame(
            self, 
            label_text="Live Metrics", 
            label_anchor="w", 
            fg_color="#313338",
            scrollbar_button_color="#2b2d31",
            scrollbar_button_hover_color="#cba6f7"
        )
        self.results_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(1, weight=1)

        # Prepare result labels
        self.result_labels = {}
        metrics = ["SIGNAL", "SPEED", "PING", "DNS", "GATEWAY", "CHANNEL"]
        
        for i, metric in enumerate(metrics):
            name_lbl = ctk.CTkLabel(self.results_frame, text=metric, font=ctk.CTkFont(weight="bold"), width=80, anchor="w")
            name_lbl.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            val_lbl = ctk.CTkLabel(self.results_frame, text="Waiting...", text_color="gray", anchor="w")
            val_lbl.grid(row=i, column=1, padx=10, pady=5, sticky="we")
            
            self.result_labels[metric.lower()] = val_lbl

        # Diagnosis section
        self.diag_frame = ctk.CTkFrame(self, fg_color="#313338")
        self.diag_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        self.diag_title = ctk.CTkLabel(self.diag_frame, text="Diagnosis & Recommendations", font=ctk.CTkFont(weight="bold"))
        self.diag_title.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.diag_text = ctk.CTkTextbox(self.diag_frame, height=120, wrap="word", fg_color="#2b2d31")
        self.diag_text.pack(fill="x", padx=10, pady=10)
        self.diag_text.insert("0.0", "Run diagnostics to get a plain-English explanation of your network issues.")
        self.diag_text.configure(state="disabled")

    def log_status(self, text):
        if self.update_status_callback:
            self.update_status_callback(text)

    def update_metric(self, metric, result):
        lbl = self.result_labels.get(metric)
        if not lbl: return
        
        status = result.get("status")
        value = result.get("value")
        details = result.get("details", "")
        
        # Cyan accents, bright status colors for Phase 2 theme
        colors = {
            Status.GOOD: "#00E676", # Bright teal/green
            Status.WARNING: "#FFEA00", # Yellow
            Status.BAD: "#FF5252", # Red
            Status.ERROR: "#D50000"
        }
        color = colors.get(status, "white")
        
        lbl.configure(text=f"{value}  —  {details}", text_color=color)

    def run_diagnostics(self):
        self.run_btn.configure(state="disabled", text="Testing...")
        self.progress_bar.start()
        
        for lbl in self.result_labels.values():
            lbl.configure(text="Testing...", text_color="gray")
            
        self.diag_text.configure(state="normal")
        self.diag_text.delete("0.0", "end")
        self.diag_text.insert("0.0", "Analyzing network data...\n")
        self.diag_text.configure(state="disabled")

        threading.Thread(target=self._test_runner, daemon=True).start()

    def _test_runner(self):
        all_results = {}
        
        self.log_status("Status: Pinging router...")
        res = check_gateway()
        self.update_metric("gateway", res)
        all_results["gateway"] = res
        
        self.log_status("Status: Testing DNS resolution...")
        res = check_dns()
        self.update_metric("dns", res)
        all_results["dns"] = res
        
        self.log_status("Status: Analyzing WiFi environment...")
        res_sig = get_wifi_signal()
        res_chan = analyze_channels()
        self.update_metric("signal", res_sig)
        self.update_metric("channel", res_chan)
        all_results["signal"] = res_sig
        all_results["channel"] = res_chan
        
        self.log_status("Status: Running latency/jitter test (10s)...")
        res = run_ping_test(count=10)
        self.update_metric("ping", res)
        all_results["ping"] = res
        
        self.log_status("Status: Running speed test (this takes a moment)...")
        res = run_speed_test()
        self.update_metric("speed", res)
        all_results["speed"] = res
        
        self.log_status("Status: Generating diagnosis...")
        suggestions = analyze_results(all_results)
        
        # Use after on master to update UI
        try:
            self.winfo_toplevel().after(0, self._finish_tests, suggestions)
        except:
            pass # Failsafe if widget destroyed
        
    def _finish_tests(self, suggestions):
        self.progress_bar.stop()
        self.run_btn.configure(state="normal", text="Re-test")
        self.log_status("Status: Finished")
        
        self.diag_text.configure(state="normal")
        self.diag_text.delete("0.0", "end")
        
        for i, sugg in enumerate(suggestions, 1):
            self.diag_text.insert("end", f"{sugg}\n\n")
            
        self.diag_text.configure(state="disabled")
