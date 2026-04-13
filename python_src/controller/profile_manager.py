import json
import os

class ProfileManager:
    """
    Gère le chargement et le basculement des profils JSON.
    Un profil contient un mapping entre les inputs physiques normalisés 
    (ex: BTN_0) et les actions logiques (ex: ACTION_A).
    """

    def __init__(self, profiles_dir="profiles"):
        self.profiles_dir = profiles_dir
        self.active_profile_name = None
        self.mapping = {}
        
        # S'assure que le dossier des profils existe
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

    def load_profile(self, profile_name):
        """Charge un profil JSON dynamiquement depuis le dossier."""
        filepath = os.path.join(self.profiles_dir, f"{profile_name}.json")
        
        if not os.path.exists(filepath):
            print(f"[ProfileManager] Profil introuvable: {filepath}")
            # Repli sur le profil par défaut si on cherchait un autre profil
            if profile_name != "default":
                print("[ProfileManager] -> Tentative de chargement du profil par défaut.")
                return self.load_profile("default")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.mapping = data.get("mapping", {})
                self.active_profile_name = profile_name
                print(f"[ProfileManager] Profil '{profile_name}' charge avec succes ({len(self.mapping)} bindings).")
                return True
        except Exception as e:
            print(f"[ProfileManager] Erreur lors du chargement du profil '{profile_name}': {e}")
            return False

    def save_profile(self):
        """Sauvegarde le mapping actuel dans le fichier JSON du profil actif."""
        if not self.active_profile_name:
            return False
            
        filepath = os.path.join(self.profiles_dir, f"{self.active_profile_name}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            data["mapping"] = self.mapping
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print(f"[ProfileManager] Profil '{self.active_profile_name}' sauvegarde avec succes.")
            return True
        except Exception as e:
            print(f"[ProfileManager] Erreur lors de la sauvegarde du profil '{self.active_profile_name}': {e}")
            return False

    def get_action_for_input(self, input_id):
        """Retourne l'action logique correspondant à un input normalisé, ou None."""
        return self.mapping.get(input_id)
