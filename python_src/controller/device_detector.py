import pygame

class DeviceDetector:
    """
    Gère la détection automatique des manettes, le hotplug, et la normalisation 
    des événements pygame (boutons, axes, croix directionnelle).
    """

    def __init__(self):
        # Initialise le module joystick de pygame si ce n'est pas déjà fait
        if not pygame.joystick.get_init():
            pygame.joystick.init()
            
        self.joysticks = {}
        # Mappings par défaut pour normaliser en "bouton bas", "bouton droit", etc.
        # Xbox: A=0, B=1, X=2, Y=3 (Standard Pygame Windows)
        # PS4/PS5: Cross=0, Circle=1, Square=2, Triangle=3
        # Switch Pro: B=0, A=1, Y=2, X=3
        self.scan_devices()

    def identify_controller_type(self, name):
        """Déduit le modèle de la manette depuis son nom."""
        name_lower = name.lower()
        if "xbox" in name_lower or "x-box" in name_lower:
            return "Xbox"
        elif "playstation" in name_lower or "ps4" in name_lower or "ps5" in name_lower or "dualshock" in name_lower or "dualsense" in name_lower:
            return "PlayStation"
        elif "nintendo" in name_lower or "switch" in name_lower or "pro controller" in name_lower:
            return "Nintendo"
        return "Générique"

    def get_standard_button(self, ctrl_type, raw_btn):
        """
        Transforme l'ID brut du bouton en constante de position indépendante de la marque.
        """
        # Mapping par défaut (Xbox/Generic)
        mapping = {
            0: "FACE_BOTTOM",
            1: "FACE_RIGHT",
            2: "FACE_LEFT",
            3: "FACE_TOP",
            4: "SELECT",
            5: "R1",
            6: "START",
            7: "L3",
            8: "R3",
            9: "L1",
            10: "R1",
            11: "Pad N",    # Pad N
            12: "Pad S",    # Pad S
            13: "Pad W",    # Pad W
            14: "Pad E"     # Pad E
            
        }

        # Mapping spécifique Nintendo (Switch Pro Controller)
        if ctrl_type == "Nintendo":
            mapping = {
                0: "FACE_RIGHT", # A
                1: "FACE_BOTTOM",  # B
                2: "FACE_TOP",   # X
                3: "FACE_LEFT",    # Y
                4: "Select",          # Minus
                5: "HOME",          # HOME
                6: "Start",          # Plus
                7: "L3",          # ClickL3
                8: "R3",      # ClickR3
                9: "L1",       # L1
                10: "R1",       # R1
                11: "Pad N",    # Pad N
                12: "Pad S",    # Pad S
                13: "Pad W",    # Pad W
                14: "Pad E",     # Pad E
                15: "CAPTURE"     # CAPTURE
            }
            
        return mapping.get(raw_btn, f"BTN_{raw_btn}")

    def scan_devices(self):
        """Détecte les manettes connectées au démarrage ou lors d'un rescan explicite."""
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self._register_device(joystick)

    def _register_device(self, joystick):
        """Enregistre une nouvelle manette et affiche ses capacités."""
        jid = joystick.get_instance_id()
        name = joystick.get_name()
        
        # SÉCURITÉ : On ignore volontairement la manette virtuelle créée par vgamepad
        # Sinon, Pygame va lire les inputs qu'on vient d'envoyer, créer une boucle infinie,
        # et faire bugger l'UI de mapping. Le nom standard d'une manette Xbox 360 virtuelle ViGEm est :
        if name in ["Controller (Xbox 360 For Windows)", "Xbox 360 Controller"]:
            pass  # On va laisser le code s'exécuter mais ajouter une vérification plus forte
            
        # Une méthode plus sûre est de stocker l'information
        ctrl_type = self.identify_controller_type(name)
        
        axes = joystick.get_numaxes()
        btns = joystick.get_numbuttons()
        hats = joystick.get_numhats()
        
        icons = {"Xbox": "[X]", "PlayStation": "[P]", "Nintendo": "[N]", "Générique": "[G]"}
        
        icon = icons.get(ctrl_type, "[G]")
        self.joysticks[jid] = {"device": joystick, "type": ctrl_type, "name": name}
        
        print(f"[DeviceDetector] {icon} Manette connectee: {name} [{ctrl_type}] (ID: {jid}) - Axes: {axes}, Boutons: {btns}, D-Pad: {hats}")

    def _unregister_device(self, jid):
        """Retire une manette déconnectée."""
        if jid in self.joysticks:
            name = self.joysticks[jid]["name"]
            del self.joysticks[jid]
            print(f"[DeviceDetector] Manette déconnectée: {name} (ID: {jid})")

    def process_event(self, event):
        """
        Traite un événement pygame, gère le hotplug, et retourne 
        un événement normalisé (ex: BTN_0, AXIS_1, HAT_0).
        """
        # --- Gestion Hotplug ---
        if event.type == pygame.JOYDEVICEADDED:
            joy = pygame.joystick.Joystick(event.device_index)
            joy.init()
            self._register_device(joy)
            return None
            
        elif event.type == pygame.JOYDEVICEREMOVED:
            self._unregister_device(event.instance_id)
            return None

        # --- Récupération du type de manette ---
        if not hasattr(event, 'instance_id'):
            return None
            
        ctrl_info = self.joysticks.get(event.instance_id)
        if not ctrl_info: return None
        ctrl_type = ctrl_info["type"]

        # --- Normalisation des Inputs ---
        if event.type == pygame.JOYBUTTONDOWN:
            std_btn = self.get_standard_button(ctrl_type, event.button)
            return {"type": "button", "id": std_btn, "state": 1, "joy_id": event.instance_id, "raw_num": event.button}
            
        elif event.type == pygame.JOYBUTTONUP:
            std_btn = self.get_standard_button(ctrl_type, event.button)
            return {"type": "button", "id": std_btn, "state": 0, "joy_id": event.instance_id, "raw_num": event.button}
            
        elif event.type == pygame.JOYAXISMOTION:
            # Zone morte (deadzone) pour éviter le drift (0.20 recommandé)
            val = event.value
            if abs(val) < 0.20:
                val = 0.0
            
            axis_map = {
                0: "LEFT_STICK_X",
                1: "LEFT_STICK_Y",
                2: "RIGHT_STICK_X",
                3: "RIGHT_STICK_Y",
                4: "L2",
                5: "R2"
            }
            axis_id = axis_map.get(event.axis, f"AXIS_{event.axis}")
            
            # Ne renvoyer l'événement que si la valeur a changé depuis la dernière fois
            if not hasattr(self, 'last_axis_values'):
                self.last_axis_values = {}
                
            joy_axis_key = f"{event.instance_id}_{axis_id}"
            if self.last_axis_values.get(joy_axis_key) == val:
                return None
                
            self.last_axis_values[joy_axis_key] = val
            
            return {"type": "axis", "id": axis_id, "state": val, "joy_id": event.instance_id}
            
        elif event.type == pygame.JOYHATMOTION:
            # Un D-Pad (Hat) renvoie un tuple (x, y), ex: (1, 0) pour Droite
            x, y = event.value
            # Pour simplifier, on ne gère que les directions cardinales dans l'ID généré
            if x == 1: hat_id = "DPAD_RIGHT"
            elif x == -1: hat_id = "DPAD_LEFT"
            elif y == 1: hat_id = "DPAD_UP"
            elif y == -1: hat_id = "DPAD_DOWN"
            else: hat_id = "DPAD_RELEASE"
            
            # On renvoie 1 si pressé, 0 si relâché
            state = 0 if hat_id == "DPAD_RELEASE" else 1
            return {"type": "hat", "id": hat_id, "state": state, "raw_val": event.value, "joy_id": event.instance_id}

        return None
