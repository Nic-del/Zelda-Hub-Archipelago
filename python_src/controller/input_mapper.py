class InputMapper:
    """
    Traduit les inputs physiques normalisés (ex: BTN_0) en actions logiques
    universelles (ex: ACTION_A) en utilisant le gestionnaire de profils actif.
    C'est la couche d'abstraction qui coupe le lien direct avec le matériel.
    """

    def __init__(self, profile_manager):
        # On injecte la dépendance vers le ProfileManager
        self.profile_manager = profile_manager

    def map_input(self, input_event):
        """Prend un événement input normalisé et retourne une action logique formatée."""
        if not input_event:
            return None

        # Format input type (ex: BTN_1, AXIS_0+, HAT_0_1,0)
        action_name = self.profile_manager.get_action_for_input(input_event["id"])
        
        # Si une action est matché dans le profil JSON, on la formatte 
        if action_name:
            # On renvoie l'action, son état (appuyé/relâché/valeur de l'axe) et la manette source
            return {
                "action": action_name,
                "state": input_event["state"],
                "joy_id": input_event["joy_id"],
                "raw_input": input_event["id"]
            }
            
        # Si non mappé, on renvoie quand même l'action pour le UI (avec la mention Non Mappé)
        # Un vrai adapteur de sortie l'ignorera simplement
        return {
            "action": "(Non Mappé)",
            "state": input_event["state"],
            "joy_id": input_event["joy_id"],
            "raw_input": input_event["id"]
        }
