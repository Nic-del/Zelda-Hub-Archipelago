import os
import time
import subprocess
import threading
import json
import copy
import sys
from abc import ABC, abstractmethod
from enum import Enum
import zipfile
from typing import Optional, Dict, List
# Chemin absolu centralisé pour la config
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
# Config should stay next to the EXE to be editable
CONFIG_PATH = os.path.abspath(os.path.join(get_exe_dir(), "config.json"))

def resolve_path(path):
    """
    Resolves a path: 
    1. Expands environment variables (%APPDATA%, etc.)
    2. If relative, joins it with the Hub's root directory (get_exe_dir())
    3. Returns a normalized absolute path.
    """
    if not path:
        return ""
    # Expands environment variables like %APPDATA% or %ProgramData%
    expanded_path = os.path.expandvars(path)
    if os.path.isabs(expanded_path):
        return os.path.normpath(expanded_path)
    # Resolve relative to the Hub root (EXE folder)
    return os.path.normpath(os.path.join(get_exe_dir(), expanded_path))

# Mock libraries for the sake of the example structure
# In a real environment, you would install: pip install pywin32 psutil keyboard
try:
    import win32gui
    import win32con
    import win32api
    import win32process
    import psutil
    # Priority Classes (Windows)
    PROCESS_PRIORITY_IDLE = psutil.IDLE_PRIORITY_CLASS
    PROCESS_PRIORITY_BELOW_NORMAL = psutil.BELOW_NORMAL_PRIORITY_CLASS
    PROCESS_PRIORITY_NORMAL = psutil.NORMAL_PRIORITY_CLASS
    PROCESS_PRIORITY_ABOVE_NORMAL = psutil.ABOVE_NORMAL_PRIORITY_CLASS
    PROCESS_PRIORITY_HIGH = psutil.HIGH_PRIORITY_CLASS
except ImportError:
    # Fallback for non-Windows environments (like this web preview)
    # so the code can at least be imported without crashing immediately
    win32gui = None
    win32con = None
    win32process = None
    psutil = None
    PROCESS_PRIORITY_IDLE = 0
    PROCESS_PRIORITY_BELOW_NORMAL = 0
    PROCESS_PRIORITY_NORMAL = 0
    PROCESS_PRIORITY_ABOVE_NORMAL = 0
    PROCESS_PRIORITY_HIGH = 0

def set_process_priority(pid, priority):
    """Sets the CPU priority of a process by its PID."""
    if not psutil: return False
    try:
        p = psutil.Process(pid)
        p.nice(priority)
        return True
    except Exception as e:
        print(f"[Priority] Could not set priority for PID {pid}: {e}")
        return False

def set_current_process_priority(priority):
    """Sets the CPU priority of the current Python process."""
    return set_process_priority(os.getpid(), priority)

class EmulatorType(Enum):
    BIZHAWK = "BizHawk"
    DOLPHIN = "Dolphin"
    RETROARCH = "RetroArch"

