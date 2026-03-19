import customtkinter as ctk
import threading
from engines.adapter_doctor import AdapterDoctor
from utils import Status

class DeepScanTab(ctk.CTkFrame):
    def __init__(self, master, bg_color="#2b2d31", **kwargs):
        super().__init__(master, fg_color=bg_color, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.doctor = AdapterDoctor()

        # Phase 2 Theme Colors mapped to Status
        self.colors = {
            Status.GOOD: "#00E676", # Green
            Status.WARNING: "#FFEA00", # Yellow
            Status.BAD: "#FF5252", # Red
            Status.ERROR: "#D50000"
        }

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        title = ctk.CTkLabel(self.header_frame, text="Adapter Config Audit", font=ctk.CTkFont(weight="bold", size=18), text_color="#cba6f7")
        title.pack(side="left")
        
        self.run_btn = ctk.CTkButton(
            self.header_frame, 
            text="Run System Audit (Requires Admin)", 
            command=self.run_audit,
            fg_color="#cba6f7",
            hover_color="#b4befe",
            text_color="#313338",
            font=ctk.CTkFont(weight="bold")
        )
        self.run_btn.pack(side="right")
        
        # Advisory notice
        notice = ctk.CTkLabel(
            self, 
            text="Note: This scan checks deep Windows configuration settings that can ruin gaming performance.\nIt does NOT modify any settings automatically. You must make the changes yourself in Device Manager.", 
            text_color="#f2f3f5",
            justify="left"
        )
        notice.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="w")
        
        # Results Scrollable Frame
        self.results_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="#313338",
            scrollbar_button_color="#2b2d31",
            scrollbar_button_hover_color="#cba6f7"
        )
        self.results_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # Store result widgets to destroy them on re-run
        self.result_widgets = []

    def run_audit(self):
        self.run_btn.configure(state="disabled", text="Scanning Windows Registry & WMI...")
        
        # Clear old results
        for widget in self.result_widgets:
            widget.destroy()
        self.result_widgets.clear()
        
        threading.Thread(target=self._audit_thread, daemon=True).start()

    def _audit_thread(self):
        results = self.doctor.run_audit()
        try:
            self.winfo_toplevel().after(0, self._display_results, results)
        except: pass

    def _display_results(self, results):
        self.run_btn.configure(state="normal", text="Re-run System Audit")
        
        for i, res in enumerate(results):
            # Create a card for each result
            card = ctk.CTkFrame(self.results_frame, fg_color="#2b2d31", corner_radius=8)
            card.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            self.result_widgets.append(card)
            
            # Header line: Name + Status/Value
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(10, 5))
            
            color = self.colors.get(res["status"], "#f2f3f5")
            
            name_lbl = ctk.CTkLabel(header, text=res["name"], font=ctk.CTkFont(weight="bold", size=14), text_color="#f2f3f5")
            name_lbl.pack(side="left")
            
            val_lbl = ctk.CTkLabel(header, text=res["value"], font=ctk.CTkFont(weight="bold"), text_color=color)
            val_lbl.pack(side="right")
            
            # Recommendation text
            rec_lbl = ctk.CTkLabel(card, text=res["recommendation"], text_color="#a6a8af", justify="left", wraplength=700)
            rec_lbl.pack(fill="x", padx=10, pady=(0, 10), anchor="w")
