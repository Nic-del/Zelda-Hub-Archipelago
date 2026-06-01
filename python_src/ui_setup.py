import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
import zipfile
import threading
import time

try:
    import pygame
    HAS_PYGAME = True
    from controller.device_detector import DeviceDetector
except ImportError:
    HAS_PYGAME = False
    DeviceDetector = None

try:
    import win32api
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

from launcher_core import CONFIG_PATH, BASE_DIR, get_exe_dir

def make_relative(path):
    """
    Rend un chemin relatif UNIQUEMENT s'il se trouve dans le dossier du projet (Hub).
    Sinon, on conserve le chemin absolu standard.
    """
    if not isinstance(path, str):
        return path
    
    if not path:
        return ""
    
    # Normalisation pour comparaison
    abs_path = os.path.normpath(os.path.abspath(os.path.expandvars(path)))
    exe_dir = os.path.normpath(get_exe_dir())
    # On considère le projet jusqu'au dossier parent de python_src
    project_root = os.path.normpath(os.path.dirname(exe_dir))

    try:
        # Si le fichier est à l'intérieur du dossier du projet
        if abs_path.startswith(project_root):
            # On le rend relatif par rapport à python_src (base du launcher)
            rel = os.path.relpath(abs_path, exe_dir)
            return rel.replace("\\", "/")
    except:
        pass
        
    # Si externe, on retourne le chemin absolu normalisé avec des slashs
    return abs_path.replace("\\", "/")
from obs_controller import obs_controller
from localization import Loc

