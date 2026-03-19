import customtkinter as ctk
import os
import sys
import threading
import pystray
from PIL import Image, ImageDraw

# Ensure tabs directory is discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tabs.dashboard import DashboardTab
from tabs.logs import LogsTab
from tabs.deep_scan import DeepScanTab
from tabs.bandwidth import BandwidthTab
from tabs.game_mode import GameModeTab
from tabs.traceroute import TracerouteTab
from tabs.packet_analyzer import PacketAnalyzerTab

# Phase 2 Theme Palette (Discord + Catppuccin)
BG_DARK = "#313338" # Discord main bg
BG_PANEL = "#2b2d31" # Discord secondary panel
ACCENT_PURPLE = "#cba6f7" # Catppuccin Mauve
ACCENT_PURPLE_HOVER = "#b4befe" # Catppuccin Lavender
TEXT_MAIN = "#f2f3f5" # Discord text color

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ShitassWifiTB - Advanced Diagnostics")
        self.geometry("850x650")
        self.resizable(False, False)
        
        # Apply dark theme background
        self.configure(fg_color=BG_DARK)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="ShitassWifiTB", 
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), 
            text_color=ACCENT_PURPLE
        )
        self.title_label.pack(side="left")
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(side="right", pady=5)

        # Tabview
        self.tabview = ctk.CTkTabview(
            self, 
            width=810, 
            height=600, 
            fg_color=BG_PANEL, 
            segmented_button_fg_color=BG_DARK, 
            segmented_button_selected_color=ACCENT_PURPLE, 
            segmented_button_selected_hover_color=ACCENT_PURPLE_HOVER, 
            segmented_button_unselected_color=BG_DARK, 
            text_color=TEXT_MAIN
        )
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Add Tabs
        self.tabview.add("Dashboard")
        self.tabview.add("Game Mode")
        self.tabview.add("Bandwidth")
        self.tabview.add("Traceroute")
        self.tabview.add("Logs")
        self.tabview.add("Deep Scan")
        self.tabview.add("Packet Analyzer")
        
        # Init Tabs
        self.dashboard_tab = DashboardTab(self.tabview.tab("Dashboard"), update_status_callback=self.log_status, fg_color="transparent")
        self.dashboard_tab.pack(fill="both", expand=True)

        self.logs_tab = LogsTab(self.tabview.tab("Logs"), bg_color="transparent")
        self.logs_tab.pack(fill="both", expand=True)

        self.deep_scan_tab = DeepScanTab(self.tabview.tab("Deep Scan"), bg_color="transparent")
        self.deep_scan_tab.pack(fill="both", expand=True)
        
        self.bandwidth_tab = BandwidthTab(self.tabview.tab("Bandwidth"), bg_color="transparent")
        self.bandwidth_tab.pack(fill="both", expand=True)
        
        self.game_mode_tab = GameModeTab(self.tabview.tab("Game Mode"), bg_color="transparent")
        self.game_mode_tab.pack(fill="both", expand=True)

        self.traceroute_tab = TracerouteTab(self.tabview.tab("Traceroute"), bg_color="transparent")
        self.traceroute_tab.pack(fill="both", expand=True)
        
        self.packet_analyzer_tab = PacketAnalyzerTab(self.tabview.tab("Packet Analyzer"), bg_color="transparent")
        self.packet_analyzer_tab.pack(fill="both", expand=True)

        # Handle close event for system tray
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.tray_icon = None

    def log_status(self, text):
        self.status_label.configure(text=text)
        self.update()

    def create_tray_icon_image(self):
        # Create a simple generic system tray icon since we don't have an .ico file
        image = Image.new('RGB', (64, 64), color=BG_DARK)
        d = ImageDraw.Draw(image)
        d.rectangle([16, 16, 48, 48], fill=ACCENT_PURPLE)
        return image

    def hide_window(self):
        self.withdraw()
        image = self.create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem('Open Dashboard', self.show_window, default=True),
            pystray.MenuItem('Quit ShitassWifiTB', self.quit_app)
        )
        self.tray_icon = pystray.Icon("ShitassWifiTB", image, "ShitassWifiTB Logging Active", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon, item):
        icon.stop()
        self.after(0, self.deiconify)

    def quit_app(self, icon, item):
        icon.stop()
        try:
            self.logs_tab.on_closing()
            self.bandwidth_tab.on_closing()
            self.game_mode_tab.on_closing()
            self.traceroute_tab.on_closing()
            self.packet_analyzer_tab.on_closing()
        except: pass
        self.after(0, self.destroy)

if __name__ == "__main__":
    app = App()
    app.mainloop()
