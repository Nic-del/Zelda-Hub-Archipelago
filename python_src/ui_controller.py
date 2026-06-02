import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob
import json
import pygame
import sys

# Ajouter le dossier courant au path pour importer les modules du controller
sys.path.append(os.path.join(os.path.dirname(__file__), 'controller'))

try:
    from controller_manager import ControllerManager, OutputAdapter
    from launcher_core import CONFIG_PATH
    from localization import Loc
except ImportError:
    print("Erreur: Impossible d'importer le système de contrôleur.")
    sys.exit(1)


    pass # Plus besoin de wrapper la sortie si on n'a plus de simulateur


class TkinterOutput(OutputAdapter):
    """
    Au lieu d'afficher dans la console, on envoie les actions à l'interface graphique.
    """
    def __init__(self, ui_callback):
        self.ui_callback = ui_callback

    def send_action(self, mapped_action):
        self.ui_callback(mapped_action)


class UIControllerApp:
    def __init__(self, root):
        self.root = root
        
        # Localisation
        self.config_path = CONFIG_PATH
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    lang = json.load(f).get("language", "fr")
                    Loc.set_lang(lang)
            except: pass

        self.root.title(Loc.get("ctrl_title"))
        self.root.geometry("1000x750")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)

        # Force foreground
        self.root.attributes('-topmost', True)
        self.root.update()
        self.root.attributes('-topmost', False)
        self.root.lift()
        self.root.focus_force()

        # Style pour le mode sombre
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 10))
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TButton", padding=6, relief="flat", background="#333", foreground="white")
        style.map("TButton", background=[('active', '#555')])

        # Split Interface
        self.left_panel = tk.Frame(root, bg="#1e1e1e")
        self.left_panel.pack(side="left", fill="both", expand=True)

        self.right_panel = tk.Frame(root, bg="#1e1e1e", width=400)
        self.right_panel.pack(side="right", fill="y", padx=10, pady=10)

        # Config globale du Hub (Droit - Haut)
        hub_frame = tk.LabelFrame(self.right_panel, text=Loc.get("hub_shortcut_frame"), bg="#1e1e1e", fg="#3498db", font=("Segoe UI", 11, "bold"))
        hub_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(hub_frame, text=Loc.get("hub_shortcut_label"), bg="#1e1e1e", fg="white", font=("Segoe UI", 9)).pack(pady=(5, 0))
        
        self.hub_btn_var = tk.StringVar(value="CAPTURE")
        self.hub_name_var = tk.StringVar()
        # Charger depuis la config au démarrage
        self.config_path = CONFIG_PATH
        print(f"[ControllerUI] Utilisation de la config : {self.config_path}")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    val = data.get("hub_controller_open_btn", "CAPTURE")
                    self.hub_btn_var.set(val)
                    
                    saved_ctrl = data.get("hub_controller_name", "")
                    if not saved_ctrl or saved_ctrl in ["Toutes", "All", "All controllers", "Toutes les manettes"]:
                        self.hub_name_var.set(Loc.get("all_controllers_option"))
                    else:
                        self.hub_name_var.set(saved_ctrl)
                    print(f"[ControllerUI] Valeur Hub chargée : {val}, Manette chargée : {self.hub_name_var.get()}")
            except Exception as e:
                print(f"[ControllerUI] Erreur lors du chargement : {e}")
                pass
            
        hub_entry_frame = tk.Frame(hub_frame, bg="#1e1e1e")
        hub_entry_frame.pack(pady=5, padx=10, fill="x")
        
        self.hub_entry = tk.Entry(hub_entry_frame, textvariable=self.hub_btn_var, bg="#2d2d2d", fg="#3498db", borderwidth=0, font=("Consolas", 10, "bold"), insertbackground="white")
        self.hub_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Petit bouton pour aider à mapper le raccourci hub
        self.btn_hub_map = ttk.Button(hub_entry_frame, text=Loc.get("assign_btn"), width=8, command=self.start_listening_hub)
        self.btn_hub_map.pack(side="right")
        
        tk.Label(hub_frame, text=Loc.get("hub_shortcut_hint"), bg="#1e1e1e", fg="#666", font=("Segoe UI", 8)).pack(pady=(0, 5))

        # NOUVEAU: Sélecteur de manette pour détection du raccourci Hub
        tk.Label(hub_frame, text=Loc.get("lbl_hub_controller_name"), bg="#1e1e1e", fg="white", font=("Segoe UI", 9)).pack(pady=(5, 0))
        
        self.hub_name_combo = ttk.Combobox(hub_frame, textvariable=self.hub_name_var, state="readonly")
        self.hub_name_combo.pack(fill="x", padx=10, pady=(2, 5))

        # Header (Gauche)
        tk.Label(self.left_panel, text=Loc.get("ctrl_header"), font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="#3498db").pack(pady=10)

        # Frame des profils (Gauche)
        prof_frame = ttk.Frame(self.left_panel)
        prof_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(prof_frame, text=Loc.get("active_profile_lbl"), font=("Segoe UI", 12, "bold")).pack(side="left")
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(prof_frame, textvariable=self.profile_var, state="readonly", width=30)
        self.profile_combo.pack(side="left", padx=10)
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        
        self.save_btn = ttk.Button(prof_frame, text=Loc.get("save_apply_btn"), command=self.save_and_apply)
        self.save_btn.pack(side="left", padx=20)
        
        self.refresh_profiles()

        # Frame des manettes connectées (Gauche)
        dev_frame = tk.LabelFrame(self.left_panel, text=Loc.get("detected_ctrls_frame"), bg="#1e1e1e", fg="#3498db", font=("Segoe UI", 11, "bold"))
        dev_frame.pack(fill="x", padx=20, pady=5)
        
        # Sélecteur de manette
        self.device_var = tk.StringVar(value=Loc.get("searching_devs"))
        self.device_combo = ttk.Combobox(dev_frame, textvariable=self.device_var, state="readonly", width=50)
        self.device_combo.pack(fill="x", padx=10, pady=10)
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_change)

        # Frame Visualisation Manette (Gauche)
        vis_frame = tk.LabelFrame(self.left_panel, text=Loc.get("live_vis_frame"), bg="#1e1e1e", fg="#3498db", font=("Segoe UI", 11, "bold"))
        vis_frame.pack(fill="x", padx=20, pady=5)
        
        self.canvas = tk.Canvas(vis_frame, width=400, height=200, bg="#2d2d2d", highlightthickness=0)
        self.canvas.pack(pady=10)
        
        self.axis_state = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        self.current_visual_mode = "base"
        self.visual_colors = {}
        self.visual_items = {}
        self.draw_controller_base()

        # Frame des logs (testing) (Gauche)
        log_frame = tk.LabelFrame(self.left_panel, text=Loc.get("test_profiles_frame"), bg="#1e1e1e", fg="#3498db", font=("Segoe UI", 11, "bold"))
        log_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Liste pour afficher les logs
        self.log_list = tk.Listbox(log_frame, bg="#2d2d2d", fg="white", font=("Consolas", 10), selectbackground="#444", relief="flat", highlightthickness=0)
        self.log_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initialiser le ControllerManager
        profiles_path = os.path.join(os.path.dirname(__file__), 'controller', 'profiles')
        # On passe directement self.log_action comme adaptateur de sortie pour la visualisation
        ui_output = TkinterOutput(self.log_action)
        self.manager = ControllerManager(profiles_path, output_adapter=ui_output)
        
        # Setup the mapping interface
        self.setup_mapping_ui()

        # Charger le profil sélectionné
        if self.profile_combo['values']:
            self.profile_combo.current(0)
            self.on_profile_change(None)
            
        # Register the interception callback for mapping mode
        self.listening_action = None
        self.listening_hub = False
        self.hub_combo_keys = set()
        self.manager.raw_input_callback = self.handle_raw_input
            
        # Lancer la boucle Pygame interne
        self.poll_controllers()

    def setup_mapping_ui(self):
        map_frame = tk.LabelFrame(self.right_panel, text=Loc.get("mapping_tab_frame"), bg="#1e1e1e", fg="#3498db", font=("Segoe UI", 11, "bold"))
        map_frame.pack(fill="both", expand=True)

        # Style pour Treeview
        style = ttk.Style()
        style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d")
        style.map("Treeview", background=[('selected', '#555')])

        cols = (Loc.get("logical_action_col"), Loc.get("physical_input_col"))
        self.tree = ttk.Treeview(map_frame, columns=cols, show="headings", height=15)
        self.tree.heading(cols[0], text=cols[0])
        self.tree.heading(cols[1], text=cols[1])
        self.tree.column(cols[0], width=150)
        self.tree.column(cols[1], width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Mapping status label
        self.mapping_status_var = tk.StringVar(value=Loc.get("mapping_status_select"))
        tk.Label(map_frame, textvariable=self.mapping_status_var, bg="#1e1e1e", fg="#fff", font=("Segoe UI", 9, "italic")).pack(pady=5)

        # Boutons d'action
        btn_frame = tk.Frame(map_frame, bg="#1e1e1e")
        btn_frame.pack(fill="x", pady=10, padx=10)

        self.btn_assign = ttk.Button(btn_frame, text=Loc.get("listening_mode_btn"), command=self.start_listening)
        self.btn_assign.pack(side="left", padx=5)

        self.btn_remove = ttk.Button(btn_frame, text=Loc.get("remove_mapping_btn"), command=self.remove_mapping)
        self.btn_remove.pack(side="left", padx=5)

        ttk.Button(map_frame, text=Loc.get("save_profile_btn"), command=self.save_mapping).pack(fill="x", padx=10, pady=10)

    def refresh_mapping_list(self):
        # Mémoriser la sélection actuelle avant mise à jour
        selected_action = None
        sel = self.tree.selection()
        if sel:
            selected_action = self.tree.item(sel[0])['values'][0]
            
        # Mémoriser la progression du scroll
        scroll_pos = self.tree.yview()

        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not hasattr(self, 'manager'): return
        
        # Inverser le mapping du profile_manager pour avoir Action -> Input
        reverse_map = {}
        for k, v in self.manager.profile_manager.mapping.items():
            reverse_map[v] = k
        
        # On utilise une liste stable d'actions pour éviter qu'elles ne disparaissent
        if not hasattr(self, 'known_actions'):
            self.known_actions = sorted(reverse_map.keys())
            
        for action in self.known_actions:
            phys_input = reverse_map.get(action, "(Non assigné)")
            item = self.tree.insert("", "end", values=(action, phys_input))
            if action == selected_action:
                self.tree.selection_set(item)
                
        # Restaurer le scroll
        self.tree.yview_moveto(scroll_pos[0])

    def start_listening(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner une action dans la liste.")
            return
            
        item = self.tree.item(selected[0])
        self.listening_action = item['values'][0]
        self.mapping_status_var.set(Loc.get("listening_for", action=self.listening_action))
        
    def handle_raw_input(self, raw_event):
        """Intercepte les inputs Pygame quand on veut remapper."""
        if not self.listening_action and not getattr(self, "listening_hub", False):
            return False # Pas en écoute, on laisse passer au mapper normal
            
        # Ignore les relâchements de boutons pour l'assignation
        if raw_event["type"] == "button" and raw_event["state"] == 0:
            return True # On l'intercepte quand même pour l'absorber
            
        # Ignore les retours à zéro d'axes et requiert une pression forte (> 0.5)
        # pour éviter d'assigner par accident un stick qui a un léger drift
        if raw_event["type"] == "axis" and abs(raw_event["state"]) < 0.5:
            return True
            
        if raw_event["type"] == "hat" and "RELEASE" in raw_event["id"]:
            return True
            
        input_id = raw_event["id"]
        
        # Cas 1 : Mapping du raccourci Hub (Support Combos)
        if getattr(self, "listening_hub", False):
            state = raw_event.get("state", 0)
            
            # On considère comme un "appui" si state est 1 (bouton/hat) ou > 0.5 (axis)
            is_press = False
            if raw_event["type"] in ["button", "hat"]:
                is_press = (state == 1 or (raw_event["type"] == "hat" and input_id != "DPAD_RELEASE"))
            elif raw_event["type"] == "axis":
                is_press = abs(state) > 0.5

            if is_press:
                # Ajout à la combinaison en cours
                if input_id not in self.hub_combo_keys:
                    self.hub_combo_keys.add(input_id)
                    # Mise à jour de l'affichage en temps réel
                    combo_str = "+".join(sorted(list(self.hub_combo_keys)))
                    self.hub_btn_var.set(combo_str)
                    print(f"[ControllerUI] Combo Hub en cours : {combo_str}")
            else:
                # C'est un relâchement. Si on a des touches capturées, on considère que le combo est fini
                # quand l'utilisateur relâche TOUT.
                if self.hub_combo_keys:
                    # On finit dès le premier relâchement d'une des touches de la combo pour valider
                    # (ou on pourrait attendre que toutes soient relâchées, mais c'est souvent moins réactif)
                    self.listening_hub = False
                    self.btn_hub_map.configure(text=Loc.get("assign_btn"))
                    final_combo = "+".join(sorted(list(self.hub_combo_keys)))
                    self.hub_btn_var.set(final_combo)
                    self._save_hub_shortcut()
                    print(f"[ControllerUI] Nouveau raccourci Hub (Combo) : {final_combo}")
            
            return True

        # Cas 2 : Mapping d'une action de profil
        action = self.listening_action
        
        # Mettre à jour le mapping en mémoire
        # 1. Retirer les anciennes associations à cet input_id s'il y en a
        pm = self.manager.profile_manager
        old_mapping = pm.mapping.copy()
        
        for k, v in old_mapping.items():
            if v == action:
                del pm.mapping[k] # Efface l'ancienne touche assignée à cette action
                
        # 2. Associer la nouvelle touche
        pm.mapping[input_id] = action
        
        self.mapping_status_var.set(Loc.get("assigned_msg", action=action, input_id=input_id))
        self.listening_action = None
        self.refresh_mapping_list()
        
        return True # On a consommé l'event

    def remove_mapping(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        action = item['values'][0]
        
        pm = self.manager.profile_manager
        for k, v in list(pm.mapping.items()):
            if v == action:
                del pm.mapping[k]
                
        self.refresh_mapping_list()
        self.mapping_status_var.set(Loc.get("mapping_removed", action=action))

    def save_mapping(self):
        if self.manager.profile_manager.save_profile():
            # Sauvegarder aussi le raccourci Hub global
            self._save_hub_shortcut()
            messagebox.showinfo("Succès", Loc.get("save_success"))
        else:
            messagebox.showerror("Erreur", "Impossible de sauvegarder le profil.")

    def start_listening_hub(self):
        """Démarre l'écoute pour le raccourci Hub (Support Combos)."""
        self.listening_hub = True
        self.listening_action = None
        self.hub_combo_keys = set() # Reset de la combo
        self.hub_btn_var.set("...") # Indicateur visuel
        self.btn_hub_map.configure(text=Loc.get("listening_btn"))

    def refresh_profiles(self):
        profiles_path = os.path.join(os.path.dirname(__file__), 'controller', 'profiles')
        if not os.path.exists(profiles_path):
            os.makedirs(profiles_path)
            
        profiles = [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(profiles_path, "*.json"))]
        if not profiles:
            profiles = ["default"]
            
        self.profile_combo['values'] = profiles

    def on_profile_change(self, event):
        selected = self.profile_var.get()
        if hasattr(self, 'manager'):
            success = self.manager.load_game_profile(selected)
            if success:
                # self.log_list.insert(tk.END, f"Profil: {selected}")
                self.log_list.yview(tk.END)
                self.refresh_mapping_list()
                
                # Switch visual template
                if selected in ["oot", "mm"]:
                    self.draw_controller_n64()
                elif selected in ["ww", "tp", "ss"]:
                    self.draw_controller_gc()
                else:
                    self.draw_controller_base()
                    
                # Mémoriser les actions du profil pour ne pas qu'elles disparaissent
                reverse_map = {}
                for k, v in self.manager.profile_manager.mapping.items():
                    reverse_map[v] = k
                self.known_actions = sorted(reverse_map.keys())
                self.refresh_mapping_list()

    def log_action(self, mapped_action):
        """Callback appelée par le OutputAdapter quand une action est déclenchée."""
        action = mapped_action["action"]
        state = mapped_action["state"]
        joy_id = mapped_action["joy_id"]
        raw = mapped_action.get("raw_input", "?")
        
        # Récupération du type de manette pour un affichage "User Friendly"
        ctrl_type = "Générique"
        if hasattr(self, 'manager') and joy_id in self.manager.detector.joysticks:
            ctrl_type = self.manager.detector.joysticks[joy_id]["type"]

        # Dictionnaire visuel pour traduire la constante sémantique en bouton physique connu
        visual_translation = {
            "Xbox": {"FACE_BOTTOM": "A", "FACE_RIGHT": "B", "FACE_LEFT": "X", "FACE_TOP": "Y"},
            "PlayStation": {"FACE_BOTTOM": "Croix (X)", "FACE_RIGHT": "Rond (O)", "FACE_LEFT": "Carré (☐)", "FACE_TOP": "Triangle (△)"},
            "Nintendo": {"FACE_BOTTOM": "B", "FACE_RIGHT": "A", "FACE_LEFT": "Y", "FACE_TOP": "X"}
        }

        # On essaie de traduire. Si ça échoue, on affiche le raw (ex: L1)
        display_name = raw
        if ctrl_type in visual_translation and raw in visual_translation[ctrl_type]:
            display_name = visual_translation[ctrl_type][raw]
        
        if type(state) is float:
            log_msg = f"[Manette {joy_id} - {ctrl_type}] {display_name} -> {action} : {state:.2f}"
            
            # MAJ Visuel Stick
            if raw == "LEFT_STICK_X": self.axis_state[0] = float(state)
            elif raw == "LEFT_STICK_Y": self.axis_state[1] = float(state)
            elif raw == "RIGHT_STICK_X": self.axis_state[2] = float(state)
            elif raw == "RIGHT_STICK_Y": self.axis_state[3] = float(state)
            
            if self.current_visual_mode == "n64":
                # N64 Stick
                n64_sx = 200 + (self.axis_state.get(0, 0.0) * 15)
                n64_sy = 110 + (self.axis_state.get(1, 0.0) * 15)
                self.canvas.coords(self.visual_items["N64_Stick"], n64_sx-8, n64_sy-8, n64_sx+8, n64_sy+8)
                
                # N64 C-Stick
                n64_cx = 300 + (self.axis_state.get(2, 0.0) * 12)
                n64_cy = 70 + (self.axis_state.get(3, 0.0) * 12)
                self.canvas.coords(self.visual_items["N64_CStick"], n64_cx-6, n64_cy-6, n64_cx+6, n64_cy+6)
                
            elif self.current_visual_mode == "gc":
                # GC Main Stick
                gc_sx = 100 + (self.axis_state.get(0, 0.0) * 15)
                gc_sy = 80 + (self.axis_state.get(1, 0.0) * 15)
                self.canvas.coords(self.visual_items["GC_Stick"], gc_sx-8, gc_sy-8, gc_sx+8, gc_sy+8)
                
                # GC C-Stick
                gc_cx = 240 + (self.axis_state.get(2, 0.0) * 12)
                gc_cy = 150 + (self.axis_state.get(3, 0.0) * 12)
                self.canvas.coords(self.visual_items["GC_CStick"], gc_cx-6, gc_cy-6, gc_cx+6, gc_cy+6)

            else:
                # Stick gauche (X=0, Y=1)
                ls_x = 100 + (self.axis_state.get(0, 0.0) * 20)
                ls_y = 100 + (self.axis_state.get(1, 0.0) * 20)
                self.canvas.coords(self.visual_items["LS"], ls_x-8, ls_y-8, ls_x+8, ls_y+8)
                # Stick droit (X=2, Y=3)
                rs_x = 250 + (self.axis_state.get(2, 0.0) * 20)
                rs_y = 140 + (self.axis_state.get(3, 0.0) * 20)
                self.canvas.coords(self.visual_items["RS"], rs_x-8, rs_y-8, rs_x+8, rs_y+8)
                
            # Check if this axis is mapped to a button conceptually (like L2 -> LButton)
            v_key = action if action in self.visual_items else raw
            if v_key in self.visual_items and "STICK" not in v_key:
                base_col, act_col = self.visual_colors.get(v_key, ("", "red"))
                color = act_col if state > 0.5 else base_col
                self.canvas.itemconfig(self.visual_items[v_key], fill=color)
                
        else:
            state_str = "PRESSE" if state else "RELACHE"
            log_msg = f"[Manette {joy_id} - {ctrl_type}] {display_name} -> {action} : {state_str}"
            
            # MAJ Visuel Boutons: on teste l'action logique PUIS l'input physique
            v_key = action if action in self.visual_items else raw
            if v_key in self.visual_items:
                base_col, act_col = self.visual_colors.get(v_key, ("", "red"))
                color = act_col if state else base_col
                self.canvas.itemconfig(self.visual_items[v_key], fill=color)
                
            if "DPAD_" in raw and self.current_visual_mode == "base":
                # Special reset for generic arrows
                for d in ["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"]:
                    if d in self.visual_items:
                        self.canvas.itemconfig(self.visual_items[d], fill="#444")
                if state == 1 and raw != "DPAD_RELEASE":
                    if raw in self.visual_items:
                        self.canvas.itemconfig(self.visual_items[raw], fill="red")
            
        self.log_list.insert(tk.END, log_msg)
        self.log_list.yview(tk.END)
        
        # Limiter la taille du log
        if self.log_list.size() > 50:
            self.log_list.delete(0)

    def on_canvas_click(self, e, key):
        """Quand l'utilisateur clique sur un bouton de la manette virtuelle."""
        action = key
        
        # Si on est sur la manette générique (qui affiche les inputs physiques),
        # il faut retrouver l'action logique actuellement assignée à ce bouton
        if getattr(self, "current_visual_mode", "base") == "base":
            mapped = self.manager.profile_manager.get_action_for_input(key)
            if mapped:
                action = mapped
            else:
                return # Bouton non mappé, on ne peut pas lancer l'assignation depuis ici
                
        # Trouver la ligne correspondante dans le tableau
        for child in self.tree.get_children():
            if self.tree.item(child)['values'][0] == action:
                self.tree.selection_set(child)
                self.tree.see(child)
                self.start_listening()
                break

    def reg_item(self, key, item, base_color="", active_color="red", text_item=None):
        self.visual_items[key] = item
        self.visual_colors[key] = (base_color, active_color)
        
        # Rend les éléments cliquables
        self.canvas.tag_bind(item, "<Button-1>", lambda e, k=key: self.on_canvas_click(e, k))
        if text_item is not None:
            self.canvas.tag_bind(text_item, "<Button-1>", lambda e, k=key: self.on_canvas_click(e, k))
        
    def draw_controller_base(self):
        """Dessine une manette simplifiée sur le canvas."""
        self.canvas.delete("all")
        self.visual_items = {}
        self.visual_colors = {}
        self.current_visual_mode = "base"
        
        # Corps central
        self.canvas.create_oval(30, 30, 170, 190, fill="#3a3a3a", outline="")
        self.canvas.create_oval(230, 30, 370, 190, fill="#3a3a3a", outline="")
        self.canvas.create_rectangle(100, 50, 300, 170, fill="#3a3a3a", outline="")
        
        # Stick Gauche (100, 100)
        self.canvas.create_oval(70, 70, 130, 130, fill="#222", outline="#555")
        self.reg_item("LS", self.canvas.create_oval(92, 92, 108, 108, fill="red"), "red", "red")
        
        # Stick Droit (250, 140)
        self.canvas.create_oval(220, 110, 280, 170, fill="#222", outline="#555")
        self.reg_item("RS", self.canvas.create_oval(242, 132, 258, 148, fill="red"), "red", "red")
        
        # Croix D-Pad (100, 150)
        self.canvas.create_rectangle(90, 135, 110, 175, fill="#222", outline="")
        self.canvas.create_rectangle(80, 145, 120, 165, fill="#222", outline="")
        self.reg_item("DPAD_UP", self.canvas.create_rectangle(90, 135, 110, 145, fill="#444", outline=""), "#444", "red")
        self.reg_item("DPAD_DOWN", self.canvas.create_rectangle(90, 165, 110, 175, fill="#444", outline=""), "#444", "red")
        self.reg_item("DPAD_LEFT", self.canvas.create_rectangle(80, 145, 90, 165, fill="#444", outline=""), "#444", "red")
        self.reg_item("DPAD_RIGHT", self.canvas.create_rectangle(110, 145, 120, 165, fill="#444", outline=""), "#444", "red")
        
        # Boutons d'Action (300, 90)
        def draw_btn(x, y, text, key):
            self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="#222", outline="#555")
            item = self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="", outline="")
            txt = self.canvas.create_text(x, y, text=text, fill="#aaa", font=("Segoe UI", 8, "bold"))
            self.reg_item(key, item, "", "red", text_item=txt)
            
        draw_btn(300, 120, "S", "FACE_BOTTOM")
        draw_btn(330, 90, "E", "FACE_RIGHT")
        draw_btn(270, 90, "W", "FACE_LEFT")
        draw_btn(300, 60, "N", "FACE_TOP")
        
        # L1 / R1
        self.canvas.create_rectangle(70, 15, 130, 35, fill="#222", outline="#555")
        item_L1 = self.canvas.create_rectangle(70, 15, 130, 35, fill="", outline="")
        txt_L1 = self.canvas.create_text(100, 25, text="L1", fill="#aaa", font=("Segoe UI", 8))
        self.reg_item("L1", item_L1, "", "white", text_item=txt_L1)
        
        self.canvas.create_rectangle(270, 15, 330, 35, fill="#222", outline="#555")
        item_R1 = self.canvas.create_rectangle(270, 15, 330, 35, fill="", outline="")
        txt_R1 = self.canvas.create_text(300, 25, text="R1", fill="#aaa", font=("Segoe UI", 8))
        self.reg_item("R1", item_R1, "", "white", text_item=txt_R1)

    def draw_controller_n64(self):
        """Dessine une manette N64 sur le canvas."""
        self.canvas.delete("all")
        self.visual_items = {}
        self.visual_colors = {}
        self.current_visual_mode = "n64"
        
        c = "#747880" # Gris N64
        
        # Prongs
        self.canvas.create_oval(50, 70, 110, 190, fill=c, outline="")
        self.canvas.create_oval(170, 70, 230, 190, fill=c, outline="")
        self.canvas.create_oval(290, 70, 350, 190, fill=c, outline="")
        # Main Body
        self.canvas.create_oval(50, 40, 350, 110, fill=c, outline="")
        
        # D-Pad (Left prong)
        self.canvas.create_rectangle(65, 85, 95, 125, fill="#222", outline="")
        self.canvas.create_rectangle(55, 95, 105, 115, fill="#222", outline="")
        self.reg_item("Dpad_Up", self.canvas.create_rectangle(70, 85, 90, 95, fill="", outline=""), "", "white")
        self.reg_item("Dpad_Down", self.canvas.create_rectangle(70, 115, 90, 125, fill="", outline=""), "", "white")
        self.reg_item("Dpad_Left", self.canvas.create_rectangle(55, 95, 65, 115, fill="", outline=""), "", "white")
        self.reg_item("Dpad_Right", self.canvas.create_rectangle(95, 95, 105, 115, fill="", outline=""), "", "white")
        
        # Center Stick (Center prong)
        self.canvas.create_oval(180, 90, 220, 130, fill="#ccc", outline="#888")
        self.reg_item("N64_Stick", self.canvas.create_oval(192, 102, 208, 118, fill="#555", outline=""), "#555", "#555")
        
        # Z-Trigger (Behind Center Prong, draw below it logically)
        self.canvas.create_rectangle(190, 150, 210, 170, fill="#333", outline="")
        item_ZR = self.canvas.create_rectangle(190, 150, 210, 170, fill="", outline="")
        txt_ZR = self.canvas.create_text(200, 160, text="Z", fill="#aaa", font=("Segoe UI", 9))
        self.reg_item("ZR", item_ZR, "", "white", text_item=txt_ZR)
        
        # C-Buttons (Yellow stick for representation)
        self.canvas.create_oval(280, 50, 320, 90, fill="#222", outline="")
        self.reg_item("N64_CStick", self.canvas.create_oval(294, 64, 306, 76, fill="#e8c100", outline=""), "#e8c100", "#e8c100")
        
        # A, B buttons (A=Blue, B=Green)
        item_B = self.canvas.create_oval(275, 100, 305, 130, fill="#0a8833", outline="")
        txt_B = self.canvas.create_text(290, 115, text="B", fill="white", font=("Segoe UI", 10, "bold"))
        self.reg_item("B", item_B, "#0a8833", "white", text_item=txt_B)
        
        item_A = self.canvas.create_oval(310, 85, 340, 115, fill="#1f4c9c", outline="")
        txt_A = self.canvas.create_text(325, 100, text="A", fill="white", font=("Segoe UI", 10, "bold"))
        self.reg_item("A", item_A, "#1f4c9c", "white", text_item=txt_A)
        
        # Start button (Red, center)
        item_S = self.canvas.create_oval(185, 55, 215, 75, fill="#cc1111", outline="")
        txt_S = self.canvas.create_text(200, 65, text="S", fill="white", font=("Segoe UI", 8, "bold"))
        self.reg_item("Start", item_S, "#cc1111", "white", text_item=txt_S)
        
        # L / R
        item_L = self.canvas.create_rectangle(60, 20, 100, 40, fill="#555", outline="")
        txt_L = self.canvas.create_text(80, 30, text="L", fill="#ddd", font=("Segoe UI", 8))
        self.reg_item("LButton", item_L, "#555", "white", text_item=txt_L)
        
        item_R = self.canvas.create_rectangle(300, 20, 340, 40, fill="#555", outline="")
        txt_R = self.canvas.create_text(320, 30, text="R", fill="#ddd", font=("Segoe UI", 8))
        self.reg_item("RButton", item_R, "#555", "white", text_item=txt_R)

    def draw_controller_gc(self):
        """Dessine une manette GameCube sur le canvas."""
        self.canvas.delete("all")
        self.visual_items = {}
        self.visual_colors = {}
        self.current_visual_mode = "gc"
        
        c = "#574ba3" # Violet Gamecube
        
        # Main Body
        self.canvas.create_oval(30, 40, 170, 190, fill=c, outline="")
        self.canvas.create_oval(230, 40, 370, 190, fill=c, outline="")
        self.canvas.create_rectangle(100, 60, 300, 150, fill=c, outline="")
        
        # Sticks
        self.canvas.create_oval(70, 50, 130, 110, fill="#ccc", outline="#888")
        self.reg_item("GC_Stick", self.canvas.create_oval(92, 72, 108, 88, fill="#555", outline=""), "#555", "#555")
        
        # C-Stick (Yellow, bottom right)
        self.canvas.create_oval(210, 120, 270, 180, fill="#ccc", outline="#888")
        self.reg_item("GC_CStick", self.canvas.create_oval(234, 144, 246, 156, fill="#e8c100", outline=""), "#e8c100", "#e8c100")
        
        # D-Pad (Bottom left)
        self.canvas.create_rectangle(105, 135, 135, 175, fill="#bbb", outline="")
        self.canvas.create_rectangle(90, 145, 150, 165, fill="#bbb", outline="")
        self.reg_item("Dpad_Up", self.canvas.create_rectangle(110, 135, 130, 145, fill="", outline=""), "", "red")
        self.reg_item("Dpad_Down", self.canvas.create_rectangle(110, 165, 130, 175, fill="", outline=""), "", "red")
        self.reg_item("Dpad_Left", self.canvas.create_rectangle(90, 145, 110, 165, fill="", outline=""), "", "red")
        self.reg_item("Dpad_Right", self.canvas.create_rectangle(130, 145, 150, 165, fill="", outline=""), "", "red")
        
        # Action Buttons
        # A Button (Center, green, large)
        item_A = self.canvas.create_oval(280, 80, 320, 120, fill="#18cc6c", outline="")
        txt_A = self.canvas.create_text(300, 100, text="A", fill="white", font=("Segoe UI", 12, "bold"))
        self.reg_item("A", item_A, "#18cc6c", "white", text_item=txt_A)
        
        # B Button (Bottom left of A, red, small)
        item_B = self.canvas.create_oval(260, 105, 280, 125, fill="#e51f43", outline="")
        txt_B = self.canvas.create_text(270, 115, text="B", fill="white", font=("Segoe UI", 8, "bold"))
        self.reg_item("B", item_B, "#e51f43", "white", text_item=txt_B)
        
        # X Button (Right of A, gray, kidney/pill shape approximated with oval)
        item_X = self.canvas.create_oval(325, 75, 345, 105, fill="#aaa", outline="")
        txt_X = self.canvas.create_text(335, 90, text="X", fill="#333", font=("Segoe UI", 8, "bold"))
        self.reg_item("X", item_X, "#aaa", "white", text_item=txt_X)
        
        # Y Button (Top of A, gray, pill shape)
        item_Y = self.canvas.create_oval(285, 55, 315, 75, fill="#aaa", outline="")
        txt_Y = self.canvas.create_text(300, 65, text="Y", fill="#333", font=("Segoe UI", 8, "bold"))
        self.reg_item("Y", item_Y, "#aaa", "white", text_item=txt_Y)
        
        # Start button (Center)
        item_S = self.canvas.create_oval(190, 80, 210, 100, fill="#ccc", outline="")
        txt_S = self.canvas.create_text(200, 90, text="S", fill="#444", font=("Segoe UI", 8, "bold"))
        self.reg_item("Start", item_S, "#ccc", "red", text_item=txt_S)
        
        # L / R Analog Triggers
        item_L = self.canvas.create_rectangle(70, 10, 130, 30, fill="#aaa", outline="")
        txt_L = self.canvas.create_text(100, 20, text="L Analog", fill="#333", font=("Segoe UI", 8))
        self.reg_item("Trigger analog L", item_L, "#aaa", "white", text_item=txt_L)
        
        item_R = self.canvas.create_rectangle(270, 10, 330, 30, fill="#aaa", outline="")
        txt_R = self.canvas.create_text(300, 20, text="R Analog", fill="#333", font=("Segoe UI", 8))
        self.reg_item("Trigger analog R", item_R, "#aaa", "white", text_item=txt_R)
        
        # L / R Digital Clicks (Thin inner rectangles)
        item_L_click = self.canvas.create_rectangle(80, 0, 120, 10, fill="#888", outline="")
        txt_L_click = self.canvas.create_text(100, 5, text="L Clic", fill="#fff", font=("Segoe UI", 6))
        self.reg_item("clic L", item_L_click, "#888", "red", text_item=txt_L_click)
        
        item_R_click = self.canvas.create_rectangle(280, 0, 320, 10, fill="#888", outline="")
        txt_R_click = self.canvas.create_text(300, 5, text="R Clic", fill="#fff", font=("Segoe UI", 6))
        self.reg_item("clic R", item_R_click, "#888", "red", text_item=txt_R_click)
        
        # Z Button (Blue, above R)
        item_Z = self.canvas.create_rectangle(270, 30, 310, 45, fill="#1f4c9c", outline="")
        txt_Z = self.canvas.create_text(290, 37, text="Z", fill="white", font=("Segoe UI", 8, "bold"))
        self.reg_item("ZR", item_Z, "#1f4c9c", "white", text_item=txt_Z)

    def update_devices_list(self):
        """Met a jour la liste des manettes dans le selecteur."""
        if not hasattr(self, 'manager'): return
        
        joys = self.manager.detector.joysticks
        if not joys:
            self.device_combo['values'] = []
            self.device_var.set(Loc.get("no_devs_found"))
            return
            
        options = []
        icons = {"Xbox": "[X]", "PlayStation": "[P]", "Nintendo": "[N]", "Generique": "[G]"}
        
        for jid, info in joys.items():
            ctrl_type = info["type"]
            name = info["name"]
            icon = icons.get(ctrl_type, "[G]")
            options.append(f"{jid}: {icon} {name}")
            
        # Mettre a jour les valeurs si elles ont change
        current_options = list(self.device_combo['values'])
        if current_options != options:
            self.device_combo['values'] = options
            
            # Selectionner la premiere par defaut si aucune selection
            if not self.device_var.get() or self.device_var.get() not in options:
                self.device_combo.current(0)
                self.on_device_change(None)

        # NOUVEAU: Mettre à jour dynamiquement la liste du sélecteur de détection du raccourci
        if hasattr(self, 'hub_name_combo'):
            connected_names = [info["name"] for info in joys.values()]
            all_option = Loc.get("all_controllers_option")
            combo_options = [all_option] + sorted(list(set(connected_names)))
            
            saved_name = self.hub_name_var.get()
            if saved_name and saved_name != all_option and saved_name not in combo_options:
                combo_options.append(saved_name)
                
            if list(self.hub_name_combo['values']) != combo_options:
                self.hub_name_combo['values'] = combo_options
                if not self.hub_name_var.get():
                    self.hub_name_var.set(all_option)

    def on_device_change(self, event):
        """Met a jour la manette active dans le manager."""
        selected = self.device_var.get()
        if not selected: return
        
        try:
            # Extraire l'ID du format "ID: [T] Name"
            jid = int(selected.split(":")[0])
            self.manager.selected_joy_id = jid
            self.log_list.insert(tk.END, f"Manette active : {selected}")
            self.log_list.yview(tk.END)
        except Exception:
            pass

    def on_hub_controller_name_change(self, event):
        """Appelé quand on sélectionne une manette spécifique pour les raccourcis dans Gérer les manettes."""
        self._save_hub_shortcut()

    def poll_controllers(self):
        """Boucle non-bloquante pour lire les inputs via pygame."""
        # Maj liste au cas où il y a eu un hotplug
        self.update_devices_list()
        
        # Lire les évènements
        self.manager.poll()
        
        # Rappeler cette fonction très rapidement
        self.root.after(20, self.poll_controllers)

    def save_and_apply(self):
        """Action du bouton : Sauvegarde le JSON et exporte aux émulateurs."""
        if not hasattr(self, 'manager'): return
        
        # Sauvegarder d'abord le raccourci Hub global
        print(f"[ControllerUI] Save & Apply: tentative de sauvegarde du raccourci Hub...")
        self._save_hub_shortcut()

        # Le manager va automatiquement sauvegarder le profil actif (ex: ww.json)
        # avant d'exporter les fichiers de configuration (.ini)
        success = self.manager.apply_config_to_emulators()
        
        if success:
            messagebox.showinfo("Succes", Loc.get("export_success", hub_btn=self.hub_btn_var.get()))
            # self.log_list.insert(tk.END, "OK")
            self.log_list.yview(tk.END)
        else:
            messagebox.showwarning("Attention", Loc.get("export_fail"))

    def _save_hub_shortcut(self):
        """Sauvegarde uniquement le raccourci Hub dans config.json."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                old_val = config.get("hub_controller_open_btn")
                new_val = self.hub_btn_var.get()
                config["hub_controller_open_btn"] = new_val
                
                # NOUVEAU: Sauvegarder aussi le nom de la manette pour la détection
                selected_name = self.hub_name_var.get()
                all_option = Loc.get("all_controllers_option")
                if selected_name == all_option:
                    config["hub_controller_name"] = ""
                else:
                    config["hub_controller_name"] = selected_name
                
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                
                print(f"!!! [ControllerUI] SAUVEGARDE RÉUSSIE !!!")
                print(f"!!! Path: {self.config_path}")
                print(f"!!! Valeur: {new_val}, Manette: {config.get('hub_controller_name')}")
                return True
            except Exception as e:
                print(f"[ControllerUI] Erreur lors de la sauvegarde du raccourci Hub : {e}")
        else:
            print(f"[ControllerUI] Fichier config non trouvé pour sauvegarde : {self.config_path}")
        return False

    def on_closing(self):
        pygame.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = UIControllerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