DEFAULT_CONFIG = {
    "emulators": {
        "bizhawk": "",
        "dolphin": "",
        "archipelago": "",
        "azahar": "",
        "poptracker": "",
        "broadcast": ""
    },
    "roms": {
        "Ocarina of Time": "",
        "Majora's Mask": "",
        "Wind Waker": "",
        "Twilight Princess": "",
        "Skyward Sword": "",
        "A Link to the Past": "",
        "Minish Cap": "",
        "OOT (SOH)": "",
        "A Link Between Worlds": "",
        "The Legend of Zelda": "",
        "Zelda II": "",
        "Oracle of Ages": "",
        "Oracle of Seasons": "",
        "Link's Awakening DX": "",
        "Phantom Hourglass": "",
        "Spirit Tracks": ""
    },
    "poptracker_enabled": {},
    "poptracker_packs": {},
    "poptracker_variants": {},
    "archipelago_settings": {
        "host": "archipelago.gg",
        "port": "",
        "password": ""
    },
    "slot_names": {
        "Ocarina of Time": "",
        "Wind Waker": "",
        "A Link to the Past": "",
        "Minish Cap": "",
        "Majora's Mask": "",
        "Skyward Sword": "",
        "Twilight Princess": "",
        "A Link Between Worlds": "",
        "The Legend of Zelda": "",
        "Zelda II": "",
        "Oracle of Ages": "",
        "Oracle of Seasons": "",
        "Link's Awakening DX": "",
        "Phantom Hourglass": "",
        "Spirit Tracks": "",
        "OOT (SOH)": ""
    },
    "auto_controller_config": True,
    "poptracker_broadcast": False,
    "broadcast_mode": "obs",
    "broadcast_enable_overlay": True,
    "broadcast_enable_obs": False,
    "broadcast_show_locations": True,
    "broadcast_disable_hw_accel": False,
    "maximize_poptracker": True,
    "poptracker_display_index": 0,
    "obs_settings": {
        "enabled": True,
        "host": "localhost",
        "port": 4455,
        "password": "",
        "scenes": {}
    },
    "active_games": {
        "Ocarina of Time": True,
        "Majora's Mask": True,
        "Wind Waker": True,
        "Twilight Princess": True,
        "Skyward Sword": True,
        "A Link to the Past": True,
        "Minish Cap": True,
        "OOT (SOH)": True,
        "A Link Between Worlds": True,
        "The Legend of Zelda": True,
        "Zelda II": True,
        "Oracle of Ages": True,
        "Oracle of Seasons": True,
        "Link's Awakening DX": True,
        "Phantom Hourglass": True,
        "Spirit Tracks": True
    },
    "language": "fr",
    "hub_keyboard_shortcut": "ctrl+shift+s",
    "hub_controller_open_btn": "CAPTURE"
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

class SetupUI(ctk.CTk):
    def __init__(self, start_page="emus"):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # self.title is set after loading config
        self.geometry("1100x850")
        self.configure(fg_color="#0d0d0d")
        
        # Load existing config
        self.config = load_config()
        
        # Initialize localization
        Loc.set_lang(self.config.get("language", "fr"))
        
        self.title(Loc.get("setup_title").upper())
        self.path_vars = {}
        self.pages = {}
        self.current_page = None
        self.last_page_id = None

        # --- Sidebar Navigation ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#141414")
        self.sidebar_frame.pack(side="left", fill="y")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ZELDA HUB", font=ctk.CTkFont(size=22, weight="bold"), text_color="#3498db")
        self.logo_label.pack(pady=(40, 5))
        
        self.sub_logo = ctk.CTkLabel(self.sidebar_frame, text=Loc.get("lbl_config"), font=ctk.CTkFont(size=10), text_color="#555")
        self.sub_logo.pack(pady=(0, 40))
        
        self.nav_buttons = {}
        nav_items = [
            (Loc.get("tab_emulators").upper(), "emus", "🎮"),
            (Loc.get("tab_roms").upper(), "games", "💿"),
            (Loc.get("tab_archipelago").upper(), "conn", "🌐"),
            (Loc.get("tab_slots").upper(), "slots", "🔑"),
            (Loc.get("tab_visibility").upper(), "active_games_page", "✅"),
            (Loc.get("tab_poptracker").upper(), "trackers", "🗺️"),
            (Loc.get("tab_obs").upper(), "obs", "🎥"),
            (Loc.get("tab_general").upper(), "general", "⚙️")
        ]
        
        for text, page_id, icon in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"{icon}  {text}", 
                fg_color="transparent", text_color="#eee", 
                hover_color="#222", anchor="w", height=50,
                font=ctk.CTkFont(size=12, weight="bold"),
                corner_radius=8,
                command=lambda p=page_id: self.show_page(p)
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.nav_buttons[page_id] = btn

        # --- Main View Container ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(side="left", fill="both", expand=True, padx=25, pady=25)
        
        # Header Info
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.page_title_label = ctk.CTkLabel(self.header_frame, text=Loc.get("setup_title").upper(), font=ctk.CTkFont(size=24, weight="bold"), text_color="#eee")
        self.page_title_label.pack(side="left")

        # Scrollable Frame for settings
        self.content_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#0d0d0d", border_width=0)
        self.content_frame.pack(fill="both", expand=True)

        # Bottom Actions
        self.actions_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.actions_frame.pack(fill="x", pady=(20, 0))
        
        self.btn_reset = ctk.CTkButton(
            self.actions_frame, text=Loc.get("btn_reset").upper(), 
            fg_color="transparent", border_width=1, border_color="#333",
            hover_color="#b22222",
            height=45,
            command=self.reset_all
        )
        self.btn_reset.pack(side="left")
        
        self.btn_save = ctk.CTkButton(
            self.actions_frame, text=Loc.get("btn_save").upper(), 
            fg_color="#3498db", hover_color="#2980b9",
            height=45, font=ctk.CTkFont(weight="bold"),
            command=self.save_and_exit
        )
        self.btn_save.pack(side="right")

        # Start with specified page
        self.show_page(start_page)


    def _create_emus_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("sec_emus"))
        self.create_path_row(page, Loc.get("lbl_emu_archipelago"), "emulators", "archipelago", is_folder=True)
        self.create_path_row(page, Loc.get("lbl_emu_bizhawk"), "emulators", "bizhawk")
        self.create_path_row(page, Loc.get("lbl_emu_dolphin"), "emulators", "dolphin")
        self.create_path_row(page, Loc.get("lbl_emu_azahar"), "emulators", "azahar")
        self.create_path_row(page, Loc.get("lbl_emu_poptracker"), "emulators", "poptracker")
        self.create_path_row(page, Loc.get("lbl_emu_broadcast"), "emulators", "broadcast", is_folder=True)
        return page

    def _create_games_page(self):
        page = self.create_page_frame()
        
        # Section Header with Autodetect button
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(header, text=Loc.get("sec_roms"), font=ctk.CTkFont(size=12, weight="bold"), text_color="#555").pack(side="left", padx=15, pady=(25, 0))
        
        btn_auto = ctk.CTkButton(
            header, text=Loc.get("btn_autodetect_roms"), 
            fg_color="#27ae60", hover_color="#219150", 
            height=32, font=ctk.CTkFont(size=11, weight="bold"),
            command=self.autodetect_roms
        )
        btn_auto.pack(side="right", padx=15, pady=(25, 0))

        games = list(self.config.get("roms", {}).keys())
        for game in games:
            self.create_path_row(page, f"{game}", "roms", game)
        return page

    def _create_conn_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("sec_net"))
        self.create_simple_row(page, Loc.get("lbl_host"), "archipelago_settings", "host")
        self.create_simple_row(page, Loc.get("lbl_port"), "archipelago_settings", "port")
        self.create_simple_row(page, Loc.get("lbl_password"), "archipelago_settings", "password", is_pass=True)
        return page

    def _create_slots_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("sec_slots"))
        slot_names = list(self.config.get("slot_names", {}).keys())
        for game in slot_names:
            self.create_simple_row(page, f"{game}", "slot_names", game)
        return page

    def _create_trackers_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("sec_tracker_global"))
        self.create_check_row(page, Loc.get("opt_maximize_tracker"), "maximize_poptracker")
        self.create_monitor_row(page, Loc.get("opt_tracker_monitor"), "poptracker_display_index")

        # Section Header with Autodetect button
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(header, text=Loc.get("sec_tracker_packs"), font=ctk.CTkFont(size=12, weight="bold"), text_color="#555").pack(side="left", padx=15, pady=(25, 0))
        
        btn_auto = ctk.CTkButton(
            header, text=Loc.get("btn_autodetect_trackers"),
            fg_color="#27ae60", hover_color="#219150", 
            height=32, font=ctk.CTkFont(size=11, weight="bold"),
            command=self.autodetect_trackers
        )
        btn_auto.pack(side="right", padx=15, pady=(25, 0))

        roms_list = list(self.config.get("roms", {}).keys())
        for game in roms_list:
            self.create_path_row(page, game, "poptracker_packs", game, is_tracker=True)
        return page

    def _create_obs_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("sec_obs_global"))
        self.create_check_row(page, Loc.get("opt_enable_obs"), "obs_settings", subkey="enabled")
        self.create_simple_row(page, Loc.get("lbl_obs_host"), "obs_settings", "host")
        self.create_simple_row(page, Loc.get("lbl_obs_port"), "obs_settings", "port")
        self.create_simple_row(page, Loc.get("lbl_obs_password"), "obs_settings", "password", is_pass=True)
        
        self.create_section_label(page, Loc.get("sec_broadcast"))
        self.create_check_row(page, Loc.get("opt_poptracker_broadcast"), "poptracker_broadcast")
        self.create_option_row(page, Loc.get("opt_broadcast_mode"), "broadcast_mode", ["all", "personal", "obs"])
        self.create_check_row(page, Loc.get("opt_broadcast_overlay"), "broadcast_enable_overlay")
        self.create_check_row(page, Loc.get("opt_broadcast_obs"), "broadcast_enable_obs")
        self.create_check_row(page, Loc.get("opt_broadcast_show_locations"), "broadcast_show_locations")
        self.create_check_row(page, Loc.get("opt_broadcast_disable_hw_accel"), "broadcast_disable_hw_accel")
        
        self.btn_test_obs = ctk.CTkButton(
            page, text=Loc.get("btn_test_obs"), 
            command=self.test_obs_connection, 
            fg_color="transparent", border_width=1, border_color="#3498db", text_color="#3498db", hover_color="#1a1a1a",
            height=40
        )
        self.btn_test_obs.pack(pady=20, padx=15, anchor="e")
        
        self.create_section_label(page, Loc.get("sec_obs_scenes"))
        roms_list = list(self.config.get("roms", {}).keys())
        for game in roms_list:
            self.create_scene_row(page, Loc.get("lbl_scene_for", name=game), game)
        return page

    def _create_active_games_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("sec_visibility"))
        active_games_config = self.config.get("active_games", {})
        roms_list = list(self.config.get("roms", {}).keys())
        for game in roms_list:
            # If game not in active_games, default to True
            if game not in active_games_config:
                active_games_config[game] = True
            self.create_check_row(page, Loc.get("opt_show_game", name=game), "active_games", subkey=game)
        return page

    def _create_general_page(self):
        page = self.create_page_frame()
        self.create_section_label(page, Loc.get("tab_general").upper())

        def on_hot_swap():
            # Si activé, désactiver auto-save
            if self.path_vars[(None, "multi_game_keep_alive")].get():
                if (None, "auto_savestate_enabled") in self.path_vars:
                    self.path_vars[(None, "auto_savestate_enabled")].set(False)

        def on_auto_save():
            # Si activé, désactiver hot-swap
            if self.path_vars[(None, "auto_savestate_enabled")].get():
                if (None, "multi_game_keep_alive") in self.path_vars:
                    self.path_vars[(None, "multi_game_keep_alive")].set(False)

        self.create_check_row(page, Loc.get("opt_multi_game_keep_alive"), "multi_game_keep_alive", command=on_hot_swap, default_val=False)
        self.create_check_row(page, Loc.get("auto_save_label"), "auto_savestate_enabled", command=on_auto_save, default_val=False)
        
        # Language frame
        row = ctk.CTkFrame(page, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=4, padx=10)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(inner, text=Loc.get("lbl_language"), width=160, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 10))
        
        self.lang_var = ctk.StringVar(value=self.config.get("language", "fr"))
        lang_menu = ctk.CTkOptionMenu(inner, values=["fr", "en"], variable=self.lang_var, height=35, command=self.change_language)
        lang_menu.pack(side="left", fill="x", expand=True, padx=5)

        self.create_section_label(page, Loc.get("sec_shortcuts"))
        self.create_simple_row(page, Loc.get("lbl_hub_keyboard_shortcut"), None, "hub_keyboard_shortcut")
        
        # Controller combo row
        row_ctrl = ctk.CTkFrame(page, fg_color="#141414", corner_radius=12)
        row_ctrl.pack(fill="x", pady=4, padx=10)
        inner_ctrl = ctk.CTkFrame(row_ctrl, fg_color="transparent")
        inner_ctrl.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(inner_ctrl, text=Loc.get("lbl_hub_controller_shortcut"), width=160, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 10))
        
        self.ctrl_shortcut_var = tk.StringVar(value=self.config.get("hub_controller_open_btn", "CAPTURE"))
        self.path_vars[(None, "hub_controller_open_btn")] = self.ctrl_shortcut_var
        
        entry_ctrl = ctk.CTkEntry(inner_ctrl, textvariable=self.ctrl_shortcut_var, height=35, fg_color="#0d0d0d", border_color="#2a2a2a")
        entry_ctrl.pack(side="left", fill="x", expand=True, padx=5)
        
        # Bouton de détection auto
        self.btn_detect_ctrl = ctk.CTkButton(
            inner_ctrl, text="🎙️ " + Loc.get("assign_btn"), width=100, height=35,
            fg_color="#2c3e50", hover_color="#34495e",
            command=self.start_controller_detection
        )
        self.btn_detect_ctrl.pack(side="left", padx=5)
        
        self.is_detecting_ctrl = False
        
        ctk.CTkLabel(inner_ctrl, text=Loc.get("hint_combo"), font=ctk.CTkFont(size=10), text_color="#555").pack(side="left", padx=5)
        
        return page

    def create_page_frame(self):
        return ctk.CTkFrame(self.content_frame, fg_color="transparent")

    def create_section_label(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#555")
        lbl.pack(pady=(25, 10), padx=15, anchor="w")

    def show_page(self, name):
        # Lazy Loading: Create page if it doesn't exist
        if name not in self.pages:
            creation_methods = {
                "emus": self._create_emus_page,
                "games": self._create_games_page,
                "conn": self._create_conn_page,
                "slots": self._create_slots_page,
                "active_games_page": self._create_active_games_page,
                "trackers": self._create_trackers_page,
                "obs": self._create_obs_page,
                "general": self._create_general_page
            }
            if name in creation_methods:
                self.pages[name] = creation_methods[name]()

        if self.current_page:
            self.current_page.pack_forget()
            if self.last_page_id in self.nav_buttons:
                self.nav_buttons[self.last_page_id].configure(fg_color="transparent", text_color="#eee")
        
        self.current_page = self.pages[name]
        self.last_page_id = name
        self.current_page.pack(fill="both", expand=True)
        self.nav_buttons[name].configure(fg_color="#3498db", text_color="white")
        
        titles = {
            "emus": "ÉMULATEURS", "games": "JEUX / ROMS", "conn": "CONNEXION AP",
            "slots": "SLOTS AP", "trackers": "TRACKERS", "obs": "STREAMING & OBS",
            "active_games_page": "SÉLECTION JEUX"
        }
        self.page_title_label.configure(text=titles.get(name, ""))

        # Reset scroll position to top
        try:
            self.content_frame._parent_canvas.yview_moveto(0)
        except:
            pass

    def create_path_row(self, parent, label_text, category, key, is_folder=False, is_tracker=False):
        row = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=4, padx=10)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        
        lbl = ctk.CTkLabel(inner, text=label_text, width=160, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
        lbl.pack(side="left", padx=(0, 10))
        
        var = tk.StringVar(value=self.config.get(category, {}).get(key, ""))
        self.path_vars[(category, key)] = var
        
        entry = ctk.CTkEntry(inner, textvariable=var, height=35, fg_color="#0d0d0d", border_color="#2a2a2a")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        if is_tracker:
            v_var = tk.StringVar(value=self.config.get("poptracker_variants", {}).get(key, ""))
            self.path_vars[("poptracker_variants", key)] = v_var
            
            v_combo = ctk.CTkComboBox(inner, variable=v_var, width=130, height=35, fg_color="#0d0d0d", border_color="#2a2a2a", values=[""])
            v_combo.pack(side="left", padx=5)
            
            def update_variants(*args):
                path = var.get().strip()
                if path.startswith("http"):
                    v_combo.configure(state="disabled")
                    v_var.set("(Web Tracker)")
                else:
                    v_combo.configure(state="normal")
                    v_list = self.get_pack_variants(path)
                    if v_list:
                        v_combo.configure(values=v_list)
                        if v_var.get() not in v_list: v_var.set(v_list[0])
                    else:
                        v_combo.configure(values=["(Défaut)"])
                        v_var.set("(Défaut)")
            
            var.trace_add("write", update_variants)
            update_variants()

        btn_browse = ctk.CTkButton(inner, text="📁", width=40, height=35, fg_color="#222", hover_color="#333", 
                                  command=lambda: self.browse_path(category, key, is_folder))
        btn_browse.pack(side="left", padx=2)
        
        btn_clear = ctk.CTkButton(inner, text="X", width=40, height=35, fg_color="#222", hover_color="#b22222",
                                 command=lambda: var.set(""))
        btn_clear.pack(side="left", padx=(2, 0))

    def get_monitors(self):
        monitors = []
        if not HAS_PYWIN32:
            return ["Écran 1 (Principal)"]
            
        try:
            enum_monitors = win32api.EnumDisplayMonitors()
            for i, (hMonitor, hdcMonitor, rect) in enumerate(enum_monitors):
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                is_primary = " (Principal)" if rect[0] == 0 and rect[1] == 0 else ""
                monitors.append(f"Écran {i+1} : {width}x{height}{is_primary}")
        except Exception as e:
            print(f"Error enumerating monitors: {e}")
            monitors = ["Écran 1 (Principal)"]
        
        if not monitors:
            monitors = ["Écran 1 (Principal)"]
        return monitors

    def create_monitor_row(self, parent, label_text, key):
        row = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=4, padx=10)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        
        lbl = ctk.CTkLabel(inner, text=label_text, width=160, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
        lbl.pack(side="left", padx=(0, 10))
        
        monitor_list = self.get_monitors()
        
        # Current value in config
        current_val = self.config.get(key, 0)
        try:
            current_idx = int(current_val)
        except:
            current_idx = 0
            
        if current_idx >= len(monitor_list):
            current_idx = 0
            
        var = tk.StringVar(value=monitor_list[current_idx])
        self.path_vars[(None, key)] = var # category is None for top-level keys
        
        def on_change(choice):
            idx = monitor_list.index(choice)
            # We don't save immediately, save_and_exit will do it
            pass

        combo = ctk.CTkOptionMenu(inner, variable=var, values=monitor_list, height=35, fg_color="#0d0d0d", button_color="#222", button_hover_color="#333")
        combo.pack(side="left", fill="x", expand=True, padx=5)

    def create_option_row(self, parent, label_text, key, options):
        row = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=4, padx=10)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        
        lbl = ctk.CTkLabel(inner, text=label_text, width=160, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
        lbl.pack(side="left", padx=(0, 10))
        
        var = tk.StringVar(value=self.config.get(key, options[0]))
        self.path_vars[(None, key)] = var
        
        combo = ctk.CTkOptionMenu(inner, variable=var, values=options, height=35, fg_color="#0d0d0d", button_color="#222", button_hover_color="#333")
        combo.pack(side="left", fill="x", expand=True, padx=5)

    def create_simple_row(self, parent, label_text, category, key, is_pass=False):
        row = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=4, padx=10)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        
        lbl = ctk.CTkLabel(inner, text=label_text, width=160, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
        lbl.pack(side="left", padx=(0, 10))
        
        var = tk.StringVar(value=self.config.get(category, {}).get(key, ""))
        self.path_vars[(category, key)] = var
        
        show = "*" if is_pass else ""
        entry = ctk.CTkEntry(inner, textvariable=var, height=35, fg_color="#0d0d0d", border_color="#2a2a2a", show=show)
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        if is_pass:
            def toggle():
                if entry.cget("show") == "*":
                    entry.configure(show="")
                    btn_t.configure(text="🔒")
                else:
                    entry.configure(show="*")
                    btn_t.configure(text="👁️")
            btn_t = ctk.CTkButton(inner, text="👁️", width=40, height=35, fg_color="#222", hover_color="#333", command=toggle)
            btn_t.pack(side="left", padx=2)

        btn_clear = ctk.CTkButton(inner, text="X", width=40, height=35, fg_color="#222", hover_color="#b22222",
                                 command=lambda: var.set(""))
        btn_clear.pack(side="left", padx=(2, 0))

    def create_check_row(self, parent, label_text, key_or_category, subkey=None, command=None, default_val=True):
        row = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=4, padx=10)
        
        if subkey:
            val = self.config.get(key_or_category, {}).get(subkey, default_val)
            var = tk.BooleanVar(value=val)
            self.path_vars[(key_or_category, subkey)] = var
        else:
            var = tk.BooleanVar(value=self.config.get(key_or_category, default_val))
            self.path_vars[(None, key_or_category)] = var
            
        cb = ctk.CTkCheckBox(row, text=label_text, variable=var, font=ctk.CTkFont(size=11, weight="bold"), fg_color="#3498db", command=command)
        cb.pack(side="left", padx=20, pady=15)
        return cb

    def create_scene_row(self, parent, label_text, game_key):
        row = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=12)
        row.pack(fill="x", pady=2, padx=10)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=5)
        
        lbl = ctk.CTkLabel(inner, text=label_text, width=160, anchor="w", font=ctk.CTkFont(size=11))
        lbl.pack(side="left", padx=(0, 10))
        
        if "obs_settings" not in self.config: self.config["obs_settings"] = {}
        if "scenes" not in self.config["obs_settings"]: self.config["obs_settings"]["scenes"] = {}
        
        var = tk.StringVar(value=self.config["obs_settings"]["scenes"].get(game_key, ""))
        self.path_vars[("obs_scenes", game_key)] = var
        
        entry = ctk.CTkEntry(inner, textvariable=var, height=30, fg_color="#0d0d0d", border_color="#2a2a2a")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        btn_clear = ctk.CTkButton(inner, text="X", width=30, height=30, fg_color="#222", hover_color="#b22222",
                                 command=lambda: var.set(""))
        btn_clear.pack(side="left", padx=(2, 0))

    def browse_path(self, category, key, is_folder=False):
        initial_dir = "/"
        current_value = self.path_vars[(category, key)].get()
        if current_value and os.path.exists(os.path.dirname(current_value) if not is_folder else current_value):
            initial_dir = os.path.dirname(current_value) if not is_folder else current_value
        else:
            base_project = BASE_DIR
            root_project = os.path.dirname(base_project)
            if category == "roms":
                patch_file_dir = os.path.join(root_project, "PatchFile")
                if os.path.exists(patch_file_dir): initial_dir = patch_file_dir

        if is_folder or category == "poptracker_packs":
            path = filedialog.askdirectory(initialdir=initial_dir, title=f"Sélectionner dossier pour {key}")
            # Si l'utilisateur annule le dossier, on peut tenter askopenfilename pour les .zip si c'est un tracker
            if not path and category == "poptracker_packs":
                filetypes = [("PopTracker Packs", "*.zip *.pmp"), ("Tous", "*.*")]
                path = filedialog.askopenfilename(initialdir=initial_dir, title=f"Sélectionner {key}", filetypes=filetypes)
        else:
            filetypes = [("Tous les fichiers", "*.*")]
            if category == "emulators":
                filetypes = [("Executables", "*.exe")]
            elif category == "roms":
                # Mapping des extensions par jeu
                rom_extensions = {
                    "Ocarina of Time": [("Nintendo 64 ROM", "*.z64 *.n64 *.v64")],
                    "Majora's Mask": [("N64/Native", "*.z64 *.n64 *.v64 *.exe")],
                    "Wind Waker": [("GameCube Image", "*.iso *.gcm")],
                    "Twilight Princess": [("GameCube/Wii Image", "*.iso *.gcm *.wbfs")],
                    "Skyward Sword": [("Wii Image", "*.iso *.wbfs")],
                    "A Link to the Past": [("SNES ROM", "*.sfc *.smc")],
                    "Minish Cap": [("GBA ROM", "*.gba")],
                    "OOT (SOH)": [("Ship of Harkinian", "*.exe")],
                    "A Link Between Worlds": [("3DS ROM", "*.cci *.3ds")],
                    "The Legend of Zelda": [("NES ROM", "*.nes")],
                    "Zelda II": [("NES ROM", "*.nes")],
                    "Oracle of Ages": [("GameBoy Color", "*.gbc *.gb")],
                    "Oracle of Seasons": [("GameBoy Color", "*.gbc *.gb")],
                    "Link's Awakening DX": [("GameBoy Color", "*.gbc *.gb")],
                    "Phantom Hourglass": [("DS ROM", "*.nds")],
                    "Spirit Tracks": [("DS ROM", "*.nds")]
                }
                if key in rom_extensions:
                    filetypes = rom_extensions[key] + [("Tous les fichiers", "*.*")]

            path = filedialog.askopenfilename(initialdir=initial_dir, title=f"Sélectionner {key}", filetypes=filetypes)

        if path:
            self.path_vars[(category, key)].set(os.path.normpath(path))

    def change_language(self, new_lang):
        Loc.set_lang(new_lang)
        self.config["language"] = new_lang # NOUVEAU: Mettre à jour la config immédiatement
        self.title(Loc.get("setup_title").upper())
        self.page_title_label.configure(text=Loc.get("setup_title").upper())
        self.sub_logo.configure(text=Loc.get("lbl_config"))
        
        # Redessiner la sidebar pour traduire les boutons
        for p_id, btn in self.nav_buttons.items():
            # Extraire l'icône et trouver le nouveau texte
            current_text = btn.cget("text")
            icon = current_text.split("  ")[0] if "  " in current_text else ""
            
            nav_loc_keys = {
                "emus": "tab_emulators", "games": "tab_roms", "conn": "tab_archipelago",
                "slots": "tab_slots", "active_games_page": "tab_visibility",
                "trackers": "tab_poptracker", "obs": "tab_obs", "general": "tab_general"
            }
            if p_id in nav_loc_keys:
                new_label = Loc.get(nav_loc_keys[p_id]).upper()
                btn.configure(text=f"{icon}  {new_label}")
        
        # Mettre à jour les titres
        self.btn_save.configure(text=Loc.get("btn_save").upper())
        self.btn_reset.configure(text=Loc.get("btn_reset").upper())
        
        # Recharger la page actuelle pour traduire son contenu
        if self.last_page_id:
            # On détruit l'ancienne page pour la forcer à se recréer avec la nouvelle langue
            if self.last_page_id in self.pages:
                self.pages[self.last_page_id].destroy()
                del self.pages[self.last_page_id]
            self.current_page = None
            self.show_page(self.last_page_id)

    def autodetect_roms(self):
        project_root = os.path.dirname(BASE_DIR)
        
        # Chemins ciblés selon ta structure
        emu_dir = os.path.join(project_root, "Emulator")
        rom_dir = os.path.join(project_root, "Rom")
        patch_dir = os.path.join(project_root, "PatchFile")
        if not os.path.exists(patch_dir):
            patch_dir = os.path.join(project_root, "patchfiles") # Support du nom au pluriel

        # Mapping des jeux vers leurs dossiers de recherche prioritaires
        search_mapping = {
            "OOT (SOH)": emu_dir,
            "Majora's Mask": emu_dir,
            "Twilight Princess": rom_dir,
            "A Link Between Worlds": rom_dir,
            "Phantom Hourglass": rom_dir,
            "Spirit Tracks": rom_dir,
            "Skyward Sword": patch_dir # On cherche dans PatchFile selon la demande utilisateur
        }

        # Mapping des mots-clés pour les exceptions
        exceptions = {
            "Skyward Sword": ["Skyward Sword", "SOUE01"],
            "OOT (SOH)": ["soh.exe"],
            "Twilight Princess": ["Twilight Princess"],
            "Majora's Mask": ["Zelda64Recompiled.exe", "Majora"],
            "Phantom Hourglass": ["Phantom Hourglass"],
            "Spirit Tracks": ["Spirit Tracks"],
            "A Link Between Worlds": ["Link Between Worlds", "ALBW"]
        }

        # Mapping des extensions pour validation
        rom_ext_map = {
            "Ocarina of Time": [".z64", ".n64", ".v64"],
            "Majora's Mask": [".z64", ".n64", ".v64", ".exe"],
            "Wind Waker": [".iso", ".gcm"],
            "Twilight Princess": [".iso", ".gcm", ".wbfs"],
            "Skyward Sword": [".iso", ".wbfs"],
            "A Link to the Past": [".sfc", ".smc"],
            "Minish Cap": [".gba"],
            "OOT (SOH)": [".exe"],
            "A Link Between Worlds": [".cci", ".3ds"],
            "The Legend of Zelda": [".nes"],
            "Zelda II": [".nes"],
            "Oracle of Ages": [".gbc", ".gb"],
            "Oracle of Seasons": [".gbc", ".gb"],
            "Link's Awakening DX": [".gbc", ".gb"],
            "Phantom Hourglass": [".nds"],
            "Spirit Tracks": [".nds"]
        }

        slot_names = self.config.get("slot_names", {})
        found_count = 0
        
        # Vérifier et demander le dossier Rom s'il n'existe pas
        if not os.path.exists(rom_dir):
            selected_rom = filedialog.askdirectory(title="Dossier 'Rom' non trouvé. Choisir le dossier contenant vos ROMs à scanner.")
            if selected_rom:
                rom_dir = selected_rom
            else:
                rom_dir = project_root
                
        # Vérifier et demander le dossier Emulator s'il n'existe pas
        if not os.path.exists(emu_dir):
            selected_emu = filedialog.askdirectory(title="Dossier 'Emulator' non trouvé. Choisir le dossier contenant vos Émulateurs/Jeux à scanner.")
            if selected_emu:
                emu_dir = selected_emu
            else:
                emu_dir = project_root
                
        # Vérifier et demander le dossier PatchFile s'il n'existe pas
        if not os.path.exists(patch_dir):
            selected_patch = filedialog.askdirectory(title="Dossier 'PatchFile' non trouvé. Choisir le dossier contenant vos fichiers de Patch à scanner.")
            if selected_patch:
                patch_dir = selected_patch
            else:
                patch_dir = project_root

        # Recréer le search_mapping avec les dossiers mis à jour
        search_mapping = {
            "OOT (SOH)": emu_dir,
            "Majora's Mask": emu_dir,
            "Twilight Princess": rom_dir,
            "A Link Between Worlds": rom_dir,
            "Phantom Hourglass": rom_dir,
            "Spirit Tracks": rom_dir,
            "Skyward Sword": patch_dir
        }

        for game, valid_exts in rom_ext_map.items():
            # Déterminer le dossier où chercher
            target_dir = search_mapping.get(game, patch_dir)
            if not os.path.exists(target_dir):
                target_dir = project_root # Fallback sur la racine du projet

            match_keywords = []
            if game in exceptions:
                match_keywords = exceptions[game]
            else:
                slot_name = slot_names.get(game)
                if slot_name:
                    match_keywords = [slot_name]
            
            if not match_keywords: continue

            best_match = None
            # Recherche récursive dans le dossier cible
            for root, _, files in os.walk(target_dir):
                for f in files:
                    filename = f.lower()
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if ext in [x.lower() for x in valid_exts]:
                        filepath = os.path.join(root, f)
                        for kw in match_keywords:
                            if kw.lower() in filename:
                                # Priorité "AP_" pour les jeux standards
                                if game not in exceptions and "ap_" in filename:
                                    best_match = filepath
                                    break
                                best_match = filepath
                        
                        if best_match and game not in exceptions and "ap_" in os.path.basename(best_match).lower():
                            break # On a trouvé le patch AP parfait
                if best_match and game not in exceptions and "ap_" in os.path.basename(best_match).lower():
                    break

            if best_match:
                var = self.path_vars.get(("roms", game))
                if var:
                    var.set(os.path.normpath(best_match))
                    found_count += 1

        messagebox.showinfo(Loc.get("msg_auto_detect_title"), Loc.get("msg_auto_rom_result", found=found_count))

    def autodetect_trackers(self):
        project_root = os.path.dirname(BASE_DIR)
        # Primary location is App/Poptracker/packs, fallback to Patcher/Poptracker/packs
        packs_dir = os.path.join(project_root, "App", "Poptracker", "packs")
        if not os.path.exists(packs_dir):
            packs_dir = os.path.join(project_root, "Patcher", "Poptracker", "packs")
        
        if not os.path.exists(packs_dir):
            packs_dir = filedialog.askdirectory(title="Dossier des packs non trouvé. Choisir le dossier 'packs' de PopTracker.")
            if not packs_dir: return

        # Liste des jeux supportés par le Launcher
        games_to_find = list(self.config.get("roms", {}).keys())
        found_count = 0
        
        # Liste tous les packs potentiels (dossiers, zip, pmp)
        # On trie pour mettre les dossiers à la fin afin qu'ils écrasent les zip si les deux existent
        sorted_items = sorted(os.listdir(packs_dir), key=lambda x: os.path.isdir(os.path.join(packs_dir, x)))
        
        import re
        
        for item in sorted_items:
            path = os.path.join(packs_dir, item)
            
            # Logic match for Webtracker-LADX and Webtracker-SS specifically requested by user
            target_game = None
            if item == "Webtracker-LADX": target_game = "Link's Awakening DX"
            elif item == "Webtracker-SS": target_game = "Skyward Sword"
            
            if target_game:
                var = self.path_vars.get(("poptracker_packs", target_game))
                if var:
                    var.set(os.path.normpath(path))
                    found_count += 1
                continue
            manifest_data = None
            
            # Tentative de lecture du manifest
            try:
                content = ""
                if os.path.isdir(path):
                    manifest_file = os.path.join(path, "manifest.json")
                    if os.path.exists(manifest_file):
                        with open(manifest_file, 'r', encoding='utf-8-sig') as f:
                            content = f.read()
                elif item.lower().endswith(('.zip', '.pmp')) and zipfile.is_zipfile(path):
                    with zipfile.ZipFile(path, 'r') as z:
                        target = next((n for n in z.namelist() if n == "manifest.json" or n.endswith("/manifest.json")), None)
                        if target:
                            with z.open(target) as f:
                                content = f.read().decode('utf-8-sig')
                
                if content:
                    # Nettoyage des commentaires JSON (fréquent dans les packs PopTracker)
                    content = re.sub(r'//.*?\n', '\n', content)
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                    manifest_data = json.loads(content)
                else:
                    # Si aucun manifest n'est trouvé, on utilise le nom du fichier/dossier
                    manifest_data = {"name": item}
            except Exception as e:
                # Fallback sur le nom du dossier si le JSON est illisible
                print(f"JSON Error for {item}: {e}. Falling back to filename matching.")
                manifest_data = {"name": item} # On injecte le nom du dossier comme fallback

            if manifest_data:
                # On récupère le nom interne du pack (name, game_name ou game)
                pack_name = (manifest_data.get("name") or manifest_data.get("game_name") or manifest_data.get("game") or "").lower()
                # Normalisation des séparateurs pour faciliter le matching
                pack_name = pack_name.replace("-", " ").replace("_", " ")
                if not pack_name: continue

                # On cherche le jeu qui correspond le mieux
                for game in games_to_find:
                    match = False
                    # Normalisation du nom pour la comparaison
                    g_low = game.lower()
                    
                    # Logique de matching intelligente
                    if g_low in pack_name: match = True
                    elif "ocarina" in g_low:
                        # On évite que "brooty" (Zelda 1) match OOT à cause du "oot" central
                        if ("ocarina" in pack_name or "oot" in pack_name) and "brooty" not in pack_name:
                            if "so_h" not in pack_name and "ship" not in pack_name: match = True
                    elif "majora" in g_low and ("mm" in pack_name or "majora" in pack_name): match = True
                    elif "wind waker" in g_low and ("tww" in pack_name or "wind" in pack_name or "ww" in pack_name): match = True
                    elif "twilight princess" in g_low and ("tp" in pack_name or "tpr" in pack_name or "twilight" in pack_name): match = True
                    elif "between worlds" in g_low and ("albw" in pack_name or "between worlds" in pack_name): match = True
                    elif "past" in g_low and ("alttp" in pack_name or "past" in pack_name): match = True
                    elif "minish" in g_low and ("tmc" in pack_name or "mc" in pack_name): match = True
                    elif "soh" in g_low and ("so h" in pack_name or "ship" in pack_name): match = True
                    elif "awakening" in g_low and ("ladx" in pack_name or "awakening" in pack_name): match = True
                    elif "ages" in g_low and ("ooa" in pack_name or "ages" in pack_name): match = True
                    elif "seasons" in g_low and ("oos" in pack_name or "seasons" in pack_name): match = True
                    elif game == "The Legend of Zelda":
                        # Pour Zelda 1, on cherche TLoZ ou Zelda 1 (en ignorant Zelda 2)
                        if "tloz" in pack_name or "brooty" in pack_name or ("zelda" in pack_name and "1" in pack_name) or ("nes" in pack_name and "zelda" in pack_name and "2" not in pack_name):
                            match = True
                    elif game == "Zelda II":
                        # Pour Zelda 2, on cherche Zelda 2, Zelda II ou Z2
                        if "zelda 2" in pack_name or "zelda ii" in pack_name or "z2" in pack_name or "ao_l" in pack_name:
                            match = True

                    if match:
                        var = self.path_vars.get(("poptracker_packs", game))
                        if var:
                            var.set(os.path.normpath(path))
                            found_count += 1
                        break

        messagebox.showinfo(Loc.get("msg_auto_detect_title"), Loc.get("msg_auto_tracker_result", found=found_count))

    def reset_all(self):
        if messagebox.askyesno("Confirmation", "Effacer TOUS les réglages ?"):
            for var in self.path_vars.values():
                if isinstance(var, tk.BooleanVar): var.set(False)
                else: var.set("")

    def start_controller_detection(self):
        """Lance l'écoute pour détecter un bouton de manette."""
        if not HAS_PYGAME:
            messagebox.showerror("Erreur", "Pygame n'est pas installé.")
            return

        if self.is_detecting_ctrl:
            self.stop_controller_detection()
            return

        # Initialisation pygame si besoin
        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        
        # Detector pour normaliser les noms (comme dans ui_controller.py)
        if not hasattr(self, 'detector') or self.detector is None:
            self.detector = DeviceDetector()

        self.is_detecting_ctrl = True
        self.btn_detect_ctrl.configure(text=Loc.get("listening_btn"), fg_color="#c0392b")
        self.ctrl_shortcut_var.set("...")
        self.listening_combo_current = set()
        self.listening_combo_final = set()
        
        # On utilise after pour ne pas bloquer l'UI
        self.poll_controller_for_shortcut()

    def stop_controller_detection(self):
        self.is_detecting_ctrl = False
        self.btn_detect_ctrl.configure(text="🎙️ " + Loc.get("assign_btn"), fg_color="#2c3e50")
        if self.ctrl_shortcut_var.get() == "...":
            self.ctrl_shortcut_var.set(self.config.get("hub_controller_open_btn", "CAPTURE"))

    def poll_controller_for_shortcut(self):
        if not self.is_detecting_ctrl:
            return

        # Vider la file d'attente et traiter les événements
        for event in pygame.event.get():
            norm_event = self.detector.process_event(event)
            if not norm_event:
                continue

            input_id = norm_event["id"]
            state = norm_event.get("state", 0)

            # Identification du type d'événement (Presse vs Relâche)
            is_press = False
            if norm_event["type"] in ["button", "hat"]:
                is_press = (state == 1)
            elif norm_event["type"] == "axis":
                is_press = abs(state) > 0.8

            if is_press:
                # Ajouter à la combo en cours
                if input_id not in self.listening_combo_final:
                    self.listening_combo_final.add(input_id)
                self.listening_combo_current.add(input_id)
                
                # Mise à jour visuelle immédiate
                combo_str = "+".join(sorted(list(self.listening_combo_final)))
                self.ctrl_shortcut_var.set(combo_str)
            else:
                # Retirer de l'état "maintenu"
                if input_id in self.listening_combo_current:
                    self.listening_combo_current.remove(input_id)
                
                # Si TOUT est relâché et qu'on a capté quelque chose -> On valide
                if not self.listening_combo_current and self.listening_combo_final:
                    final_str = "+".join(sorted(list(self.listening_combo_final)))
                    self.ctrl_shortcut_var.set(final_str)
                    self.stop_controller_detection()
                    self.config["hub_controller_open_btn"] = final_str
                    return

        # Continuer de poller si rien trouvé ou si boutons encore maintenus
        self.after(20, self.poll_controller_for_shortcut)

    def save_and_exit(self):
        for (category, key), var in self.path_vars.items():
            if category is None:
                val = var.get()
                # Special handling for monitor index if it's stored as a string from the OptionMenu
                if key == "poptracker_display_index":
                    monitor_list = self.get_monitors()
                    try:
                        val = monitor_list.index(val)
                    except:
                        val = 0
                self.config[key] = val
            elif category == "obs_scenes":
                if "obs_settings" not in self.config: self.config["obs_settings"] = {}
                if "scenes" not in self.config["obs_settings"]: self.config["obs_settings"]["scenes"] = {}
                self.config["obs_settings"]["scenes"][key] = var.get()
            else:
                if category not in self.config: self.config[category] = {}
                # Appliquer make_relative uniquement aux catégories contenant des chemins
                if category in ["emulators", "roms", "poptracker_packs"]:
                    self.config[category][key] = make_relative(var.get())
                else:
                    self.config[category][key] = var.get()
        
        if hasattr(self, 'lang_var'):
            self.config["language"] = self.lang_var.get()
            Loc.set_lang(self.config["language"])
        
        if save_config(self.config):
            messagebox.showinfo(Loc.get("msg_success"), Loc.get("msg_config_saved"))
            self.destroy()
        else:
            messagebox.showerror("Erreur", "Sauvegarde impossible.")

    def test_obs_connection(self):
        obs_controller.host = self.path_vars[("obs_settings", "host")].get()
        try:
            obs_controller.port = int(self.path_vars[("obs_settings", "port")].get())
        except:
            messagebox.showerror("Erreur", "Le port doit être un nombre.")
            return
        obs_controller.password = self.path_vars[("obs_settings", "password")].get()
        
        self.btn_test_obs.configure(state="disabled", text="CONNEXION EN COURS...")
        self.update()
        success, message = obs_controller.test_connection()
        self.btn_test_obs.configure(state="normal", text="TESTER LA CONNEXION OBS")
        
        if success: messagebox.showinfo("OBS", message)
        else: messagebox.showerror("OBS", message)

    def get_pack_variants(self, pack_path: str):
        if not pack_path or not os.path.exists(pack_path): return []
        try:
            manifest_data = None
            if os.path.isdir(pack_path):
                manifest_file = os.path.join(pack_path, "manifest.json")
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r', encoding='utf-8-sig') as f:
                        manifest_data = json.load(f)
            elif zipfile.is_zipfile(pack_path):
                with zipfile.ZipFile(pack_path, 'r') as z:
                    target = next((n for n in z.namelist() if n == "manifest.json" or n.endswith("/manifest.json")), None)
                    if target:
                        with z.open(target) as f:
                            manifest_data = json.loads(f.read().decode('utf-8-sig'))
            if manifest_data and "variants" in manifest_data:
                return list(manifest_data["variants"].keys())
        except Exception as e: print(f"Manifest error: {e}")
        return []

    def on_closing(self):
        if HAS_PYGAME and pygame.get_init():
            pygame.quit()
        self.destroy()

if __name__ == "__main__":
    import sys
    start_p = "emus"
    if "--page" in sys.argv:
        try:
            idx = sys.argv.index("--page")
            if idx + 1 < len(sys.argv):
                start_p = sys.argv[idx + 1]
        except: pass
        
    app = SetupUI(start_page=start_p)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
