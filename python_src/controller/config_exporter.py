import os
import configparser
import shutil

class ConfigExporter:
    """
    Génère les fichiers de configuration pour les émulateurs 
    en utilisant les ID réels de la manette physique détectée.
    """
    
    def __init__(self, base_path):
        self.base_path = base_path

    def _get_dolphin_game_settings_path(self, game_id):
        """
        Tente de trouver le chemin du fichier .ini de jeu (ex: GZL.ini ou GZ2.ini) 
        dynamiquement via config.json.
        """
        import json
        config_path = os.path.abspath(os.path.join(self.base_path, "..", "config.json"))
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                dolphin_exe_path = config.get("emulators", {}).get("dolphin", "")
                if dolphin_exe_path:
                    dolphin_dir = os.path.dirname(dolphin_exe_path)
                    # Supporte les chemins fournis par l'utilisateur (Sys/GameSettings/)
                    settings_path = os.path.join(dolphin_dir, "Sys", "GameSettings", f"{game_id}.ini")
                    return settings_path
            except Exception as e:
                 print(f"[ConfigExporter] Erreur lors de la lecture de config.json: {e}")
        
        return None

    def _get_bizhawk_config_path(self):
        """
        Tente de trouver le chemin de config.ini de BizHawk dynamiquement.
        """
        import json
        config_path = os.path.abspath(os.path.join(self.base_path, "..", "config.json"))
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                bizhawk_exe_path = config.get("emulators", {}).get("bizhawk", "")
                if bizhawk_exe_path:
                    bizhawk_dir = os.path.dirname(bizhawk_exe_path)
                    return os.path.join(bizhawk_dir, "config.ini")
            except Exception:
                pass
        
        return None

    def _prepare_dolphin_game_settings(self, game_id, profile_name):
        """
        Vérifie et met à jour le fichier .ini du jeu (GZL.ini, GZ2.ini) 
        pour s'assurer que le bon profil de manette est utilisé.
        """
        ini_path = self._get_dolphin_game_settings_path(game_id)
        
        if not ini_path or not os.path.exists(ini_path):
            print(f"[ConfigExporter] Information: {game_id}.ini non trouvé ({ini_path}).")
            return

        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(ini_path, encoding="utf-8")

            modified = False
            
            # Cas standard GameCube
            if not config.has_section("Controls"):
                config.add_section("Controls")
                modified = True
            
            # PadType0 = 6 (Standard Controller)
            if config.get("Controls", "PadType0", fallback=None) != "6":
                config.set("Controls", "PadType0", "6")
                modified = True
                
            # PadProfile1 = nom du profil (sans .ini)
            clean_profile = profile_name.replace(".ini", "")
            if config.get("Controls", "PadProfile1", fallback=None) != clean_profile:
                config.set("Controls", "PadProfile1", clean_profile)
                modified = True

            if modified:
                with open(ini_path, 'w', encoding="utf-8") as f:
                    config.write(f, space_around_delimiters=True)
                print(f"[ConfigExporter] {game_id}.ini mis à jour avec le profil : {clean_profile}")
            else:
                print(f"[ConfigExporter] {game_id}.ini est déjà correctement configuré.")

        except Exception as e:
            print(f"[ConfigExporter] Erreur lors de la vérification de {game_id}.ini : {e}")

    def remove_dolphin_game_settings(self, game_id):
        """
        Retire les réglages de manette injectés dans le .ini du jeu (GZL.ini, GZ2.ini).
        Ceci permet à Dolphin de revenir aux réglages manuels de l'utilisateur.
        """
        ini_path = self._get_dolphin_game_settings_path(game_id)
        if not ini_path or not os.path.exists(ini_path):
            return

        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(ini_path, encoding="utf-8")

            modified = False
            if config.has_section("Controls"):
                if config.has_option("Controls", "PadProfile1"):
                    config.remove_option("Controls", "PadProfile1")
                    modified = True
                if config.has_option("Controls", "PadType0"):
                    config.remove_option("Controls", "PadType0")
                    modified = True
                
                # Si la section est vide après retrait, on peut l'enlever aussi
                if not config.options("Controls"):
                    config.remove_section("Controls")
                    modified = True

            if modified:
                with open(ini_path, 'w', encoding="utf-8") as f:
                    config.write(f, space_around_delimiters=True)
                print(f"[ConfigExporter] {game_id}.ini nettoyé (Auto-config désactivée).")

        except Exception as e:
            print(f"[ConfigExporter] Erreur lors du nettoyage de {game_id}.ini : {e}")

    def force_copy_profile(self, profile_name):
        """
        Copie directement un fichier .ini existant depuis le dossier Profiles
        vers le fichier de configuration active GCPadNew.ini.
        """
        appdata_path = os.environ.get('APPDATA')
        if not appdata_path:
            print("[ConfigExporter] Erreur: APPDATA introuvable.")
            return False
            
        source = os.path.join(appdata_path, "Dolphin Emulator", "Config", "Profiles", "GCPad", profile_name)
        dest = os.path.join(appdata_path, "Dolphin Emulator", "Config", "GCPadNew.ini")
        
        try:
            if os.path.exists(source):
                shutil.copyfile(source, dest)
                print(f"[ConfigExporter] Profil '{profile_name}' copié avec succès vers {dest}")
                return True
            else:
                print(f"[ConfigExporter] Fichier source introuvable : {source}")
                return False
        except Exception as e:
            print(f"[ConfigExporter] Erreur lors de la copie shutil : {e}")
            return False

    def export_dolphin_config(self, joy_name, mapping, profile_name="GCPadNew.ini", ctrl_type="Generic"):
        """
        Génère un fichier .ini pour Dolphin au format exact demandé.
        """
        # On déduit le GameID si possible pour mettre à jour le .ini spécifique au jeu
        # ww.ini -> GZL, tp.ini -> GZ2
        game_map = {"ww.ini": "GZL", "tp.ini": "GZ2"}
        if profile_name in game_map:
            self._prepare_dolphin_game_settings(game_map[profile_name], profile_name)
        

        config = configparser.ConfigParser()
        # On désactive la mise en minuscule automatique des clés (Dolphin est sensible à la casse)
        config.optionxform = str 
        
        section = "Profile"
        config.add_section(section)
        
        # Dolphin utilise souvent le format "SDL/0/Name" ou "DInput/0/Name" ou "WGInput/0/Name"
        prefix = "SDL/0/"
        if ctrl_type == "PlayStation":
            prefix = "WGInput/0/"
            
        config.set(section, "Device", f"{prefix}{joy_name}")
        
        # Mapping des boutons (Dolphin Key -> Action Logique attendue dans le profil)
        btn_map = {
            "Buttons/A": "A",
            "Buttons/B": "B",
            "Buttons/X": "X",
            "Buttons/Y": "Y",
            "Buttons/Z": "ZR",
            "Buttons/Start": "Start",
        }
        
        # Mapping des sticks
        stick_map = {
            "Main Stick/Up": ("Joystick_Y", "+"),
            "Main Stick/Down": ("Joystick_Y", "-"),
            "Main Stick/Left": ("Joystick_X", "-"),
            "Main Stick/Right": ("Joystick_X", "+"),
            "C-Stick/Up": ("C-Stick_Y", "+"),
            "C-Stick/Down": ("C-Stick_Y", "-"),
            "C-Stick/Left": ("C-Stick_X", "-"),
            "C-Stick/Right": ("C-Stick_X", "+"),
        }
        
        # Mapping des Triggers
        trigger_map = {
            "Triggers/L": "Trigger analog L",
            "Triggers/R": "Trigger analog R",
            "Triggers/L-Analog": "Trigger analog L",
            "Triggers/R-Analog": "Trigger analog R",
        }
        
        # Mapping du D-Pad
        dpad_map = {
            "D-Pad/Up": "Dpad_Up",
            "D-Pad/Down": "Dpad_Down",
            "D-Pad/Left": "Dpad_Left",
            "D-Pad/Right": "Dpad_Right",
        }

        def get_dolphin_val(phys_id, axis_dir=None):
            """Transforme un ID physique interne en chaîne compréhensible par Dolphin."""
            if not phys_id: return None
            
            # Cas Boutons
            if ctrl_type == "PlayStation":
                ps_names = {
                    "FACE_BOTTOM": "Cross", "FACE_RIGHT": "Circle", "FACE_LEFT": "Square", "FACE_TOP": "Triangle",
                    "Start": "Menu", "Select": "Menu", "START": "Menu", "SELECT": "Menu",
                    "L1": "Bumper L", "R1": "Bumper R",
                    "L3": "Click L", "R3": "Click R",
                    "Pad N": "Switch 0 N", "Pad S": "Switch 0 S", "Pad W": "Switch 0 W", "Pad E": "Switch 0 E",
                    "Shoulder R": "Bumper R", "Shoulder L": "Bumper L"
                }
                if phys_id in ps_names:
                    name = ps_names[phys_id]
                    if name in ["Circle", "Square", "Triangle", "Cross", "Menu"]:
                        return name
                    return f"`{name}`"
            
            # Par défaut (Switch/Xbox/Generic)
            btn_names = {
                "FACE_BOTTOM": "S", "FACE_RIGHT": "E", "FACE_LEFT": "W", "FACE_TOP": "N",
                "START": "Start", "SELECT": "Start", 
                "Start": "Start", "Select": "Start", 
                "L1": "Shoulder L", "R1": "Shoulder R",
                "L2": "Trigger L", "R2": "Trigger R",
                "L3": "Thumb L", "R3": "Thumb R",
                "Pad N": "Pad N", "Pad S": "Pad S", "Pad W": "Pad W", "Pad E": "Pad E"
            }
            
            if phys_id in btn_names:
                name = btn_names[phys_id]
                # Checklist des noms qui ne doivent PAS avoir le préfixe "Button"
                no_button_prefix = ["Start", "Shoulder L", "Shoulder R", "Trigger L", "Trigger R", "Pad N", "Pad S", "Pad W", "Pad E"]
                
                if name in no_button_prefix:
                    return f"`{name}`"
                return f"`Button {name}`"
            elif "BTN_" in phys_id:
                return f"`Button {phys_id.replace('BTN_', '')}`"
            
            # Cas D-Pad (Si l'ID arrive déjà formaté 'Pad N' par exemple)
            if phys_id in ["Pad N", "Pad S", "Pad W", "Pad E"]:
                return f"`{phys_id}`"
            
            # Cas Axes (Sticks et Triggers analogiques si détectés comme tels)
            axis_names = {
                "LEFT_STICK_X": "Left X", "LEFT_STICK_Y": "Left Y",
                "RIGHT_STICK_X": "Right X", "RIGHT_STICK_Y": "Right Y",
                "L2": "Trigger L", "R2": "Trigger R"
            }
            if phys_id in axis_names:
                name = axis_names[phys_id]
                if axis_dir: # Pour les sticks: direction + ou - sans ESPACE
                    return f"`{name}{axis_dir}`"
                return f"`{name}`"
            elif "AXIS_" in phys_id:
                num = phys_id.replace("AXIS_", "")
                if axis_dir: return f"`Axis {num}{axis_dir}`"
                return f"`Axis {num}`"
                
            # Cas D-Pad (Hats)
            hat_names = {"DPAD_UP": "N", "DPAD_DOWN": "S", "DPAD_LEFT": "W", "DPAD_RIGHT": "E"}
            if phys_id in hat_names:
                return f"`Pad {hat_names[phys_id]}`"
                
            return None

        # Remplissage de la config
        # 1. Boutons
        for dol_key, logic_act in btn_map.items():
            phys = mapping.get(logic_act)
            val = get_dolphin_val(phys)
            if val: config.set(section, dol_key, val)
            
        # 2. Sticks
        for dol_key, (logic_act, direction) in stick_map.items():
            phys = mapping.get(logic_act)
            val = get_dolphin_val(phys, direction)
            if val: config.set(section, dol_key, val)
        config.set(section, "Main Stick/Calibration", "100.00")
        config.set(section, "C-Stick/Calibration", "100.00")

        # 3. Triggers
        for dol_key, logic_act in trigger_map.items():
            phys = mapping.get(logic_act)
            val = get_dolphin_val(phys)
            if val: config.set(section, dol_key, val)

        # 4. D-Pad
        for dol_key, logic_act in dpad_map.items():
            phys = mapping.get(logic_act)
            val = get_dolphin_val(phys)
            if val: config.set(section, dol_key, val)
            
        # 5. Rumble
        config.set(section, "Rumble/Motor", "`Motor L` | `Motor R`")

        # 1. Sauvegarde comme Profil (.ini dans le dossier Profiles)
        # Dolphin attend [Profile] dans ces fichiers
        appdata_path = os.environ.get('APPDATA')
        if appdata_path:
            profile_path = os.path.join(appdata_path, "Dolphin Emulator", "Config", "Profiles", "GCPad", profile_name)
            active_path = os.path.join(appdata_path, "Dolphin Emulator", "Config", "GCPadNew.ini")
        else:
            profile_path = os.path.join(self.base_path, "dolphin_config", profile_name)
            active_path = None
            
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        with open(profile_path, 'w', encoding="utf-8") as f:
            config.write(f)
        print(f"[ConfigExporter] Profil Dolphin exporté : {profile_path}")

        # 2. Sauvegarde comme Configuration ACTIVE (GCPadNew.ini)
        # Dolphin attend [GCPadNew1], [GCPadNew2]... dans ce fichier global
        if active_path:
            # On crée une nouvelle config pour changer l'en-tête de section
            active_config = configparser.ConfigParser()
            active_config.optionxform = str
            new_section = "GCPadNew1"
            active_config.add_section(new_section)
            
            # On copie toutes les valeurs de [Profile] vers [GCPadNew1]
            for key, value in config.items("Profile"):
                active_config.set(new_section, key, value)
                
            os.makedirs(os.path.dirname(active_path), exist_ok=True)
            print(f"[ConfigExporter] Configuration ACTIVE Dolphin mise à jour ([GCPadNew1]) : {active_path}")


    def get_dolphin_val_internal(self, phys_id, axis_dir=None, ctrl_type="Generic"):
        """Version interne réutilisable de get_dolphin_val."""
        if not phys_id: return None
        
        # Cas Boutons
        if ctrl_type == "PlayStation":
            ps_names = {
                "FACE_BOTTOM": "Cross", "FACE_RIGHT": "Circle", "FACE_LEFT": "Square", "FACE_TOP": "Triangle",
                "Start": "Menu", "Select": "Menu", "START": "Menu", "SELECT": "Menu",
                "L1": "Bumper L", "R1": "Bumper R",
                "L3": "Click L", "R3": "Click R",
                "Pad N": "Switch 0 N", "Pad S": "Switch 0 S", "Pad W": "Switch 0 W", "Pad E": "Switch 0 E",
                "Shoulder R": "Bumper R", "Shoulder L": "Bumper L"
            }
            if phys_id in ps_names:
                name = ps_names[phys_id]
                if name in ["Circle", "Square", "Triangle", "Cross", "Menu"]:
                    return name
                return f"`{name}`"
        
        # Par défaut (Switch/Xbox/Generic)
        btn_names = {
            "FACE_BOTTOM": "S", "FACE_RIGHT": "E", "FACE_LEFT": "W", "FACE_TOP": "N",
            "START": "Start", "SELECT": "Start", 
            "Start": "Start", "Select": "Start", 
            "L1": "Shoulder L", "R1": "Shoulder R",
            "L2": "Trigger L", "R2": "Trigger R",
            "L3": "Thumb L", "R3": "Thumb R",
            "Pad N": "Pad N", "Pad S": "Pad S", "Pad W": "Pad W", "Pad E": "Pad E"
        }
        
        if phys_id in btn_names:
            name = btn_names[phys_id]
            # Checklist des noms qui ne doivent PAS avoir le préfixe "Button"
            no_button_prefix = ["Start", "Shoulder L", "Shoulder R", "Trigger L", "Trigger R", "Pad N", "Pad S", "Pad W", "Pad E", "Thumb L", "Thumb R"]
            
            if name in no_button_prefix:
                return f"`{name}`"
            return f"`Button {name}`"
        elif "BTN_" in phys_id:
            return f"`Button {phys_id.replace('BTN_', '')}`"
        
        # Cas D-Pad (Si l'ID arrive déjà formaté 'Pad N' par exemple)
        if phys_id in ["Pad N", "Pad S", "Pad W", "Pad E"]:
            return f"`{phys_id}`"
        
        # Cas Axes (Sticks et Triggers analogiques si détectés comme tels)
        axis_names = {
            "LEFT_STICK_X": "Left X", "LEFT_STICK_Y": "Left Y",
            "RIGHT_STICK_X": "Right X", "RIGHT_STICK_Y": "Right Y",
            "L2": "Trigger L", "R2": "Trigger R"
        }
        if phys_id in axis_names:
            name = axis_names[phys_id]
            if axis_dir: # Pour les sticks: direction + ou - sans ESPACE
                return f"`{name}{axis_dir}`"
            return f"`{name}`"
        elif "AXIS_" in phys_id:
            num = phys_id.replace("AXIS_", "")
            if axis_dir: return f"`Axis {num}{axis_dir}`"
            return f"`Axis {num}`"
            
        # Cas D-Pad (Hats)
        hat_names = {"DPAD_UP": "N", "DPAD_DOWN": "S", "DPAD_LEFT": "W", "DPAD_RIGHT": "E"}
        if phys_id in hat_names:
            return f"`Pad {hat_names[phys_id]}`"
            
        return None

    def export_bizhawk_config(self, mapping, ctrl_type="Generic", system="N64"):
        """
        Génère la configuration des contrôles pour BizHawk dans config.ini (Format JSON).
        Supporte :
        - N64 (Nintendo 64 Controller)
        - GBA (GBA Controller)
        - SNES (SNES Controller)
        """
        config_path = self._get_bizhawk_config_path()
        if not config_path or not os.path.exists(config_path):
            print(f"[ConfigExporter] Attention: config.ini BizHawk non trouvé ({config_path}).")
            return False

        # Mapping des noms de section par système
        system_section_map = {
            "N64": "Nintendo 64 Controller",
            "GBA": "GBA Controller",
            "SNES": "SNES Controller",
            "NES": "NES Controller",
            "NDS": "NDS Controller"
        }
        section_name = system_section_map.get(system, "Nintendo 64 Controller")
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 1. SECTION BOUTONS (AllTrollers)
            if "AllTrollers" not in config_data:
                config_data["AllTrollers"] = {}
            
            if section_name not in config_data["AllTrollers"]:
                config_data["AllTrollers"][section_name] = {}
            
            btn_section = config_data["AllTrollers"][section_name]

            # Mapping BizHawk Boutons (Key -> Action Logique)
            if system == "N64":
                biz_btn_map = {
                    "P1 A": "A",
                    "P1 B": "B",
                    "P1 Start": "Start",
                    "P1 Z": "ZR",
                    "P1 L": "LButton",
                    "P1 R": "RButton",
                    "P1 DPad U": "Dpad_Up",
                    "P1 DPad D": "Dpad_Down",
                    "P1 DPad L": "Dpad_Left",
                    "P1 DPad R": "Dpad_Right",
                    "P1 C Up": ("Cbutton_Y", "+"),
                    "P1 C Down": ("Cbutton_Y", "-"),
                    "P1 C Left": ("Cbutton_X", "-"),
                    "P1 C Right": ("Cbutton_X", "+"),
                }
            elif system == "GBA":
                biz_btn_map = {
                    # Touches courtes (utilisées par certains cores)
                    "A": "A",
                    "B": "B",
                    "L": "L",
                    "R": "R",
                    "Start": "Start",
                    "Select": "Select",
                    "Up": "Dpad_Up",
                    "Down": "Dpad_Down",
                    "Left": "Dpad_Left",
                    "Right": "Dpad_Right",
                    # Touches préfixées P1
                    "P1 A": "A",
                    "P1 B": "B",
                    "P1 L": "L",
                    "P1 R": "R",
                    "P1 Start": "Start",
                    "P1 Select": "Select",
                    "P1 D-Pad U": "Dpad_Up",
                    "P1 D-Pad D": "Dpad_Down",
                    "P1 D-Pad L": "Dpad_Left",
                    "P1 D-Pad R": "Dpad_Right",
                }
            elif system == "SNES":
                biz_btn_map = {
                    "P1 A": "A",
                    "P1 B": "B",
                    "P1 X": "X",
                    "P1 Y": "Y",
                    "P1 L": "L",
                    "P1 R": "R",
                    "P1 Start": "Start",
                    "P1 Select": "Select",
                    "P1 D-Pad U": "Dpad_Up",
                    "P1 D-Pad D": "Dpad_Down",
                    "P1 D-Pad L": "Dpad_Left",
                    "P1 D-Pad R": "Dpad_Right",
                }
            elif system == "NES":
                biz_btn_map = {
                    "P1 A": "A",
                    "P1 B": "B",
                    "P1 Start": "Start",
                    "P1 Select": "Select",
                    "P1 Up": "Dpad_Up",
                    "P1 Down": "Dpad_Down",
                    "P1 Left": "Dpad_Left",
                    "P1 Right": "Dpad_Right",
                }
            elif system == "NDS":
                biz_btn_map = {
                    "P1 A": "A",
                    "P1 B": "B",
                    "P1 X": "X",
                    "P1 Y": "Y",
                    "P1 Start": "Start",
                    "P1 Select": "Select",
                    "P1 L": "L",
                    "P1 R": "R",
                    "P1 Up": "Dpad_Up",
                    "P1 Down": "Dpad_Down",
                    "P1 Left": "Dpad_Left",
                    "P1 Right": "Dpad_Right",
                }
            else:
                biz_btn_map = {}

            def get_biz_btn_val(phys_id):
                """Transforme un ID physique en chaîne XInput BizHawk (Bouton)."""
                if not phys_id: return ""
                
                # Mapping de base (Xbox / Standard)
                # A=Bas, B=Droite, X=Gauche, Y=Haut
                x1_table = {
                    "FACE_BOTTOM": "A", "FACE_RIGHT": "B", "FACE_LEFT": "X", "FACE_TOP": "Y",
                    "START": "Start", "Start": "Start",
                    "SELECT": "Back", "Select": "Back",
                    "L1": "LeftShoulder", "R1": "RightShoulder",
                    "L2": "LeftTrigger", "R2": "RightTrigger",
                    "L3": "LeftThumb", "R3": "RightThumb",
                    "Pad N": "DpadUp", "Pad S": "DpadDown", "Pad W": "DpadLeft", "Pad E": "DpadRight",
                    "DPAD_UP": "DpadUp", "DPAD_DOWN": "DpadDown", "DPAD_LEFT": "DpadLeft", "DPAD_RIGHT": "DpadRight"
                }

                # Ajustement pour manettes Nintendo (Switch)
                # On inverse pour que le label physique A (Droite) envoie le signal A à l'émulateur
                if ctrl_type == "Nintendo":
                    x1_table.update({
                        "FACE_BOTTOM": "B",
                        "FACE_RIGHT": "A",
                        "FACE_LEFT": "Y",
                        "FACE_TOP": "X"
                    })

                if phys_id in x1_table:
                    return f"X1 {x1_table[phys_id]}"
                return ""

            # Mapping des "extras" par touche pour GBA (Stick -> Dpad)
            gba_stick_extras = {
                "Up": "X1 LStickUp",
                "Down": "X1 LStickDown",
                "Left": "X1 LStickLeft",
                "Right": "X1 LStickRight",
                "P1 D-Pad U": "X1 LStickUp",
                "P1 D-Pad D": "X1 LStickDown",
                "P1 D-Pad L": "X1 LStickLeft",
                "P1 D-Pad R": "X1 LStickRight",
            }

            # Mapping des "extras" par touche pour NES (Dpad sur Sticks et claviers/joypads par défaut)
            nes_extras = {
                "P1 Up": "Up, J1 POV1U, X1 LStickUp",
                "P1 Down": "Down, J1 POV1D, X1 LStickDown",
                "P1 Left": "Left, J1 POV1L, X1 LStickLeft",
                "P1 Right": "Right, J1 POV1R, X1 LStickRight",
                "P1 Start": "Enter, J1 B10",
                "P1 Select": "Space, J1 B9",
                "P1 B": "Z, J1 B1",
                "P1 A": "X, J1 B2"
            }

            modified = False
            for biz_key, logic in biz_btn_map.items():
                logic_act = logic
                if isinstance(logic, tuple):
                    logic_act, _ = logic # Les directions C-Buttons sont gérées en analogique ou ignorées ici
                
                phys = mapping.get(logic_act)
                val = get_biz_btn_val(phys)
                
                if val:
                    # AJOUT DES EXTRAS POUR GBA (Sticks sur D-Pad)
                    if system == "GBA" and biz_key in gba_stick_extras:
                        extra = gba_stick_extras[biz_key]
                        if extra not in val:
                            val = f"{val}, {extra}"
                            
                    # AJOUT DES EXTRAS POUR NES (Clavier, Joypad1, Sticks)
                    if system == "NES" and biz_key in nes_extras:
                        extra = nes_extras[biz_key]
                        # On s'assure de ne pas doubler les entrées X1
                        val = f"{extra}, {val}"

                    # BizHawk peut avoir plusieurs entrées séparées par des virgules
                    # On s'assure que notre valeur est présente
                    current = btn_section.get(biz_key, "")
                    if val not in current:
                        # Pour le Zelda Hub, on force notre mapping calculé
                        if btn_section.get(biz_key) != val:
                            btn_section[biz_key] = val
                            modified = True

            # Ajout des champs par défaut pour NES
            if system == "NES":
                nes_defaults = {
                    "P2 Fire": "WMouse L",
                    "P3 Fire": "WMouse L",
                    "Reset": "",
                    "Power": ""
                }
                for k, v in nes_defaults.items():
                    if k not in btn_section or btn_section[k] != v:
                        btn_section[k] = v
                        modified = True

            # 2. SECTION ANALOGIQUE (AllTrollersAnalog)
            if "AllTrollersAnalog" not in config_data:
                config_data["AllTrollersAnalog"] = {}
            
            if section_name not in config_data["AllTrollersAnalog"]:
                config_data["AllTrollersAnalog"][section_name] = {}
            
            ana_section = config_data["AllTrollersAnalog"][section_name]

            biz_ana_map = {
                "P1 X Axis": "Joystick_X",
                "P1 Y Axis": "Joystick_Y"
            }

            for biz_key, logic_act in biz_ana_map.items():
                phys = mapping.get(logic_act)
                if phys == "LEFT_STICK_X":
                    val = "X1 LeftThumbX Axis"
                elif phys == "LEFT_STICK_Y":
                    val = "X1 LeftThumbY Axis"
                elif phys == "RIGHT_STICK_X":
                    val = "X1 RightThumbX Axis"
                elif phys == "RIGHT_STICK_Y":
                    val = "X1 RightThumbY Axis"
                else:
                    continue

                if biz_key not in ana_section or ana_section[biz_key].get("Value") != val:
                    ana_section[biz_key] = {
                        "Value": val,
                        "Mult": 1.0,
                        "Deadzone": 0.1
                    }
                    modified = True

            if modified:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2)
                print(f"[ConfigExporter] BizHawk config.ini (JSON) mis à jour : {config_path}")
            else:
                print(f"[ConfigExporter] BizHawk config.ini (JSON) est déjà à jour.")
            
            return True

        except Exception as e:
            print(f"[ConfigExporter] Erreur lors de l'export BizHawk : {e}")
            import traceback
            traceback.print_exc()
            return False

    def export_azahar_config(self, joy_name, mapping, ctrl_type="Generic"):
        """
        Génère la configuration des contrôles pour Azahar (3DS) dans qt-config.ini.
        Supporte le format multi-profils avec GUID.
        """
        appdata = os.environ.get('APPDATA')
        if not appdata: return False
        
        config_path = os.path.join(appdata, "Azahar", "config", "qt-config.ini")
        if not os.path.exists(config_path):
            print(f"[ConfigExporter] Attention: qt-config.ini Azahar non trouvé ({config_path}).")
            return False

        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(config_path, encoding="utf-8")

            if not config.has_section("Controls"):
                config.add_section("Controls")

            # On active l'utilisation des profils
            config.set("Controls", "use_artic_base_controller", "false")
            config.set("Controls", "profile", "1") # On utilise le profil 1 pour Link
            
            # Gestion de la taille des profils
            current_size = config.getint("Controls", "profiles\\size", fallback=0)
            if current_size < 1:
                config.set("Controls", "profiles\\size", "1")

            # Profil 1: Link
            p = "profiles\\1\\"
            config.set("Controls", f"{p}name", "Link")
            config.set("Controls", f"{p}name\\default", "false")

            # Mapping Azahar -> Action Logique (D'après le template de l'utilisateur)
            guid = "0300bb977e0500000920000010026803" # Switch Pro Controller / Standard
            
            btn_map = {
                "button_a": ("A", 0),
                "button_b": ("B", 1),
                "button_x": ("X", 2),
                "button_y": ("Y", 3),
                "button_l": ("L", 9),
                "button_r": ("R", 10),
                "button_start": ("Start", 6),
                "button_select": ("Select", 4),
                "button_home": ("Home", 5),
                "button_power": ("Power", 15),
                "button_up": ("Dpad_Up", 11),
                "button_down": ("Dpad_Down", 12),
                "button_left": ("Dpad_Left", 13),
                "button_right": ("Dpad_Right", 14)
            }

            for citra_key, (logic, default_btn) in btn_map.items():
                config.set("Controls", f"{p}{citra_key}\\default", "false")
                val = f'"button:{default_btn},engine:sdl,guid:{guid},port:0"'
                config.set("Controls", f"{p}{citra_key}", val)

            # Triggers (ZL/ZR) comme axes dans son template
            config.set("Controls", f"{p}button_zl\\default", "false")
            config.set("Controls", f"{p}button_zl", f'"axis:4,engine:sdl,guid:{guid},port:0"')
            config.set("Controls", f"{p}button_zr\\default", "false")
            config.set("Controls", f"{p}button_zr", f'"axis:5,engine:sdl,guid:{guid},port:0"')

            # Circle Pad & C-Stick
            config.set("Controls", f"{p}circle_pad\\default", "false")
            config.set("Controls", f"{p}circle_pad", f'"axis_x:0,axis_y:1,deadzone:0.100000,engine:sdl,guid:{guid},port:0"')
            config.set("Controls", f"{p}c_stick\\default", "false")
            config.set("Controls", f"{p}c_stick", f'"axis_x:2,axis_y:3,deadzone:0.000000,engine:sdl,guid:{guid},port:0"')

            # Global fallback as requested (même si profile=1 est prioritaire)
            config.set("Controls", "button_a", '"engine:sdl,button:0,joystick:0"') # Ajustement based on template A=0
            config.set("Controls", "button_b", '"engine:sdl,button:1,joystick:0"')

            with open(config_path, "w", encoding="utf-8") as f:
                config.write(f)
            print(f"[ConfigExporter] Azahar qt-config.ini mis à jour (Profil 1: Link) : {config_path}")
            
            return True

        except Exception as e:
            print(f"[ConfigExporter] Erreur lors de l'export Azahar : {e}")
            import traceback
            traceback.print_exc()
            return False
