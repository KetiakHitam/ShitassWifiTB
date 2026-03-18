import customtkinter as ctk
import threading
import time

# Import diagnostics
from diagnostics.signal import get_wifi_signal
from diagnostics.speed import run_speed_test
from diagnostics.ping import run_ping_test
from diagnostics.dns import check_dns
from diagnostics.gateway import check_gateway
from diagnostics.channel import analyze_channels
from troubleshooter import analyze_results
from utils import Status

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ShitassWifiTB - WiFi Troubleshooter")
        self.geometry("700x600")
        self.resizable(False, False)

        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Network Diagnostics", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(side="left")
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(side="right", pady=5)

        # Controls
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.run_btn = ctk.CTkButton(self.controls_frame, text="Run Full Diagnostics", command=self.run_diagnostics)
        self.run_btn.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(self.controls_frame, mode="indeterminate")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(20, 0))
        self.progress_bar.set(0)

        # Results Panel
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Live Metrics", label_anchor="w")
        self.results_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
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
        self.diag_frame = ctk.CTkFrame(self)
        self.diag_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        self.diag_title = ctk.CTkLabel(self.diag_frame, text="Diagnosis & Recommendations", font=ctk.CTkFont(weight="bold"))
        self.diag_title.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.diag_text = ctk.CTkTextbox(self.diag_frame, height=120, wrap="word")
        self.diag_text.pack(fill="x", padx=10, pady=10)
        self.diag_text.insert("0.0", "Run diagnostics to get a plain-English explanation of your network issues.")
        self.diag_text.configure(state="disabled")

    def log_status(self, text):
        self.status_label.configure(text=text)
        self.update()

    def update_metric(self, metric, result):
        lbl = self.result_labels.get(metric)
        if not lbl: return
        
        status = result.get("status")
        value = result.get("value")
        details = result.get("details", "")
        
        # Color coding
        colors = {
            Status.GOOD: "green",
            Status.WARNING: "orange",
            Status.BAD: "red",
            Status.ERROR: "red"
        }
        color = colors.get(status, "white")
        
        lbl.configure(text=f"{value}  —  {details}", text_color=color)

    def run_diagnostics(self):
        # Disable button and start loading
        self.run_btn.configure(state="disabled", text="Testing...")
        self.progress_bar.start()
        
        # Reset labels
        for lbl in self.result_labels.values():
            lbl.configure(text="Testing...", text_color="gray")
            
        self.diag_text.configure(state="normal")
        self.diag_text.delete("0.0", "end")
        self.diag_text.insert("0.0", "Analyzing network data...\n")
        self.diag_text.configure(state="disabled")

        # Run tests in a background thread so UI doesn't freeze
        threading.Thread(target=self._test_runner, daemon=True).start()

    def _test_runner(self):
        all_results = {}
        
        # Run sequentially to avoid overwhelming the network connection during tests
        # 1. Gateway
        self.log_status("Status: Pinging router...")
        res = check_gateway()
        self.update_metric("gateway", res)
        all_results["gateway"] = res
        
        # 2. DNS
        self.log_status("Status: Testing DNS resolution...")
        res = check_dns()
        self.update_metric("dns", res)
        all_results["dns"] = res
        
        # 3. Signal & Channel (Fast local checks)
        self.log_status("Status: Analyzing WiFi environment...")
        res_sig = get_wifi_signal()
        res_chan = analyze_channels()
        self.update_metric("signal", res_sig)
        self.update_metric("channel", res_chan)
        all_results["signal"] = res_sig
        all_results["channel"] = res_chan
        
        # 4. Sustained Ping (Takes ~10 seconds for the test)
        self.log_status("Status: Running latency/jitter test (10s)...")
        res = run_ping_test(count=10) # 10s for UI responsiveness, can be increased
        self.update_metric("ping", res)
        all_results["ping"] = res
        
        # 5. Speed Test (Slowest, do last)
        self.log_status("Status: Running speed test (this takes a moment)...")
        res = run_speed_test()
        self.update_metric("speed", res)
        all_results["speed"] = res
        
        # Generate Diagnosis
        self.log_status("Status: Generating diagnosis...")
        suggestions = analyze_results(all_results)
        
        # Update UI back on main thread
        self.after(0, self._finish_tests, suggestions)
        
    def _finish_tests(self, suggestions):
        self.progress_bar.stop()
        self.run_btn.configure(state="normal", text="Re-test")
        self.log_status("Status: Finished")
        
        self.diag_text.configure(state="normal")
        self.diag_text.delete("0.0", "end")
        
        for i, sugg in enumerate(suggestions, 1):
            self.diag_text.insert("end", f"{sugg}\n\n")
            
        self.diag_text.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()
