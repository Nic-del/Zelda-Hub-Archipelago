import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import json
import os
import threading
import subprocess
import sys
import time
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

# Ajout des imports pour la gestion des manettes
sys.path.append(os.path.join(os.path.dirname(__file__), "controller"))
from controller_manager import ControllerManager

from launcher_core import GameManager, BizHawkController, DolphinController, CONFIG_PATH
from obs_controller import obs_controller

try:
    import win32gui
    import win32process
    import win32con
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

class QuickSwitcherUI:
    def __init__(self, main_ui, root):
        self.main_ui = main_ui
        self.root = root
        self.overlay = None
        self.selected_index = 0
        self.buttons = []
        self.axis_active = False
        self.canvas = None
        self.scrollable_frame = None

    def show(self):
        if self.overlay:
            self.overlay.destroy()
        
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("Quick Switcher")
        self.overlay.attributes("-topmost", True)
        self.overlay.overrideredirect(True)
        self.overlay.configure(bg="#121212")
        
        # Centrer sur l'écran
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = 300, 480
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        self.overlay.geometry(f"{w}x{h}+{x}+{y}")

        # Etat global du Hub
        is_busy = self.main_ui.status_var.get().startswith("Launching")
        active_game = self.main_ui.manager.active_game_name
        self.buttons = []
        self.games_list = list(self.main_ui.manager.games.keys())
        
        # Trouver l'index du jeu actif pour démarrer la sélection dessus
        try:
            self.selected_index = self.games_list.index(active_game) if active_game in self.games_list else 0
        except:
            self.selected_index = 0

        # Titre
        title_text = "LANCEMENT EN COURS..." if is_busy else "SÉLECTION RAPIDE"
        title_color = "#ff9900" if is_busy else "#00ff99"
        tk.Label(self.overlay, text=title_text, font=("Segoe UI", 12, "bold"), bg="#121212", fg=title_color).pack(pady=15)
        
        # Container avec Scrollbar (Canvas)
        container = tk.Frame(self.overlay, bg="#121212")
        container.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(container, bg="#121212", highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        # On ne l'affiche que si nécessaire ? Non, on la laisse pour le moment ou on met une version auto
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#121212")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=260)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        # scrollbar.pack(side="right", fill="y") # On cache la scrollbar pour une UI plus "Console", ou on l'ajoute
        
        for i, game in enumerate(self.games_list):
            is_active = (game == active_game)
            btn_bg = "#004422" if is_active else "#1e1e1e"
            btn_fg = "#00ff99" if is_active else "white"
            
            btn = tk.Button(
                self.scrollable_frame, text=f"{game} (Actif)" if is_active else game, 
                font=("Segoe UI", 10, "bold" if is_active else "normal"),
                bg=btn_bg, fg=btn_fg, activebackground="#333", activeforeground="#00ff99",
                relief="flat", pady=8, cursor="hand2" if not is_busy else "arrow",
                state="disabled" if is_busy else "normal",
                command=lambda g=game: self.switch_to(g)
            )
            btn.pack(fill="x", pady=4, padx=5)
            self.buttons.append(btn)
        
        # Appliquer le highlight initial
        self._update_selection()
        
        # Instructions
        tk.Label(self.overlay, text="[Bouton Bas] Valider  •  [Echap] Quitter", font=("Segoe UI", 8), bg="#121212", fg="#888").pack(pady=10)
        
        self.overlay.bind("<Escape>", lambda e: self.close())
        self.overlay.focus_set()

    def toggle(self):
        if self.overlay:
            self.close()
        else:
            self.show()

    def handle_controller_input(self, event):
        """Gère la navigation Haut/Bas et validation via manette."""
        if not self.overlay or not self.buttons:
            return False

        # 1. NAVIGATION (Stick ou D-Pad)
        move = 0
        if event["type"] == "hat":
            # On ne bouge que sur l'appui initial (state=1)
            if event["state"] == 1:
                if event["id"] == "DPAD_UP": move = -1
                elif event["id"] == "DPAD_DOWN": move = 1
        
        elif event["type"] == "axis" and event["id"] == "LEFT_STICK_Y":
            val = event["state"]
            if abs(val) > 0.7:
                if not self.axis_active:
                    move = -1 if val < 0 else 1
                    self.axis_active = True
            elif abs(val) < 0.3:
                self.axis_active = False
            
        if move != 0:
            self.selected_index = (self.selected_index + move) % len(self.buttons)
            self._update_selection()
            return True

        # 2. VALIDATION / ANNULATION
        if event["type"] == "button" and event["state"] == 1:
            btn_id = event["id"]
            
            # Détection du type de manette via le manager
            # Sur Nintendo: A=FACE_RIGHT, B=FACE_BOTTOM
            # Sur Xbox/Autres: A=FACE_BOTTOM, B=FACE_RIGHT
            
            # Pour simplifier, on accepte les deux boutons du bas/droite pour valider/quitter
            # mais on privilégie la logique du constructeur si possible.
            
            if btn_id in ["FACE_BOTTOM", "FACE_RIGHT"]:
                # Validation (A sur Xbox, B sur Nintendo - ou l'inverse selon les goûts)
                # On va dire que le bouton du bas valide toujours par défaut pour l'ergonomie moderne
                if btn_id == "FACE_BOTTOM":
                    self._on_confirm()
                    return True
                else: # FACE_RIGHT pour quitter
                    self.close()
                    return True
            
            # Bouton Select/Start/L3/R3 pour quitter aussi si besoin
            if btn_id in ["SELECT", "START", "L3", "R3"]:
                self.close()
                return True

        return False

    def _update_selection(self):
        """Met à jour l'apparence visuelle et assure la visibilité du bouton sélectionné."""
        if not self.buttons: return
        
        for i, btn in enumerate(self.buttons):
            if i == self.selected_index:
                btn.configure(bg="#00ff99", fg="black") # Highlight vert
                
                # S'assurer que le bouton est visible (Auto-Scroll)
                if self.canvas:
                    self.root.update_idletasks() # Forcer le calcul des géométries
                    
                    # Hauteur totale et position du bouton
                    btn_y = btn.winfo_y()
                    btn_h = btn.winfo_height()
                    canvas_h = self.canvas.winfo_height()
                    
                    # Position relative (en %) pour yview_moveto
                    total_h = self.scrollable_frame.winfo_height()
                    if total_h > canvas_h:
                        # On centre un peu la vue ou on s'assure juste que c'est dedans
                        # On calcule la fraction actuelle de défilement
                        top, bottom = self.canvas.yview()
                        
                        btn_top_rel = btn_y / total_h
                        btn_bottom_rel = (btn_y + btn_h) / total_h
                        
                        if btn_top_rel < top:
                            self.canvas.yview_moveto(btn_top_rel)
                        elif btn_bottom_rel > bottom:
                            # Faire défiler pour que le bas du bouton soit visible
                            self.canvas.yview_moveto(btn_bottom_rel - (canvas_h / total_h))
            else:
                # Restaurer style original
                game_name = self.games_list[i]
                is_active = (game_name == self.main_ui.manager.active_game_name)
                bg = "#004422" if is_active else "#1e1e1e"
                fg = "#00ff99" if is_active else "white"
                btn.configure(bg=bg, fg=fg)

    def _on_confirm(self):
        """Simule un clic sur le bouton sélectionné."""
        if 0 <= self.selected_index < len(self.games_list):
            game = self.games_list[self.selected_index]
            self.switch_to(game)

    def switch_to(self, game):
        if self.main_ui.status_var.get().startswith("Launching"):
            return
        self.close()
        self.main_ui.launch_game(game)

    def close(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

class LauncherUI:
    def __init__(self, root, manager, controller_manager):
        self.manager = manager
        self.controller_manager = controller_manager
        self.root = root
        self.root.title("Zelda Multi-Launcher")
        self.root.geometry("850x800")
        self.root.resizable(True, True)
        self.root.configure(bg="#121212")
        # Chemins absolus
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.assets_dir = os.path.join(self.base_dir, "assets", "images")

        self.poptracker_vars = {}
        self.poptracker_process = None
        self.poptracker_last_rect = None
        self.action_widgets = []
        self.game_images = {}
        self.game_images_disabled = {}
        self.auto_config_per_game = {}
        self.quick_switcher = QuickSwitcherUI(self, root)
        
        # Charger la config initiale
        self.manager.load_config()

        # Activer l'écoute des manettes pour le Hub
        self.hub_btn = self.manager.hub_controller_open_btn # Initial value
        self.controller_manager.raw_input_callback = self._handle_controller_input
        
        # Charger les images
        self._load_game_images()
        
        # Hotkey global (Ctrl+Shift+S)
        if keyboard:
            try:
                keyboard.add_hotkey('ctrl+shift+s', self.root.after, args=(0, self.quick_switcher.show))
                keyboard.add_hotkey('ctrl+f2', self.root.after, args=(0, self.quick_switcher.show)) # Backup
                print("[Launcher] Raccourcis activés.")
            except Exception as e:
                print(f"[Launcher] Erreur raccourci : {e}")
                messagebox.showwarning("Avertissement", f"Le raccourci Ctrl+Shift+S n'a pas pu être activé.\nErreur : {e}\n\nEssayez de lancer le Hub en tant qu'administrateur.")
        else:
            messagebox.showwarning("Avertissement", "Le module 'keyboard' est manquant. Le Quick Switcher ne fonctionnera pas.")

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#333", foreground="white")
        style.map("TButton", background=[('active', '#555')])

        # Header with subtle glow effect
        header_frame = tk.Frame(root, bg="#121212")
        header_frame.pack(fill="x", pady=(30, 20))
        
        title_font = ("Montserrat", 24, "bold") if "Montserrat" in tkfont.families() else ("Segoe UI", 24, "bold")
        self.label = tk.Label(header_frame, text="ZELDA HUB", font=title_font, bg="#121212", fg="#00ff99")
        self.label.pack()
        
        # Decorative underline
        line = tk.Frame(header_frame, bg="#00ff99", height=2, width=100)
        line.pack(pady=5)
        
        self.sub_label = tk.Label(header_frame, text="MULTI-LAUNCHER • ARCHIPELAGO • TRACKER", 
                                font=("Segoe UI", 7, "bold"), bg="#121212", fg="#333")
        self.sub_label.pack(pady=(2, 0))

        # Container for game selection with Scrollbar
        self.container = tk.Frame(root, bg="#121212")
        self.container.pack(fill="both", expand=True, padx=20)
        
        self.canvas = tk.Canvas(self.container, bg="#121212", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        
        self.game_frame = tk.Frame(self.canvas, bg="#121212")
        self.game_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.game_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel support
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Archipelago Port Quick-Change
        self.port_frame = tk.Frame(root, bg="#1e1e1e")
        self.port_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(self.port_frame, text="Port AP:", bg="#1e1e1e", fg="#e0e0e0").pack(side="left")
        self.port_var = tk.StringVar()
        self.port_entry = tk.Entry(self.port_frame, textvariable=self.port_var, width=10, bg="#333", fg="white", borderwidth=0, highlightthickness=1, highlightbackground="#444", insertbackground="white")
        self.port_entry.pack(side="left", padx=5)
        self.action_widgets.append(self.port_entry)
        
        btn_port = ttk.Button(self.port_frame, text="OK", width=4, command=self.update_port)
        btn_port.pack(side="left")
        self.action_widgets.append(btn_port)
        
        # Bouton Quick Switcher de secours
        btn_qs = ttk.Button(self.port_frame, text="Selection Rapide", command=self.quick_switcher.show)
        btn_qs.pack(side="right", padx=5)
        self.action_widgets.append(btn_qs)

        self.load_games()

        # Config Buttons
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        settings_btn = ttk.Button(btn_frame, text="⚙️ Config", command=self.open_setup)
        settings_btn.pack(side="left", padx=5)
        self.action_widgets.append(settings_btn)

        controller_btn = ttk.Button(btn_frame, text="🎮 Gérer les Manettes", command=self.open_controller_settings)
        controller_btn.pack(side="left", padx=5)
        self.action_widgets.append(controller_btn)

        stop_btn = ttk.Button(btn_frame, text="⏹️ Quitter le Jeu (Propre)", command=self.stop_active_game)
        stop_btn.pack(side="left", padx=5)
        self.action_widgets.append(stop_btn)


        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        # Auto-config Toggle
        self.auto_config_var = tk.BooleanVar(value=True)
        self.load_settings()
        
        self.auto_config_cb = tk.Checkbutton(
            root, text="Configuration automatique des manettes", 
            variable=self.auto_config_var, onvalue=True, offvalue=False,
            bg="#1e1e1e", fg="#e0e0e0", selectcolor="#333",
            activebackground="#1e1e1e", activeforeground="#00ff99",
            command=self.save_settings
        )
        self.auto_config_cb.pack(pady=5)
        self.action_widgets.append(self.auto_config_cb)

        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#333", fg="#aaa")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Lancer le polling périodique des manettes
        self.poll_controllers()

    def _load_game_images(self, size=(200, 200)):
        """Charge, crope en carré et teinte les images pour les cartes du launcher."""
        self.game_images = {}
        self.game_images_disabled = {}
        if not HAS_PIL:
            return
            
        image_colors = {
            "Ocarina of Time": ("oot.png", "#2ecc71"),
            "OOT (SOH)": ("oot_soh.png", "#2ecc71"),
            "Majora's Mask": ("mm.png", "#9b59b6"),
            "Wind Waker": ("ww.png", "#3498db"),
            "Twilight Princess": ("tp.png", "#34495e"),
            "Skyward Sword": ("ss.png", "#e67e22"),
            "A Link Between Worlds": ("albw.png", "#f1c40f"),
            "A Link to the Past": ("alttp.png", "#27ae60"),
            "Minish Cap": ("mc.png", "#e74c3c"),
            "Link's Awakening DX": ("ladx.png", "#1abc9c"),
            "The Legend of Zelda": ("z1.png", "#f39c12"),
            "Zelda II": ("z2.png", "#c0392b"),
            "Zelda II: The Adventure of Link": ("z2.png", "#c0392b"),
            "Oracle of Ages": ("ooa.png", "#2980b9"),
            "Oracle of Seasons": ("oos.png", "#d35400"),
            "Spirit Tracks": ("st.png", "#16a085"),
            "Phantom Hourglass": ("ph.png", "#1abc9c")
        }
        
        # Créer le placeholder d'abord
        try:
            placeholder = Image.new('RGB', size, color='#333333')
            self.game_images["_default"] = ImageTk.PhotoImage(placeholder)
        except:
            print("[Launcher] Erreur lors de la création du placeholder.")
            return

        for game, (filename, color_hex) in image_colors.items():
            path = os.path.join(self.assets_dir, filename)
            if os.path.exists(path):
                print(f"[Launcher] Found asset for {game}: {filename}")
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
                    
                    # 3. No more tinting - Keep images clear
                    # tint = Image.new("RGBA", size, color_hex)
                    # img = Image.blend(img, tint, 0.6)
                    
                    self.game_images[game] = ImageTk.PhotoImage(img)
                    
                    # 4. Create disabled version (grayscale + darkened)
                    disabled_img = img.convert("L").convert("RGBA")
                    enhancer = ImageEnhance.Brightness(disabled_img)
                    disabled_img = enhancer.enhance(0.4) # Darken substantially
                    self.game_images_disabled[game] = ImageTk.PhotoImage(disabled_img)
                except Exception as e:
                    print(f"[Launcher] Erreur chargement image {game}: {e}")
            else:
                print(f"[Launcher] Asset missing for {game}: {filename}")

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
                if subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
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
                    # On cherche une fenêtre qui contient PopTracker
                    if "PopTracker" in title:
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
                config_path = os.path.join(os.path.dirname(__file__), "config.json")
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
        """Attend que la nouvelle fenêtre PopTracker apparaisse et lui applique l'ancienne position (Sécurité)."""
        if not HAS_PYWIN32 or not rect:
            return
        
        def _poll_and_restore():
            x, y, x2, y2 = rect
            w, h = x2 - x, y2 - y
            
            for i in range(100): # 10 secondes max d'attente
                time.sleep(0.1)
                if new_process.poll() is not None: break
                
                hwnds = []
                def enum_cb(hwnd, results):
                    try:
                        if win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if "PopTracker" in title:
                                results.append(hwnd)
                    except: pass
                
                win32gui.EnumWindows(enum_cb, hwnds)
                if hwnds:
                    hwnd = hwnds[0]
                    # On force le repositionnement plusieurs fois au cas où l'app se recentre elle-même
                    for _ in range(5):
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, w, h, win32con.SWP_SHOWWINDOW)
                        time.sleep(0.3)
                    print(f"[Launcher] Restauration WindowPos forcée terminée.")
                    return

        threading.Thread(target=_poll_and_restore, daemon=True).start()

    def _handle_controller_input(self, raw_event):
        """Intercepte les inputs manette pour les raccourcis du Hub."""
        # 1. Si le Quick Switcher est ouvert, il est prioritaire sur les inputs
        if self.quick_switcher.overlay:
            if self.quick_switcher.handle_controller_input(raw_event):
                return True

        # 2. Raccourci Global pour toggle le Hub
        # On ne réagit que si c'est le bouton configuré et qu'il est pressé (state=1)
        if raw_event["type"] == "button" and raw_event["id"] == self.hub_btn and raw_event["state"] == 1:
            print(f"[Launcher] Controller shortcut detected ({self.hub_btn}). Toggling Quick Switcher.")
            self.root.after(0, self.quick_switcher.toggle)
            return True # On consomme l'event s'il est mappé, sinon non
        return False

    def poll_controllers(self):
        """Met à jour l'état des manettes régulièrement."""
        if hasattr(self, 'controller_manager'):
            self.controller_manager.poll()
        self.root.after(200, self.poll_controllers)

    def _set_ui_state(self, state):
        """Active ou désactive tous les widgets inscrits dans action_widgets."""
        for widget in self.action_widgets:
            try:
                widget.configure(state=state)
            except:
                pass

    def create_game_btn(self, name, code, row=0, col=0):
        # Premium Card Design with Hover Effect
        card_border = tk.Frame(self.game_frame, bg="#222", padx=1, pady=1)
        card_border.grid(row=row, column=col, padx=15, pady=15)
        
        card = tk.Frame(card_border, bg="#0a0a0a", bd=0)
        card.pack()
        
        config_path = self.config_path
        
        # Individual Theme Color
        image_colors = {
            "Ocarina of Time": "#2ecc71", "OOT (SOH)": "#2ecc71",
            "Majora's Mask": "#9b59b6", "Wind Waker": "#3498db",
            "Twilight Princess": "#34495e", "Skyward Sword": "#e67e22",
            "A Link Between Worlds": "#f1c40f", "A Link to the Past": "#27ae60",
            "Minish Cap": "#e74c3c", "Link's Awakening DX": "#1abc9c",
            "The Legend of Zelda": "#f39c12", "Zelda II": "#c0392b",
            "Oracle of Ages": "#2980b9", "Oracle of Seasons": "#d35400",
            "Spirit Tracks": "#16a085", "Phantom Hourglass": "#1abc9c"
        }
        theme_color = image_colors.get(name, "#00ff99")

        def on_enter(e):
            card_border.configure(bg=theme_color)
            lbl_tag.configure(fg=theme_color)
            
        def on_leave(e):
            card_border.configure(bg="#222")
            lbl_tag.configure(fg="white")

        is_registered = name in self.manager.games
        
        if (name in self.game_images or name in self.game_images_disabled) and HAS_PIL:
            # Name Tag - Now at the top of the card
            display_name = name.upper().replace("THE LEGEND OF ZELDA: ", "")
            if len(display_name) > 22: 
                display_name = display_name[:19] + "..."

            lbl_tag = tk.Label(
                card, text=display_name, 
                font=("Segoe UI", 8, "bold"), fg="white" if is_registered else "#555", bg="#0a0a0a",
                pady=12
            )
            lbl_tag.pack(side="top", fill="x")
            
            # Main Button (Image)
            if is_registered:
                img = self.game_images.get(name, self.game_images.get("_default"))
            else:
                img = self.game_images_disabled.get(name, self.game_images.get("_default"))
            
            btn = tk.Button(
                card, image=img, command=lambda: self.launch_game(name),
                bg="#0a0a0a", activebackground="#111", borderwidth=0, 
                relief="flat", cursor="hand2" if is_registered else "arrow", 
                highlightthickness=0, state="normal" if is_registered else "disabled"
            )
            btn.pack()
            self.action_widgets.append(btn)
            
            # Hover bindings - only if registered
            if is_registered:
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
            
            # Controls Footer
            ctrl_bg = tk.Frame(card, bg="#0a0a0a", height=50)
            ctrl_bg.pack(side="bottom", fill="x")
            ctrl_bg.pack_propagate(False)

            ctrl_container = tk.Frame(ctrl_bg, bg="#0a0a0a", bd=0)
            ctrl_container.pack(expand=True)
            
            def create_icon_toggle(parent, text, var, color="#f1c40f"):
                cb = tk.Checkbutton(
                    parent, text=text, variable=var,
                    indicatoron=False,
                    bg="#000000", fg="#444", selectcolor="#000000",
                    activebackground="#000000", activeforeground=color,
                    font=("Segoe UI", 13), borderwidth=0, padx=12, pady=0,
                    cursor="hand2" if is_registered else "arrow"
                )
                def update_color():
                    cb.configure(fg=color if var.get() else "#444")
                    self.save_settings()
                
                cb.configure(command=update_color)
                if var.get(): cb.configure(fg=color)
                
                cb.pack(side="left")
                if not is_registered:
                    cb.configure(state="disabled")
                self.action_widgets.append(cb)
                return cb

            # Toggles
            # Only show tracker if a pack is configured AND the path is not empty
            has_tracker = self.manager.poptracker_packs.get(name)
            
            v_pop = tk.BooleanVar()
            self.poptracker_vars[name] = v_pop
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        enabled_map = json.load(f).get("poptracker_enabled", {})
                        v_pop.set(enabled_map.get(name, False))
                except: pass
            
            if has_tracker:
                create_icon_toggle(ctrl_container, "🗺️", v_pop, "#00ff99")
            
            v_pad = tk.BooleanVar()
            self.auto_config_per_game[name] = v_pad
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        pad_map = json.load(f).get("auto_controller_per_game", {})
                        v_pad.set(pad_map.get(name, True))
                except: pass
            
            create_icon_toggle(ctrl_container, "🎮", v_pad, "#3498db")

        else:
            # Placeholder with improved look
            txt = name.upper().replace("THE LEGEND OF ZELDA: ", "")
            placeholder_btn = tk.Button(
                card, text=txt, command=lambda: self.launch_game(name),
                width=24, height=14, bg="#111", fg="#333",
                font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                activebackground="#151515", activeforeground="#00ff99"
            )
            placeholder_btn.pack()
            placeholder_btn.bind("<Enter>", lambda e: card_border.configure(bg="#00ff99"))
            placeholder_btn.bind("<Leave>", lambda e: card_border.configure(bg="#222"))
            if name not in self.manager.games:
                placeholder_btn.configure(state="disabled")
            self.action_widgets.append(placeholder_btn)

    def launch_game(self, name):
        """Lance un jeu dans un thread avec un petit delai (Suggestion utilisateur)."""
        # --- NOUVEAU: Arreter le jeu precedent si necessaire ---
        if self.manager.active_game_name and self.manager.active_game_name != name:
            print(f"[Launcher] Changement de jeu détecté. Arrêt de {self.manager.active_game_name}...")
            self.stop_active_game()
            time.sleep(1) # Petit délai pour laisser les processus se fermer

        self._set_ui_state(tk.DISABLED)
        self.status_var.set(f"Launching {name}...")
        self.root.update()
        
        # 1. AUTOMATION MANETTE (Thread Principal)
        # On définit quel profil charger pour chaque jeu
        profile_map = {
            "Ocarina of Time": "oot",
            "Wind Waker": "ww",
            "A Link to the Past": "alttp", # Profil spécifique pour ALttP (SNES)
            "Majora's Mask": "mm",   # Profil pour Majora's Mask (Native/Port)
            "Twilight Princess": "tp", # Profil spécifique pour TP (Dolphin)
            "Minish Cap": "mc",      # Profil spécifique pour Minish Cap (BizHawk)
            "Oracle of Ages": "ooa", # Profil spécifique pour Oracle of Ages (BizHawk/GBC)
            "Oracle of Seasons": "oos", # Profil spécifique pour Oracle of Seasons (BizHawk/GBC)
            "The Legend of Zelda": "z1", # Profil spécifique pour Zelda 1 (BizHawk/NES)
            "Zelda II": "z2", # Profil spécifique pour Zelda 2 (BizHawk/NES)
            "A Link Between Worlds": "albw", # Profil spécifique pour ALBW (Azahar)
            "Phantom Hourglass": "ph", # DS via BizHawk
            "Spirit Tracks": "st", # DS via BizHawk
            "OOT (SOH)": "soh"
        }
        
        # Utiliser le réglage global ET le réglage par jeu
        is_global_auto = self.auto_config_var.get()
        is_game_auto = self.auto_config_per_game.get(name, tk.BooleanVar(value=True)).get()

        if is_global_auto and is_game_auto and name in profile_map:
            profile = profile_map[name]
            print(f"[Launcher] Preparation manette pour {name} (Profil: {profile})...")
            
            # Charger et appliquer (Dolphin / BizHawk)
            self.controller_manager.load_game_profile(profile)
            self.controller_manager.apply_config_to_emulators()
            
            # Cas spécial Dolphin qui préfère parfois une copie directe si le INI est récalcitrant
            if name == "Wind Waker":
                self.controller_manager.exporter.force_copy_profile("ww.ini")
        else:
            print(f"[Launcher] Configuration automatique ignorée pour {name} (Global:{is_global_auto}, Game:{is_game_auto}).")

        # 2. RUN LOGIC IN THREAD WITH DELAY
        def _threaded_launch():
            # Trigger OBS Scene Switch
            obs_controller.switch_scene(name)
            
            # Détection initiale
            is_bizhawk_ap = "ArchipelagoBizHawkController" in str(type(self.manager.games.get(name)))
            is_ap_mode = False
            selected_variant = self.manager.poptracker_variants.get(name, "")

            # --- 0. LANCEMENT POPTRACKER (Si activé) ---
            if name in self.poptracker_vars and self.poptracker_vars[name].get():
                try:
                    # Détection AP déplacée ici pour être protégée
                    is_ap_mode = self.manager.is_ap_mode(name, selected_variant) or is_bizhawk_ap
                    print(f"[Launcher] Mode AP détecté pour {name} : {is_ap_mode}")

                    pack_path = self.manager.poptracker_packs.get(name, "")
                    is_web = pack_path.startswith("http")
                    
                    # 1. Capture position actuelle
                    current_rect = self._get_poptracker_window_rect()
                    if current_rect:
                        self.poptracker_last_rect = current_rect

                    # 2. Fermer l'ancien s'il existe
                    if self.poptracker_process and self.poptracker_process.poll() is None:
                        print("[Launcher] Fermeture de l'ancien tracker...")
                        self.poptracker_process.terminate()
                        try:
                            self.poptracker_process.wait(timeout=2)
                        except:
                            self.poptracker_process.kill()

                    if is_web:
                        print(f"[Launcher] Lancement du tracker WEB : {pack_path}")
                        python_exe = self._find_python_with_webview()
                        host_script = os.path.join(os.path.dirname(__file__), "web_tracker_host.py")
                        
                        # Si python_exe contient des espaces ou est une commande composée
                        if "py -" in python_exe:
                            parts = python_exe.split()
                            cmd = parts + [host_script, pack_path]
                        else:
                            cmd = [python_exe, host_script, pack_path]

                        if self.poptracker_last_rect:
                            x, y, x2, y2 = self.poptracker_last_rect
                            cmd.extend([str(x), str(y), str(x2-x), str(y2-y)])
                        
                        self.poptracker_process = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))
                    else:
                        pop_path = self.manager.poptracker_path
                        if pop_path and os.path.exists(pop_path):
                            print(f"[Launcher] Lancement de PopTracker pour {name}...")
                            variant = self.manager.poptracker_variants.get(name, "")
                            cmd = [pop_path]
                            if variant:
                                cmd.extend(["--pack-variant", variant])
                            
                            # --- New: Auto-Connect and Broadcast Commands ---
                            if is_ap_mode:
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
                                cmd.append("--broadcast")

                            if pack_path and os.path.exists(pack_path):
                                cmd.append(pack_path)
                            
                            env = os.environ.copy()
                            for k in list(env.keys()):
                                if k.startswith("SDL_"): del env[k]
                            
                            # Synchronisation des infos de connexion et de la position
                            self._update_poptracker_settings_file(game_name=name, rect=self.poptracker_last_rect)

                            print(f"[Launcher] Commande PopTracker : {' '.join(cmd)}")
                            self.poptracker_process = subprocess.Popen(cmd, cwd=os.path.dirname(pop_path), env=env)
                            

                            if self.poptracker_last_rect:
                                self._restore_poptracker_window(self.poptracker_process, self.poptracker_last_rect)
                        else:
                            print(f"[Launcher] PopTracker activé mais chemin invalide : {pop_path}")
                except Exception as e:
                    print(f"[Launcher] Erreur lors du lancement du tracker : {e}")

            time.sleep(0.5) # Delai suggere par l'utilisateur
            
            # --- 1. PRE-LANCEMENT CLIENT ARCHIPELAGO ---
            # Utilise la détection calculée au début
            if (is_ap_mode or name in ["Wind Waker", "Twilight Princess", "A Link Between Worlds", "Skyward Sword", "Ocarina of Time", "Link's Awakening DX"]) and (not is_bizhawk_ap or name == "Link's Awakening DX"):
                # Note: On autorise l'exception pour LADX pour qu'il utilise la méthode "WW style" (send_input.ps1)
                client_names = {
                     "Wind Waker": "The Wind Waker Client",
                     "Twilight Princess": "Twilight Princess Client",
                     "A Link Between Worlds": "A Link Between Worlds Client",
                     "Skyward Sword": "Skyward Sword Client",
                     "Link's Awakening DX": "Links Awakening DX Beta Client",
                     "Ocarina of Time": "OoT Client"
                 }
                # Fallback dynamique si le jeu n'est pas dans la liste
                target_client = client_names.get(name, f"{name} Client")
                client_p = self._launch_archipelago_client(name, target_client)
                if client_p:
                    game_ctrl = self.manager.games.get(name)
                    if game_ctrl:
                        game_ctrl.extra_processes.append(client_p)

            # --- 2. LANCEMENT DU JEU ---
            success = self.manager.start_game(name)
            
            if success:
                print(f"[Launcher] {name} lance avec succes. Debut du monitoring...")
                self.root.after(0, lambda: self.status_var.set(f"Playing: {name}"))
                
                # --- 3. AUTOMATISATION CONNEXION ---
                if (is_ap_mode or name in ["Wind Waker", "Twilight Princess", "A Link Between Worlds", "Skyward Sword", "Ocarina of Time", "Link's Awakening DX"]) and (not is_bizhawk_ap or name == "Link's Awakening DX"):
                    client_titles = {
                        "Wind Waker": "Archipelago The Wind Waker Client*",
                        "Twilight Princess": "Archipelago Twilight Princess Client*",
                        "A Link Between Worlds": "Archipelago A Link Between Worlds Client*",
                        "Skyward Sword": "Archipelago Skyward Sword Client*",
                        "Link's Awakening DX": "*Links Awakening DX Beta Client*",
                        "Ocarina of Time": "Archipelago Ocarina of Time Client*"
                    }
                    # Fallback dynamique pour le titre de la fenêtre
                    target_title = client_titles.get(name, f"Archipelago {name} Client*")
                    def _run_connect():
                        conn_p = self._connect_archipelago(name, target_title)
                        if conn_p:
                            game_ctrl = self.manager.games.get(name)
                            if game_ctrl:
                                game_ctrl.extra_processes.append(conn_p)

                    threading.Thread(target=_run_connect, daemon=True).start()
                # ------------------------------------------

                # Monitor end
                game_ctrl = self.manager.games.get(name)
                if game_ctrl and game_ctrl.process:
                    print(f"[Launcher] En attente de la fermeture de {name} (PID: {game_ctrl.process.pid})...")
                    self.root.after(0, lambda: self._set_ui_state(tk.NORMAL))
                    game_ctrl.process.wait()
                    print(f"[Launcher] {name} s'est ferme.")
                
                self.manager.active_game_name = None
                self.root.after(0, lambda: self.status_var.set("Ready"))
            else:
                print(f"[Launcher] Echec du lancement de {name}.")
                self.root.after(0, lambda: self._set_ui_state(tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set(f"Echec: {name}"))

        threading.Thread(target=_threaded_launch, daemon=True).start()

    def stop_active_game(self):
        """Arrête manuellement le jeu et les clients en cours."""
        if self.manager.active_game_name:
            name = self.manager.active_game_name
            self.status_var.set(f"Stopping {name}...")
            self.root.update()
            
            # 1. Fermer PopTracker si ouvert
            if self.poptracker_process and self.poptracker_process.poll() is None:
                print("[Launcher] Fermeture de PopTracker...")
                self.poptracker_process.terminate()

            # 2. Récupérer le contrôleur et appeler stop() (qui est maintenant gracieux)
            game_ctrl = self.manager.games.get(name)
            if game_ctrl:
                game_ctrl.stop()
            
            self.manager.active_game_name = None
            self.status_var.set("Ready")
            print(f"[Launcher] Jeu '{name}' arrêté manuellement.")
        else:
            messagebox.showinfo("Info", "Aucun jeu n'est actuellement actif.")

    def open_controller_settings(self):
        self.status_var.set("Gestion des manettes...")
        self.root.update()
        
        # Bloquer la fenêtre principale
        self.root.attributes('-disabled', True)
        
        def run_controller():
            # Ouvre `ui_controller.py` (chemin absolu) et attend
            ui_path = os.path.join(self.base_dir, "ui_controller.py")
            subprocess.run([sys.executable, ui_path])
            
            # Une fois fermé, on débloque
            print("[Launcher] Retour de la gestion des manettes. Reloading config...")
            self.root.after(0, self.finish_setup)
            
        threading.Thread(target=run_controller, daemon=True).start()

    def open_setup(self):
        self.status_var.set("Configuration en cours...")
        self.root.update()
        
        # Bloquer la fenêtre principale pour empêcher toute interaction
        self.root.attributes('-disabled', True)
        
        def run_setup():
            # Ouvre `ui_setup.py` (chemin absolu) et attend
            setup_path = os.path.join(self.base_dir, "ui_setup.py")
            subprocess.run([sys.executable, setup_path])
            
            # Une fois fermé, on débloque
            print("[Launcher] Retour du setup des chemins. Reloading config...")
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
            self.status_var.set("Ready")
        else:
            self.status_var.set(f"Playing: {self.manager.active_game_name}")

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
                
                # Charger l'état PopTracker pour chaque jeu
                enabled_map = config.get("poptracker_enabled", {})
                for g_name, var in self.poptracker_vars.items():
                    if g_name in enabled_map:
                        var.set(enabled_map[g_name])

                # Charger l'état Auto-Pad pour chaque jeu
                auto_pad_map = config.get("auto_controller_per_game", {})
                for g_name, var in self.auto_config_per_game.items():
                    if g_name in auto_pad_map:
                        var.set(auto_pad_map[g_name])
                
                # NOUVEAU: Synchroniser le bouton Hub et le manager
                self.manager.load_config()
                self.hub_btn = self.manager.hub_controller_open_btn
                print(f"[Launcher] Settings reloaded. Hub button: {self.hub_btn}")
            except Exception as e:
                print(f"Erreur lors du chargement des paramètres : {e}")

    def save_settings(self):
        """Sauvegarde les paramètres généraux comme l'auto-config."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                config["auto_controller_config"] = self.auto_config_var.get()
                
                # Sauvegarder l'état PopTracker
                if "poptracker_enabled" not in config:
                    config["poptracker_enabled"] = {}
                for g_name, var in self.poptracker_vars.items():
                    config["poptracker_enabled"][g_name] = var.get()

                # Sauvegarder l'état Auto-Pad par jeu
                if "auto_controller_per_game" not in config:
                    config["auto_controller_per_game"] = {}
                for g_name, var in self.auto_config_per_game.items():
                    config["auto_controller_per_game"][g_name] = var.get()
                
                # S'assurer que le raccourci Hub est préservé même si on sauve depuis ici
                if hasattr(self.manager, 'hub_controller_open_btn'):
                    config["hub_controller_open_btn"] = self.manager.hub_controller_open_btn
                    print(f"[Launcher] Syncing Hub button to config: {self.manager.hub_controller_open_btn}")

                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                print(f"[Launcher] Paramètres sauvegardés.")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde des paramètres : {e}")

    def load_games(self):
        # Clear existing buttons
        # Nettoyage de la liste des widgets : on ne garde que ceux qui existent encore
        # et qui ne sont pas des enfants de game_frame (car ils vont être détruits)
        self.action_widgets = [w for w in self.action_widgets if w.winfo_exists() and not str(w).startswith(str(self.game_frame))]

        for widget in self.game_frame.winfo_children():
            widget.destroy()
            
        # Charger la config via le manager (Core)
        self.manager.load_config()
        self.poptracker_vars.clear()
        
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
        games_to_show = [
            "Ocarina of Time", 
            "Majora's Mask",
            "Wind Waker", 
            "Twilight Princess",
            "Skyward Sword",
            "A Link Between Worlds",
            "A Link to the Past",
            "Minish Cap",
            "The Legend of Zelda",
            "Zelda II",
            "Oracle of Ages",
            "Oracle of Seasons",
            "Link's Awakening DX",
            "Phantom Hourglass",
            "Spirit Tracks",
            "OOT (SOH)"
        ]

        cols = 3
        for i, name in enumerate(games_to_show):
            row = i // cols
            col = i % cols
            self.create_game_btn(name, name, row, col)
            
        # Update canvas window width & scrollregion
        self.root.update() 
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Force a small delay then refresh scrollregion again
        self.root.after(100, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        current_w = self.canvas.winfo_width()
        if current_w > 100:
            self.canvas.itemconfig(self.canvas_window, width=current_w)
        
        print(f"[UI] Game list loaded ({len(games_to_show)} cards).")

    def _launch_archipelago_client(self, game_name, client_name):
        """Lance le client Archipelago associé à un jeu."""
        try:
            # --- Nettoyage préventif des clients déjà ouverts ---
            print(f"[Launcher] Nettoyage des processus Archipelago avant lancement de {client_name}...")
            subprocess.run(["taskkill", "/F", "/IM", "ArchipelagoLauncher.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "ArchipelagoBizHawkClient.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "ArchipelagoLinksAwakeningDXBetaClient.exe"], capture_output=True)
            # Petit délai pour laisser Windows fermer les processus
            time.sleep(0.5)
            
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
                "powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script,
                "-Name", slot, "-Password", pwd, "-Port", port, "-Server", host, "-Title", client_title
            ]
            
            print(f"[Launcher] Connexion auto pour {game_name} : {' '.join(ps_cmd)}")
            return subprocess.Popen(ps_cmd, shell=False)
        except Exception as e:
            print(f"[Launcher] Erreur lors de la connexion automate pour {game_name} : {e}")
            return None

if __name__ == "__main__":
    # Correction du path pour trouver le module controller
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(current_dir, "controller"))
    
    manager = GameManager()
    
    root = tk.Tk()
    
    # Initialisation du ControllerManager (silencieuse)
    # On le fait APRES tk.Tk() pour une meilleure compatibilité des contexts OS/SDL
    controller_manager = ControllerManager(profiles_dir=os.path.join(current_dir, "controller", "profiles"))
    
    app = LauncherUI(root, manager, controller_manager)
    root.mainloop()