class GameState(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"

def ensure_bizhawk_maximized(emu_path):
    """Force MainWindowMaximized=True dans le config.ini de BizHawk."""
    emu_dir = os.path.dirname(emu_path)
    config_ini = os.path.join(emu_dir, "config.ini")
    if not os.path.exists(config_ini): return

    try:
        with open(config_ini, "r", encoding="utf-8") as f:
            content = f.read()
        
        if content.strip().startswith("{"):
            data = json.loads(content)
            data["MainWindowMaximized"] = True
            with open(config_ini, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"[BizHawk] MainWindowMaximized force à True dans {config_ini}")
        else:
            lines = content.splitlines()
            new_lines = []
            found = False
            for line in lines:
                if "MainWindowMaximized" in line:
                    if ":" in line: new_lines.append('  "MainWindowMaximized": true,')
                    else: new_lines.append("MainWindowMaximized=True")
                    found = True
                else: new_lines.append(line)
            if not found: new_lines.append("MainWindowMaximized=True")
            with open(config_ini, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
    except Exception as e:
        print(f"[BizHawk] Erreur modif config.ini : {e}")

class EmulatorController(ABC):
    """
    Abstract base class for controlling different emulators.
    """
    def __init__(self, emulator_path: str, rom_path: str):
        self.emulator_path = emulator_path
        self.rom_path = rom_path
        self.game_name = "" # Will be set by GameManager
        self.process: Optional[subprocess.Popen] = None
        self.window_handle = None
        self.window_keyword = "" # To be set by subclasses
        self.extra_processes: List[subprocess.Popen] = []

    @abstractmethod
    def launch(self):
        """Launch the emulator with the ROM."""
        pass

    @abstractmethod
    def load_save_state(self, slot: int):
        """Load a specific save state slot."""
        pass

    @abstractmethod
    def save_state(self, slot: int):
        """Save to a specific save state slot."""
        pass

    @abstractmethod
    def pause(self):
        """Pause the emulation."""
        pass

    @abstractmethod
    def resume(self):
        """Resume the emulation."""
        pass

    def stop(self):
        """Termine proprement le jeu et tous les processus associés (ex: clients Archipelago)."""
        # 1. Fermer les processus extra (Clients AP, etc.)
        for p in self.extra_processes:
            try:
                if p.poll() is None:
                    print(f"[Launcher] Terminating extra process (PID: {p.pid})...")
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                    self._wait_for_pid(p.pid)
            except Exception as e:
                print(f"[Launcher] Error stopping extra process: {e}")
        self.extra_processes = []

        # 2. Fermer le processus principal (Emulateur / Jeu) de manière multi-strate
        if self.process and self.process.poll() is None:
            pid = self.process.pid
            
            # Récupérer le handle si possible
            hwnd = self.window_handle
            if not hwnd and self.window_keyword and win32gui:
                 hwnd = self.find_window(self.window_keyword)
            
            # STRATE 0: LUA SIGNAL (Le seul autorisé pour BizHawk selon la demande utilisateur)
            temp_dir = os.path.join(get_exe_dir(), "temp")
            
            # Utilisation du préfixe spécifique au jeu pour le flag de shutdown
            prefix = self.game_name.lower().replace(" ", "").replace("'", "") if hasattr(self, "game_name") and self.game_name else "bizhawk"
            shutdown_flag = os.path.join(temp_dir, f"{prefix}_shutdown.flag")
            
            if not os.path.exists(temp_dir):
                try: os.makedirs(temp_dir)
                except: pass

            is_bizhawk = "BizHawk" in str(type(self)) or (self.window_keyword and "EmuHawk" in self.window_keyword)
            if is_bizhawk:
                try:
                    with open(shutdown_flag, "w", encoding="utf-8") as f:
                        f.write("OFF")
                    print(f"[Launcher] Signal de fermeture Lua envoyé à BizHawk ({prefix}_shutdown.flag) (Attente 4s)...")
                    if self._wait_for_shutdown(timeout=4.0):
                        if os.path.exists(shutdown_flag): os.remove(shutdown_flag)
                        print("[Launcher] BizHawk fermé proprement via Lua.")
                    else:
                        print("[Launcher] Attention: BizHawk n'a pas répondu au signal Lua dans le délai imparti.")
                    
                    # On s'arrête ici pour BizHawk : pas de fallback (WM_CLOSE, terminate ou taskkill)
                    self.process = None
                    self.window_handle = None
                    return
                except Exception as e:
                    print(f"[Launcher] Lua shutdown error: {e}")
                    # En cas d'erreur sur le fichier, on ne fallback pas non plus pour respecter la consigne
                    self.process = None
                    return

            # STRATE 1: WM_CLOSE (Propre)
            if hwnd and win32gui:
                try:
                    if win32gui.IsWindow(hwnd):
                        print(f"[Launcher] Sending WM_CLOSE to handle {hwnd}...")
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        if self._wait_for_shutdown(timeout=2.0):
                            return
                except Exception as e:
                    print(f"[Launcher] PostMessage failed (Handle might be invalid): {e}")

            # STRATE 2: Terminate (Moins propre)
            print(f"[Launcher] Terminating process {pid}...")
            try:
                self.process.terminate()
                if self._wait_for_shutdown(timeout=2.0):
                    return
            except: pass

            # STRATE 3: Force Kill (Dernier recours)
            print(f"[Launcher] Force killing process tree for PID {pid}...")
            try:
                # /T kills the entire process tree
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
                self._wait_for_pid(pid)
            except: pass
        
        self.process = None
        self.window_handle = None

    def _wait_for_shutdown(self, timeout=1.0):
        """Attend que le processus principal s'arrête."""
        start = time.time()
        while time.time() - start < timeout:
            if self.process and self.process.poll() is not None:
                print(f"[Launcher] Process stopped successfully.")
                return True
            time.sleep(0.2)
        return False

    def _wait_for_pid(self, pid, timeout=3):
        """Attend que le PID disparaisse du système."""
        if not psutil: 
            time.sleep(1) # Fallback sans psutil
            return
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not psutil.pid_exists(pid):
                return
            time.sleep(0.3)
        print(f"[Launcher] Warning: PID {pid} still exists after {timeout}s.")

    def get_clean_env(self):
        """Retourne un environnement propre sans les variables SDL qui bloquent les fenêtres."""
        env = copy.deepcopy(dict(os.environ))
        # Retirer les variables SDL qui forcent le mode 'dummy' ou autres conflits
        for key in list(env.keys()):
            if key.startswith("SDL_"):
                del env[key]
        return env

    def focus(self):
        """Bring the emulator window to the foreground with aggressive techniques."""
        if not self.window_handle or not win32gui:
            return False
            
        try:
            # 1. Maximize directement (On évite le flicker du RESTORE)
            win32gui.ShowWindow(self.window_handle, 3) # SW_MAXIMIZE
            
            # 2. Try to bring to foreground
            # ALT-key trick: Windows allows SetForegroundWindow if ALT is pressed
            try:
                # Wake up window focus system
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                win32gui.SetForegroundWindow(self.window_handle)
            except:
                # Fallback to TopMost toggle if win32api is missing or fails
                win32gui.SetWindowPos(self.window_handle, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                win32gui.SetWindowPos(self.window_handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                try: 
                    win32gui.SetForegroundWindow(self.window_handle)
                except: 
                    pass
            
            # Action optionnelle post-focus (ex: minimiser la console Lua)
            self.post_focus_actions()
            
            print(f"[Launcher] Focus aggressive attempted on handle {self.window_handle}")
            return True
        except Exception as e:
            print(f"[Launcher] Focus warning: {e}")
            return False

    def post_focus_actions(self):
        """Hook pour les actions à effectuer après le focus (ex: minimiser la console Lua)."""
        pass

    def wait_and_focus(self, timeout=12):
        """Attend que la fenêtre apparaisse et insiste pour la mettre au premier plan."""
        if not self.window_keyword or not win32gui:
            return False
            
        print(f"[Launcher] Waiting and focusing '{self.window_keyword}' (timeout {timeout}s)...")
        start_time = time.time()
        found = False
        
        while time.time() - start_time < timeout:
            handle = self.find_window(self.window_keyword, silent=True)
            if handle:
                # Une fois la fenêtre trouvée, on insiste sur le focus plusieurs fois
                # car d'autres processus (AP client, PopTracker) peuvent "voler" le focus au démarrage
                self.focus()
                found = True
                # On continue de surveiller le focus pendant 2-3 secondes pour être sûr
                if time.time() - start_time > 3: # Si on a déjà passé pas mal de temps, on s'arrête
                    return True
            time.sleep(0.2) # Réduit de 1.0s à 0.2s pour une détection plus rapide
            
        return found

    def hide(self):
        """Hide the emulator window."""
        if self.window_handle and win32gui:
            win32gui.ShowWindow(self.window_handle, win32con.SW_MINIMIZE)

    def find_window(self, keyword_or_list, silent=False):
        """Trouve et stocke le HWND de la fenêtre basée sur un ou plusieurs mots-clés (Insensible à la casse)."""
        if not win32gui: return None
        keywords = [keyword_or_list] if isinstance(keyword_or_list, str) else keyword_or_list
        kws_lower = [k.lower() for k in keywords]
        
        found = [None]
        max_matches = [-1]
        
        def _enum_cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                matches = 0
                
                # Vérifier les mots-clés
                for kw in keywords:
                    kw_lower = kw.lower()
                    is_mandatory = kw.startswith("+")
                    actual_kw = kw_lower[1:] if is_mandatory else kw_lower
                    
                    if actual_kw in title:
                        if "lua console" in title: # On ignore la console de scripts qui vole le focus
                             return True
                        matches += 1
                    elif is_mandatory:
                        # DEBUG: Pourquoi on rejette
                        # print(f"[Debug] Rejet de '{title}' car absent: '{actual_kw}'")
                        return True 
                
                if matches > 0 and matches > max_matches[0]:
                    max_matches[0] = matches
                    found[0] = hwnd
                    # Si on a trouvé TOUS les mots-clés obligatoires et au moins un mot-clé de base, c'est bon
                    mandatory_count = sum(1 for kw in keywords if kw.startswith("+"))
                    found_mandatory = sum(1 for kw in keywords if kw.startswith("+") and kw[1:].lower() in title)
                    if found_mandatory == mandatory_count and any(kw.lower() in title for kw in keywords if not kw.startswith("+")):
                        return False # Match idéal trouvé
            return True
            
        try: 
            win32gui.EnumWindows(_enum_cb, None)
        except: 
            pass
        
        self.window_handle = found[0]
        if self.window_handle:
            title = win32gui.GetWindowText(self.window_handle)
            print(f"[Launcher] Fenêtre détectée : '{title}' (Handle: {self.window_handle}) pour {keywords}")
        else:
            if not silent:
                print(f"[Launcher] AUCUNE fenêtre trouvée pour {keywords}")
        return self.window_handle

class BizHawkController(EmulatorController):
    def __init__(self, emulator_path: str, rom_path: str):
        super().__init__(emulator_path, rom_path)
        self.window_keyword = ["EmuHawk", "BizHawk"]
        self.slot_name = ""

    def launch(self):
        print(f"[BizHawk] Launching {self.rom_path}...")
        ensure_bizhawk_maximized(self.emulator_path)
        
        # --- WRAPPER LUA UNIFIÉ ---
        temp_dir = os.path.join(get_exe_dir(), "temp")
        wrapper_path = os.path.join(temp_dir, "bizhawk_launcher_wrapper.lua")
        shutdown_flag_path = os.path.join(temp_dir, "bizhawk_shutdown.flag")
        
        # Prefixe unique pour ce jeu
        prefix = self.game_name.lower().replace(" ", "").replace("'", "")
        
        # On crée un script qui contient la surveillance ET -- BizHawk Launcher Wrapper (Dynamic)
        wrapper_content = f"""
-- BizHawk Launcher Wrapper (Dynamic)
local hub_temp_dir = os.getenv("HUB_TEMP_DIR") or [[{temp_dir}]]
local hub_prefix = os.getenv("HUB_GAME_PREFIX") or "bizhawk"
local _HUB_PAUSED = false

local shutdown_flag = hub_temp_dir .. "/" .. hub_prefix .. "_shutdown.flag"
local save_flag = hub_temp_dir .. "/" .. hub_prefix .. "_save.flag"
local load_flag = hub_temp_dir .. "/" .. hub_prefix .. "_load.flag"
local pause_flag = hub_temp_dir .. "/" .. hub_prefix .. "_pause.flag"
local resume_flag = hub_temp_dir .. "/" .. hub_prefix .. "_resume.flag"

local function check_launcher_signals()
    local fs = io.open(save_flag, "r")
    if fs then
        local slot_str = fs:read("*a")
        fs:close()
        os.remove(save_flag)
        local slot = tonumber(slot_str) or 10
        savestate.saveslot(slot)
        print("Launcher: Auto-saved (Slot " .. slot .. ")")
    end

    local fl = io.open(load_flag, "r")
    if fl then
        local slot_str = fl:read("*a")
        fl:close()
        os.remove(load_flag)
        local slot = tonumber(slot_str) or 10
        savestate.loadslot(slot)
        print("Launcher: Auto-loaded (Slot " .. slot .. ")")
    end

    if io.open(shutdown_flag, "r") then
        os.remove(shutdown_flag)
        client.exit()
    end

    if io.open(pause_flag, "r") then
        os.remove(pause_flag)
        client.pause()
    end

    if io.open(resume_flag, "r") then
        os.remove(resume_flag)
        client.unpause()
    end
end

local frame_count = 0
event.onframestart(function()
    check_launcher_signals()
end)

-- Onpaint runs even when paused (on UI redraw/focus)
if event.onpaint then
    event.onpaint(function()
        if client.ispaused() then check_launcher_signals() end
    end)
elseif gui and gui.register then
    gui.register(function()
        if client.ispaused() then check_launcher_signals() end
    end)
end

print("Launcher: BizHawk Wrapper Active.")
"""
        # Pour BizHawkController standard, on s'arrête là ou on ajoute la ROM si c'est un script
        if self.rom_path and self.rom_path.endswith(".lua"):
            wrapper_content += f'\ndofile([[{self.rom_path}]])'

        try:
            with open(wrapper_path, "w", encoding="utf-8") as f:
                f.write(wrapper_content)
            cmd = [self.emulator_path, self.rom_path, f"--lua={wrapper_path}"]
        except:
            cmd = [self.emulator_path, self.rom_path]

        emu_dir = os.path.dirname(self.emulator_path)
        
        try:
            # On utilise un environnement propre pour eviter d'heriter du mode 'dummy' video de pygame
            env = self.get_clean_env()
            env["HUB_TEMP_DIR"] = temp_dir.replace("\\", "/")
            env["HUB_GAME_PREFIX"] = prefix
            
            self.process = subprocess.Popen(
                cmd, 
                cwd=emu_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                env=env
            )
            print(f"[BizHawk] Debug: Process PID={self.process.pid}")

            # Attente courte pour vérifier si le processus reste vivant
            time.sleep(0.5) # Réduit de 1.5s à 0.5s
            poll = self.process.poll()
            if poll is not None:
                print(f"[BizHawk] Erreur: Le processus s'est arrete prematurement (Code: {poll}).")
                return False
                
            # Wait for window to appear
            print(f"[BizHawk] Waiting for window {self.window_keyword} (6s)...")
            handle = self.find_window(self.window_keyword)
            if handle:
                return True
            else:
                print("[BizHawk] Attention: Fenetre non trouvee apres 6s.")
                return True # On retourne True car le process est vivant
        except Exception as e:
            print(f"[BizHawk] Erreur lors du lancement : {e}")
            return False

    def load_save_state(self, slot: int):
        print(f"[BizHawk] Requesting load state {slot}...")
        temp_dir = os.path.join(get_exe_dir(), "temp")
        load_flag = os.path.join(temp_dir, "bizhawk_load.flag")
        if not os.path.exists(temp_dir): os.makedirs(temp_dir, exist_ok=True)
        try:
            with open(load_flag, "w", encoding="utf-8") as f:
                f.write(str(slot))
        except Exception as e:
            print(f"[BizHawk] Error sending load signal: {e}")

    def save_state(self, slot: int):
        print(f"[BizHawk] Requesting save state {slot}...")
        temp_dir = os.path.join(get_exe_dir(), "temp")
        save_flag = os.path.join(temp_dir, "bizhawk_save.flag")
        if not os.path.exists(temp_dir): os.makedirs(temp_dir, exist_ok=True)
        try:
            with open(save_flag, "w", encoding="utf-8") as f:
                f.write(str(slot))
        except Exception as e:
            print(f"[BizHawk] Error sending save signal: {e}")

    def pause(self):
        print(f"[BizHawk] Pausing {self.game_name}...")
        temp_dir = os.path.join(get_exe_dir(), "temp")
        prefix = self.game_name.lower().replace(" ", "").replace("'", "")
        pause_flag = os.path.join(temp_dir, f"{prefix}_pause.flag")
        if not os.path.exists(temp_dir): os.makedirs(temp_dir, exist_ok=True)
        try:
            with open(pause_flag, "w", encoding="utf-8") as f:
                f.write("PAUSE")
        except: pass

    def resume(self):
        print(f"[BizHawk] Resuming {self.game_name} (Aggressive Unpause)...")
        temp_dir = os.path.join(get_exe_dir(), "temp")
        prefix = self.game_name.lower().replace(" ", "").replace("'", "")
        resume_flag = os.path.join(temp_dir, f"{prefix}_resume.flag")
        if not os.path.exists(temp_dir): os.makedirs(temp_dir, exist_ok=True)
        try:
            with open(resume_flag, "w", encoding="utf-8") as f:
                f.write("RESUME")
        except: pass
        
        # Poke hardware key 'R' (0x52) with aggressive methods
        self._send_bizhawk_key(0x52)

    def _send_bizhawk_key(self, vk_code):
        # On utilise le script de debug validé par l'utilisateur
        temp_dir = os.path.join(get_exe_dir(), "temp")
        ps_script_path = os.path.normpath(os.path.join(temp_dir, "debug_unpause.ps1"))
        
        if not os.path.exists(ps_script_path):
            print(f"[BizHawk] Erreur: Script {ps_script_path} non trouvé.")
            return

        print(f"[BizHawk] Hub: Ouverture du script de reprise dans un nouveau terminal...")
        
        try:
            # On passe le slot_name en paramètre pour une recherche précise
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script_path]
            if hasattr(self, "slot_name") and self.slot_name:
                cmd.extend(["-slotname", self.slot_name])
                print(f"[BizHawk] Cible demandée : {self.slot_name}")

            # On lance dans une NOUVELLE CONSOLE visible (COMME LE BOUTON)
            subprocess.Popen(cmd, cwd=temp_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            print(f"[BizHawk] Erreur Hub (Appel Terminal Externe) : {e}")

    def post_focus_actions(self):
        """Minimise la console Lua dès que l'émulateur est focalisé."""
        def minimize_lua_thread():
            time.sleep(0.5)
            ps_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minimize_lua_console.ps1")
            if os.path.exists(ps_script):
                print(f"[BizHawk] Minimizing Lua Console for {self.game_name}...")
                subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
        
        threading.Thread(target=minimize_lua_thread, daemon=True).start()

class DolphinController(EmulatorController):
    def __init__(self, emulator_path: str, rom_path: str, game_id: str = ""):
        super().__init__(emulator_path, rom_path)
        self.game_id = game_id
        if game_id:
            # On cherche d'abord le code jeu pour être sûr de focus la bonne session de Dolphin
            # Le '+' rend l'ID obligatoire pour éviter de focus une autre instance de Dolphin par erreur
            self.window_keyword = ["+" + game_id.upper(), "Dolphin"]
        else:
            self.window_keyword = "Dolphin"

    def launch(self):
        print(f"[Dolphin] Launching {self.rom_path}...")
        # Dolphin CLI args: -b (batch) -e (exec)
        cmd = [self.emulator_path, '-b', '-e', self.rom_path]
        emu_dir = os.path.dirname(self.emulator_path)
        
        print(f"[Dolphin] Debug: emu_path={os.path.abspath(self.emulator_path)}")
        print(f"[Dolphin] Debug: rom_path={os.path.abspath(self.rom_path)}")
        print(f"[Dolphin] Debug: cmd={cmd}")
        
        try:
            env = self.get_clean_env()
            self.process = subprocess.Popen(cmd, cwd=emu_dir, env=env)
            print(f"[Dolphin] Debug: Process PID={self.process.pid}")
            
            time.sleep(0.5) # Réduit de 1.5s à 0.5s
            poll = self.process.poll()
            if poll is not None:
                print(f"[Dolphin] Erreur: Le processus s'est arrete prematurement (Code: {poll}).")
                return False
                
            time.sleep(0.5) # Réduit de 2s à 0.5s
            self.find_window(self.window_keyword)
            return True
        except Exception as e:
            print(f"[Dolphin] Erreur lors du lancement : {e}")
            return False


    def pause(self):
        """Met en pause Dolphin en envoyant F10 via keybd_event."""
        if self.process and self.process.poll() is None:
            print(f"[Dolphin] Tentative de mise en PAUSE (F10)...")
            
            # 1. Focus agressif avant de faire quoi que ce soit
            self.find_window(self.window_keyword)
            if self.window_handle:
                self.focus()
                # On laisse le temps au focus de se faire au niveau du système
                time.sleep(0.4)
            else:
                print(f"[Dolphin] Erreur: Fenêtre de jeu non trouvée pour pause.")
                return

            # 2. Utilisation de la même méthode que les save states (keybd_event)
            # 0x79 = F10, 0x44 = Scan Code F10
            keys = "[Win32]::keybd_event(0x79, 0x44, 0, 0); Start-Sleep -m 150; [Win32]::keybd_event(0x79, 0x44, 2, 0);"
            
            # SW_MAXIMIZE (3) pour garder la fenêtre en plein écran lors de la pause
            self._run_dolphin_keys(keys, show_cmd=3)
            
            print(f"[Dolphin] Commande Pause envoyée (Fenêtre focalisée et maximisée).")

    def resume(self):
        """Réactive Dolphin en envoyant F10 via keybd_event."""
        if self.process and self.process.poll() is None:
            print(f"[Dolphin] Tentative de REPRISE (F10)...")
            self.find_window(self.window_keyword)
            if self.window_handle:
                # Focus agressif
                self.focus()
            else:
                print(f"[Dolphin] Erreur: Fenêtre de jeu non trouvée pour resume.")
                return

            # Utilisation de keybd_event
            keys = "[Win32]::keybd_event(0x79, 0x44, 0, 0); Start-Sleep -m 150; [Win32]::keybd_event(0x79, 0x44, 2, 0);"
            # Maximisation (3) à la reprise pour remettre le jeu en première place
            self._run_dolphin_keys(keys, show_cmd=3)
            print(f"[Dolphin] Commande Resume envoyée (Focalisé et Maximisé).")

    def _run_dolphin_keys(self, keys_ps: str, wait_after: float = 0.0, show_cmd: int = 5):
        """Helper pour exécuter des touches via PowerShell avec focus atomique."""
        if not self.window_handle:
            return
            
        ps_cmd = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern void ShowWindow(IntPtr hWnd, int nCmdShow);
}}
'@
$hwnd = [IntPtr]{self.window_handle}
# Par défaut SW_SHOW (5), mais peut être mis à SW_RESTORE (9) pour dé-maximiser
[Win32]::ShowWindow($hwnd, {show_cmd}) 
[Win32]::SetForegroundWindow($hwnd)
Start-Sleep -m 800
[Win32]::keybd_event(0x12, 0, 2, 0) # ALT Up
[Win32]::keybd_event(0x11, 0, 2, 0) # CTRL Up
{keys_ps}
"""
        subprocess.run(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        if wait_after > 0:
            time.sleep(wait_after)

    def _get_dolphin_states_snapshot(self) -> Dict[str, float]:
        """Prend un instantané des dates de modification des fichiers .s08 (Slot 8)."""
        appdata = os.environ.get('APPDATA')
        if not appdata: return {}
        states_dir = os.path.join(appdata, "Dolphin Emulator", "StateSaves")
        if not os.path.exists(states_dir): return {}
        
        snapshot = {}
        try:
            for f in os.listdir(states_dir):
                if f.lower().endswith(".s08"):
                    path = os.path.join(states_dir, f)
                    snapshot[f] = os.path.getmtime(path)
        except: pass
        return snapshot

    def _has_dolphin_save_happened(self, old_snapshot: Dict[str, float]) -> bool:
        """Vérifie si un fichier .s08 a été mis à jour par rapport à l'instantané."""
        appdata = os.environ.get('APPDATA')
        if not appdata: return False
        states_dir = os.path.join(appdata, "Dolphin Emulator", "StateSaves")
        if not os.path.exists(states_dir): return False
        
        try:
            for f in os.listdir(states_dir):
                if f.lower().endswith(".s08"):
                    path = os.path.join(states_dir, f)
                    new_time = os.path.getmtime(path)
                    if f not in old_snapshot or new_time > old_snapshot[f]:
                        return True
        except: pass
        return False

    def load_save_state(self, slot: int):
        print(f"[Dolphin] Hardware Load (F8)...")
        self.find_window([self.game_name, "Dolphin", "FPS"])
        keys = """
[Win32]::keybd_event(0x10, 0, 2, 0) # SHIFT Up
[Win32]::keybd_event(0x77, 0x42, 0, 0) # F8 Down
Start-Sleep -m 200
[Win32]::keybd_event(0x77, 0x42, 2, 0) # F8 Up
"""
        self._run_dolphin_keys(keys)

    def save_state(self, slot: int):
        print(f"[Dolphin] Détection et sauvegarde forcée (Shift+F8)...")
        # Rafraîchissement agressif du handle avant de tenter quoi que ce soit
        if not self.find_window([self.game_name, "Dolphin", "FPS"]):
            print("[Dolphin] Fenêtre non trouvée, tentative de secours...")
            self.find_window(["Dolphin", "FPS"])
            
        if not self.window_handle:
            print("[Dolphin] ERREUR : Impossible de détecter la fenêtre pour sauvegarder.")
            return

        # 1. Snapshot avant
        old_snapshot = self._get_dolphin_states_snapshot()
        
        # 2. Envoi des touches
        keys = """
[Win32]::keybd_event(0x10, 0x2A, 0, 0) # Shift Down
Start-Sleep -m 100
[Win32]::keybd_event(0x77, 0x42, 0, 0) # F8 Down
Start-Sleep -m 400
[Win32]::keybd_event(0x77, 0x42, 2, 0) # F8 Up
[Win32]::keybd_event(0x10, 0x2A, 2, 0) # Shift Up
"""
        self._run_dolphin_keys(keys)
        
        # 3. Polling intelligent (Max 5 secondes)
        print("[Dolphin] Attente de la confirmation d'écriture sur disque...")
        start_wait = time.time()
        confirmed = False
        while time.time() - start_wait < 5.0:
            if self._has_dolphin_save_happened(old_snapshot):
                confirmed = True
                break
            time.sleep(0.2)
            
        if confirmed:
            print(f"[Dolphin] Sauvegarde CONFIRMÉE sur le disque en {round(time.time()-start_wait, 2)}s.")
        else:
            print("[Dolphin] ATTENTION : Pas de confirmation disque après 5s. On force quand même.")
        
        time.sleep(0.5) # Petit souffle final

    def stop(self):
        """Arrête proprement Dolphin et tue le processus dolphin-emu si nécessaire."""
        super().stop()
        print("[Dolphin] Fermeture forcée de dolphin-emu.exe...")
        if psutil:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == "dolphin-emu.exe":
                        proc.kill()
                except:
                    pass
        else:
            # Fallback taskkill
            subprocess.run(["taskkill", "/F", "/IM", "dolphin-emu.exe"], capture_output=True)

class AzaharController(EmulatorController):
    def __init__(self, emulator_path: str, rom_path: str):
        super().__init__(emulator_path, rom_path)
        self.window_keyword = "Azahar"

    def launch(self):
        print(f"[Azahar] Launching {self.rom_path}...")
        # Azahar CLI args: -v (load file)
        cmd = [self.emulator_path, self.rom_path]
        emu_dir = os.path.dirname(self.emulator_path)
        
        try:
            env = self.get_clean_env()
            self.process = subprocess.Popen(cmd, cwd=emu_dir, env=env)
            print(f"[Azahar] Debug: Process PID={self.process.pid}")
            
            time.sleep(0.5) # Réduit de 2s à 0.5s
            self.find_window("Azahar")
            return True
        except Exception as e:
            print(f"[Azahar] Erreur lors du lancement : {e}")
            return False

    def load_save_state(self, slot: int):
        pass

    def save_state(self, slot: int):
        pass

    def pause(self):
        """Met en pause Azahar en envoyant F4."""
        if self.process and self.process.poll() is None:
            print(f"[Azahar] Tentative de mise en PAUSE (F4)...")
            # Rafraîchir le handle
            self.find_window(self.window_keyword)
            if self.window_handle:
                self.focus()
                # On attend un peu que le focus soit effectif
                time.sleep(0.4)
            else:
                print(f"[Azahar] Erreur: Fenêtre Azahar non trouvée.")
                return

            # 0x73 = F4, 0x3E = Scan Code F4
            keys = "[Win32]::keybd_event(0x73, 0x3E, 0, 0); Start-Sleep -m 150; [Win32]::keybd_event(0x73, 0x3E, 2, 0);"
            # On utilise show_cmd=3 (Maximize) pour être sûr qu'il est en vue lors de la pause
            self._run_azahar_keys(keys, show_cmd=3)
            print(f"[Azahar] Commande Pause envoyée (F4 - Fenêtre focalisée).")

    def resume(self):
        """Réactive Azahar en envoyant F4."""
        if self.process and self.process.poll() is None:
            print(f"[Azahar] Tentative de REPRISE (F4)...")
            self.find_window(self.window_keyword)
            if self.window_handle:
                self.focus()
            else:
                print(f"[Azahar] Erreur: Fenêtre Azahar non trouvée.")
                return

            # 0x73 = F4, 0x3E = Scan Code F4
            keys = "[Win32]::keybd_event(0x73, 0x3E, 0, 0); Start-Sleep -m 150; [Win32]::keybd_event(0x73, 0x3E, 2, 0);"
            self._run_azahar_keys(keys, show_cmd=3)
            print(f"[Azahar] Commande Resume envoyée (F4 - Fenêtre focalisée).")

    def _run_azahar_keys(self, keys_ps: str, show_cmd: int = 5):
        """Helper pour exécuter des touches via PowerShell avec focus atomique."""
        if not self.window_handle:
            return
            
        ps_cmd = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern void ShowWindow(IntPtr hWnd, int nCmdShow);
}}
'@
$hwnd = [IntPtr]{self.window_handle}
[Win32]::ShowWindow($hwnd, {show_cmd}) 
[Win32]::SetForegroundWindow($hwnd)
Start-Sleep -m 500
[Win32]::keybd_event(0x12, 0, 2, 0) # ALT Up
[Win32]::keybd_event(0x11, 0, 2, 0) # CTRL Up
{keys_ps}
"""
        subprocess.run(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)


class MelonDSController(EmulatorController):
    def __init__(self, emulator_path: str, rom_path: str):
        super().__init__(emulator_path, rom_path)
        self.window_keyword = "melonDS"

    def launch(self):
        print(f"[melonDS] Launching {self.rom_path}...")
        # melonDS CLI: melonds.exe [rom]
        cmd = [self.emulator_path, self.rom_path]
        emu_dir = os.path.dirname(self.emulator_path)
        try:
            env = self.get_clean_env()
            self.process = subprocess.Popen(cmd, cwd=emu_dir, env=env)
            time.sleep(2)
            self.find_window("melonDS")
            return True
        except Exception as e:
            print(f"[melonDS] Erreur lors du lancement : {e}")
            return False

    def load_save_state(self, slot: int): pass
    def save_state(self, slot: int): pass
    def pause(self): pass
    def resume(self): pass

class NativeController(EmulatorController):
    """
    Controller for native PC executables (like Ship of Harkinian).
    The 'emulator_path' is actually the executable path.
    'rom_path' is ignored or used for the executable as well.
    """
    def __init__(self, exe_path: str, game_name: str = "", arch_settings: dict = None, slot_name: str = ""):
        super().__init__(exe_path, "")
        self.exe_path = exe_path
        self.game_name = game_name
        self.arch_settings = arch_settings
        self.slot_name = slot_name
        # Keyword par défaut pour SoH ou generic native
        if "soh" in exe_path.lower():
            self.window_keyword = "Ship of Harkinian"
        elif "zelda64recompiled" in exe_path.lower():
            self.window_keyword = "Zelda 64: Recompiled"
        elif self.game_name == "Majora's Mask":
            self.window_keyword = "Majora" # Plus générique pour attraper les différentes versions natives
        else:
            # On prend le nom du fichier sans l'extension .exe
            name_only = os.path.basename(exe_path)
            if name_only.lower().endswith(".exe"):
                name_only = name_only[:-4]
            self.window_keyword = name_only

    def launch(self):
        print(f"[Native] Launching {self.exe_path}...")
        exe_dir = os.path.dirname(self.exe_path)
        
        cmd = [self.exe_path]
        
        # Pour Majora's Mask (Zelda64Recompiled), on écrit le fichier de connexion manuellement
        # au lieu d'utiliser --connect si l'utilisateur le demande.
        if (self.game_name == "Majora's Mask") and self.arch_settings:
            try:
                # Utiliser %LOCALAPPDATA% pour être plus propre que le chemin absolu direct
                local_appdata = os.path.expandvars("%LOCALAPPDATA%")
                ap_connect_path = os.path.join(local_appdata, "Zelda64Recompiled", "saves", "mm_recomp_rando", "apconnect.txt")
                
                # S'assurer que le dossier existe
                os.makedirs(os.path.dirname(ap_connect_path), exist_ok=True)
                
                host = self.arch_settings.get("host", "archipelago.gg")
                port = self.arch_settings.get("port", "")
                slot = self.slot_name or "Linkmm" # Fallback sur Linkmm s'il n'y a rien
                password = self.arch_settings.get("password", "") or ""
                
                # Format: IP:Port \n Slot \n Password (optionnel)
                content = f"{host}:{port}\n{slot}\n{password}\n"
                with open(ap_connect_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[Native] Fichier de connexion écrit (avec mdp) : {ap_connect_path}")
            except Exception as e:
                print(f"[Native] Erreur lors de l'écriture du fichier de connexion MM: {e}")
        
        # Pour Ocarina of Time (SOH), le client est intégré au jeu (on garde --connect ici au cas où)
        # Mais pour MM, l'utilisateur préfère le fichier texte donc on saute l'argument.
        if (self.game_name == "Ocarina of Time") and self.arch_settings:
            host = self.arch_settings.get("host", "archipelago.gg")
            port = self.arch_settings.get("port", "")
            if host and port:
                conn_str = f"{host}:{port}"
                cmd.extend(["--connect", conn_str])

        try:
            env = self.get_clean_env()
            self.process = subprocess.Popen(cmd, cwd=exe_dir, env=env)
            return True
        except Exception as e:
            print(f"[Native] Erreur lors du lancement : {e}")
            return False

    def load_save_state(self, slot: int): pass
    def save_state(self, slot: int): pass
    def pause(self):
        """Met en pause le jeu natif en suspendant le processus."""
        if self.process and self.process.poll() is None:
            print(f"[Native] Suspending process {self.process.pid}...")
            try:
                p = psutil.Process(self.process.pid)
                p.suspend()
                # On ne masque plus par défaut pour préserver la mise en page (Choix utilisateur)
                # self.hide()
            except Exception as e:
                print(f"[Native] Pause error: {e}")

    def resume(self):
        """Réactive le jeu natif en reprenant le processus."""
        if self.process and self.process.poll() is None:
            print(f"[Native] Resuming process {self.process.pid}...")
            try:
                p = psutil.Process(self.process.pid)
                p.resume()
                # On remet la fenêtre au premier plan
                self.focus()
            except Exception as e:
                print(f"[Native] Resume error: {e}")

class ArchipelagoBizHawkController(BizHawkController):
    """
    Controller for games via Archipelago and BizHawk (Minish Cap, Oracle of Ages, Zelda 1, etc.).
    Requires the archipelago folder path.
    """
    def __init__(self, archipelago_dir: str, rom_path: str, bizhawk_path: str, settings: dict, slot_name: str, 
                 game_name: str = "Game", client_exe: str = "ArchipelagoBizHawkClient.exe", 
                 lua_script: str = "connector_bizhawk_generic.lua"):
        super().__init__(archipelago_dir, rom_path)
        self.archipelago_dir = archipelago_dir
        self.bizhawk_path = bizhawk_path
        self.settings = settings
        self.slot_name = slot_name
        self.game_name = game_name
        self.client_exe = client_exe
        self.lua_script = lua_script
        self.window_keyword = ["EmuHawk", "BizHawk"]
        if self.slot_name:
            self.window_keyword.append("+" + self.slot_name)
        
        # S'assurer que le chemin de shutdown est bien défini ici aussi
        temp_dir = os.path.join(get_exe_dir(), "temp")
        self.shutdown_flag_path = os.path.join(temp_dir, "bizhawk_shutdown.flag")

    def launch(self):
        print(f"[Archipelago] Lancement direct de {self.game_name} (Client + BizHawk)...")
        ensure_bizhawk_maximized(self.bizhawk_path)
        
        # 1. Chemins des composants
        arch_client_path = ""
        if self.client_exe:
            arch_client_path = os.path.join(self.archipelago_dir, self.client_exe)
            if not os.path.exists(arch_client_path):
                arch_client_path = os.path.join(r"C:\ProgramData\Archipelago", self.client_exe)

        lua_path = os.path.join(self.archipelago_dir, self.lua_script)
        if not os.path.exists(lua_path):
            lua_path = os.path.join(self.archipelago_dir, "data", "lua", self.lua_script)
            
        if not os.path.exists(lua_path):
            lua_path = os.path.join(r"C:\ProgramData\Archipelago", self.lua_script)
            
        if not os.path.exists(lua_path):
            lua_path = os.path.join(r"C:\ProgramData\Archipelago", "data", "lua", self.lua_script)
        
        if self.client_exe and not os.path.exists(arch_client_path):
            print(f"[Archipelago] Erreur: {self.client_exe} non trouvé.")
            return False
            
        if not os.path.exists(lua_path):
            print(f"[Archipelago] Erreur: Script LUA non trouvé ({self.lua_script}).")
            return False

        if not os.path.exists(self.bizhawk_path):
            print(f"[Archipelago] Erreur: BizHawk (EmuHawk.exe) non trouvé à : {self.bizhawk_path}")
            return False

        try:
            env = self.get_clean_env()
            
            # --- LANCEMENT CLIENT ARCHIPELAGO (Si applicable) ---
            if self.client_exe and self.game_name != "Link's Awakening DX":
                host = self.settings.get("host", "archipelago.gg")
                port = self.settings.get("port", "38281")
                password = self.settings.get("password", "") or "None"
                
                # Detection du client (Direct EXE vs Launcher fallback)
                client_path = os.path.join(self.archipelago_dir, self.client_exe)
                if not os.path.exists(client_path):
                    client_path = os.path.join(r"C:\ProgramData\Archipelago", self.client_exe)
                
                # Construction arguments de connexion (Sauf pour LA DX qui utilise le script de connexion "WW style")
                client_args = []
                if self.game_name != "Link's Awakening DX":
                    if host and port and self.slot_name:
                        conn_str = f"{self.slot_name}:{password}@{host}:{port}"
                        client_args.extend(["--connect", conn_str])
                    elif host and port:
                        client_args.extend(["--connect", f"{host}:{port}"])

                try:
                    client_p = None
                    # Determine if we are using the generic launcher
                    is_launcher = "ArchipelagoLauncher.exe" in client_path
                    
                    if os.path.exists(client_path):
                        cmd_base = [client_path]
                        if is_launcher:
                            # Re-calculate friendly name for LADX or others
                            friendly_name = self.client_exe.replace("Archipelago", "").replace("Client.exe", "").strip()
                            if friendly_name == "Launcher": friendly_name = self.game_name
                            if self.game_name == "Link's Awakening DX": friendly_name = "Links Awakening DX Client"
                            if friendly_name == "OoT": friendly_name = "OoT Client"
                            cmd_base.append(friendly_name)
                            
                        print(f"[Archipelago] Lancement Client : {' '.join(cmd_base + client_args)}")
                        client_p = subprocess.Popen(cmd_base + client_args, cwd=os.path.dirname(client_path), env=env, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        # Fallback logic if the specified client doesn't exist
                        launcher_exe = os.path.join(self.archipelago_dir, "ArchipelagoLauncher.exe")
                        if not os.path.exists(launcher_exe):
                            launcher_exe = os.path.join(r"C:\ProgramData\Archipelago", "ArchipelagoLauncher.exe")
                        
                        if os.path.exists(launcher_exe):
                            friendly_name = self.client_exe.replace("Archipelago", "").replace("Client.exe", "").strip()
                            if friendly_name == "Launcher": friendly_name = self.game_name
                            if self.game_name == "Link's Awakening DX": friendly_name = "Links Awakening DX Client"
                            if friendly_name == "OoT": friendly_name = "OoT Client"
                            
                            cmd = [launcher_exe, friendly_name] + client_args
                            print(f"[Archipelago] Fallback Launcher : {' '.join(cmd)}")
                            client_p = subprocess.Popen(cmd, cwd=os.path.dirname(launcher_exe), env=env, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    
                    if client_p:
                        self.extra_processes.append(client_p)
                        
                        # --- MINIMISER LE CLIENT ARCHIPELAGO ---
                        def minimize_client_thread():
                            print(f"[Archipelago] Attente du client pour minimisation...")
                            found_and_minimized = False
                            # On cherche une fenêtre qui contient "Archipelago" et "Client"
                            for _ in range(20): # Attendre jusqu'à 20 secondes
                                if found_and_minimized: break
                                time.sleep(1)
                                if not win32gui: break
                                
                                def enum_handler(hwnd, lparam):
                                    nonlocal found_and_minimized
                                    if win32gui.IsWindowVisible(hwnd):
                                        title = win32gui.GetWindowText(hwnd).lower()
                                        if "archipelago" in title and "client" in title:
                                            # On vérifie si elle n'est pas déjà minimisée
                                            try:
                                                import win32gui_struct, win32con
                                                # Fallback plus simple : IsIconic
                                                if not win32gui.IsIconic(hwnd):
                                                    print(f"[Archipelago] Client trouvé ('{title}'). Minimisation...")
                                                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                                                    found_and_minimized = True
                                                    return False # Stopper l'énumération
                                            except:
                                                # Fallback sans checks avancés
                                                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                                                found_and_minimized = True
                                                return False
                                    return True
                                
                                try:
                                    win32gui.EnumWindows(enum_handler, None)
                                except: 
                                    break
                        
                        threading.Thread(target=minimize_client_thread, daemon=True).start()
                except Exception as e:
                    print(f"[Archipelago] Erreur lors du lancement du client : {e}")
            
            # --- WRAPPER LUA ARCHIPELAGO UNIFIÉ ---
            temp_dir = os.path.join(get_exe_dir(), "temp")
            wrapper_path = os.path.join(temp_dir, "bizhawk_archipelago_wrapper.lua")
            shutdown_flag_path = os.path.join(temp_dir, "bizhawk_shutdown.flag")
            
            # Nettoyage préventif du flag de shutdown
            if os.path.exists(shutdown_flag_path):
                try:
                    os.remove(shutdown_flag_path)
                    print(f"[Archipelago] Stale shutdown flag removed.")
                except: pass

            lua_dir = os.path.dirname(lua_path)

            # Prefixe unique pour ce jeu
            prefix = self.game_name.lower().replace(" ", "").replace("'", "")
            
            wrapper_content = f"""
