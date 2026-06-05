import tkinter as tk
from tkinter import ttk
import os
import json
from localization import Loc

class GameCard:
    """
    Handles the UI and logic for a single game card in the launcher grid.
    """
    def __init__(self, parent_ui, game_name, game_code, row=0, col=0):
        self.ui = parent_ui
        self.name = game_name
        self.code = game_code
        self.row = row
        self.col = col
        
        # Individual Theme Color (Defaulting if not in metadata)
        # This will be overridden by metadata if passed
        self.theme_color = "#00ff99"
        
        self._create_widgets()

    def _create_widgets(self):
        # Premium Card Design with Hover Effect
        self.card_border = tk.Frame(self.ui.game_frame, bg=self.ui.colors["border"], padx=1, pady=1)
        self.card_border.grid(row=self.row, column=self.col, padx=15, pady=15)
        
        self.card = tk.Frame(self.card_border, bg=self.ui.colors["card_bg"], bd=0)
        self.card.pack()
        
        is_registered = self.name in self.ui.manager.games
        
        # Load metadata if possible for this game
        game_meta = getattr(self.ui, 'games_metadata', {}).get(self.name, {})
        self.theme_color = game_meta.get("color", "#00ff99")

        def on_enter(e):
            self.card_border.configure(bg=self.theme_color)
            self.lbl_tag.configure(fg=self.theme_color)
            
        def on_leave(e):
            self.card_border.configure(bg=self.ui.colors["border"])
            self.lbl_tag.configure(fg="white")

        # Name Tag - Now at the top of the card
        display_name = self.name.upper().replace("THE LEGEND OF ZELDA: ", "")
        if len(display_name) > 22: 
            display_name = display_name[:19] + "..."

        self.lbl_tag = tk.Label(
            self.card, text=display_name, 
            font=("Segoe UI", 9, "bold"), fg="white" if is_registered else "#555", bg=self.ui.colors["card_bg"],
            pady=12
        )
        self.lbl_tag.pack(side="top", fill="x")
        
        # Image Loading Logic
        has_pil = getattr(self.ui, 'HAS_PIL', False)
        if has_pil and (self.name in self.ui.game_images or self.name in self.ui.game_images_disabled):
            if is_registered:
                img = self.ui.game_images.get(self.name, self.ui.game_images.get("_default"))
            else:
                img = self.ui.game_images_disabled.get(self.name, self.ui.game_images.get("_default"))
            
            btn = tk.Button(
                self.card, image=img, command=lambda: self.ui.launch_game(self.name),
                bg=self.ui.colors["card_bg"], activebackground="#25252d", borderwidth=0, 
                relief="flat", cursor="hand2" if is_registered else "arrow", 
                highlightthickness=0, state="normal" if is_registered else "disabled"
            )
        else:
            # Placeholder with improved look
            txt = self.name.upper().replace("THE LEGEND OF ZELDA: ", "")
            btn = tk.Button(
                self.card, text=txt, command=lambda: self.ui.launch_game(self.name),
                width=24, height=14, bg="#111", fg="#333",
                font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                activebackground="#151515", activeforeground="#00ff99",
                state="normal" if is_registered else "disabled"
            )

        btn.is_game_registered = is_registered
        btn.pack()
        self.ui.action_widgets.append(btn)
        
        # Hover bindings - only if registered
        if is_registered:
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Controls Footer
        self.ctrl_bg = tk.Frame(self.card, bg=self.ui.colors["card_bg"], height=50)
        self.ctrl_bg.pack(side="bottom", fill="x")
        self.ctrl_bg.pack_propagate(False)

        self.ctrl_container = tk.Frame(self.ctrl_bg, bg=self.ui.colors["card_bg"], bd=0)
        self.ctrl_container.pack(expand=True)
        
        # Toggles
        has_tracker = self.ui.manager.poptracker_packs.get(self.name)
        
        v_pop = tk.BooleanVar()
        self.ui.poptracker_vars[self.name] = v_pop
        
        # Load current state from config via LauncherUI
        if os.path.exists(self.ui.config_path):
            try:
                with open(self.ui.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    v_pop.set(config_data.get("poptracker_enabled", {}).get(self.name, False))
            except: pass
        
        if has_tracker:
            self.create_icon_toggle(self.ctrl_container, "🗺️", v_pop, "#00ff99", is_registered)

        v_broad = tk.BooleanVar(value=True)
        self.ui.broadcast_vars[self.name] = v_broad
        
        if os.path.exists(self.ui.config_path):
            try:
                with open(self.ui.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    v_broad.set(config_data.get("broadcast_enabled_games", {}).get(self.name, True))
            except: pass
            
        self.create_icon_toggle(self.ctrl_container, "📡", v_broad, "#e67e22", is_registered)
        
        # v_pad = tk.BooleanVar()
        # self.ui.auto_config_per_game[self.name] = v_pad
        # if os.path.exists(self.ui.config_path):
        #     try:
        #         with open(self.ui.config_path, "r", encoding="utf-8") as f:
        #             config_data = json.load(f)
        #             v_pad.set(config_data.get("auto_controller_per_game", {}).get(self.name, True))
        #     except: pass
        
        # gp_cb = self.create_icon_toggle(self.ctrl_container, "🎮", v_pad, "#3498db", is_registered)
        # gp_cb.is_auto_config_supported = (self.name != "A Link Between Worlds")
        # if not gp_cb.is_auto_config_supported:
        #     gp_cb.configure(state="disabled")
        # self.ui.gamepad_widgets.append(gp_cb)

    def create_icon_toggle(self, parent, text, var, color, is_registered):
        cb = tk.Checkbutton(
            parent, text=text, variable=var,
            indicatoron=False,
            bg=self.ui.colors["card_bg"], fg="#444", selectcolor=self.ui.colors["card_bg"],
            activebackground=self.ui.colors["card_bg"], activeforeground=color,
            font=("Segoe UI", 13), borderwidth=0, padx=12, pady=0,
            cursor="hand2" if is_registered else "arrow"
        )
        def update_color():
            cb.configure(fg=color if var.get() else "#444")
            if text == "📡":
                self.ui.update_global_broadcast_state()
            else:
                self.ui.save_settings()
        
        cb.configure(command=update_color)
        if var.get(): cb.configure(fg=color)
        
        cb.pack(side="left")
        cb.is_game_registered = is_registered
        if not is_registered:
            cb.configure(state="disabled")
        self.ui.action_widgets.append(cb)
        return cb
