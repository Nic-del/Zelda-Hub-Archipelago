import tkinter as tk
import json
import os
from localization import Loc

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
        
        # Performance: Speed up polling while Hub is open
        self.main_ui.controller_polling_interval = 30 # Plus réactif
        
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
        
        # Filtrage par jeux actifs (utilisant le manager pour avoir la liste complète disponible)
        active_games_cfg = {}
        if os.path.exists(self.main_ui.config_path):
            try:
                with open(self.main_ui.config_path, "r", encoding="utf-8") as f:
                    active_games_cfg = json.load(f).get("active_games", {})
            except: pass

        self.games_list = [g for g in list(self.main_ui.manager.games.keys()) if active_games_cfg.get(g, True)]
        
        # Trouver l'index du jeu actif pour démarrer la sélection dessus
        try:
            self.selected_index = self.games_list.index(active_game) if active_game in self.games_list else 0
        except:
            self.selected_index = 0

        # Titre
        title_text = Loc.get("qs_busy") if is_busy else Loc.get("qs_title")
        title_color = "#ff9900" if is_busy else "#00ff99"
        tk.Label(self.overlay, text=title_text, font=("Segoe UI", 12, "bold"), bg="#121212", fg=title_color).pack(pady=(15, 5))
        
        # Ligne de séparation verte esthétique sous le titre (pour séparer proprement le menu)
        separator = tk.Frame(self.overlay, bg="#00ff99", height=2, width=220)
        separator.pack(pady=(0, 15))
        
        # Container avec Scrollbar (Canvas) - Abaissé pour éviter tout chevauchement avec le titre
        container = tk.Frame(self.overlay, bg="#121212")
        container.pack(fill="both", expand=True, padx=10, pady=(5, 5))

        self.canvas = tk.Canvas(container, bg="#121212", highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#121212")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        
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
            if btn_id in ["FACE_BOTTOM", "FACE_RIGHT"]:
                if btn_id == "FACE_BOTTOM":
                    self._on_confirm()
                    return True
                else: # FACE_RIGHT pour quitter
                    self.close()
                    return True
            
            if btn_id in ["SELECT", "START", "L3", "R3"]:
                self.close()
                return True

        return False

    def _update_selection(self):
        """Met à jour l'apparence visuelle et assure la visibilité du bouton sélectionné."""
        if not self.buttons: return
        
        for i, btn in enumerate(self.buttons):
            if i == self.selected_index:
                btn.configure(bg="#00ff99", fg="black") 
                
                if self.canvas:
                    # Force la mise à jour de l'affichage pour obtenir les dimensions réelles
                    self.overlay.update_idletasks()
                    
                    btn_y = btn.winfo_y()
                    btn_h = btn.winfo_height()
                    canvas_h = self.canvas.winfo_height()
                    total_h = self.scrollable_frame.winfo_height()
                    
                    if self.selected_index == 0:
                        # Toujours scroller tout en haut pour le premier élément
                        self.canvas.yview_moveto(0)
                    elif canvas_h > 1 and total_h > 1 and total_h > canvas_h:
                        top, bottom = self.canvas.yview()
                        
                        btn_top_rel = btn_y / total_h
                        btn_bottom_rel = (btn_y + btn_h) / total_h
                        
                        if btn_top_rel < top:
                            self.canvas.yview_moveto(btn_top_rel)
                        elif btn_bottom_rel > bottom:
                            self.canvas.yview_moveto(btn_bottom_rel - (canvas_h / total_h))
            else:
                game_name = self.games_list[i]
                is_active = (game_name == self.main_ui.manager.active_game_name)
                bg = "#004422" if is_active else "#1e1e1e"
                fg = "#00ff99" if is_active else "white"
                btn.configure(bg=bg, fg=fg)

    def _on_confirm(self):
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
            if self.main_ui.is_optimizing_for_game:
                self.main_ui.controller_polling_interval = 100 # Un peu plus lent en jeu pour économiser du CPU
            else:
                self.main_ui.controller_polling_interval = 30 # Rapide dans le Hub