-- BizHawk Archipelago Wrapper (Dynamic Paths via Environment)
local hub_temp_dir = os.getenv("HUB_TEMP_DIR") or [[{temp_dir}]]
local shutdown_flag = hub_temp_dir .. "/{prefix}_shutdown.flag"

-- 1. Shutdown / Save / Load Listener
local save_flag = hub_temp_dir .. "/{prefix}_save.flag"
local load_flag = hub_temp_dir .. "/{prefix}_load.flag"
local pause_flag = hub_temp_dir .. "/{prefix}_pause.flag"
local resume_flag = hub_temp_dir .. "/{prefix}_resume.flag"

local function check_launcher_signals()
    local fs = io.open(save_flag, "r")
    if fs then
        local slot_str = fs:read("*a")
        fs:close()
        os.remove(save_flag)
        local prefix = os.getenv("HUB_GAME_PREFIX") or "bizhawk"
        local slot = tonumber(slot_str) or 10
        savestate.saveslot(slot)
        print("Launcher: Auto-saved (AP) to slot " .. slot .. " (" .. prefix .. ")")
    end

    local fl = io.open(load_flag, "r")
    if fl then
        local slot_str = fl:read("*a")
        fl:close()
        os.remove(load_flag)
        local prefix = os.getenv("HUB_GAME_PREFIX") or "bizhawk"
        local slot = tonumber(slot_str) or 10
        savestate.loadslot(slot)
        print("Launcher: Auto-loaded (AP) from slot " .. slot .. " (" .. prefix .. ")")
    end

    local f = io.open(shutdown_flag, "r")
    if f then
        f:close()
        os.remove(shutdown_flag)
        client.exit()
    end
    
    local fp = io.open(pause_flag, "r")
    if fp then
        fp:close()
        os.remove(pause_flag)
        client.pause()
    end

    local fr = io.open(resume_flag, "r")
    if fr then
        fr:close()
        os.remove(resume_flag)
        client.unpause()
    end
