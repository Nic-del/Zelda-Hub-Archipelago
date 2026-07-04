import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import json
import os
import threading
import subprocess
import sys
import time
import psutil
try:
    import keyboard
except ImportError:
    keyboard = None

try:
    from PIL import Image, ImageTk, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[Launcher] Erreur: Pillow (PIL) n'est pas installé. Utilisation du mode texte.")

from launcher_core import (
    GameManager, BizHawkController, DolphinController, CONFIG_PATH, BASE_DIR, get_exe_dir, resolve_path,
    set_current_process_priority, PROCESS_PRIORITY_NORMAL, PROCESS_PRIORITY_BELOW_NORMAL
)
from obs_controller import obs_controller
from localization import Loc

sys.path.append(os.path.join(BASE_DIR, "controller"))
from controller_manager import ControllerManager

try:
    import win32gui
    import win32process
    import win32con
    import win32api
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

from quick_switcher import QuickSwitcherUI
from game_card import GameCard
from process_manager import ProcessManager


class LauncherUI:
    def __init__(self, root, manager, controller_manager):
        self.manager = manager
        self.controller_manager = controller_manager
        self.root = root
        
        # Chemins absolus
        self.base_dir = BASE_DIR
        self.config_path = CONFIG_PATH
        self.assets_dir = os.path.join(self.base_dir, "assets", "images")
        self.metadata_path = os.path.join(self.base_dir, "games_metadata.json")
        self.games_metadata = {}
        self._load_metadata()

        # Charger la langue initiale
        forced_lang = None
        if "--lang" in sys.argv:
            idx = sys.argv.index("--lang")
            if idx + 1 < len(sys.argv):
                forced_lang = sys.argv[idx + 1]

        if forced_lang:
            Loc.set_lang(forced_lang)
        elif os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    lang = json.load(f).get("language", "fr")
                    Loc.set_lang(lang)
            except: pass

        self.root.title(Loc.get("title"))
        
        # Charger la géométrie de la fenêtre si elle existe
        self.root.geometry("850x800") # Par défaut
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    geom = json.load(f).get("main_window_geometry")
                    if geom: self.root.geometry(geom)
            except: pass

        self.root.resizable(True, True)
        self.root.configure(bg="#121212")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.poptracker_vars = {}
        self.poptracker_process = None
        self.poptracker_last_rect = None
        self.action_widgets = []
        self.gamepad_widgets = []
        self.game_images = {}
        self.game_images_disabled = {}
        self.auto_config_per_game = {}
        self.quick_switcher = QuickSwitcherUI(self, root)
        
        # Performance & State tracking
        self.is_optimizing_for_game = False
        self.controller_polling_interval = 30 # Augmenté de 200ms à 30ms pour plus de fluidité
        self.poptracker_vars = {}
        self.broadcast_vars = {}
        self.remaining_tracker_vars = {}
        self.remaining_tracker_enabled_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar()
        self.auto_config_var = tk.BooleanVar(value=True)
        self.auto_save_var = tk.BooleanVar(value=False)
        self.multi_game_keep_alive_var = tk.BooleanVar(value=False)
        self.broadcast_enabled_var = tk.BooleanVar(value=True)
        self.broadcast_mode_var = tk.StringVar(value="obs")
        self.broadcast_enable_overlay_var = tk.BooleanVar(value=True)
        self.broadcast_enable_obs_var = tk.BooleanVar(value=False)
        self.broadcast_show_locations_var = tk.BooleanVar(value=True)
        self.broadcast_disable_hw_accel_var = tk.BooleanVar(value=False)
        self.poptracker_display_index = 0
        
        # Activer l'écoute des manettes pour le Hub
        self.hub_btn = self.manager.hub_controller_open_btn # Initial value
        self.hub_keyboard_shortcut = "ctrl+shift+s"

        # Charger la config et les réglages
        self.manager.load_config()
        self.load_settings()
        self.controller_pressed_buttons = set()
        if self.controller_manager:
            self.controller_manager.raw_input_callback = self._handle_controller_input
        
        # Charger les images
        self.HAS_PIL = HAS_PIL # Expose HAS_PIL for GameCard
        self._load_game_images()
        
        # Hotkey global (Ctrl+Shift+S)
        if keyboard:
            try:
                keyboard.add_hotkey('ctrl+shift+s', self.root.after, args=(0, self.quick_switcher.show))
                keyboard.add_hotkey('ctrl+f2', self.root.after, args=(0, self.quick_switcher.show)) # Backup
                print(Loc.get("msg_shortcut_enabled"))
            except Exception as e:
                print(f"[Launcher] Error shortcut: {e}")
        else:
            messagebox.showwarning("Avertissement", Loc.get("msg_keyboard_missing"))

        # Style
        style = ttk.Style()
        style.theme_use('clam')


        # --- DESIGN SYSTEM ---
        self.colors = {
            "bg": "#0f0f12",
            "card_bg": "#16161a",
            "sidebar_bg": "#1a1a20",
            "accent": "#00ff99",
            "accent_dim": "#00a362",
            "text": "#ffffff",
            "text_dim": "#a0a0a0",
            "danger": "#ff4d4d",
            "border": "#2a2a32"
        }

        # Modern Button Style
        style.configure("TButton", 
            padding=(12, 6), 
            relief="flat", 
            background="#25252d", 
            foreground="white",
            font=("Segoe UI", 9, "bold")
        )
        style.map("TButton", 
            background=[('active', "#32323d"), ('disabled', "#1a1a1f")],
            foreground=[('disabled', "#555")]
        )
        
        # Modern Entry Style (for the port)
        style.configure("TEntry", fieldbackground="#1a1a1f", foreground="white", borderwidth=0)

        # Main Layout Root Config
        self.root.configure(bg=self.colors["bg"])

        # --- MAIN STRUCTURE (SIDEBAR + CONTENT) ---
        self.main_frame = tk.Frame(root, bg=self.colors["bg"])
        self.main_frame.pack(fill="both", expand=True)

        # 1. SIDEBAR (Fixed left)
        self.sidebar = tk.Frame(self.main_frame, bg=self.colors["sidebar_bg"], width=70)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        def create_side_btn(icon, cmd, tooltip=""):
            btn = tk.Button(
                self.sidebar, text=icon, font=("Segoe UI", 18), 
                bg=self.colors["sidebar_bg"], fg=self.colors["text_dim"],
                activebackground=self.colors["accent"], activeforeground="black",
                relief="flat", bd=0, cursor="hand2", command=cmd, pady=15
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e: btn.configure(fg=self.colors["accent"]))
            btn.bind("<Leave>", lambda e: btn.configure(fg=self.colors["text_dim"]))
            return btn

        self.btn_nav_ctrl = None # create_side_btn("🎮", self.open_controller_settings)
        self.btn_nav_settings = create_side_btn("⚙️", self.open_setup)
        
        # Initial Selection Style
        self._update_nav_styles(None)

        # Bottom Sidebar Exit
        self.btn_nav_exit = tk.Button(
            self.sidebar, text="✕", font=("Segoe UI", 14, "bold"), 
            bg=self.colors["sidebar_bg"], fg="#500",
            activebackground=self.colors["danger"], activeforeground="white",
            relief="flat", bd=0, cursor="hand2", command=self.on_closing, pady=15
        )
        self.btn_nav_exit.pack(side="bottom", fill="x")

        # 2. RIGHT CONTENT AREA
        self.content_area = tk.Frame(self.main_frame, bg=self.colors["bg"])
        self.content_area.pack(side="right", fill="both", expand=True)

        # 1. TOP BAR (Inside content area)
        self.top_bar = tk.Frame(self.content_area, bg=self.colors["sidebar_bg"], height=60, padx=20)
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)

        # Title/Logo in Top Bar
        title_font = ("Montserrat", 16, "bold") if "Montserrat" in tkfont.families() else ("Segoe UI", 16, "bold")
        self.label = tk.Label(self.top_bar, text="ZELDA HUB", font=title_font, bg=self.colors["sidebar_bg"], fg=self.colors["accent"], cursor="hand2")
        self.label.pack(side="left")
        self.label.bind("<Button-1>", lambda e: self.show_launcher_view())


        # Port & Quick Switcher on the right of Top Bar
        self.top_right_frame = tk.Frame(self.top_bar, bg=self.colors["sidebar_bg"])
        self.top_right_frame.pack(side="right")

        self.lbl_port = tk.Label(self.top_right_frame, text=Loc.get("port_label"), bg=self.colors["sidebar_bg"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_port.pack(side="left", padx=(10, 5))
        
        self.port_var = tk.StringVar()
        self.port_entry = tk.Entry(
            self.top_right_frame, textvariable=self.port_var, width=8, 
            bg="#121215", fg="white", borderwidth=0, 
            highlightthickness=1, highlightbackground=self.colors["border"], 
            insertbackground="white", font=("Consolas", 10)
        )
        self.port_entry.pack(side="left", padx=5, pady=15)
        self.action_widgets.append(self.port_entry)

        self.btn_port = ttk.Button(self.top_right_frame, text=Loc.get("ok_btn").upper(), width=4, command=self.update_port)
        self.btn_port.pack(side="left", padx=5)
        self.action_widgets.append(self.btn_port)

        self.btn_qs = ttk.Button(self.top_right_frame, text=Loc.get("quick_switcher_btn").upper(), command=self.quick_switcher.show)
        self.btn_qs.pack(side="left", padx=(15, 0))
        self.action_widgets.append(self.btn_qs)

        # Bouton Config du Quick Switcher
        self.btn_qs_setup = tk.Button(
            self.top_right_frame, text="⚙️", font=("Segoe UI", 10),
            bg=self.colors["sidebar_bg"], fg=self.colors["text_dim"],
            activebackground=self.colors["accent"], activeforeground="black",
            relief="flat", bd=0, cursor="hand2", 
            command=lambda: self.open_setup("general")
        )
        self.btn_qs_setup.pack(side="left", padx=(5, 0), pady=15)
        self.btn_qs_setup.bind("<Enter>", lambda e: self.btn_qs_setup.configure(fg=self.colors["accent"]))
        self.btn_qs_setup.bind("<Leave>", lambda e: self.btn_qs_setup.configure(fg=self.colors["text_dim"]))

        # 2. MAIN CONTENT (Scrollable Game Grid)
        self.container = tk.Frame(self.content_area, bg=self.colors["bg"])
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.container, bg=self.colors["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        
        self.game_frame = tk.Frame(self.canvas, bg=self.colors["bg"])
        self.game_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.game_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel support
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Grid responsiveness
        self.container.bind("<Configure>", self._on_container_configure)

        # 3. BOTTOM CONTROL PANEL (Inside content area)
        self.bottom_panel = tk.Frame(self.content_area, bg=self.colors["sidebar_bg"], padx=20, pady=10)
        self.bottom_panel.pack(side="bottom", fill="x")

        # Global Actions (Left) - Moved to sidebar
        self.actions_left = tk.Frame(self.bottom_panel, bg=self.colors["sidebar_bg"])
        self.actions_left.pack(side="left")

        # Toggles (Center)
        self.toggles_frame = tk.Frame(self.bottom_panel, bg=self.colors["sidebar_bg"])
        self.toggles_frame.pack(side="left", expand=True)

        checkbox_style = {
            "bg": self.colors["sidebar_bg"], 
            "fg": self.colors["text_dim"], 
            "selectcolor": "#000", 
            "activebackground": self.colors["sidebar_bg"], 
            "activeforeground": self.colors["accent"], 
            "font": ("Segoe UI", 8, "bold")
        }

        # self.auto_config_cb = tk.Checkbutton(self.toggles_frame, text="🎮 CONTROLLERS", variable=self.auto_config_var, **checkbox_style, command=self._on_auto_config_change)
        # self.auto_config_cb.pack(side="left", padx=10)
        # self.action_widgets.append(self.auto_config_cb)
        self.auto_config_cb = None

        self.auto_save_cb = tk.Checkbutton(self.toggles_frame, text=f"💾 {Loc.get('toggle_auto_save')}", variable=self.auto_save_var, **checkbox_style, command=self._on_auto_save_change)
        self.auto_save_cb.pack(side="left", padx=10)
        self.action_widgets.append(self.auto_save_cb)

        self.broadcast_enabled_cb = tk.Checkbutton(self.toggles_frame, text=f"📡 {Loc.get('toggle_broadcast')}", variable=self.broadcast_enabled_var, **checkbox_style, command=self._on_global_broadcast_change)
        self.broadcast_enabled_cb.pack(side="left", padx=10)
        self.action_widgets.append(self.broadcast_enabled_cb)

        self.multi_game_cb = tk.Checkbutton(self.toggles_frame, text=f"🔄 {Loc.get('toggle_hot_swap')}", variable=self.multi_game_keep_alive_var, **checkbox_style, command=self._on_hot_swap_change)
        self.multi_game_cb.pack(side="left", padx=10)
        self.action_widgets.append(self.multi_game_cb)

        # Quit Button (Right) - Highlighted with red
        self.stop_btn = tk.Button(
            self.bottom_panel, text=Loc.get("quit_game_btn").upper(), 
            command=self.stop_active_game, bg="#3d1515", fg="white", 
            activebackground="#5a1a1a", relief="flat", padx=20, pady=6,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self.stop_btn.pack(side="right", padx=5)
        self.action_widgets.append(self.stop_btn)

        # Status Bar / Toggles Extra
        self.status_bar = tk.Label(self.content_area, textvariable=self.status_var, bd=0, anchor=tk.W, bg="#0a0a0c", fg="#666", pady=4, padx=15, font=("Segoe UI", 8))
        self.status_bar.pack(side="bottom", fill="x")

        self.load_games()

        # Lancer le polling périodique des manettes
        self.poll_controllers()

    def _on_hot_swap_change(self):
        """Si on active le Hot-Swap, on désactive l'Auto-Save."""
        if self.multi_game_keep_alive_var.get():
            self.auto_save_var.set(False)
        self.save_settings()

    def _on_auto_save_change(self):
        """Si on active l'Auto-Save, on désactive le Hot-Swap."""
        if self.auto_save_var.get():
            self.multi_game_keep_alive_var.set(False)
        self.save_settings()

    def _on_global_broadcast_change(self):
        """Met à jour tous les jeux individuels pour correspondre au toggle global."""
        val = self.broadcast_enabled_var.get()
        for var in self.broadcast_vars.values():
            var.set(val)
        self.save_settings()
        self.load_games()

    def update_global_broadcast_state(self):
        """Met à jour le toggle global en fonction de l'état des toggles individuels."""
        if not self.broadcast_vars:
            return
        any_checked = any(var.get() for var in self.broadcast_vars.values())
        self.broadcast_enabled_var.set(any_checked)
        self.save_settings()

    def _update_nav_styles(self, active_btn):
        """Met à jour l'apparence des boutons de navigation pour montrer la page active."""
        nav_buttons = [b for b in [self.btn_nav_ctrl, self.btn_nav_settings] if b is not None]
        for btn in nav_buttons:
            if btn == active_btn:
                btn.configure(fg=self.colors["accent"], bg="#1d1d26")
            else:
                btn.configure(fg=self.colors["text_dim"], bg=self.colors["sidebar_bg"])

    def show_launcher_view(self):
        """Affiche la vue principale du Launcher."""
        self._update_nav_styles(None) # Reset highlight when in grid
        self.load_games()

    def _on_container_configure(self, event):
        """Déclenché lors d'un redimensionnement pour ajuster la grille."""
        # On utilise un timer pour éviter de recalculer trop souvent
        if hasattr(self, "_resize_timer"):
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(200, self.load_games)

    def _load_metadata(self):
        """Charge les métadonnées des jeux depuis le fichier JSON."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.games_metadata = {g["id"]: g for g in json.load(f).get("games", [])}
                print(f"[Launcher] Loaded metadata for {len(self.games_metadata)} games.")
            except Exception as e:
                print(f"[Launcher] Error loading metadata: {e}")

    def _load_game_images(self, size=(200, 200)):
        """Charge, crope en carré et teinte les images pour les cartes du launcher."""
        self.game_images = {}
        self.game_images_disabled = {}
        if not HAS_PIL:
            return
            
        # Créer le placeholder d'abord
        try:
            placeholder = Image.new('RGB', size, color='#333333')
            self.game_images["_default"] = ImageTk.PhotoImage(placeholder)
        except:
            print("[Launcher] Erreur lors de la création du placeholder.")
            return

        for game_id, meta in self.games_metadata.items():
            filename = meta.get("image")
            if not filename: continue
            
            path = os.path.join(self.assets_dir, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGBA")
                    
                    # 1. Square Crop (Center)
                    w, h = img.size
                    min_dim = min(w, h)
                    left = (w - min_dim) // 2
                    top = (h - min_dim) // 2
                    right = left + min_dim
                    bottom = top + min_dim
                    img = img.crop((left, top, right, bottom))
                    
                    # 2. Resize
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    
                    self.game_images[game_id] = ImageTk.PhotoImage(img)
                    
                    # 4. Create disabled version (grayscale + darkened)
                    disabled_img = img.convert("L").convert("RGBA")
                    enhancer = ImageEnhance.Brightness(disabled_img)
                    disabled_img = enhancer.enhance(0.4) # Darken substantially
                    self.game_images_disabled[game_id] = ImageTk.PhotoImage(disabled_img)
                    print(f"[Launcher] Loaded image for {game_id}")
                except Exception as e:
                    print(f"[Launcher] Erreur chargement image {game_id}: {e}")
            else:
                print(f"[Launcher] Asset missing for {game_id}: {filename}")

    def _find_python_with_webview(self):
        """Trouve un exécutable Python qui possède le module 'webview'."""
        # On teste d'abord l'exécutable actuel
        try:
            import webview
            return sys.executable
        except ImportError:
            pass
        
        # Sinon on teste les versions connues via le launcher 'py'
        for ver in ["3.12", "3.13", "3.7"]:
            try:
                cmd = ["py", f"-{ver}", "-c", "import webview"]
                if subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW) == 0:
                    return f"py -{ver}"
            except:
                pass
        
        # Fallback sur sys.executable en espérant que l'utilisateur l'installe
        return sys.executable

    def _get_poptracker_window_rect(self):
        """Récupère les coordonnées de la fenêtre PopTracker actuelle (indépendant du PID)."""
        if not HAS_PYWIN32:
            return None
        
        def enum_cb(hwnd, results):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    # On cherche une fenêtre qui contient PopTracker ou Zelda Hub - Web Tracker
                    if "PopTracker" in title or "Zelda Hub - Web Tracker" in title:
                        results.append(win32gui.GetWindowRect(hwnd))
            except: pass
        
        rects = []
        win32gui.EnumWindows(enum_cb, rects)
        return rects[0] if rects else None

    def _update_poptracker_settings_file(self, game_name=None, rect=None):
        """Met à jour le fichier de config de PopTracker (Position + Archipelago Settings)."""
        try:
            appdata = os.environ.get('APPDATA')
            if not appdata: return
            
            settings_path = os.path.join(appdata, "PopTracker", "PopTracker.json")
            if not os.path.exists(settings_path): return
            
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            dirty = False
            
            # 1. Position/Taille
            if rect:
                x, y, x2, y2 = rect
                w, h = x2 - x, y2 - y
                if "window" not in data: data["window"] = {}
                data["window"]["pos"] = [x, y]
                data["window"]["size"] = [w, h]
                data["window"]["display_pos"] = [x, y]
                dirty = True
            
            # 2. Synchronisation Archipelago
            if game_name:
                config_path = self.config_path
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as fcf:
                        cfg = json.load(fcf)
                    
                    slot = cfg.get("slot_names", {}).get(game_name, "")
                    host = cfg.get("archipelago_settings", {}).get("host", "archipelago.gg")
                    port = cfg.get("archipelago_settings", {}).get("port", "38281")
                    
                    # On ne met à jour PopTracker que si on a au moins un slot défini
                    if slot:
                        data["at_slot"] = slot
                        data["at_uri"] = f"{host}:{port}"
                        data["at_auto_connect"] = True 
                        dirty = True

            if dirty:
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                print(f"[Launcher] PopTracker.json synchronisé.")
        except Exception as e:
            print(f"[Launcher] Erreur lors de la mise à jour de PopTracker.json: {e}")

    def _restore_poptracker_window(self, new_process, rect):
        """Lance le script PowerShell pour maximiser PopTracker (Plus robuste)."""
        def run_maximizer():
            ps_script = os.path.join(self.base_dir, "maximize_poptracker.ps1")
            if os.path.exists(ps_script):
                print(f"[Launcher] Lancement du maximiseur PopTracker sur l'écran {self.poptracker_display_index}...")
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", f"& '{ps_script}' -MonitorIndex {self.poptracker_display_index}"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        
        threading.Thread(target=run_maximizer, daemon=True).start()

    def _center_broadcast_window(self):
        """Lance le script PowerShell pour centrer la fenêtre de Broadcast PopTracker."""
        def run_centerer():
            ps_script = os.path.join(self.base_dir, "center_broadcast.ps1")
            if os.path.exists(ps_script):
                print("[Launcher] Centrage de la fenêtre de Broadcast via PowerShell...")
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", f"& '{ps_script}'"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
        
        threading.Thread(target=run_centerer, daemon=True).start()

    def _update_keyboard_shortcuts(self):
        """Met à jour les raccourcis clavier globaux."""
        if not keyboard: return
        try:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception as e:
                print(f"[Launcher] Warning unhooking hotkeys: {e}")
            keyboard.add_hotkey(self.hub_keyboard_shortcut, self.root.after, args=(0, self.quick_switcher.toggle))
            # Backup
            keyboard.add_hotkey('ctrl+f2', self.root.after, args=(0, self.quick_switcher.toggle))
            print(f"[Launcher] Keyboard shortcuts updated: {self.hub_keyboard_shortcut}")
        except Exception as e:
            print(f"[Launcher] Error updating shortcuts: {e}")

    def _handle_controller_input(self, raw_event):
        """Intercepte les inputs manette pour les raccourcis du Hub (Support Combos)."""
        # Filtrage par nom de manette préférée (hub_controller_name)
        joy_id = raw_event.get("joy_id")
        if joy_id is not None and self.controller_manager:
            joy_info = self.controller_manager.detector.joysticks.get(joy_id)
            if joy_info:
                ctrl_name = joy_info.get("name")
                preferred_ctrl = getattr(self.manager, 'hub_controller_name', "")
                if preferred_ctrl and preferred_ctrl not in ["Toutes", "All", "All controllers", "Toutes les manettes"] and ctrl_name != preferred_ctrl:
                    # Ignore les inputs de cette manette
                    return False

        # Mise à jour de l'état des boutons pressés
        btn_id = raw_event.get("id")
        if not btn_id: return False
        
        state = raw_event.get("state", 0)
        
        # On track les boutons, le D-Pad et les pressions d'axes (Triggers)
        if raw_event["type"] in ["button", "hat"]:
            if state == 1 or (raw_event["type"] == "hat" and btn_id != "DPAD_RELEASE"):
                self.controller_pressed_buttons.add(btn_id)
            else:
                if btn_id == "DPAD_RELEASE":
                    # On nettoie toutes les directions si release
                    for d in ["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"]:
                        self.controller_pressed_buttons.discard(d)
                else:
                    self.controller_pressed_buttons.discard(btn_id)
        elif raw_event["type"] == "axis":
            if abs(state) > 0.8:
                self.controller_pressed_buttons.add(btn_id)
            else:
                self.controller_pressed_buttons.discard(btn_id)

        # 1. Si le Quick Switcher est ouvert, il est prioritaire sur les inputs
        if self.quick_switcher.overlay:
            if self.quick_switcher.handle_controller_input(raw_event):
                return True

        # 2. Raccourci Global pour toggle le Hub
        # Parsing du raccourci configuré (ex: "L3+R3" ou "CAPTURE")
        combo = [b.strip() for b in str(self.hub_btn).split("+")]
        
        # On vérifie si TOUS les boutons du combo sont actuellement pressés
        is_combo_pressed = all(b in self.controller_pressed_buttons for b in combo)
        
        if is_combo_pressed and state == 1:
            print(f"[Launcher] Controller combo detected ({self.hub_btn}). Toggling Quick Switcher.")
            self.root.after(0, self.quick_switcher.toggle)
            return True 

        return False

    def poll_controllers(self):
        """Met à jour l'état des manettes régulièrement."""
        if self.controller_manager:
            self.controller_manager.poll()
        self.root.after(self.controller_polling_interval, self.poll_controllers)

    def _on_auto_config_change(self):
        """Appelé quand on change l'auto-config globale."""
        self.save_settings()
        self._sync_gamepad_widgets()

    def _sync_gamepad_widgets(self):
        """Met à jour l'état visuel des icônes manette en fonction de l'auto-config globale."""
        is_global_on = self.auto_config_var.get()
        for cb in self.gamepad_widgets:
            if cb.winfo_exists():
                # On ne réactive que si le jeu est enregistré ET supporte l'auto-config
                is_reg = getattr(cb, "is_game_registered", True)
                is_supported = getattr(cb, "is_auto_config_supported", True)
                
                if not is_reg or not is_supported:
                    cb.configure(state=tk.DISABLED)
                else:
                    cb.configure(state=tk.NORMAL if is_global_on else tk.DISABLED)

    def _get_monitor_coords(self, index):
        """Récupère les coordonnées Top-Left d'un moniteur par son index."""
        if not HAS_PYWIN32:
            return 0, 0
            
        try:
            monitors = win32api.EnumDisplayMonitors()
            if index < len(monitors):
                rect = monitors[index][2] # (left, top, right, bottom)
                return rect[0], rect[1]
        except Exception as e:
            print(f"[Launcher] Error getting monitor coords: {e}")
        return 0, 0

    def _set_ui_state(self, state):
        """Active ou désactive tous les widgets inscrits dans action_widgets."""
        for widget in self.action_widgets:
            try:
                if state == tk.NORMAL:
                    # Ne réactiver que ce qui est légitime
                    is_reg = getattr(widget, "is_game_registered", True)
                    if not is_reg:
                        widget.configure(state=tk.DISABLED)
                    else:
                        widget.configure(state=tk.NORMAL)
                else:
                    widget.configure(state=state)
            except:
                pass
        
        # Resynchroniser les icônes de manette (qui dépendent aussi du toggle global)
        if state == tk.NORMAL:
            self._sync_gamepad_widgets()

    def create_game_btn(self, name, code, row=0, col=0):
        # Utiliser la classe GameCard externalisée
        GameCard(self, name, code, row, col)

    def launch_game(self, name):
        """Lance un jeu dans un thread avec un petit delai (Suggestion utilisateur)."""
        if name not in self.manager.games:
            print(f"[Launcher] Action ignorée: {name} n'est pas enregistré.")
            return

        # --- NOUVEAU: Synchroniser les options avec le manager avant le lancement ---
        if self.manager.active_game_name and self.manager.active_game_name != name:
            self.manager.auto_savestate_enabled = self.auto_save_var.get()
            self.manager.multi_game_keep_alive = self.multi_game_keep_alive_var.get()

        self._set_ui_state(tk.DISABLED)
        self.status_var.set(Loc.get("status_launching", name=name))
        self.root.update()
        
        # 1. AUTOMATION MANETTE DESACTIVEE (Selon la consigne utilisateur)
        print(f"[Launcher] Configuration automatique des profils manettes pour épurateurs désactivée (manuel préféré) pour {name}.")

        # 2. RUN LOGIC IN THREAD WITH DELAY
        def _threaded_launch():
            # Trigger OBS Scene Switch
            obs_controller.switch_scene(name)
            
            # Détection initiale
            is_bizhawk_ap = "ArchipelagoBizHawkController" in str(type(self.manager.games.get(name)))
            selected_variant = self.manager.poptracker_variants.get(name, "")
            is_ap_mode = self.manager.is_ap_mode(name, selected_variant) or is_bizhawk_ap
            print(f"[Launcher] Mode AP détecté pour {name} : {is_ap_mode}")

            # --- 0. LANCEMENT POPTRACKER (Si activé) ---
            if name in self.poptracker_vars and self.poptracker_vars[name].get():
                try:
                    pack_path = self.manager.poptracker_packs.get(name, "")
                    is_web = pack_path.startswith("http")
                    
                    if not pack_path or not os.path.exists(pack_path):
                        print(f"[Launcher] Warning: Tracker pack path for {name} is empty or does not exist: '{pack_path}'")

                    # 2. Fermer l'ancien s'il existe
                    if self.poptracker_process and self.poptracker_process.poll() is None:
                        print("[Launcher] Fermeture de l'ancien tracker...")
                        ProcessManager.kill_process_tree(self.poptracker_process.pid)
                        time.sleep(0.5)

                    # Détection si c'est un tracker WEB (URL ou Dossier contenant un index.html ou dist)
                    is_web_folder = os.path.isdir(pack_path) and (os.path.exists(os.path.join(pack_path, "index.html")) or os.path.exists(os.path.join(pack_path, "dist")) or os.path.exists(os.path.join(pack_path, "build")))
                    
                    # Détection si c'est un tracker PYTHON (Magpie / LADX)
                    is_python_tracker = os.path.isdir(pack_path) and os.path.exists(os.path.join(pack_path, "scripts", "startLocal.bat"))

                    print(f"[Launcher] Pack detection for {name}: is_web={is_web}, is_web_folder={is_web_folder}, is_python={is_python_tracker}")

                    if is_web or is_web_folder:
                        print(f"[Launcher] Lancement du tracker WEB : {pack_path}")
                        python_exe = self._find_python_with_webview()
                        host_script = os.path.join(self.base_dir, "web_tracker_host.py")
                        
                        # Commande de base
                        cmd = (python_exe.split() if "py -" in python_exe else [python_exe]) + [host_script, pack_path]

                        # 1. Géométrie (x, y, w, h)
                        x, y = self._get_monitor_coords(self.poptracker_display_index)
                        print(f"[Launcher] Coordonnées moniteur {self.poptracker_display_index} : {x}, {y}")
                        cmd.extend([str(x), str(y), "1280", "720"])
                        
                        # 2. Paramètres Archipelago
                        host = self.manager.archipelago_settings.get("host", "archipelago.gg")
                        port = self.manager.archipelago_settings.get("port", "38281")
                        slot = self.manager.slot_names.get(name, "Link")
                        pwd = self.manager.archipelago_settings.get("password", "None") or "None"
                        cmd.extend([str(host), str(port), str(slot), str(pwd)])

                        self.poptracker_process = subprocess.Popen(cmd, cwd=os.path.dirname(__file__), creationflags=subprocess.CREATE_NO_WINDOW)
                        
                        # Maximisation si demandée dans le setup
                        do_maximize = True
                        try:
                            with open(self.config_path, "r", encoding="utf-8") as f:
                                do_maximize = json.load(f).get("maximize_poptracker", True)
                        except: pass

                        if do_maximize:
                            self._restore_poptracker_window(self.poptracker_process, self.poptracker_last_rect)
                    elif is_python_tracker:
                        print(f"[Launcher] Lancement du tracker PYTHON (LADX) : {pack_path}")
                        bat_path = os.path.join(pack_path, "scripts", "startLocal.bat")
                        scripts_dir = os.path.join(pack_path, "scripts")
                        
                        # Paramètres Archipelago
                        host = self.manager.archipelago_settings.get("host", "archipelago.gg")
                        port = self.manager.archipelago_settings.get("port", "38281")
                        slot = self.manager.slot_names.get(name, "Link")
                        
                        # On utilise l'environnement propre
                        env = os.environ.copy()
                        for k in list(env.keys()):
                            if k.startswith("SDL_"): del env[k]

                        # On lance le .bat directement SANS powershell Start-Process pour garder le handle PID
                        # CREATE_NO_WINDOW permet de cacher la console CMD
                        self.poptracker_process = subprocess.Popen(
                            [bat_path, "--screen", str(self.poptracker_display_index), "--ap-server", f"{host}:{port}", "--ap-slot", slot],
                            cwd=scripts_dir,
                            env=env,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )

                        # Maximisation si demandée dans le setup
                        do_maximize = True
                        try:
                            with open(self.config_path, "r", encoding="utf-8") as f:
                                do_maximize = json.load(f).get("maximize_poptracker", True)
                        except: pass

                        if do_maximize:
                            self._restore_poptracker_window(self.poptracker_process, self.poptracker_last_rect)
                    else:
                        pop_path = self.manager.poptracker_path
                        if not pop_path or not os.path.exists(pop_path):
                            # Tentative de fallback dans le dossier App (local ou parent)
                            potential_app_dirs = [
                                os.path.join(get_exe_dir(), "..", "App"),
                                os.path.join(get_exe_dir(), "App")
                            ]
                            for app_dir in potential_app_dirs:
                                pop_fallback = os.path.join(app_dir, "Poptracker", "poptracker.exe")
                                auto_fallback = os.path.join(app_dir, "autotrack", "autotrack.exe")
                                if os.path.exists(pop_fallback):
                                    pop_path = pop_fallback
                                    break
                                elif os.path.exists(auto_fallback):
                                    pop_path = auto_fallback
                                    break

                        if pop_path and os.path.exists(pop_path):
                            print(f"[Launcher] Lancement de PopTracker pour {name}...")
                            variant = self.manager.poptracker_variants.get(name, "")
                            cmd = [pop_path]
                            if variant:
                                cmd.extend(["--pack-variant", variant])
                            
                            # --- New: Auto-Connect and Broadcast Commands ---
                            if is_ap_mode or name == "OOT (SOH)":
                                host = self.manager.archipelago_settings.get("host", "archipelago.gg")
                                port = self.manager.archipelago_settings.get("port", "38281")
                                if host and port:
                                    cmd.extend(["--ap-uri", f"{host}:{port}"])
                                
                                slot = self.manager.slot_names.get(name, "")
                                if slot:
                                    cmd.extend(["--ap-slot", slot])
                                
                                password = self.manager.archipelago_settings.get("password", "")
                                if password:
                                    cmd.extend(["--ap-password", password])

                            if self.manager.poptracker_broadcast:
                                cmd.append("--broadcast-transparent")

                            if pack_path and os.path.exists(pack_path):
                                cmd.append(pack_path)
                            
                            env = os.environ.copy()
                            for k in list(env.keys()):
                                if k.startswith("SDL_"): del env[k]
                            
                            # Synchronisation des infos de connexion (Position désactivée car pose problème)
                            self._update_poptracker_settings_file(game_name=name, rect=None)

                            print(f"[Launcher] Commande PopTracker : {' '.join(cmd)}")
                            self.poptracker_process = subprocess.Popen(cmd, cwd=os.path.dirname(pop_path), env=env)
                            
                            if self.manager.poptracker_broadcast:
                                self._center_broadcast_window()
                            

                            # Maximisation si demandée dans le setup
                            do_maximize = True
                            try:
                                with open(self.config_path, "r", encoding="utf-8") as f:
                                    do_maximize = json.load(f).get("maximize_poptracker", True)
                            except: pass

                            if do_maximize:
                                self._restore_poptracker_window(self.poptracker_process, self.poptracker_last_rect)
                        else:
                            print(f"[Launcher] PopTracker activé mais chemin invalide : {pop_path}")
                except Exception as e:
                    print(f"[Launcher] Erreur lors du lancement du tracker : {e}")

            time.sleep(0.1) # Réduit de 0.5s à 0.1s pour un lancement plus rapide
            
            # --- 2. LANCEMENT DU JEU ---
            success = self.manager.start_game(name)
            
            if success:
                print(f"[Launcher] {name} success.")
                self.root.after(0, lambda: self.status_var.set(Loc.get("status_playing", name=name)))
                self.root.after(0, lambda: self._set_ui_state(tk.NORMAL)) # Dégriser l'UI dès que le lancement est validé
                
                # --- NOUVEAU: REFOCUS DU TRACKER (PopTracker / Web Tracker) ---
                if name in self.poptracker_vars and self.poptracker_vars[name].get():
                    do_maximize = True
                    try:
                        with open(self.config_path, "r", encoding="utf-8") as f:
                            do_maximize = json.load(f).get("maximize_poptracker", True)
                    except: pass
                    
                    if do_maximize:
                        print(f"[Launcher] Refocusing tracker for {name}...")
                        self._restore_poptracker_window(self.poptracker_process, self.poptracker_last_rect)
                
                game_ctrl = self.manager.games.get(name)

                # --- 2.5 LANCEMENT BROADCAST APP (Automatique si dispo) ---
                broadcast_dir = ""
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        broadcast_dir = json.load(f).get("emulators", {}).get("broadcast", "")
                except:
                    pass
                
                if broadcast_dir:
                    broadcast_dir = resolve_path(broadcast_dir)
                
                # Fallback pour le Broadcast App si le chemin est vide ou invalide
                if not broadcast_dir or not os.path.exists(os.path.join(broadcast_dir, "start_cli.py")):
                    potential_app_dirs = [
                        os.path.join(get_exe_dir(), "..", "App"),
                        os.path.join(get_exe_dir(), "App")
                    ]
                    for app_dir in potential_app_dirs:
                        # On teste plusieurs noms possibles
                        broadcast_fallback = os.path.join(app_dir, "BroadCast-Archipelago")
                        broadcast_fallback_alt = os.path.join(app_dir, "uibroadcast")
                        
                        if os.path.exists(os.path.join(broadcast_fallback, "start_cli.py")):
                            broadcast_dir = broadcast_fallback
                            break
                        elif os.path.exists(os.path.join(broadcast_fallback_alt, "start_cli.py")):
                            broadcast_dir = broadcast_fallback_alt
                            break
                
                is_broad = self.broadcast_vars.get(name).get() if (name in self.broadcast_vars) else True
                if self.broadcast_enabled_var.get() and is_broad and broadcast_dir and os.path.exists(os.path.join(broadcast_dir, "start_cli.py")):
                    # --- NOUVEAU: Verifier si un broadcast tourne déjà (Support Mode Multi-Jeu / Hot Swap) ---
                    is_b_alive = False
                    
                    # 1. Vérification système via psutil (Nécessaire pour le mode Keep Alive / Hot Swap)
                    try:
                        for proc in psutil.process_iter(['cmdline']):
                            try:
                                cmdline = proc.info.get('cmdline')
                                if cmdline and any("start_cli.py" in str(arg) for arg in cmdline):
                                    print(f"[Launcher] Broadcast Overlay détecté déjà opérationnel sur le système. Réutilisation (Mode Hot Swap).")
                                    is_b_alive = True
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                continue
                    except Exception as e:
                        print(f"[Launcher] Erreur lors du scan psutil pour le broadcast: {e}")

                    # 2. Fallback: Vérification dans les processus suivis du contrôleur actuel (si pas déjà trouvé)
                    if not is_b_alive and game_ctrl:
                        for p in game_ctrl.extra_processes:
                            try:
                                if p.poll() is None and any("start_cli.py" in str(arg) for arg in getattr(p, "args", [])):
                                    print(f"[Launcher] UI Broadcast déjà actif pour {name}. On ne le relance pas.")
                                    is_b_alive = True
                                    break
                            except: pass
                    
                    if not is_b_alive:
                        b_host = self.manager.archipelago_settings.get("host", "archipelago.gg")
                        b_port = self.manager.archipelago_settings.get("port", "")
                        b_slot = self.manager.slot_names.get(name, "")
                        b_pwd = self.manager.archipelago_settings.get("password", "")
                        
                        if not b_port or not b_slot:
                            print(f"[Launcher] [ATTENTION] Le Broadcast pour '{name}' n'est pas lancé car le 'Slot Name' ou le 'Port' Archipelago n'est pas configuré dans l'onglet Configuration du Hub.")
                        else:
                            # Trouver un interprète Python valide externe quand on est compilé (frozen)
                            python_exe_list = ["py", "-3.12"]
                            if getattr(sys, 'frozen', False):
                                for interp in [["py", "-3.12"], ["py", "-3.14"], ["python"], ["py"]]:
                                    try:
                                        if subprocess.call(interp + ["-c", "pass"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW) == 0:
                                            python_exe_list = interp
                                            break
                                    except: pass
                            else:
                                python_exe_list = [sys.executable]

                            mode = self.broadcast_mode_var.get()
                            
                            # Synchroniser les réglages du Hub avec le fichier de configuration du Broadcast
                            try:
                                b_settings_path = os.path.join(broadcast_dir, "broadcast_settings.json")
                                b_settings = {}
                                if os.path.exists(b_settings_path):
                                    with open(b_settings_path, "r", encoding="utf-8") as bf:
                                        b_settings = json.load(bf)
                                
                                b_settings["server"] = f"{b_host}:{b_port}"
                                b_settings["slot"] = b_slot
                                b_settings["password"] = b_pwd
                                b_settings["enable_overlay"] = self.broadcast_enable_overlay_var.get()
                                b_settings["enable_obs"] = self.broadcast_enable_obs_var.get()
                                b_settings["show_locations"] = self.broadcast_show_locations_var.get()
                                b_settings["disable_hw_accel"] = self.broadcast_disable_hw_accel_var.get()
                                b_settings["sync_mode"] = "all" if mode == "obs" else mode
                                
                                with open(b_settings_path, "w", encoding="utf-8") as bf:
                                    json.dump(b_settings, bf, indent=4)
                                print(f"[Launcher] Config du Broadcast synchronisée avec succès.")
                            except Exception as e:
                                print(f"[Launcher] Erreur de synchronisation du Broadcast : {e}")

                            b_cmd = python_exe_list + [
                                "start_cli.py",
                                "--server", f"{b_host}:{b_port}",
                                "--slot", b_slot
                            ]
                            
                            if self.broadcast_enable_overlay_var.get():
                                b_cmd.append("--overlay")
                            else:
                                b_cmd.append("--no-overlay")
                                
                            if self.broadcast_enable_obs_var.get():
                                b_cmd.append("--obs")
                            else:
                                b_cmd.append("--no-obs")
                                
                            if mode != "obs":
                                b_cmd.extend(["--mode", mode])
                                
                            if b_pwd:
                                b_cmd.extend(["--password", b_pwd])
                                
                            print(f"[Launcher] Starting broadcast overlay: {' '.join(b_cmd)}")
                            try:
                                broadcast_p = subprocess.Popen(
                                    b_cmd, 
                                    cwd=broadcast_dir, 
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                if game_ctrl:
                                    game_ctrl.extra_processes.append(broadcast_p)
                            except Exception as e:
                                print(f"[Launcher] Error starting broadcast overlay: {e}")

                # --- 2.75 LANCEMENT REMAINING ITEMS TRACKER (AP Mini Tracker) ---
                has_rem_enabled = name in self.remaining_tracker_vars and self.remaining_tracker_vars[name].get()
                if self.remaining_tracker_enabled_var.get() and has_rem_enabled and self.manager.remaining_tracker_path:
                    rt_path = self.manager.remaining_tracker_path
                    if os.path.exists(rt_path):
                        rt_host = self.manager.archipelago_settings.get("host", "archipelago.gg")
                        rt_port = self.manager.archipelago_settings.get("port", "38281")
                        rt_slot = self.manager.slot_names.get(name, "")
                        rt_pwd = self.manager.archipelago_settings.get("password", "")
                        
                        if rt_slot and rt_port:
                            rt_cmd = [
                                rt_path,
                                "--gui",
                                "--server", f"{rt_host}:{rt_port}",
                                "--slot", rt_slot,
                                "--game", name
                            ]
                            if rt_pwd:
                                rt_cmd.extend(["--password", rt_pwd])
                                
                            print(f"[Launcher] Starting remaining items tracker: {' '.join(rt_cmd)}")
                            try:
                                env = os.environ.copy()
                                env["KIVY_NO_ARGS"] = "1"
                                env["KIVY_GRAPHICS_WINDOW_STATE"] = "hidden"
                                env["KIVY_GRAPHICS_HIDDEN"] = "1"
                                
                                rt_proc = subprocess.Popen(
                                    rt_cmd,
                                    cwd=os.path.dirname(rt_path),
                                    env=env,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                if game_ctrl:
                                    game_ctrl.extra_processes.append(rt_proc)
                            except Exception as e:
                                print(f"[Launcher] Error starting remaining items tracker: {e}")

                # --- 3. LANCEMENT CLIENT ARCHIPELAGO (Après démarrage jeu pour éviter cleanup) ---
                meta = self.games_metadata.get(name, {})
                client_name = meta.get("client_name")
                is_native = meta.get("is_native", False)
                # On ne lance pas le client AP pour les jeux natifs (SoH, MM native) car ils gèrent souvent leur propre connexion
                if not is_native and (is_ap_mode or client_name) and (not is_bizhawk_ap or name in ["Link's Awakening DX", "Link's Awakening DX Beta"]):
                    target_client = client_name or f"{name} Client"
                    client_p = self._launch_archipelago_client(name, target_client)
                    if client_p:
                        game_ctrl = self.manager.games.get(name)
                        if game_ctrl:
                            game_ctrl.extra_processes.append(client_p)

                    # --- AUTOMATISATION CONNEXION ---
                    target_title = meta.get("client_title", f"Archipelago {name} Client*")
                    def _run_connect():
                        conn_p = self._connect_archipelago(name, target_title)
                        if conn_p:
                            game_ctrl = self.manager.games.get(name)
                            if game_ctrl:
                                game_ctrl.extra_processes.append(conn_p)

                    threading.Thread(target=_run_connect, daemon=True).start()
                
                # Monitor end
                game_ctrl = self.manager.games.get(name)
                if game_ctrl and game_ctrl.process:
                    print(f"[Launcher] En attente de la fermeture de {name} (PID: {game_ctrl.process.pid})...")
                    
                    # --- PERFORMANCE OPTIMIZATION: Hub Side ---
                    print("[Optimization] Reducing Hub priority and polling rate...")
                    set_current_process_priority(PROCESS_PRIORITY_BELOW_NORMAL)
                    self.controller_polling_interval = 1000 # Slow down polling to once per second
                    self.is_optimizing_for_game = True
                    
                    # Minimize Hub to save GPU/CPU redraws
                    self.root.after(0, self.root.iconify)
                    
                    self.root.after(0, lambda: self._set_ui_state(tk.NORMAL))
                    game_ctrl.process.wait()
                    print(f"[Launcher] {name} s'est ferme. Nettoyage des processus associés...")
                    game_ctrl.stop() # Ferme automatiquement le broadcast et les clients AP
                    obs_controller.switch_to_loading_scene()
                    
                    # --- RESTORE PERFORMANCE ---
                    print("[Optimization] Restoring Hub priority and polling rate...")
                    set_current_process_priority(PROCESS_PRIORITY_NORMAL)
                    self.controller_polling_interval = 30 # Maintenu à 30ms
                    self.is_optimizing_for_game = False
                    # On ne restaure pas la fenêtre automatiquement, on laisse l'utilisateur le faire
                    # pour éviter de voler le focus s'il est occupé ailleurs après le jeu.
                
                self.manager.active_game_name = None
                self.root.after(0, lambda: self.status_var.set("Ready"))
            else:
                print(f"[Launcher] failed {name}.")
                self.root.after(0, lambda: self._set_ui_state(tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set(Loc.get("status_failed", name=name)))

        threading.Thread(target=_threaded_launch, daemon=True).start()

    def stop_active_game(self):
        """Arrête manuellement le jeu, le tracker et les clients en cours."""
        # 1. Fermer PopTracker / Magpie si ouvert (Même si le jeu s'est déjà arrêté de lui-même)
        if hasattr(self, 'poptracker_process') and self.poptracker_process and self.poptracker_process.poll() is None:
            print("[Launcher] Fermeture de PopTracker/Magpie...")
            ProcessManager.kill_process_tree(self.poptracker_process.pid)
            self.poptracker_process = None

        if self.manager.active_game_name:
            name = self.manager.active_game_name
            self.status_var.set(Loc.get("status_stopping", name=name))
            self.root.update()
            
            # 2. Récupérer le contrôleur et appeler stop() (qui est maintenant gracieux)
            game_ctrl = self.manager.games.get(name)
            if game_ctrl:
                if self.auto_save_var.get():
                    print(f"[Launcher] Auto-saving {name} before stop...")
                    game_ctrl.save_state(slot=10)
                    time.sleep(0.5) # Réduit car DolphinController attend déjà la fin de l'écriture
                
                game_ctrl.stop()
                obs_controller.switch_to_loading_scene()
            
            self.manager.active_game_name = None
            self.status_var.set("Ready")
            print(f"[Launcher] Jeu '{name}' arrêté manuellement.")
        else:
            # Si on arrive ici via le Hub sans jeu actif (mais avec tracker), on ne montre pas de box d'info
            # pour ne pas être intrusif à la fermeture du Hub.
            pass

    def open_controller_settings(self):
        self.status_var.set("Gestion des manettes...")
        self.root.update()
        
        # Bloquer la fenêtre principale
        self.root.attributes('-disabled', True)
        
        def run_controller():
            # Ouvre `ui_controller.py` (chemin absolu) et attend
            ui_path = os.path.join(self.base_dir, "ui_controller.py")
            subprocess.run([sys.executable, ui_path], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Une fois fermé, on débloque
            print("[Launcher] Retour de la gestion des manettes. Reloading config...")
            self.root.after(0, self.finish_setup)
            
        threading.Thread(target=run_controller, daemon=True).start()

    def open_setup(self, page="emus"):
        self.status_var.set("Configuration en cours...")
        self.root.update()
        
        # Bloquer la fenêtre principale pour empêcher toute interaction
        self.root.attributes('-disabled', True)
        
        def run_setup():
            # Ouvre `ui_setup.py` (chemin absolu) avec la page demandée et attend
            setup_path = os.path.join(self.base_dir, "ui_setup.py")
            subprocess.run([sys.executable, setup_path, "--page", page], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Une fois fermé, on débloque
            print(f"[Launcher] Retour du setup ({page}). Reloading config...")
            self.root.after(0, self.finish_setup)
            
        threading.Thread(target=run_setup, daemon=True).start()
        
    def finish_setup(self):
        # Débloquer la fenêtre principale
        self.root.attributes('-disabled', False)
        
        # Astuce Windows pour forcer la fenêtre en plein milieu de l'écran par dessus tout le reste
        self.root.attributes('-topmost', True)
        self.root.update()
        self.root.attributes('-topmost', False)
        
        self.root.lift()
        self.root.focus_force()
        self.load_settings() # NOUVEAU: Recharger les paramètres (Hub btn, auto-config)
        self.load_games()
        obs_controller.load_config() # Reload OBS settings
        
        if not self.manager.active_game_name:
            self.status_var.set(Loc.get("status_ready"))
        else:
            self.status_var.set(Loc.get("status_playing", name=self.manager.active_game_name))

    def update_port(self):
        new_port = self.port_var.get().strip()
        if not new_port: return
        
        try:
            # Charger config, modifier port, sauvegarder
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                if "archipelago_settings" not in config:
                    config["archipelago_settings"] = {}
                config["archipelago_settings"]["port"] = new_port
                
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                
                # Recharger le manager pour mettre à jour les controllers
                self.manager.load_config()
                self.status_var.set(f"Port mis à jour: {new_port}")
                print(f"[Launcher] Port Archipelago mis à jour : {new_port}")
        except Exception as e:
            print(f"Erreur lors de l'update du port : {e}")
            messagebox.showerror("Erreur", f"Impossible de mettre à jour le port : {e}")

    def load_settings(self):
        """Charge les paramètres généraux comme l'auto-config."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.auto_config_var.set(config.get("auto_controller_config", True))
                self.auto_save_var.set(config.get("auto_savestate_enabled", False))
                self.multi_game_keep_alive_var.set(config.get("multi_game_keep_alive", False))
                self.broadcast_enabled_var.set(config.get("auto_broadcast_enabled", True))
                self.broadcast_mode_var.set(config.get("broadcast_mode", "obs"))
                self.broadcast_enable_overlay_var.set(config.get("broadcast_enable_overlay", True))
                self.broadcast_enable_obs_var.set(config.get("broadcast_enable_obs", False))
                self.broadcast_show_locations_var.set(config.get("broadcast_show_locations", True))
                self.broadcast_disable_hw_accel_var.set(config.get("broadcast_disable_hw_accel", False))
                self.poptracker_last_rect = config.get("poptracker_last_rect")
                self.poptracker_display_index = int(config.get("poptracker_display_index", 0))
                self.remaining_tracker_enabled_var.set(config.get("remaining_tracker_enabled", False))
                
                # Charger l'état Remaining Tracker pour chaque jeu
                rem_map = config.get("remaining_tracker_enabled_games", {})
                for g_name, var in self.remaining_tracker_vars.items():
                    if g_name in rem_map:
                        var.set(rem_map[g_name])
                
                # Charger l'état PopTracker pour chaque jeu
                enabled_map = config.get("poptracker_enabled", {})
                for g_name, var in self.poptracker_vars.items():
                    if g_name in enabled_map:
                        var.set(enabled_map[g_name])

                # Charger l'état Broadcast pour chaque jeu
                broadcast_map = config.get("broadcast_enabled_games", {})
                for g_name, var in self.broadcast_vars.items():
                    if g_name in broadcast_map:
                        var.set(broadcast_map[g_name])

                # Charger l'état Auto-Pad pour chaque jeu
                auto_pad_map = config.get("auto_controller_per_game", {})
                for g_name, var in self.auto_config_per_game.items():
                    if g_name in auto_pad_map:
                        var.set(auto_pad_map[g_name])
                
                # NOUVEAU: Synchroniser le bouton Hub et le manager
                self.manager.load_config()
                self.hub_btn = self.manager.hub_controller_open_btn
                
                # NOUVEAU: Mettre à jour les raccourcis clavier
                old_kb = self.hub_keyboard_shortcut
                self.hub_keyboard_shortcut = config.get("hub_keyboard_shortcut", "ctrl+shift+s")
                if old_kb != self.hub_keyboard_shortcut or not hasattr(self, '_shortcuts_init_done'):
                    self._update_keyboard_shortcuts()
                    self._shortcuts_init_done = True

                # NOUVEAU: Mettre à jour la langue dynamiquement
                new_lang = config.get("language", "fr")
                Loc.set_lang(new_lang)
                self.root.title(Loc.get("title"))
                if getattr(self, 'label', None):
                    self.label.configure(text=Loc.get("header_title"))
                if getattr(self, 'sub_label', None):
                    self.sub_label.configure(text=Loc.get("header_subtitle"))
                
                # NOUVEAU: Mettre à jour tous les textes de l'UI principale
                # NOUVEAU: Mettre à jour tous les textes de l'UI principale
                if getattr(self, 'lbl_port', None): self.lbl_port.configure(text=Loc.get("port_label"))
                if getattr(self, 'btn_port', None): self.btn_port.configure(text=Loc.get("ok_btn"))
                if getattr(self, 'btn_qs', None): self.btn_qs.configure(text=Loc.get("quick_switcher_btn"))
                if getattr(self, 'stop_btn', None): self.stop_btn.configure(text=Loc.get("quit_game_btn"))
                if getattr(self, 'auto_config_cb', None): self.auto_config_cb.configure(text=Loc.get("auto_config_label"))
                if getattr(self, 'auto_save_cb', None): 
                    self.auto_save_cb.configure(text=f"💾 {Loc.get('toggle_auto_save')}")
                if getattr(self, 'multi_game_cb', None): 
                    self.multi_game_cb.configure(text=f"🔄 {Loc.get('toggle_hot_swap')}")
                if getattr(self, 'broadcast_enabled_cb', None): 
                    self.broadcast_enabled_cb.configure(text=f"📡 {Loc.get('toggle_broadcast')}")
                
                print(f"[Launcher] Settings reloaded. Language: {new_lang}, Hub button: {self.hub_btn}")
            except Exception as e:
                print(f"Erreur lors du chargement des paramètres : {e}")

    def save_settings(self):
        """Sauvegarde les paramètres généraux comme l'auto-config."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                config["auto_controller_config"] = self.auto_config_var.get()
                config["auto_savestate_enabled"] = self.auto_save_var.get()
                self.manager.auto_savestate_enabled = self.auto_save_var.get()  # Sync memory
                config["multi_game_keep_alive"] = self.multi_game_keep_alive_var.get()
                self.manager.multi_game_keep_alive = self.multi_game_keep_alive_var.get() # Sync memory
                config["auto_broadcast_enabled"] = self.broadcast_enabled_var.get()
                config["broadcast_mode"] = self.broadcast_mode_var.get()
                config["broadcast_enable_overlay"] = self.broadcast_enable_overlay_var.get()
                config["broadcast_enable_obs"] = self.broadcast_enable_obs_var.get()
                config["broadcast_show_locations"] = self.broadcast_show_locations_var.get()
                config["broadcast_disable_hw_accel"] = self.broadcast_disable_hw_accel_var.get()
                config["poptracker_last_rect"] = self.poptracker_last_rect
                config["poptracker_display_index"] = self.poptracker_display_index
                config["remaining_tracker_enabled"] = self.remaining_tracker_enabled_var.get()
                self.manager.remaining_tracker_enabled = self.remaining_tracker_enabled_var.get()
                
                # Sauvegarder l'état Remaining Tracker par jeu
                if "remaining_tracker_enabled_games" not in config:
                    config["remaining_tracker_enabled_games"] = {}
                for g_name, var in self.remaining_tracker_vars.items():
                    config["remaining_tracker_enabled_games"][g_name] = var.get()
                
                # Sauvegarder l'état PopTracker
                if "poptracker_enabled" not in config:
                    config["poptracker_enabled"] = {}
                for g_name, var in self.poptracker_vars.items():
                    config["poptracker_enabled"][g_name] = var.get()

                # Sauvegarder l'état Broadcast par jeu
                if "broadcast_enabled_games" not in config:
                    config["broadcast_enabled_games"] = {}
                for g_name, var in self.broadcast_vars.items():
                    config["broadcast_enabled_games"][g_name] = var.get()

                # Sauvegarder l'état Auto-Pad par jeu
                if "auto_controller_per_game" not in config:
                    config["auto_controller_per_game"] = {}
                for g_name, var in self.auto_config_per_game.items():
                    config["auto_controller_per_game"][g_name] = var.get()
                
                 # S'assurer que le raccourci Hub est préservé même si on sauve depuis ici
                if hasattr(self.manager, 'hub_controller_open_btn'):
                    config["hub_controller_open_btn"] = self.manager.hub_controller_open_btn
                    print(f"[Launcher] Syncing Hub button to config: {self.manager.hub_controller_open_btn}")
                
                if hasattr(self.manager, 'hub_controller_name'):
                    config["hub_controller_name"] = self.manager.hub_controller_name
                    print(f"[Launcher] Syncing Hub controller name to config: {self.manager.hub_controller_name}")

                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                print(f"[Launcher] Paramètres sauvegardés.")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde des paramètres : {e}")

    def load_games(self):
        # Clear existing buttons
        # Nettoyage de la liste des widgets : on ne garde que ceux qui existent encore
        # et qui ne sont pas des enfants de game_frame (car ils vont être détruits)
        self.action_widgets = [w for w in self.action_widgets if w and w.winfo_exists() and not str(w).startswith(str(self.game_frame))]

        for widget in self.game_frame.winfo_children():
            widget.destroy()
            
        # Charger la config via le manager (Core)
        self.manager.load_config()
        self.poptracker_vars.clear()
        self.broadcast_vars.clear()
        self.remaining_tracker_vars.clear()
        self.gamepad_widgets.clear()
        
        # Mettre à jour la variable du port dans l'UI depuis la config
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    port = cfg.get("archipelago_settings", {}).get("port", "38281")
                    self.port_var.set(port)
            except: pass
            
        # Rafraichir le bouton Hub Configuré
        self.hub_btn = self.manager.hub_controller_open_btn
        print(f"[Launcher] Shortcut Hub mis à jour : {self.hub_btn}")

        # Liste des jeux à afficher (Ordre d'affichage)
        all_games = list(self.games_metadata.keys())

        # Filtrage par jeux actifs
        active_games_cfg = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    active_games_cfg = json.load(f).get("active_games", {})
            except: pass
        
        games_to_show = [g for g in all_games if active_games_cfg.get(g, True)]

        # Dynamic responsiveness
        # On essaie de d'obtenir la largeur du conteneur réel
        container_width = self.container.winfo_width()
        # Fallback si l'UI n'est pas encore totalement rendue
        if container_width < 200: container_width = self.root.winfo_width() - 70 # - Sidebar
        
        card_width = 240 
        cols = max(1, container_width // card_width)
        
        for i, name in enumerate(games_to_show):
            row = i // cols
            col = i % cols
            self.create_game_btn(name, None, row, col)
            
        # Update canvas window width & scrollregion
        self.root.update() 
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Force a small delay then refresh scrollregion again
        self.root.after(100, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        current_w = self.canvas.winfo_width()
        if current_w > 100:
            self.canvas.itemconfig(self.canvas_window, width=current_w)
        
        print(f"[UI] Game list loaded ({len(games_to_show)} cards).")
        self._sync_gamepad_widgets()

    def _launch_archipelago_client(self, game_name, client_name):
        """Lance le client Archipelago associé à un jeu."""
        try:
            # --- NOUVEAU: Check si un client tourne déjà pour ce jeu (Support Mode Keep Alive) ---
            game_ctrl = self.manager.games.get(game_name)
            if game_ctrl and self.manager.multi_game_keep_alive:
                for p in game_ctrl.extra_processes:
                    try:
                        # Si le processus tourne encore et n'est pas le broadcast (start_cli.py)
                        if p.poll() is None and not any("start_cli.py" in str(arg) for arg in getattr(p, "args", [])):
                             print(f"[Launcher] Client Archipelago déjà actif pour {game_name}. On ne le relance pas.")
                             return p
                    except: pass

            # --- Nettoyage préventif des clients (Sauf en mode Hot Swap / Keep Alive) ---
            if not self.manager.multi_game_keep_alive:
                print(f"[Launcher] Nettoyage des processus Archipelago avant lancement de {client_name}...")
                ProcessManager.kill_by_name("ArchipelagoLauncher.exe")
                ProcessManager.kill_by_name("ArchipelagoBizHawkClient.exe")
                ProcessManager.kill_by_name("ArchipelagoLinksAwakeningDXBetaClient.exe")
                # Petit délai pour laisser Windows fermer les processus
                time.sleep(0.5)
            else:
                print(f"[Launcher] Mode Hot Swap: Conservation des clients Archipelago existants.")
            
            if not os.path.exists(CONFIG_PATH):
                print(f"[Launcher] Config non trouvée pour le lancement client : {CONFIG_PATH}")
                return None
            
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            
            arch_path = cfg.get("emulators", {}).get("archipelago", "C:\\ProgramData\\Archipelago")
            launcher_exe = os.path.join(arch_path, "ArchipelagoLauncher.exe")
            
            # Fallback: Si le client_name ressemble à un exe ou si on peut le trouver en tant que tel
            # Par exemple OoT Client -> ArchipelagoOoTClient.exe
            potential_exe = os.path.join(arch_path, f"Archipelago{client_name.replace(' ', '')}.exe")
            
            print(f"[Launcher] {game_name} détecté. Pré-lancement de {client_name}...")
            env = os.environ.copy()
            for k in list(env.keys()):
                if k.startswith("SDL_"): del env[k]
            
            # On tente d'abord l'exécutable direct si il existe (plus fiable pour le PID)
            if os.path.exists(potential_exe):
                print(f"[Launcher] Client direct trouvé : {os.path.basename(potential_exe)}")
                return subprocess.Popen([potential_exe], cwd=arch_path, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Sinon on passe par le launcher
            if os.path.exists(launcher_exe):
                cmd = [launcher_exe, client_name]
                print(f"[Launcher] Passage par le launcher : {' '.join(cmd)}")
                return subprocess.Popen(cmd, cwd=arch_path, shell=False, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                print(f"[Launcher] Erreur: Launcher non trouvé à {launcher_exe}")
                return None
        except Exception as e:
            print(f"[Launcher] Erreur lors du pré-lancement Archipelago pour {game_name}: {e}")
            return None

    def _connect_archipelago(self, game_name, client_title):
        """Automatisation de la connexion pour un client Archipelago déjà lancé."""
        # On laisse un peu de temps au client pour finir de s'ouvrir
        time.sleep(6) 
        
        # --- VERIFICATION ACTIVITE ---
        # Si entre temps le jeu a été changé ou fermé, on annule tout
        if self.manager.active_game_name != game_name:
            print(f"[Launcher] Annulation de la connexion auto pour {game_name} (n'est plus le jeu actif).")
            return None
            
        try:
            config_path = "config.json"
            if not os.path.exists(config_path): return
            
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            
            slot = cfg.get("slot_names", {}).get(game_name, "Link")
            host = cfg.get("archipelago_settings", {}).get("host", "archipelago.gg")
            port = cfg.get("archipelago_settings", {}).get("port", "63802")
            pwd = cfg.get("archipelago_settings", {}).get("password", "None") or "None"
            
            # Utiliser le chemin absolu du script PS
            current_dir = os.path.dirname(os.path.abspath(__file__))
            ps_script = os.path.join(current_dir, "send_input.ps1")
            
            ps_cmd = [
                "powershell", "-ExecutionPolicy", "Bypass",
                "-Command", f"& '{ps_script}' -Name '{slot}' -Password '{pwd}' -Port '{port}' -Server '{host}' -Title '{client_title}'"
            ]
            
            print(f"[Launcher] Connexion auto pour {game_name} : {' '.join(ps_cmd)}")
            return subprocess.Popen(ps_cmd, shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"[Launcher] Erreur lors de la connexion automate pour {game_name} : {e}")
            return None

    def on_closing(self):
        """Sauvegarde la position de la fenêtre et arrête le jeu en cours avant de quitter."""
        try:
            # 1. Arrêter le jeu proprement si actif
            if self.manager.active_game_name:
                self.stop_active_game()
                time.sleep(0.5)

            # 2. Sauvegarder géométrie
            geom = self.root.geometry()
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                config["main_window_geometry"] = geom
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                    print(f"[Launcher] Géométrie sauvegardée : {geom}")
        except Exception as e:
            print(f"[Launcher] Erreur lors de la fermeture : {e}")
        
        self.root.destroy()

if __name__ == "__main__":
    import sys
    # Interception pour exécuter ui_controller ou ui_setup dans l'exécutable compilé
    if len(sys.argv) > 1:
        if sys.argv[1].endswith("ui_controller.py"):
            import ui_controller
            root = tk.Tk()
            app = ui_controller.UIControllerApp(root)
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            root.mainloop()
            sys.exit(0)
        elif sys.argv[1].endswith("ui_setup.py"):
            start_p = "emus"
            if "--page" in sys.argv:
                try:
                    idx = sys.argv.index("--page")
                    if idx + 1 < len(sys.argv):
                        start_p = sys.argv[idx + 1]
                except:
                    pass
            import ui_setup
            app = ui_setup.SetupUI(start_page=start_p)
            app.protocol("WM_DELETE_WINDOW", app.on_closing)
            app.mainloop()
            sys.exit(0)
        elif sys.argv[1].endswith("web_tracker_host.py"):
            import web_tracker_host
            sys.argv = [sys.argv[0]] + sys.argv[2:]
            web_tracker_host.main()
            sys.exit(0)

    # Support argument pour forcer la langue (--lang en ou --lang fr)
    force_lang = None
    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")
        if idx + 1 < len(sys.argv):
            force_lang = sys.argv[idx + 1]

    # Correction du path pour trouver le module controller
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(current_dir, "controller"))
    
    manager = GameManager()
    
    # Appliquer la langue forcée si présente
    if force_lang:
        from localization import Loc
        Loc.set_lang(force_lang)

    root = tk.Tk()
    
    # Initialisation du ControllerManager
    controller_manager = ControllerManager(profiles_dir=os.path.join(current_dir, "controller", "profiles"))
    
    app = LauncherUI(root, manager, controller_manager)
    root.mainloop()
