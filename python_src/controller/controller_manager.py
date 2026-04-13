import pygame
import os

class OutputAdapter:
    """Interface de base pour les sorties d'actions (UI, Export, etc.)"""
    def send_action(self, mapped_action):
        pass

from device_detector import DeviceDetector
from profile_manager import ProfileManager
from input_mapper import InputMapper
from config_exporter import ConfigExporter

class ControllerManager:
    """
    Système principal de la couche d'abstraction de manettes.
    C'est la seule classe que l'application cliente (Tkinter, boucle de jeu) 
    devrait instancier et appeler.
    """

    def __init__(self, profiles_dir="profiles", output_adapter=None):
        # Initialisation silencieuse de Pygame en fond (sans fenêtre)
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()

        # Instanciation de l'architecture modulaire
        self.detector = DeviceDetector()
        self.profile_manager = ProfileManager(profiles_dir=profiles_dir)
        self.mapper = InputMapper(self.profile_manager)
        
        # Callback pour intercepter les touches brutes avant traduction (pour le mode "écoute" de la GUI)
        self.raw_input_callback = None
        
        # Liste des sorties (utilisée par l'UI pour la visualisation en direct)
        self.outputs = []
        if output_adapter:
            self.outputs.append(output_adapter)
        
        # Outil d'exportation pour le mapping direct
        self.exporter = ConfigExporter(base_path=os.path.dirname(__file__))
        
        # ID de la manette sélectionnée pour l'export (si None, prend la première)
        self.selected_joy_id = None
        
        print("[ControllerManager] Initialise (Mode Mapping Direct).")

    def apply_config_to_emulators(self, profile_name=None):
        """
        Prend le profil actuellement chargé (ou celui spécifié), le sauvegarde sur disque, 
        puis l'exporte au format physique direct pour les émulateurs.
        """
        if profile_name:
            # On s'assure que le profil spécifié est celui qui sera sauvegardé
            self.profile_manager.active_profile_name = profile_name
            
        # Sauvegarde automatique du profil JSON (ex: ww.json) avant l'export
        self.profile_manager.save_profile()

        # On récupère la manette à utiliser
        joys = self.detector.joysticks
        if not joys:
            print("[ControllerManager] Aucune manette détectée, rescan en cours...")
            self.detector.scan_devices()
            joys = self.detector.joysticks
            
        if not joys:
            print("[ControllerManager] Erreur: Toujours aucune manette physique détectée pour l'export.")
            return False
            
        # Priorité à la manette sélectionnée par l'utilisateur
        target_joy_id = self.selected_joy_id
        if target_joy_id is None or target_joy_id not in joys:
            # Fallback sur la première disponible
            target_joy_id = list(joys.keys())[0]
            
        joy_name = joys[target_joy_id]["name"]
        ctrl_type = joys[target_joy_id].get("type", "Generic")
        
        # On inverse le mapping du profile_manager pour avoir : ActionLogique -> BoutonPhysique
        reverse_map = {}
        for k, v in self.profile_manager.mapping.items():
            reverse_map[v] = k
            
        # Nom du fichier d'export Dolphin (.ini) basé sur le profil
        export_name = "GCPadNew.ini"
        if profile_name:
            export_name = f"{profile_name}.ini"
        elif self.profile_manager.active_profile_name:
            export_name = f"{self.profile_manager.active_profile_name}.ini"

        # Export Dolphin
        self.exporter.export_dolphin_config(joy_name, reverse_map, profile_name=export_name, ctrl_type=ctrl_type)
        
        # Déterminer le système pour BizHawk
        system = "N64"
        if profile_name:
            if profile_name.startswith("mc"):
                system = "GBA"
            elif profile_name.startswith("alttp"):
                system = "SNES"
            elif profile_name.startswith("z1") or profile_name.startswith("z2"):
                system = "NES"
            elif profile_name.startswith("st") or profile_name.startswith("ph"):
                system = "NDS"
        elif self.profile_manager.active_profile_name:
            active = self.profile_manager.active_profile_name
            if active.startswith("mc"):
                system = "GBA"
            elif active.startswith("alttp"):
                system = "SNES"
            elif active.startswith("z1") or active.startswith("z2"):
                system = "NES"
            elif active.startswith("st") or active.startswith("ph"):
                system = "NDS"

        # Export BizHawk
        self.exporter.export_bizhawk_config(reverse_map, ctrl_type=ctrl_type, system=system)
        
        # Export Azahar (Désactivé pour l'instant)
        # if profile_name == "albw" or self.profile_manager.active_profile_name == "albw":
        #     self.exporter.export_azahar_config(joy_name, reverse_map, ctrl_type=ctrl_type)
        
        return True
        
    def disable_config_for_emulators(self, profile_name):
        """
        Retire les configurations injectées pour ce profil (Dolphin uniquement pour l'instant).
        """
        # ww -> GZL, tp -> GZ2
        game_map = {"ww": "GZL", "tp": "GZ2"}
        if profile_name in game_map:
            print(f"[ControllerManager] Nettoyage configuration Dolphin pour {profile_name}...")
            self.exporter.remove_dolphin_game_settings(game_map[profile_name])

    def load_game_profile(self, game_name):
        """Demande au ProfileManager de basculer vers le profil demandé (ex: 'oot')."""
        return self.profile_manager.load_profile(game_name)

    def poll(self):
        """
        Pompe les événements Pygame sans bloquer (boucle asynchrone / thread-safe).
        À appeler régulièrement (ex: via root.after dans Tkinter ou dans la boucle principale).
        """
        for event in pygame.event.get():
            # 1. Le détecteur reçoit l'événement brut et le normalise (BTN_0, AXIS_1, etc.)
            raw_input = self.detector.process_event(event)
            
            if not raw_input:
                continue
                
            # Interception GUI "Mode Écoute"
            if self.raw_input_callback:
                if self.raw_input_callback(raw_input):
                    continue
            
            # 2. Le mapper l'intercepte pour essayer de le traduire en action (ACTION_A, MOVE_X)
            mapped_action = self.mapper.map_input(raw_input)
            
            # 3. Envoyer l'action aux sorties enregistrées (ex: UI pour allumer les boutons)
            if mapped_action:
                for out in self.outputs:
                    out.send_action(mapped_action)

# --- EXEMPLE D'UTILISATION (CLI / Test) ---
if __name__ == "__main__":
    import time
    
    print("=== TEST DU SYSTÈME D'ABSTRACTION MANETTE ===")
    
    # 1. Initialisation du cœur
    manager = ControllerManager()
    
    # 2. Chargement du profil "Ocarina of Time" ou repli sur "default"
    manager.load_game_profile("oot")
    
    print("\nBranchez une manette Xbox, PlayStation, ou Switch Pro et pressez des boutons. CTRL+C pour quitter.\n")
    
    # 3. Boucle principale (Exemple sans blocage)
    try:
        while True:
            # Poll constant (très léger en ressources)
            manager.poll()
            
            # Repos court pour éviter que la boucle CPU tourne à 100%
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nArrêt du système d'abstraction manette.")
        pygame.quit()