end

local frame_count = 0
local last_check = os.clock()

local function listener_logic()
    frame_count = frame_count + 1
    if frame_count < 5 then return end
    frame_count = 0
    check_launcher_signals()
    last_check = os.clock()
end

event.onframestart(listener_logic)

-- Robust registration with fallback\n-- Onpaint runs even when paused (on UI redraw/focus)
-- Robust registration with fallback
if event.onpaint then
    event.onpaint(function()
        if client.ispaused() then check_launcher_signals() end
    end)
elseif gui and gui.register then
    gui.register(function()
        if client.ispaused() then check_launcher_signals() end
    end)
end

-- 2. Setup Paths for Archipelago
local arch_lua_dir = os.getenv("ARCH_LUA_DIR") or [[C:\\ProgramData\\Archipelago\\data\\lua]]
package.path = arch_lua_dir .. "\\\\?.lua;" .. package.path
package.cpath = arch_lua_dir .. "\\\\?.dll;" .. arch_lua_dir .. "\\\\x64\\\\?.dll;" .. arch_lua_dir .. "\\\\x86\\\\?.dll;" .. package.cpath

-- Mock io.popen('cd') car socket.lua l'utilise pour trouver ses DLLs
local old_popen = io.popen
io.popen = function(cmd, mode)
    if cmd == "cd" then
        return {{
            read = function() return arch_lua_dir end,
            close = function() return true end
        }}
    end
    if old_popen then return old_popen(cmd, mode) end
    return nil
