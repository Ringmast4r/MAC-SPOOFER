#!/usr/bin/env python3
"""
MAC Address Spoofer GUI
A graphical interface to spoof MAC addresses with vendor presets
Requires administrator/root privileges on Windows
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import re
import random
import platform
import ctypes
import sys
import time

# Windows-only module - import conditionally for cross-platform compatibility
try:
    import winreg
except ImportError:
    winreg = None  # Linux/macOS don't have Windows Registry

class MACSpooferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎭 MAC Address Spoofer")
        self.root.geometry("800x600")
        self.root.minsize(550, 480)  # Ensure Log and System Stats always visible
        self.root.resizable(True, True)

        self.os_type = platform.system()
        self.original_macs = {}
        self.current_interface = None
        self.current_adapter_guid = None
        self.is_spoofed = False

        # Animation state for status indicator
        self.pulse_active = False
        self.pulse_brightness = 1.0
        self.pulse_direction = -1  # -1 for dimming, 1 for brightening

        # Theme system
        self.current_theme_index = 0
        self.themes = self.setup_themes()
        self.apply_theme(self.themes[self.current_theme_index])

        # Configure root window
        self.root.configure(bg=self.bg_color)

        # Vendor MAC prefixes (OUI - Organizationally Unique Identifier)
        # Comprehensive list from IEEE OUI database with country information
        self.vendor_macs = {
            "Apple (USA)": ["00:03:93", "00:05:02", "00:0A:27", "00:0A:95", "00:0D:93", "00:10:FA", "00:11:24", "00:14:51", "00:16:CB", "00:17:F2"],
            "Samsung (Korea)": ["00:00:F0", "00:02:78", "00:07:AB", "00:09:18", "00:0D:AE", "00:12:47", "00:13:77", "00:15:B9", "00:16:32", "00:1A:8A"],
            "Huawei (China)": ["00:18:82", "00:1E:10", "00:25:9E", "00:46:4B", "00:66:4B", "00:E0:FC", "04:C0:6F", "08:19:A6", "10:47:80", "20:08:ED"],
            "Cisco (USA)": ["00:00:0C", "00:01:42", "00:01:43", "00:01:63", "00:01:64", "00:01:96", "00:02:3D", "00:02:FC", "00:03:6B", "00:03:FD"],
            "Dell (USA)": ["00:06:5B", "00:08:74", "00:0B:DB", "00:0D:56", "00:11:43", "00:12:3F", "00:13:72", "00:14:22", "00:15:C5", "00:16:F0"],
            "HP (USA)": ["00:01:E6", "00:01:E7", "00:04:EA", "00:08:83", "00:0E:7F", "00:10:E3", "00:11:0A", "00:12:79", "00:13:21", "00:14:38"],
            "Intel (USA)": ["00:02:B3", "00:03:47", "00:04:23", "00:07:E9", "00:0E:0C", "00:13:02", "00:13:20", "00:15:00", "00:16:6F", "00:19:D1"],
            "Microsoft (USA)": ["00:03:FF", "00:0D:3A", "00:12:5A", "00:15:5D", "00:17:FA", "00:50:F2", "28:18:78", "7C:1E:52", "DC:B4:C4"],
            "Google (USA)": ["00:1A:11", "3C:5A:B4", "54:60:09", "6C:AD:F8", "94:EB:2C", "F4:F5:E8", "F8:8F:CA"],
            "Amazon (USA)": ["0C:47:C9", "44:65:0D", "68:37:E9", "74:C2:46", "84:D6:D0", "AC:63:BE", "F0:D2:F1"],
            "Lenovo (China)": ["00:21:86", "00:23:24", "00:26:6C", "54:42:49", "68:F7:28", "70:F3:95", "A4:4E:31", "BC:30:5B"],
            "ASUS (Taiwan)": ["00:0C:6E", "00:0E:A6", "00:11:2F", "00:13:D4", "00:15:F2", "00:17:31", "00:1A:92", "00:1D:60", "08:60:6E", "30:85:A9"],
            "TP-Link (Hong Kong)": ["00:0A:EB", "00:27:19", "14:CF:92", "50:C7:BF", "A0:F3:C1", "C4:6E:1F", "EC:08:6B"],
            "D-Link (Taiwan)": ["00:05:5D", "00:0D:88", "00:11:95", "00:13:46", "00:15:E9", "00:17:9A", "00:19:5B", "00:1B:11", "1C:7E:E5", "34:08:04"],
            "Netgear (USA)": ["00:09:5B", "00:0F:B5", "00:14:6C", "00:1B:2F", "00:1E:2A", "00:1F:33", "00:22:3F", "00:24:B2", "20:E5:2A", "74:44:01"],
            "Nokia (Finland)": ["00:02:EE", "00:0B:E1", "00:0E:ED", "00:12:62", "00:15:A0", "00:18:13", "00:19:2D", "00:1A:16", "00:1B:AF"],
            "Sony (Japan)": ["00:00:95", "00:04:1F", "00:0A:D9", "00:0E:07", "00:13:15", "00:16:20", "00:19:63", "00:1C:A4", "00:1E:45", "00:23:45"],
            "LG (Korea)": ["00:1C:62", "00:1E:75", "00:22:A9", "10:68:3F", "20:21:A5", "58:A2:B5", "70:05:14", "98:D6:F7", "A8:16:B2"],
            "Motorola (USA)": ["00:0A:28", "00:0E:C7", "00:23:68", "00:24:37", "40:83:DE", "5C:0E:8B", "60:BE:B5", "C4:7D:CC", "E0:75:7D"],
            "HTC (Taiwan)": ["00:23:76", "38:E7:D8", "50:2E:5C", "7C:61:93", "84:7A:88", "A0:F4:50", "BC:CF:CC", "E8:99:C4"],
            "Xiaomi (China)": ["00:9E:C8", "0C:1D:AF", "34:CE:00", "64:09:80", "64:B4:73", "78:11:DC", "8C:BE:BE", "98:FA:E3", "9C:99:A0"],
            "OPPO (China)": ["1C:77:F6", "38:29:5A", "88:D5:0C", "A0:93:47", "B8:37:65", "C0:9F:05", "D4:50:3F", "E4:47:90"],
            "Vivo (China)": ["2C:AB:A4", "3C:F5:91", "50:76:AF", "7C:1D:D9", "A4:50:46", "BC:76:5E", "D8:55:A3", "EC:1D:8B"],
            "ZTE (China)": ["00:19:C6", "00:25:12", "34:4B:50", "48:28:2F", "B0:75:D5", "E0:C3:F3", "F8:DF:A8"],
            "Toshiba (Japan)": ["00:00:39", "00:08:0D", "00:15:B7", "24:2F:FA", "98:6D:C8", "E8:9D:87", "FC:00:12"],
            "Nintendo (Japan)": ["00:09:BF", "00:16:56", "00:17:AB", "00:19:1D", "00:1A:E9", "00:1B:7A", "00:1C:BE", "00:1E:35", "18:2A:7B", "34:AF:2C"],
            "Broadcom (USA)": ["00:05:B5", "00:0A:F7", "00:10:18", "18:C0:86", "D4:01:29"],
            "Qualcomm (USA)": ["00:A0:C6", "64:9C:81", "88:12:4E", "8C:FD:F0"],
            "Nvidia (USA)": ["00:04:4B"],
            "Espressif (China)": ["18:FE:34", "24:0A:C4", "30:AE:A4", "60:01:94", "A0:20:A6", "AC:D0:74"],
            "Texas Instruments (USA)": ["00:17:E9", "00:17:EB", "00:18:31", "00:1A:B6", "00:22:A5", "08:00:28", "10:2E:AF"],
            "Roku (USA)": ["00:0D:4B", "08:05:81", "AC:3A:7A", "B0:A7:37", "B8:3E:59", "CC:6D:A0", "D0:4D:2C", "DC:3A:5E"],
            "Ubiquiti (USA)": ["00:15:6D", "00:27:22", "24:A4:3C", "68:72:51", "80:2A:A8", "DC:9F:DB", "F0:9F:C2"],
            "Aruba Networks (USA)": ["00:0B:86", "00:1A:1E", "00:24:6C", "20:4C:03", "24:DE:C6", "6C:F3:7F", "94:B4:0F", "D8:C7:C8"],
            "Juniper Networks (USA)": ["00:05:85", "00:12:1E", "00:17:CB", "00:19:E2", "00:1F:12", "00:21:59", "00:23:9C", "00:26:88", "28:8A:1C", "54:E0:32"],
            "Ruckus Wireless (USA)": ["00:13:92", "00:24:82", "24:C9:A1", "50:A7:33", "54:3D:37", "84:D4:7E", "C4:10:8A", "E4:5D:51"],
            "IBM (USA)": ["00:00:81", "00:04:AC", "00:06:29", "6C:AE:8B", "74:99:75"],
            "3Com (USA)": ["00:01:02", "00:01:03", "00:05:1A", "00:0A:04", "00:10:4B", "00:20:AF", "00:50:04", "00:60:08"],
            "Linksys (USA)": ["00:04:5A", "00:06:25", "00:0C:41", "00:0F:66", "00:12:17", "00:13:10", "00:14:BF", "00:16:B6", "48:F8:B3", "98:FC:11"],
            "Belkin (USA)": ["00:11:50", "00:17:3F", "00:1C:DF", "00:30:BD", "08:86:3B", "94:10:3E", "EC:1A:59"],
            "Panasonic (Japan)": ["00:0F:12", "00:1B:D3", "04:20:9A", "30:4C:7E", "8C:C1:21", "D8:AF:F1", "E0:EE:1B"],
            "Fujitsu (Japan)": ["00:00:0E", "00:0B:5D", "00:10:55", "00:17:42", "08:E5:DA", "50:26:90", "90:1B:0E", "B0:AC:FA"],
            "Realme (China)": ["7E:3E:3A", "A0:15:65", "C4:06:83", "D4:6E:5C", "E8:9F:80", "F0:E3:11"],
            "Honor (China)": ["10:2A:B3", "20:76:00", "28:D1:27", "70:66:1B", "9C:28:EF", "C0:84:7D", "E4:A7:C5"],
        }

        self.setup_styles()
        self.setup_ui()
        self.check_admin()
        self.refresh_interfaces()

        # Bind theme switch keys
        self.root.bind('<t>', lambda event: self.cycle_theme())
        self.root.bind('<T>', lambda event: self.cycle_theme())
        self.root.bind('<s>', lambda event: self.randomize_skittles())
        self.root.bind('<S>', lambda event: self.randomize_skittles())

    def setup_themes(self):
        """Setup color themes"""
        themes = [
            # Dark Mode (Default)
            {
                "name": "Dark Mode",
                "bg_color": "#1e1e1e",
                "fg_color": "#e0e0e0",
                "frame_bg": "#2d2d2d",
                "entry_bg": "#3c3c3c",
                "entry_fg": "#ffffff",
                "button_bg": "#404040",
                "select_bg": "#0d5aa3"
            },
            # Flash Bang
            {
                "name": "Flash Bang",
                "bg_color": "#f5f5f5",
                "fg_color": "#2b2b2b",
                "frame_bg": "#e0e0e0",
                "entry_bg": "#ffffff",
                "entry_fg": "#2b2b2b",
                "button_bg": "#d0d0d0",
                "select_bg": "#4a90d9"
            },
            # Cyberpunk
            {
                "name": "Cyberpunk",
                "bg_color": "#0a0e27",
                "fg_color": "#00ff9f",
                "frame_bg": "#1a1f3a",
                "entry_bg": "#0d1126",
                "entry_fg": "#00ffff",
                "button_bg": "#2d1b69",
                "select_bg": "#ff006e"
            },
            # Matrix
            {
                "name": "Matrix",
                "bg_color": "#000000",
                "fg_color": "#00ff00",
                "frame_bg": "#0d0d0d",
                "entry_bg": "#001a00",
                "entry_fg": "#00ff00",
                "button_bg": "#003300",
                "select_bg": "#00aa00"
            },
            # Ocean
            {
                "name": "Ocean",
                "bg_color": "#1a2332",
                "fg_color": "#a8dadc",
                "frame_bg": "#243447",
                "entry_bg": "#1d2d3e",
                "entry_fg": "#f1faee",
                "button_bg": "#457b9d",
                "select_bg": "#1d3557"
            },
            # Sunset
            {
                "name": "Sunset",
                "bg_color": "#2d1b2e",
                "fg_color": "#ffd6ba",
                "frame_bg": "#3d2b3e",
                "entry_bg": "#4a2f4f",
                "entry_fg": "#ffe5d4",
                "button_bg": "#6b4c6f",
                "select_bg": "#ff6b9d"
            },
            # Hacker Green
            {
                "name": "Hacker Green",
                "bg_color": "#0c1618",
                "fg_color": "#33ff33",
                "frame_bg": "#1a2b2e",
                "entry_bg": "#0f1d1f",
                "entry_fg": "#66ff66",
                "button_bg": "#1f3a3d",
                "select_bg": "#00cc00"
            },
            # Purple Haze
            {
                "name": "Purple Haze",
                "bg_color": "#1a0d2e",
                "fg_color": "#e1bee7",
                "frame_bg": "#2a1b3d",
                "entry_bg": "#1f1333",
                "entry_fg": "#f3e5f5",
                "button_bg": "#512da8",
                "select_bg": "#aa00ff"
            },
            # Nord
            {
                "name": "Nord",
                "bg_color": "#2e3440",
                "fg_color": "#eceff4",
                "frame_bg": "#3b4252",
                "entry_bg": "#434c5e",
                "entry_fg": "#eceff4",
                "button_bg": "#4c566a",
                "select_bg": "#5e81ac"
            },
            # Dracula
            {
                "name": "Dracula",
                "bg_color": "#282a36",
                "fg_color": "#f8f8f2",
                "frame_bg": "#44475a",
                "entry_bg": "#21222c",
                "entry_fg": "#f8f8f2",
                "button_bg": "#6272a4",
                "select_bg": "#bd93f9"
            },
        ]

        # Add Skittles theme (random bright colors)
        themes.append(self.generate_skittles_theme())

        return themes

    def generate_skittles_theme(self):
        """Generate a random bright colorful Skittles theme with 16 random colors"""
        import random

        # Generate 16 bright, vibrant colors
        skittles_colors = []
        for _ in range(16):
            # Create vibrant colors by ensuring at least one channel is very high
            # and others are varied
            color_type = random.randint(0, 2)
            if color_type == 0:  # Red-based
                r = random.randint(200, 255)
                g = random.randint(0, 200)
                b = random.randint(0, 200)
            elif color_type == 1:  # Green-based
                r = random.randint(0, 200)
                g = random.randint(200, 255)
                b = random.randint(0, 200)
            else:  # Blue-based
                r = random.randint(0, 200)
                g = random.randint(0, 200)
                b = random.randint(200, 255)

            skittles_colors.append(f"#{r:02x}{g:02x}{b:02x}")

        # Shuffle for randomness
        random.shuffle(skittles_colors)

        # Use different colors for different UI elements
        return {
            "name": "Skittles",
            "bg_color": skittles_colors[0],
            "fg_color": skittles_colors[1],
            "frame_bg": skittles_colors[2],
            "entry_bg": skittles_colors[3],
            "entry_fg": skittles_colors[4],
            "button_bg": skittles_colors[5],
            "select_bg": skittles_colors[6]
        }

    def apply_theme(self, theme):
        """Apply a color theme"""
        self.bg_color = theme["bg_color"]
        self.fg_color = theme["fg_color"]
        self.frame_bg = theme["frame_bg"]
        self.entry_bg = theme["entry_bg"]
        self.entry_fg = theme["entry_fg"]
        self.button_bg = theme["button_bg"]
        self.select_bg = theme["select_bg"]
        self.current_theme_name = theme["name"]

    def cycle_theme(self):
        """Cycle to next theme"""
        self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)

        # Regenerate Skittles theme if it's selected
        if self.themes[self.current_theme_index]["name"] == "Skittles":
            self.themes[self.current_theme_index] = self.generate_skittles_theme()

        self.apply_theme(self.themes[self.current_theme_index])
        self.setup_styles()
        self.refresh_ui_colors()
        self.log(f"Theme changed to: {self.current_theme_name}")

    def randomize_skittles(self):
        """Randomize Skittles theme without cycling through others"""
        # Find Skittles theme index
        skittles_index = None
        for i, theme in enumerate(self.themes):
            if theme["name"] == "Skittles":
                skittles_index = i
                break

        if skittles_index is not None:
            # Generate new Skittles theme
            self.themes[skittles_index] = self.generate_skittles_theme()
            self.current_theme_index = skittles_index
            self.apply_theme(self.themes[skittles_index])
            self.setup_styles()
            self.refresh_ui_colors()
            self.log("🌈 Skittles randomized!")

    def refresh_ui_colors(self):
        """Refresh all UI elements with new theme colors"""
        # Update root window
        self.root.configure(bg=self.bg_color)

        # Update theme label
        self.theme_label.config(text=f'Theme: {self.current_theme_name} (press "t" to change | "s" for skittles)')

        # Update log text widget
        self.log_text.configure(bg=self.entry_bg, fg=self.fg_color,
                               insertbackground=self.fg_color,
                               selectbackground=self.select_bg,
                               selectforeground=self.fg_color)

    def setup_styles(self):
        """Setup dark mode ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('.', background=self.bg_color, foreground=self.fg_color,
                       fieldbackground=self.entry_bg, bordercolor=self.frame_bg)

        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TLabelframe', background=self.bg_color, foreground=self.fg_color,
                       bordercolor=self.frame_bg)
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.fg_color)

        style.configure('TButton', background=self.button_bg, foreground=self.fg_color,
                       bordercolor=self.frame_bg, focuscolor=self.select_bg)
        style.map('TButton', background=[('active', self.select_bg)])

        style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg,
                       insertcolor=self.fg_color, bordercolor=self.frame_bg)

        style.configure('TCombobox', fieldbackground=self.entry_bg, foreground=self.entry_fg,
                       selectbackground=self.select_bg, selectforeground=self.fg_color,
                       arrowcolor=self.fg_color, bordercolor=self.frame_bg)
        style.map('TCombobox', fieldbackground=[('readonly', self.entry_bg)],
                 selectbackground=[('readonly', self.entry_bg)])

        # Title label style
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'),
                       background=self.bg_color, foreground=self.fg_color)

        # Status styles
        style.configure('StatusGreen.TLabel', font=('Arial', 12, 'bold'),
                       background=self.bg_color, foreground='#00ff00')
        style.configure('StatusRed.TLabel', font=('Arial', 12, 'bold'),
                       background=self.bg_color, foreground='#ff0000')

    def check_admin(self):
        """Check if running with admin privileges"""
        try:
            if self.os_type == "Windows":
                is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                if not is_admin:
                    messagebox.showwarning("Admin Required",
                        "This application requires administrator privileges.\n"
                        "Please run as administrator for full functionality.")
        except:
            pass

    def setup_ui(self):
        """Setup the GUI interface"""
        # Configure root window to expand properly
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main_frame to expand
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)  # Log area should expand

        # Title
        self.title_label = ttk.Label(main_frame, text="MAC Address Spoofer", style='Title.TLabel')
        self.title_label.grid(row=0, column=0, columnspan=2, pady=8)

        # Status indicator
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=1, column=0, columnspan=2, pady=5)

        self.status_label = ttk.Label(self.status_frame, text="● ORIGINAL MAC",
                                     style='StatusGreen.TLabel')
        self.status_label.pack()

        # Interface selection
        interface_frame = ttk.LabelFrame(main_frame, text="Network Interface", padding="8")
        interface_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)

        # Configure interface_frame to expand
        interface_frame.columnconfigure(1, weight=1)
        interface_frame.columnconfigure(2, weight=0)

        ttk.Label(interface_frame, text="Select Interface:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.interface_combo = ttk.Combobox(interface_frame, state="readonly", width=20)
        self.interface_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        self.interface_combo.bind("<<ComboboxSelected>>", self.on_interface_selected)

        ttk.Button(interface_frame, text="Refresh", command=self.refresh_interfaces).grid(row=0, column=2, padx=5)

        # Current MAC display
        style = ttk.Style()
        style.configure('Mono.TLabel', font=('Courier', 10), background=self.bg_color,
                       foreground=self.fg_color)
        self.current_mac_label = ttk.Label(interface_frame, text="Current MAC: Not selected",
                                          style='Mono.TLabel')
        self.current_mac_label.grid(row=1, column=0, columnspan=3, pady=5)

        # Vendor selection
        vendor_frame = ttk.LabelFrame(main_frame, text="Vendor MAC Presets", padding="8")
        vendor_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=6)

        # Configure vendor_frame to expand
        vendor_frame.columnconfigure(1, weight=1)
        vendor_frame.columnconfigure(2, weight=0)
        vendor_frame.columnconfigure(3, weight=0)

        ttk.Label(vendor_frame, text="Select Vendor:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.vendor_combo = ttk.Combobox(vendor_frame, state="readonly",
                                        values=list(self.vendor_macs.keys()), width=20)
        self.vendor_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        ttk.Button(vendor_frame, text="Random Vendor",
                  command=self.use_vendor_mac).grid(row=0, column=2, padx=(5, 2))
        ttk.Button(vendor_frame, text="Same Vendor",
                  command=self.regenerate_vendor_mac).grid(row=0, column=3, padx=(2, 5))

        # Custom MAC entry
        custom_frame = ttk.LabelFrame(main_frame, text="Custom MAC Address", padding="8")
        custom_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=6)

        # Configure custom_frame to expand
        custom_frame.columnconfigure(1, weight=1)
        custom_frame.columnconfigure(2, weight=0)

        ttk.Label(custom_frame, text="Enter MAC:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.custom_mac_entry = ttk.Entry(custom_frame, width=20)
        self.custom_mac_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E), columnspan=2)
        # No default value - field starts empty, gets populated by Random/Same Vendor buttons

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=2, pady=10)

        # Compact SPOOF button
        button_style = ttk.Style()
        button_style.configure('Large.TButton', font=('Arial', 13, 'bold'), padding=(10, 8))

        self.spoof_button = ttk.Button(control_frame, text="⚫ SPOOF ON",
                                      command=self.toggle_spoof, width=22, style='Large.TButton')
        self.spoof_button.pack(pady=5)

        # Bottom section container
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        bottom_frame.columnconfigure(0, weight=1)  # Log takes more space
        bottom_frame.columnconfigure(1, weight=0, minsize=190)  # Stats compact width
        bottom_frame.rowconfigure(0, weight=1)

        # Log output (left side)
        log_frame = ttk.LabelFrame(bottom_frame, text="Log", padding="6")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=5,
                                                  bg=self.entry_bg, fg=self.fg_color,
                                                  insertbackground=self.fg_color,
                                                  selectbackground=self.select_bg,
                                                  selectforeground=self.fg_color,
                                                  wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # System Stats (right side)
        stats_frame = ttk.LabelFrame(bottom_frame, text="System Stats", padding="6")
        stats_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.W, tk.E), padx=(5, 0))

        # Uniform monospace font for all stats (smaller and compact)
        stats_label_font = ('Consolas', 9)
        stats_value_font = ('Consolas', 9)

        # Original MAC
        ttk.Label(stats_frame, text="Original MAC:", font=stats_label_font).pack(anchor=tk.W, pady=(0,1))
        self.stats_original_mac = ttk.Label(stats_frame, text="Not selected",
                                           font=stats_value_font, foreground='#00ff00')
        self.stats_original_mac.pack(anchor=tk.W, padx=(3,0), pady=(0,6))

        # Current MAC
        ttk.Label(stats_frame, text="Current MAC:", font=stats_label_font).pack(anchor=tk.W, pady=(0,1))
        self.stats_current_mac = ttk.Label(stats_frame, text="Not selected",
                                          font=stats_value_font, foreground='#00aaff')
        self.stats_current_mac.pack(anchor=tk.W, padx=(3,0), pady=(0,6))

        # IP Address
        ttk.Label(stats_frame, text="IP Address:", font=stats_label_font).pack(anchor=tk.W, pady=(0,1))
        self.stats_ip = ttk.Label(stats_frame, text="N/A",
                                 font=stats_value_font, foreground='#ffaa00')
        self.stats_ip.pack(anchor=tk.W, padx=(3,0))

        # Theme indicator - discrete at bottom
        self.theme_label = ttk.Label(main_frame, text=f'Theme: {self.current_theme_name} (press "t" to change | "s" for skittles)',
                                     font=('Arial', 8, 'italic'))
        self.theme_label.grid(row=7, column=0, columnspan=2, pady=(5, 5))

        self.log("MAC Spoofer initialized")
        self.log(f"Operating System: {self.os_type}")
        self.log(f"Current Theme: {self.current_theme_name}")

        # Start live stats update
        self.update_stats_live()

    def update_stats_live(self):
        """Update system stats panel in real-time"""
        if self.current_interface:
            # Get current MAC and IP
            current_mac = self.get_current_mac(self.current_interface)
            ip_address = self.get_ip_address(self.current_interface)

            # Always display Original MAC (never changes once stored)
            original_mac = self.original_macs.get(self.current_interface, "Not stored")
            self.stats_original_mac.config(text=original_mac)

            # Update Current MAC (live, changes when spoofed)
            if current_mac:
                self.stats_current_mac.config(text=current_mac)
                self.current_mac_label.config(text=f"Current MAC: {current_mac}")

            # Update IP Address (live, changes with VPN/network)
            self.stats_ip.config(text=ip_address)

        # Schedule next update in 1000ms (1 second)
        self.root.after(1000, self.update_stats_live)

    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def get_interfaces(self):
        """Get list of network interfaces (only connected/active ones)"""
        interfaces = []
        try:
            if self.os_type == "Windows":
                result = subprocess.check_output("netsh interface show interface",
                                                shell=True, stderr=subprocess.DEVNULL).decode()
                lines = result.split('\n')[3:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        # Only include connected interfaces (filter out disconnected Wintun, etc.)
                        if len(parts) >= 4 and parts[1] == "Connected":
                            interface_name = ' '.join(parts[3:])
                            interfaces.append(interface_name)
            else:
                result = subprocess.check_output("ip link show", shell=True).decode()
                for line in result.split('\n'):
                    match = re.search(r'^\d+:\s+(\S+):', line)
                    if match:
                        interfaces.append(match.group(1))
        except Exception as e:
            self.log(f"Error getting interfaces: {e}")
        return interfaces

    def get_current_mac(self, interface):
        """Get the current MAC address of an interface"""
        try:
            if self.os_type == "Windows":
                # Use PowerShell Get-NetAdapter to get actual active MAC (including spoofed)
                cmd = f'powershell "Get-NetAdapter -Name \'{interface}\' | Select-Object -ExpandProperty MacAddress"'
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
                # PowerShell returns MAC in format: XX-XX-XX-XX-XX-XX
                if result and re.match(r"^([0-9A-Fa-f]{2}[-:]){5}([0-9A-Fa-f]{2})$", result):
                    # Convert to colon format for consistency
                    return result.replace('-', ':')
            else:
                result = subprocess.check_output(f"ip link show {interface}", shell=True).decode()
                mac_match = re.search(r"link/ether\s+([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})", result)
                if mac_match:
                    return mac_match.group(0).split()[-1]
        except Exception as e:
            self.log(f"Error getting MAC: {e}")
        return None

    def get_ip_address(self, interface):
        """Get the current IP address of an interface"""
        try:
            if self.os_type == "Windows":
                cmd = f'netsh interface ip show addresses "{interface}"'
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                ip_match = re.search(r"IP Address:\s+(\d+\.\d+\.\d+\.\d+)", result)
                if ip_match:
                    return ip_match.group(1)
            else:
                result = subprocess.check_output(f"ip addr show {interface}", shell=True).decode()
                ip_match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", result)
                if ip_match:
                    return ip_match.group(1)
        except Exception as e:
            pass  # Silently fail for IP
        return "N/A"

    def refresh_interfaces(self):
        """Refresh the list of network interfaces"""
        interfaces = self.get_interfaces()
        self.interface_combo['values'] = interfaces
        if interfaces:
            self.interface_combo.current(0)
            self.on_interface_selected(None)
        self.log("Interfaces refreshed")

    def on_interface_selected(self, event):
        """Handle interface selection"""
        self.current_interface = self.interface_combo.get()
        if self.current_interface:
            current_mac = self.get_current_mac(self.current_interface)
            ip_address = self.get_ip_address(self.current_interface)

            if current_mac:
                # Store original MAC if not already stored
                if self.current_interface not in self.original_macs:
                    self.original_macs[self.current_interface] = current_mac
                self.current_mac_label.config(text=f"Current MAC: {current_mac}")
                self.log(f"Selected interface: {self.current_interface} (MAC: {current_mac})")

                # Update stats panel
                original_mac = self.original_macs.get(self.current_interface, "Not stored")
                self.stats_original_mac.config(text=original_mac)
                self.stats_current_mac.config(text=current_mac)
                self.stats_ip.config(text=ip_address)

    def generate_random_mac(self, prefix=None):
        """Generate a random MAC address"""
        if prefix:
            # Use vendor prefix, but make it locally administered for Intel compatibility
            mac_bytes = prefix.split(':')
            # Convert first octet to locally administered (set bit 1)
            first_octet = int(mac_bytes[0], 16) | 0x02
            mac_bytes[0] = f"{first_octet:02X}"
            # Add random bytes for last 3 octets
            mac_bytes += [f"{random.randint(0, 255):02X}" for _ in range(3)]
        else:
            # Generate completely random MAC (locally administered)
            first_octet = random.randint(0, 255) & 0xFE | 0x02
            mac_bytes = [f"{first_octet:02X}"] + [f"{random.randint(0, 255):02X}" for _ in range(5)]
        return ':'.join(mac_bytes)

    def get_adapter_guid(self, interface_name):
        """Get the adapter GUID from the interface name"""
        try:
            # Use PowerShell to get adapter GUID
            cmd = f'powershell "Get-NetAdapter | Where-Object {{$_.Name -eq \'{interface_name}\' -or $_.InterfaceDescription -like \'*{interface_name}*\'}} | Select-Object -ExpandProperty InterfaceGuid"'
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if result:
                return result
        except:
            pass
        return None

    def find_adapter_registry_key(self, interface_name):
        """Find the adapter registry key path"""
        try:
            # Network adapters registry path
            adapters_path = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"

            # Open the network adapters key
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, adapters_path, 0, winreg.KEY_READ) as adapters_key:
                # Enumerate all subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(adapters_key, i)
                        i += 1

                        # Skip non-numeric keys
                        if not subkey_name.isdigit():
                            continue

                        # Open each adapter subkey
                        subkey_path = f"{adapters_path}\\{subkey_name}"
                        try:
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path, 0, winreg.KEY_READ) as adapter_key:
                                try:
                                    # Get DriverDesc (adapter description)
                                    desc, _ = winreg.QueryValueEx(adapter_key, "DriverDesc")

                                    # Check if this matches our interface
                                    if interface_name.lower() in desc.lower() or desc.lower() in interface_name.lower():
                                        return subkey_path

                                    # Also check NetCfgInstanceId
                                    try:
                                        instance_id, _ = winreg.QueryValueEx(adapter_key, "NetCfgInstanceId")
                                        guid = self.get_adapter_guid(interface_name)
                                        if guid and instance_id.lower() == guid.lower():
                                            return subkey_path
                                    except:
                                        pass
                                except:
                                    pass
                        except:
                            pass
                    except OSError:
                        break
        except Exception as e:
            self.log(f"Registry search error: {e}")
        return None

    def change_mac_windows(self, interface, new_mac):
        """Change MAC address on Windows using registry method"""
        try:
            # Clean MAC address (remove colons/dashes)
            new_mac_clean = new_mac.replace(':', '').replace('-', '').upper()

            self.log(f"Attempting to change MAC to {new_mac}")
            self.log("Finding adapter in registry...")

            # Find the adapter's registry key
            registry_path = self.find_adapter_registry_key(interface)

            if not registry_path:
                self.log("ERROR: Could not find adapter in registry!")
                self.log("Try selecting a different network adapter.")
                return False

            self.log(f"Found adapter at: {registry_path}")

            # STEP 1: First restore original MAC (delete registry override)
            # This ensures Intel adapters fully reset before applying new spoof
            self.log("Clearing previous MAC override...")
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0,
                                   winreg.KEY_SET_VALUE) as key:
                    try:
                        winreg.DeleteValue(key, "NetworkAddress")
                        self.log("Previous override cleared")
                    except FileNotFoundError:
                        self.log("No previous override found")
            except PermissionError:
                self.log("ERROR: Permission denied! Run as Administrator.")
                messagebox.showerror("Permission Denied",
                    "Administrator privileges required to modify registry.\n"
                    "Please run this application as Administrator.")
                return False

            # STEP 2: Restart adapter to apply original MAC
            self.log("Resetting adapter to hardware MAC...")
            try:
                disable_cmd = f'netsh interface set interface "{interface}" disable'
                result = subprocess.run(disable_cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Warning: Could not disable adapter: {result.stderr}")
                else:
                    time.sleep(3)
                    self.log("Adapter disabled")

                enable_cmd = f'netsh interface set interface "{interface}" enable'
                result = subprocess.run(enable_cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Warning: Could not enable adapter: {result.stderr}")
                else:
                    time.sleep(3)
                    self.log("Adapter reset to hardware MAC")
            except Exception as e:
                self.log(f"Error resetting adapter: {e}")

            # STEP 3: Now apply the new spoofed MAC
            self.log(f"Applying new MAC: {new_mac}")
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0,
                                   winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
                    winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, new_mac_clean)
                    self.log(f"Registry updated with new MAC: {new_mac_clean}")
            except PermissionError:
                self.log("ERROR: Permission denied! Run as Administrator.")
                return False

            # STEP 4: Restart adapter again to apply new spoofed MAC
            self.log("Restarting adapter with new MAC...")
            try:
                disable_cmd = f'netsh interface set interface "{interface}" disable'
                result = subprocess.run(disable_cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Warning: Could not disable adapter: {result.stderr}")
                else:
                    time.sleep(3)
                    self.log("Adapter disabled")

                enable_cmd = f'netsh interface set interface "{interface}" enable'
                result = subprocess.run(enable_cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Warning: Could not enable adapter: {result.stderr}")
                else:
                    time.sleep(3)
                    self.log("Adapter enabled")
                    self.log("✓ MAC address changed successfully!")
                    return True
            except Exception as e:
                self.log(f"Error restarting adapter: {e}")
                self.log("Please manually disable/enable the adapter in Network Settings.")
                return True  # Registry was set, just adapter restart failed

            return True
        except Exception as e:
            self.log(f"Error: {e}")
            return False

    def change_mac_linux(self, interface, new_mac):
        """Change MAC address on Linux/macOS"""
        try:
            subprocess.run(["sudo", "ip", "link", "set", interface, "down"], check=True)
            subprocess.run(["sudo", "ip", "link", "set", interface, "address", new_mac], check=True)
            subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
            self.log(f"MAC changed to {new_mac}")
            return True
        except Exception as e:
            self.log(f"Error: {e}")
            return False

    def use_vendor_mac(self):
        """Select a random vendor and generate MAC preview"""
        # Automatically select a random vendor
        vendor = random.choice(list(self.vendor_macs.keys()))
        self.vendor_combo.set(vendor)  # Update dropdown to show selected vendor

        # Generate MAC from vendor prefix
        prefix = random.choice(self.vendor_macs[vendor])
        new_mac = self.generate_random_mac(prefix)

        # Display in Custom MAC field for preview
        self.custom_mac_entry.delete(0, tk.END)
        self.custom_mac_entry.insert(0, new_mac)

        self.log(f"Generated {vendor} MAC: {new_mac}")

    def regenerate_vendor_mac(self):
        """Generate a new MAC from the currently selected vendor"""
        vendor = self.vendor_combo.get()

        if not vendor:
            messagebox.showinfo("No Vendor Selected",
                              "Please select a vendor from the dropdown first,\nor click 'Random Vendor' to pick one.")
            return

        # Generate new MAC from selected vendor prefix
        prefix = random.choice(self.vendor_macs[vendor])
        new_mac = self.generate_random_mac(prefix)

        # Display in Custom MAC field for preview
        self.custom_mac_entry.delete(0, tk.END)
        self.custom_mac_entry.insert(0, new_mac)

        self.log(f"Regenerated {vendor} MAC: {new_mac}")

    def use_random_mac(self):
        """Generate and use completely random MAC"""
        if not self.current_interface:
            messagebox.showwarning("No Interface", "Please select a network interface first")
            return

        new_mac = self.generate_random_mac()
        self.log(f"Generated random MAC: {new_mac}")

        if self.change_mac(new_mac):
            self.is_spoofed = True
            self.update_status()

    def change_mac(self, new_mac):
        """Change MAC address"""
        if self.os_type == "Windows":
            return self.change_mac_windows(self.current_interface, new_mac)
        else:
            return self.change_mac_linux(self.current_interface, new_mac)

    def restore_original_windows(self, interface):
        """Restore original MAC on Windows by removing registry override"""
        try:
            self.log("Restoring original MAC address...")

            # Find the adapter's registry key
            registry_path = self.find_adapter_registry_key(interface)

            if not registry_path:
                self.log("ERROR: Could not find adapter in registry!")
                return False

            self.log(f"Found adapter at: {registry_path}")

            # Delete the NetworkAddress registry value
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0,
                                   winreg.KEY_SET_VALUE) as key:
                    try:
                        winreg.DeleteValue(key, "NetworkAddress")
                        self.log("Registry override removed")
                    except FileNotFoundError:
                        self.log("No registry override found (already using original MAC)")
            except PermissionError:
                self.log("ERROR: Permission denied! Run as Administrator.")
                return False

            # Restart adapter
            self.log("Restarting network adapter...")
            try:
                disable_cmd = f'netsh interface set interface "{interface}" disable'
                subprocess.run(disable_cmd, shell=True, capture_output=True)
                time.sleep(1)
                self.log("Adapter disabled")

                enable_cmd = f'netsh interface set interface "{interface}" enable'
                subprocess.run(enable_cmd, shell=True, capture_output=True)
                time.sleep(2)
                self.log("Adapter enabled")
                self.log("✓ Original MAC address restored!")
                return True
            except Exception as e:
                self.log(f"Error restarting adapter: {e}")
                return True

        except Exception as e:
            self.log(f"Error: {e}")
            return False

    def restore_original(self):
        """Restore original MAC address"""
        if not self.current_interface:
            messagebox.showwarning("No Interface", "Please select a network interface first")
            return

        if self.current_interface not in self.original_macs:
            messagebox.showinfo("Info", "No original MAC stored for this interface")
            return

        original_mac = self.original_macs[self.current_interface]
        self.log(f"Restoring original MAC: {original_mac}")

        # On Windows, remove the registry override instead of setting a value
        if self.os_type == "Windows":
            success = self.restore_original_windows(self.current_interface)
        else:
            success = self.change_mac(original_mac)

        if success:
            self.is_spoofed = False
            self.update_status()
            # Refresh MAC display
            time.sleep(1)
            self.on_interface_selected(None)

    def toggle_spoof(self):
        """Toggle spoofing on/off"""
        if not self.current_interface:
            messagebox.showwarning("No Interface", "Please select a network interface first")
            return

        if not self.is_spoofed:
            # Turn spoofing ON
            # Priority: 1) Custom MAC field, 2) Selected vendor, 3) Random MAC
            custom_mac = self.custom_mac_entry.get().strip()

            # Check if custom MAC field has valid MAC
            if custom_mac and re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", custom_mac):
                # Use MAC from entry field
                self.log(f"Using MAC from entry field: {custom_mac}")
                if self.change_mac(custom_mac):
                    self.is_spoofed = True
                    self.update_status()
            else:
                # Fall back to vendor or random
                vendor = self.vendor_combo.get()
                if vendor:
                    # Use selected vendor MAC
                    prefix = random.choice(self.vendor_macs[vendor])
                    new_mac = self.generate_random_mac(prefix)
                    self.log(f"Generated {vendor} MAC: {new_mac}")
                    if self.change_mac(new_mac):
                        self.is_spoofed = True
                        self.update_status()
                else:
                    # No vendor selected, use completely random MAC
                    self.use_random_mac()
        else:
            # Turn spoofing OFF - restore original
            self.restore_original()

    def update_status(self):
        """Update status indicator"""
        if self.is_spoofed:
            self.status_label.config(text="● SPOOFED MAC", style='StatusRed.TLabel')
            self.spoof_button.config(text="🟢 RESTORE ORIGINAL")
            # Start pulsing animation
            if not self.pulse_active:
                self.pulse_active = True
                self.pulse_status_indicator()
        else:
            self.status_label.config(text="● ORIGINAL MAC", style='StatusGreen.TLabel', foreground='#00ff00')
            self.spoof_button.config(text="⚫ SPOOF ON")
            # Stop pulsing animation
            self.pulse_active = False

    def pulse_status_indicator(self):
        """Gentle pulsing animation for SPOOFED MAC indicator"""
        if not self.pulse_active:
            return

        # Adjust brightness (0.4 to 1.0 range for gentle pulse)
        self.pulse_brightness += self.pulse_direction * 0.04

        # Reverse direction at boundaries
        if self.pulse_brightness <= 0.4:
            self.pulse_brightness = 0.4
            self.pulse_direction = 1
        elif self.pulse_brightness >= 1.0:
            self.pulse_brightness = 1.0
            self.pulse_direction = -1

        # Calculate color based on brightness (red channel)
        red_value = int(255 * self.pulse_brightness)
        color = f'#{red_value:02x}0000'

        # Update the label color directly
        self.status_label.config(foreground=color)

        # Continue animation (50ms = smooth 20fps)
        if self.pulse_active:
            self.root.after(50, self.pulse_status_indicator)

def main():
    root = tk.Tk()
    app = MACSpooferGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
