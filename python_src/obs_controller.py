import json
import os
import threading
try:
    from obswebsocket import obsws, requests as obs_req
    HAS_OBS = True
except ImportError:
    HAS_OBS = False

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

class OBSController:
    def __init__(self):
        self.client = None
        self.enabled = False
        self.host = "localhost"
        self.port = 4455
        self.password = ""
        self.scenes = {}
        self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            obs_settings = config.get("obs_settings", {})
            self.enabled = obs_settings.get("enabled", False)
            self.host = obs_settings.get("host", "localhost")
            self.port = obs_settings.get("port", 4455)
            self.password = obs_settings.get("password", "")
            self.scenes = obs_settings.get("scenes", {})
        except Exception as e:
            print(f"[OBS] Error loading config: {e}")

    def switch_scene(self, game_name):
        if not self.enabled or not HAS_OBS:
            return

        scene_name = self.scenes.get(game_name)
        if not scene_name:
            print(f"[OBS] No scene configured for game: {game_name}")
            return

        def _threaded_switch():
            try:
                print(f"[OBS] Connecting to {self.host}:{self.port}...")
                
                cl = obsws(self.host, self.port, self.password)
                cl.connect()
                print(f"[OBS] Switching to scene: {scene_name}")
                # The user's exact syntax: call(requests.SetCurrentProgramScene(...))
                cl.call(obs_req.SetCurrentProgramScene(sceneName=scene_name))
                cl.disconnect()
                    
            except Exception as e:
                print(f"[OBS] Failed to switch scene: {e}")

        threading.Thread(target=_threaded_switch, daemon=True).start()

    def test_connection(self):
        """Tests the connection and returns (success, message)."""
        if not HAS_OBS:
            return False, "Bibliothèque 'obs-websocket-py' non installée."
        
        try:
            cl = obsws(self.host, self.port, self.password)
            cl.connect()
            v = cl.call(obs_req.GetVersion())
            cl.disconnect()
            return True, f"Connecté ! (OBS {v.getObsVersion()})"
        except Exception as e:
            return False, f"Échec : {str(e)}"

# Global instance
obs_controller = OBSController()