end

-- 3. Launch Archipelago Script
print("BizHawk Boot Wrapper: Waiting for emulator to be ready (0.5s)...")
for i = 1, 30 do
    check_launcher_signals()
    emu.frameadvance()
end
"""

            if self.game_name == "Ocarina of Time":
                wrapper_content += """
print("Ocarina of Time: Waiting 4s before launching connector...")
-- 4 seconds at 60fps is ~240 frames
for i = 1, 240 do
    check_launcher_signals()
    emu.frameadvance()
end
"""

            wrapper_content += f"""
print("Launching Archipelago Connector...")
-- Re-inject the listener check before dofile to ensure it's still active
dofile([[{lua_path}]])
"""
            
            try:
                with open(wrapper_path, "w", encoding="utf-8") as f:
                    f.write(wrapper_content)
                bizhawk_cmd = [self.bizhawk_path, self.rom_path, f"--lua={wrapper_path}"]
            except:
                bizhawk_cmd = [self.bizhawk_path, self.rom_path, f"--lua={lua_path}"]

            # On recupere l'env pour eviter d'heriter du dummy video de pygame
            env = self.get_clean_env()
            env["HUB_TEMP_DIR"] = temp_dir.replace("\\", "/")
            env["HUB_GAME_PREFIX"] = prefix
            
            print(f"[Archipelago] Lancement BizHawk : {' '.join(bizhawk_cmd)}")
            self.process = subprocess.Popen(
                bizhawk_cmd, 
                cwd=os.path.dirname(self.bizhawk_path),
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            # On laisse le GameManager gérer le post-focus via wait_and_focus
            return True
        except Exception as e:
            print(f"[Archipelago] Erreur lors du lancement : {e}")
            msg = f'Erreur Lancement {self.game_name}: {str(e)}'
            subprocess.Popen(["powershell", "-Command", f'Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show("{msg}")'])
            return False


class URIController(EmulatorController):
    """
    Controller for protocol URIs (like archipelago://).
    Uses the system default handler.
    """
    def __init__(self, uri: str):
        super().__init__("", uri)
        self.uri = uri

    def launch(self):
        print(f"[URI] Launching protocol URI: {self.uri}")
        try:
            # os.startfile is Windows only and perfect for protocol URIs
            os.startfile(self.uri)
            return True
        except Exception as e:
            print(f"[URI] Erreur lors du lancement : {e}")
            return False

    def load_save_state(self, slot: int): pass
    def save_state(self, slot: int): pass
    def pause(self): pass
    def resume(self): pass

class GameManager:
    """
    Manages the active game and switching logic.
    """
    def __init__(self):
        self.games: Dict[str, EmulatorController] = {}
        self.active_game_name: Optional[str] = None
        self.poptracker_path: str = ""
        self.poptracker_packs: Dict[str, str] = {}
        self.poptracker_variants: Dict[str, str] = {}
        self.hub_controller_open_btn: str = "CAPTURE"
        self.archipelago_settings: dict = {}
        self.slot_names: dict = {}
        self.poptracker_broadcast: bool = False
        self.auto_savestate_enabled: bool = True # Global toggle for the feature
        self.multi_game_keep_alive: bool = False # Nouveau mode Multi-Jeu

    def register_game(self, name: str, controller: EmulatorController):
        self.games[name] = controller

    def load_config(self):
        """Charge les chemins depuis config.json et enregistre les jeux."""
        if not os.path.exists(CONFIG_PATH):
            print(f"[GameManager] Config non trouvée à: {CONFIG_PATH}")
            return

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"[GameManager] Config CHARGÉE depuis: {CONFIG_PATH}")
            print(f"[GameManager] Hub Button loaded: {config.get('hub_controller_open_btn')}")
            self.auto_savestate_enabled = config.get("auto_savestate_enabled", True)
        except Exception as e:
            print(f"Error loading config in GameManager: {e}")
            return

        # --- AUTO-DETECTION DES CHEMINS MANQUANTS (Dossier App) ---
        dirty = False
        if "emulators" not in config:
            config["emulators"] = {}
            dirty = True
        
        # Dossier App (local ou parent)
        potential_app_dirs = [
            os.path.join(get_exe_dir(), "..", "App"),
            os.path.join(get_exe_dir(), "App")
        ]
        
        # 1. PopTracker
        pop_path = config["emulators"].get("poptracker")
        if not pop_path or not os.path.exists(pop_path):
            for app_dir in potential_app_dirs:
                if not os.path.exists(app_dir): continue
                # Test Poptracker
                pop_exe = os.path.join(app_dir, "Poptracker", "poptracker.exe")
                if os.path.exists(pop_exe):
                    config["emulators"]["poptracker"] = os.path.normpath(pop_exe)
                    print(f"[GameManager] Auto-fill PopTracker: {pop_exe}")
                    dirty = True
                    break
                # Test Autotrack (nom alternatif)
                auto_exe = os.path.join(app_dir, "autotrack", "autotrack.exe")
                if os.path.exists(auto_exe):
                    config["emulators"]["poptracker"] = os.path.normpath(auto_exe)
                    print(f"[GameManager] Auto-fill Autotrack: {auto_exe}")
                    dirty = True
                    break

        # 2. Broadcast App
        bc_path = config["emulators"].get("broadcast")
        if not bc_path or not os.path.exists(bc_path):
            for app_dir in potential_app_dirs:
                if not os.path.exists(app_dir): continue
                bc_dir = os.path.join(app_dir, "UiBroadCast-Archipelago")
                if os.path.exists(os.path.join(bc_dir, "start_cli.py")):
                    config["emulators"]["broadcast"] = os.path.normpath(bc_dir)
                    print(f"[GameManager] Auto-fill Broadcast: {bc_dir}")
                    dirty = True
                    break
                bc_dir_alt = os.path.join(app_dir, "uibroadcast")
                if os.path.exists(os.path.join(bc_dir_alt, "start_cli.py")):
                    config["emulators"]["broadcast"] = os.path.normpath(bc_dir_alt)
                    print(f"[GameManager] Auto-fill Broadcast: {bc_dir_alt}")
                    dirty = True
                    break

        if dirty:
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                print("[GameManager] Config mise à jour avec les chemins auto-détectés.")
            except Exception as e:
                print(f"[GameManager] Erreur sauvegarde auto-fill: {e}")

        bizhawk_path = resolve_path(config.get("emulators", {}).get("bizhawk", ""))
        dolphin_path = resolve_path(config.get("emulators", {}).get("dolphin", ""))
        archipelago_path = resolve_path(config.get("emulators", {}).get("archipelago", ""))
        self.poptracker_path = resolve_path(config.get("emulators", {}).get("poptracker", ""))
        
        # Load and resolve all Poptracker packs
        raw_packs = config.get("poptracker_packs", {})
        self.poptracker_packs = {k: resolve_path(v) for k, v in raw_packs.items()}
        
        self.poptracker_variants = config.get("poptracker_variants", {})
        
        # Load and resolve all ROM paths
        raw_roms = config.get("roms", {})
        roms_config = {k: resolve_path(v) for k, v in raw_roms.items()}
        
        # Resolve other emulators if present
        self.azahar_path = resolve_path(config.get("emulators", {}).get("azahar", ""))
        self.broadcast_path = resolve_path(config.get("emulators", {}).get("broadcast", ""))

        self.slot_names = config.get("slot_names", {})
        self.archipelago_settings = config.get("archipelago_settings", {})
        self.poptracker_broadcast = config.get("poptracker_broadcast", False)
        self.hub_controller_open_btn = config.get("hub_controller_open_btn", "CAPTURE")
        
        # Preserve running games
        running_games = {name: ctrl for name, ctrl in self.games.items() if ctrl.process and ctrl.process.poll() is None}
        self.games.clear()
        self.games.update(running_games)
        
        # Definitions standards
        defs = [
            ("Ocarina of Time", ArchipelagoBizHawkController, archipelago_path),
            ("Wind Waker", DolphinController, dolphin_path),
            ("A Link to the Past", ArchipelagoBizHawkController, archipelago_path),
            ("Majora's Mask", NativeController, ""),
            ("Twilight Princess", DolphinController, dolphin_path),
            ("Skyward Sword", DolphinController, dolphin_path),
            ("Minish Cap", ArchipelagoBizHawkController, archipelago_path),
            ("Oracle of Ages", ArchipelagoBizHawkController, archipelago_path),
            ("Oracle of Seasons", ArchipelagoBizHawkController, archipelago_path),
            ("Zelda II", ArchipelagoBizHawkController, archipelago_path),
            ("The Legend of Zelda", ArchipelagoBizHawkController, archipelago_path),
            ("Phantom Hourglass", ArchipelagoBizHawkController, archipelago_path),
            ("Spirit Tracks", ArchipelagoBizHawkController, archipelago_path),
            ("A Link Between Worlds", AzaharController, self.azahar_path),
            ("Link's Awakening DX", ArchipelagoBizHawkController, archipelago_path),
            ("OOT (SOH)", NativeController, "")
        ]

        for name, ctrl_class, emu_path in defs:
            # Ne pas écraser si le jeu tourne déjà
            if name in self.games:
                continue

            rom_path = roms_config.get(name, "")
            
            # Cas spécial URI (archipelago://)
            if rom_path and rom_path.startswith("archipelago://"):
                self.register_game(name, URIController(rom_path))
                continue

            # Cas spécial SOH / Native (Majora's Mask, etc.)
            if ctrl_class == NativeController:
                if rom_path and os.path.exists(rom_path):
                    slot = self.slot_names.get(name, "")
                    self.register_game(name, NativeController(rom_path, game_name=name, arch_settings=self.archipelago_settings, slot_name=slot))
                continue

            # Cas spécial Archipelago BizHawk (Minish Cap, Oracle of Ages, Zelda 1, etc.)
            if ctrl_class == ArchipelagoBizHawkController:
                if archipelago_path and rom_path and os.path.exists(archipelago_path) and os.path.exists(rom_path):
                    slot = self.slot_names.get(name, "")
                    if name == "The Legend of Zelda":
                        self.register_game(name, ArchipelagoBizHawkController(
                            archipelago_path, rom_path, bizhawk_path, self.archipelago_settings, slot, 
                            game_name=name, client_exe="ArchipelagoZelda1Client.exe", lua_script="connector_tloz.lua"
                        ))
                    elif name == "A Link to the Past":
                        self.register_game(name, ArchipelagoBizHawkController(
                            archipelago_path, rom_path, bizhawk_path, self.archipelago_settings, slot, 
                            game_name=name, client_exe="ArchipelagoSNIClient.exe", lua_script=r"SNI\lua\Connector.lua"
                        ))
                    elif name == "Link's Awakening DX":
                         self.register_game(name, ArchipelagoBizHawkController(
                            archipelago_path, rom_path, bizhawk_path, self.archipelago_settings, slot, 
                            game_name=name, client_exe="", lua_script="connector_ladx_bizhawk.lua"
                        ))
                    elif name == "Ocarina of Time":
                        self.register_game(name, ArchipelagoBizHawkController(
                            archipelago_path, rom_path, bizhawk_path, self.archipelago_settings, slot, 
                            game_name=name, client_exe="ArchipelagoOoTClient.exe", lua_script="connector_oot.lua"
                        ))
                    else:
                        self.register_game(name, ArchipelagoBizHawkController(archipelago_path, rom_path, bizhawk_path, self.archipelago_settings, slot, game_name=name))
                continue

            # Cas standard Émulateurs
            if emu_path and rom_path and os.path.exists(emu_path) and os.path.exists(rom_path):
                if ctrl_class == DolphinController:
                    # Codes spécifiques utilisateur pour le focus (GZLE99=WW, GZ2E01=TP, SOUE01=SS)
                    game_codes = {
                        "Wind Waker": "GZLE99",
                        "Twilight Princess": "GZ2E01",
                        "Skyward Sword": "SOUE01" 
                    }
                    ctrl = DolphinController(emu_path, rom_path, game_id=game_codes.get(name, ""))
                else:
                    ctrl = ctrl_class(emu_path, rom_path)
                ctrl.game_name = name
                self.register_game(name, ctrl)
            else:
                if rom_path and (not emu_path or not os.path.exists(emu_path) or not os.path.exists(rom_path)):
                    reason = ""
                    if not emu_path: reason = "Emulator path empty"
                    elif not os.path.exists(emu_path): reason = f"Emulator not found: {emu_path}"
                    elif not os.path.exists(rom_path): reason = f"ROM not found: {rom_path}"
                    print(f"[GameManager] Skipping {name}: {reason}")

    def start_game(self, name: str):
        if name not in self.games:
            print(f"Game {name} not found.")
            return False

        # Verification robuste: meme si l'etat interne dit actif, on verifie si le processus tourne
        if self.active_game_name == name:
            game = self.games[name]
            if game.process and game.process.poll() is None:
                print(f"{name} is already running.")
                return True
            else:
                print(f"{name} detecte comme actif mais le processus est mort. Autorise le relancement.")
                self.active_game_name = None

        # Switch Logic: Stop or Pause current game
        if self.active_game_name:
            prev_game = self.games[self.active_game_name]
            
            if self.multi_game_keep_alive:
                print(f"[GameManager] Multi-Game mode: Pausing {self.active_game_name} instead of stopping.")
                
                # --- NOUVEAU: VERIFIER POPTRACKER POUR DOLPHIN/AZAHAR ---
                if isinstance(prev_game, (DolphinController, AzaharController)):
                    # Vérification plus large : PopTracker EXE OU Fenêtre Zelda Hub (Web Tracker SS)
                    found_pop = False
                    if psutil:
                        for proc in psutil.process_iter(['name']):
                            try:
                                if proc.info['name'] and proc.info['name'].lower() in ["poptracker.exe", "autotrack.exe"]:
                                    found_pop = True
                                    break
                            except: pass
                    
                    if not found_pop:
                        # On tente plusieurs fois (retry loop) car les fenêtres web peuvent mettre du temps à apparaître
                        # On utilise des fragments pour être plus robuste aux caractères spéciaux (tirets, etc.)
                        for _ in range(15):
                            if hasattr(prev_game, "find_window"):
                                if prev_game.find_window(["PopTracker", "Zelda", "Hub", "Web", "Tracker"], silent=True):
                                    found_pop = True
                                    break
                            time.sleep(1.0)

                    if not found_pop:
                        print(f"[GameManager] WARNING: Tracker detection failed for {self.active_game_name} before pause!")
                        # On alerte l'utilisateur via une notification système discrète
                        msg = Loc.get("msg_tracker_missing") if 'Loc' in globals() else "Tracker non détecté !"
                        subprocess.Popen(["powershell", "-Command", f"Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('{msg}', 'Hub Alert', 0, 48)"], creationflags=subprocess.CREATE_NO_WINDOW)

                prev_game.pause()
                
                # --- MINIMISER LA CONSOLE LUA (Seulement pour les jeux BizHawk) ---
                if isinstance(prev_game, BizHawkController):
                    game_to_pause = self.active_game_name
                    def minimize_lua_on_pause(game_name):
                        time.sleep(0.5) # Laisser le temps à la pause de se faire
                        ps_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minimize_lua_console.ps1")
                        if os.path.exists(ps_script):
                            print(f"[GameManager] Minimizing Lua Console for {game_name}...")
                            subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    threading.Thread(target=minimize_lua_on_pause, args=(game_to_pause,), daemon=True).start()
                
                # On ne met pas active_game_name à None ici car start_game va s'en charger
            else:
                if self.auto_savestate_enabled:
                    print(f"[GameManager] Auto-saving {self.active_game_name} before switch...")
                    prev_game.save_state(slot=10)
                    time.sleep(2.5) # Délai augmenté pour éviter la corruption (N64)

                print(f"Stopping {self.active_game_name} before launching {name}...")
                prev_game.stop()
                # Sécurité supplémentaire : On attend un peu pour être sûr
                time.sleep(0.5)

        # On ne nettoie plus systématiquement tous les flags lors d'un switch
        # pour éviter de supprimer un signal de pause qui n'a pas encore été lu
        self.cleanup_orphans()

        # Start or Resume new game
        new_game = self.games[name]
        success = False
        
        if new_game.process is None or new_game.process.poll() is not None:
            success = new_game.launch()
            if success:
                # Lancement asynchrone du focus pour ne pas bloquer l'UI
                # Délai étendu à 20s pour BizHawk/Archipelago qui met du temps à changer de titre
                threading.Thread(target=new_game.wait_and_focus, args=(20,), daemon=True).start()
                
                if self.auto_savestate_enabled:
                    def delayed_load():
                        time.sleep(8.0) # Délai augmenté pour stabilité (N64 + AP)
                        new_game.load_save_state(slot=10)
                    threading.Thread(target=delayed_load, daemon=True).start()
        else:
            new_game.resume()
            new_game.focus()
            # On ne recharge pas forcement la save si on fait du hot-swap (car la RAM est intacte)
            # sauf si l'utilisateur le souhaite vraiment, mais generalement resume suffit.
            # On laisse le load_save_state seulement si on n'est pas en keep_alive ou par securite ?
            # User choice: "reprendre de la ou on etait" -> resume suffices.
            # On va quand même le garder si auto-save est on pour garantir la synchro AP si besoin.
            if self.auto_savestate_enabled and not self.multi_game_keep_alive:
                new_game.load_save_state(slot=10) 
            # Re-focus après resume par sécurité
            threading.Thread(target=new_game.wait_and_focus, args=(5,), daemon=True).start()
            success = True

        if success:
            self.active_game_name = name
            print(f"Active game is now: {name}")
            
            # OPTIMIZATION: Boost game priority, Hub priority reduction is handled by the UI
            if new_game.process:
                print(f"[Optimization] Boosting {name} priority to ABOVE_NORMAL...")
                set_process_priority(new_game.process.pid, PROCESS_PRIORITY_ABOVE_NORMAL)
            
            return True
        else:
            print(f"Failure: Could not start or focus {name}.")
            return False

    def cleanup_orphans(self):
        """Recherche et tue les processus orphelins connus."""
        if not psutil: return
        targets = {
            "dolphin.exe", "dolphin-emu.exe", "azahar.exe", "melonds.exe",
            "soh.exe", "zelda64recompiled.exe", "emuhawk.exe", "bizhawk.exe",
            "archipelagobizhawkclient.exe", "archipelagolauncher.exe",
            "archipelagosniclient.exe", "archipelagozelda1client.exe",
            "archipelagothewindwakerclient.exe", "archipelagoootclient.exe"
        }
        print("[Launcher] Nettoyage des processus orphelins...")
        
        # Récupérer la liste des PIDs gérés par le hub pour ne pas les tuer
        active_pids = set()
        for g in self.games.values():
            if g.process and g.process.poll() is None:
                active_pids.add(g.process.pid)
            for ep in g.extra_processes:
                if ep.poll() is None:
                    active_pids.add(ep.pid)

        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['pid'] in active_pids:
                    continue
                if proc.info['name'] and proc.info['name'].lower() in targets:
                    print(f"  -> Killing orphan: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
            except: pass

    def clear_temp_flags(self):
        """Supprime tous les fichiers de contrôle temporaires pour éviter les actions fantômes au boot."""
        temp_dir = os.path.join(get_exe_dir(), "temp")
        if not os.path.exists(temp_dir):
            return
            
        print("[Launcher] Nettoyage des flags temporaires...")
        flags = [
            "bizhawk_save.flag", "bizhawk_load.flag", 
            "bizhawk_pause.flag", "bizhawk_resume.flag",
            "bizhawk_shutdown.flag"
        ]
        for flag in flags:
            path = os.path.join(temp_dir, flag)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"  -> {flag} supprimé.")
                except: pass

    def get_pack_variants(self, pack_path: str) -> List[str]:
        """
        Extract variant IDs from a PopTracker pack's manifest.json.
        Works for both directories and ZIP files.
        """
        if not pack_path or not os.path.exists(pack_path):
            return []
            
        manifest_data = None
        try:
            if os.path.isdir(pack_path):
                manifest_file = os.path.join(pack_path, "manifest.json")
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r', encoding='utf-8-sig') as f:
                        manifest_data = json.load(f)
            elif zipfile.is_zipfile(pack_path):
                with zipfile.ZipFile(pack_path, 'r') as z:
                    # Search for manifest.json at root or in a single subfolder
                    namelist = z.namelist()
                    target = None
                    if "manifest.json" in namelist:
                        target = "manifest.json"
                    else:
                        # Sometimes packed as a folder inside the zip
                        for name in namelist:
                            if name.endswith("/manifest.json") and name.count("/") == 1:
                                target = name
                                break
                    
                    if target:
                        with z.open(target) as f:
                            manifest_data = json.loads(f.read().decode('utf-8-sig'))
            
            if manifest_data and "variants" in manifest_data:
                return list(manifest_data["variants"].keys())
        except Exception as e:
            print(f"[GameManager] Erreur lecture manifest: {e}")
            
        return []

    def is_ap_mode(self, game_name: str, variant_id: str) -> bool:
        """
        Détecte de manière robuste si un mode PopTracker est destiné à Archipelago.
        Vérifie:
        1. Le nom du variant (ID)
        2. Les 'flags' dans manifest.json (flag: "ap")
        3. La présence de scripts 'archipelago.lua' dans le pack
        """
        # 1. Test rapide sur le nom (si present)
        if variant_id:
            v_lower = variant_id.lower()
            if "ap" in v_lower or "archipelago" in v_lower:
                return True
            
        pack_path = self.poptracker_packs.get(game_name, "")
        if not pack_path or not os.path.exists(pack_path):
            return False
            
        try:
            # 2. Inspection du Manifest
            manifest_data = None
            files = []
            
            if os.path.isdir(pack_path):
                manifest_file = os.path.join(pack_path, "manifest.json")
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r', encoding='utf-8-sig') as f:
                        manifest_data = json.load(f)
                # Liste recursive simple pour les dossiers
                for root, _, filenames in os.walk(pack_path):
                    for f in filenames:
                        files.append(os.path.join(root, f).lower())
                        
            elif zipfile.is_zipfile(pack_path):
                with zipfile.ZipFile(pack_path, 'r') as z:
                    files = [n.lower() for n in z.namelist()]
                    target = next((n for n in z.namelist() if n.endswith("manifest.json")), None)
                    if target:
                        with z.open(target) as f:
                            manifest_data = json.loads(f.read().decode('utf-8-sig'))
            
            # 3. Verifier les flags du variant dans le manifest
            if manifest_data and "variants" in manifest_data:
                variant_cfg = manifest_data["variants"].get(variant_id)
                if variant_cfg and "flags" in variant_cfg:
                    if "ap" in variant_cfg["flags"] or "archipelago" in variant_cfg["flags"]:
                        return True
            
            # 4. Verifier la presence de scripts Archipelago
            for f in files:
                if "archipelago.lua" in f or f.endswith("/ap.lua") or f.endswith("\\ap.lua"):
                    return True
                    
        except Exception as e:
            print(f"[GameManager] Erreur detection AP mode: {e}")
            
        return False

# --- Example Usage (CLI) ---
if __name__ == "__main__":
    manager = GameManager()
    
    # Chargement dynamique au lieu du hardcoding
    manager.load_config()
    
    print("--- Zelda Multi-Launcher Core (CLI Test) ---")
    if not manager.games:
        print("Aucun jeu configure dans config.json.")
        sys.exit(0)

    print("Jeux disponibles :")
    for i, name in enumerate(manager.games.keys(), 1):
        print(f"{i}. {name}")
    print(f"{len(manager.games)+1}. Quit")
    
    while True:
        choice = input("Select: ")
        if choice == "1":
            manager.start_game("Ocarina of Time")
        elif choice == "2":
            manager.start_game("Wind Waker")
        elif choice == "3":
            break
