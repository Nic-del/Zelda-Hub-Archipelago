import os
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import time

CONFIG_FILE = "config.json"

# Mapping extensions
GAME_MAPPING = {
    ".aplttp": "A Link to the Past",
    ".apbp": "A Link to the Past",
    ".apz5": "Ocarina of Time",
    ".apoot": "Ocarina of Time",
    ".apmm": "Majora's Mask",
    ".aptloz": "The Legend of Zelda",
    ".apz1": "The Legend of Zelda",
    ".apz2": "Zelda 2: The Adventure of Link",
    ".apalbw": "A Link Between Worlds",
    ".aptmc": "The Minish Cap",
    ".apst": "Spirit Tracks",
    ".apph": "Phantom Hourglass",
    ".aptp": "Twilight Princess",
    ".apladxb": "Link's Awakening DX",
    ".apladx": "Link's Awakening DX",
    ".apooa": "Oracle of Ages",
    ".apoos": "Oracle of Seasons",
}

# Games to explicitly ignore
EXCLUDED_EXTENSIONS = {".apssr", ".apsmw", ".aptww", ".apww"}

DEFAULT_CONFIG = {
    "launcher_path": "",
    "bizhawk_path": "",
    "patch_dir": "",
    "roms": {}
}

# Mapping games to host.yaml keys
HOST_YAML_MAPPING = {
    "A Link to the Past": ["lttp_options", "rom_file"],
    "Ocarina of Time": ["oot_options", "rom_file"],
    "The Legend of Zelda": ["tloz_options", "rom_file"],
    "Zelda 2: The Adventure of Link": ["zelda2_options", "rom_file"],
    "A Link Between Worlds": ["albw_settings", "rom_file"],
    "Link's Awakening DX": ["ladx_options", "rom_file"],
    "Oracle of Ages": ["tloz_ooa_options", "rom_file"],
    "Oracle of Seasons": ["tloz_oos_options", "rom_file"],
    "The Minish Cap": ["tmc_options", "rom_file"],
}

ROM_DIR_NAME = "Rom"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
            except:
                return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def discover_roms(config):
    """Standalone function to discover ROMs and update the config dictionary."""
    import sys
    if getattr(sys, 'frozen', False):
        # Running as EXE
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as Script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    rom_root = os.path.join(base_dir, ROM_DIR_NAME)
    if not os.path.exists(rom_root):
        # Try one level up if we are in Extractor/
        rom_root = os.path.abspath(os.path.join(base_dir, "..", ROM_DIR_NAME))
    
    if not os.path.exists(rom_root):
        # Try two levels up if we are in Extractor/Patcher/
        rom_root = os.path.abspath(os.path.join(base_dir, "..", "..", ROM_DIR_NAME))
    
    if not os.path.exists(rom_root):
        # Try three levels up if we are in Extractor/Patcher/dist/
        rom_root = os.path.abspath(os.path.join(base_dir, "..", "..", "..", ROM_DIR_NAME))
    
    if not os.path.exists(rom_root):
        return config

    search_map = {
        "A Link to the Past": ["Link to the Past", "Kamigami"],
        "Ocarina of Time": ["Ocarina of Time"],
        "The Legend of Zelda": ["Legend of Zelda (U)", "The Legend of Zelda"],
        "Zelda 2: The Adventure of Link": ["Zelda II", "Adventure of Link"],
        "A Link Between Worlds": ["Link Between Worlds"],
        "The Minish Cap": ["Minish Cap"],
        "Twilight Princess": ["Twilight Princess"],
        "Link's Awakening DX": ["Link's Awakening DX"],
        "Oracle of Ages": ["Oracle of Ages"],
        "Oracle of Seasons": ["Oracle of Seasons"],
    }

    roms = config.get("roms", {})
    try:
        folders = os.listdir(rom_root)
        for game_name, terms in search_map.items():
            # Skip if already has a valid path (optional, but requested to always fill)
            # if roms.get(game_name): continue
            
            for folder in folders:
                folder_path = os.path.join(rom_root, folder)
                if not os.path.isdir(folder_path): continue
                
                if any(term.lower() in folder.lower() for term in terms):
                    for file in os.listdir(folder_path):
                        if os.path.splitext(file)[1].lower() in [".sfc", ".z64", ".n64", ".nes", ".gba", ".gbc", ".gb", ".iso", ".wbfs", ".cci", ".3ds"]:
                            roms[game_name] = os.path.abspath(os.path.join(folder_path, file)).replace('\\', '/')
                            break
                    if roms.get(game_name): break
    except:
        pass
    
    config["roms"] = roms
    return config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

class PatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Archipelago Zelda Patcher (Dynamic)")
        self.config = load_config()
        
        # 1. Initialize variables first
        self.launcher_var = tk.StringVar(value=self.config.get("launcher_path", ""))
        self.bizhawk_var = tk.StringVar(value=self.config.get("bizhawk_path", ""))
        self.patch_dir_var = tk.StringVar(value=self.config.get("patch_dir", ""))
        self.rom_vars = {}
        
        # 2. Initial logic for patch_dir if empty
        if not self.patch_dir_var.get():
            self.auto_detect_patch_dir()

        # 3. Scan for games
        self.detected_games = self.scan_for_games()
        
        # 4. Setup UI (Config is already populated by discover_roms before init)
        self.setup_ui()

    def auto_detect_patch_dir(self):
        """Attempts to find the Archipelago/output folder based on launcher path."""
        launcher = self.launcher_var.get()
        if launcher and os.path.exists(launcher):
            output_dir = os.path.join(os.path.dirname(launcher), "output")
            if os.path.exists(output_dir):
                self.patch_dir_var.set(output_dir)

    def get_patch_dir(self):
        """Returns the directory where patch files are stored."""
        path = self.patch_dir_var.get()
        if path and os.path.exists(path):
            return path
        return "."

    def scan_for_games(self):
        """Scans the patch directory for files starting with .ap and maps them to games."""
        detected = set()
        patch_dir = self.get_patch_dir()
        
        if not os.path.exists(patch_dir):
            return []

        try:
            for f in os.listdir(patch_dir):
                ext = os.path.splitext(f)[1].lower()
                if ext.startswith(".ap") and ext not in EXCLUDED_EXTENSIONS:
                    if ext in GAME_MAPPING:
                        detected.add(GAME_MAPPING[ext])
                    else:
                        game_name = f"Inconnu ({ext})"
                        detected.add(game_name)
        except:
            pass
            
        return sorted(list(detected))

    def setup_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        config_frame = tk.LabelFrame(self.root, text=" Configuration ", padx=15, pady=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Launcher Path
        tk.Label(config_frame, text="ArchipelagoLauncher.exe :").grid(row=0, column=0, sticky="w")
        tk.Entry(config_frame, textvariable=self.launcher_var, width=50).grid(row=0, column=1, padx=5)
        tk.Button(config_frame, text="Parcourir", command=lambda: self.browse_executable()).grid(row=0, column=2)

        # BizHawk Path
        tk.Label(config_frame, text="EmuHawk.exe (BizHawk) :").grid(row=1, column=0, sticky="w")
        tk.Entry(config_frame, textvariable=self.bizhawk_var, width=50).grid(row=1, column=1, padx=5)
        tk.Button(config_frame, text="Parcourir", command=lambda: self.browse_bizhawk()).grid(row=1, column=2)

        # Patch Directory (Manual selection)
        tk.Label(config_frame, text="Dossier des patchs (.ap*) :").grid(row=2, column=0, sticky="w", pady=(5,0))
        tk.Entry(config_frame, textvariable=self.patch_dir_var, width=50).grid(row=2, column=1, padx=5, pady=(5,0))
        tk.Button(config_frame, text="Choisir Dossier", command=lambda: self.browse_patch_dir()).grid(row=2, column=2, pady=(5,0))

        # ROMs Section
        tk.Label(config_frame, text="Jeux détectés (Configurez vos ROMs) :", font=("Arial", 9, "italic")).grid(row=3, column=0, columnspan=3, pady=(15, 5), sticky="w")

        # Unified list of games to show: either detected or from our search map to ensure all are there
        all_games = sorted(list(set(self.detected_games) | {
            "A Link to the Past", "Ocarina of Time", "The Legend of Zelda",
            "Zelda 2: The Adventure of Link", "A Link Between Worlds",
            "Link's Awakening DX", "Oracle of Ages", "Oracle of Seasons",
            "The Minish Cap", "Twilight Princess"
        }))
        
        row = 4
        for rom_name in all_games:
            tk.Label(config_frame, text=f"{rom_name} :").grid(row=row, column=0, sticky="w")
            stored_path = self.config.get("roms", {}).get(rom_name, "")
            var = tk.StringVar(value=stored_path)
            self.rom_vars[rom_name] = var
            tk.Entry(config_frame, textvariable=var, width=50).grid(row=row, column=1, padx=5, pady=2)
            tk.Button(config_frame, text="Parcourir", command=lambda r=rom_name, v=var: self.browse_rom(r, v)).grid(row=row, column=2)
            row += 1

        # Action Buttons
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        tk.Button(btn_frame, text="Actualiser", command=self.refresh, padx=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Sauvegarder", command=self.save_and_notify, bg="#4CAF50", fg="white", padx=10).pack(side="left", padx=10)
        
        self.test_btn = tk.Button(btn_frame, text="Tester 1 Fichier", command=self.test_one_file, bg="#FF9800", fg="white", padx=10)
        self.test_btn.pack(side="left", padx=10)

        self.run_btn = tk.Button(btn_frame, text="Lancer l'Extraction Totale", command=self.run_patching, bg="#2196F3", fg="white", padx=10, font=("Arial", 10, "bold"))
        self.run_btn.pack(side="left", padx=10)

        # Log Area
        log_label = tk.Label(self.root, text="Journal d'activité :", font=("Arial", 9, "bold"))
        log_label.pack(anchor="w", padx=10)
        
        self.log_text = tk.Text(self.root, height=13, width=85, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def log(self, message, color="black"):
        self.log_text.config(state="normal")
        self.log_text.tag_config("red", foreground="red")
        self.log_text.tag_config("green", foreground="green")
        self.log_text.tag_config("blue", foreground="blue")
        self.log_text.tag_config("orange", foreground="orange")
        self.log_text.insert("end", f"{message}\n", color)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    def auto_discover_roms(self):
        """Redundant but keeping for manual refresh logic if needed."""
        self.config = discover_roms(self.config)
        for game_name, path in self.config.get("roms", {}).items():
            if game_name in self.rom_vars:
                self.rom_vars[game_name].set(path)
        self.log("Re-scan des ROMs effectué.", "green")

    def sync_host_yaml(self):
        # Ensure we have the latest paths from the UI
        self.save_internal()
        
        launcher = self.launcher_var.get()
        if not launcher or not os.path.exists(launcher): return
        archipelago_dir = os.path.dirname(launcher)
        host_yaml_path = os.path.join(archipelago_dir, "host.yaml")
        if not os.path.exists(host_yaml_path): return

        try:
            with open(host_yaml_path, "r", encoding="utf-8") as f: lines = f.readlines()
            modified = False
            for game_name, path in self.config.get("roms", {}).items():
                if game_name in HOST_YAML_MAPPING and path:
                    # Only sync if game is in detected_games
                    if game_name not in self.detected_games:
                        continue
                        
                    section, key = HOST_YAML_MAPPING[game_name]
                    in_section = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith(f"{section}:"): in_section = True; continue
                        if in_section:
                            if ":" in line and not line.startswith(" "): 
                                if not line.startswith("  "):
                                    in_section = False
                                    continue
                            
                            if line.strip().startswith(f"{key}:"):
                                indent = line[:line.find(key)]
                                clean_path = path.replace('\\', '/')
                                lines[i] = f"{indent}{key}: \"{clean_path}\"\n"
                                modified = True; break
            
            # Sync BizHawk Path
            bizhawk_path = self.bizhawk_var.get()
            if bizhawk_path:
                in_bizhawk_section = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("bizhawkclient_options:"): 
                        in_bizhawk_section = True
                        continue
                    if in_bizhawk_section:
                        if ":" in line and not line.startswith(" "):
                            if not line.startswith("  "):
                                in_bizhawk_section = False
                                continue
                        if line.strip().startswith("emuhawk_path:"):
                            indent = line[:line.find("emuhawk_path")]
                            clean_bizhawk = bizhawk_path.replace('\\', '/')
                            lines[i] = f"{indent}emuhawk_path: \"{clean_bizhawk}\"\n"
                            modified = True
                            break

            if modified:
                with open(host_yaml_path, "w", encoding="utf-8") as f: f.writelines(lines)
                self.log("Synchronisation de host.yaml réussie.", "green")
        except Exception as e: self.log(f"Sync error: {e}", "red")

    def cleanup_processes(self):
        # Traditional kill for known emulators
        targets = ["EmuHawk.exe", "retroarch.exe", "dolphin.exe", "sni.exe", "snes9x.exe", "fceux.exe", "project64.exe"]
        for target in targets:
            try: subprocess.run(["taskkill", "/F", "/T", "/IM", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            except: pass
        
        # Radical kill via PowerShell for EVERYTHING containing "Archipelago"
        # This catches: ArchipelagoLauncher, ArchipelagoDXClient, ArchipelagoBizHawkClient, etc.
        try:
            ps_cmd = 'Get-Process | Where-Object { $_.Name -like "*Archipelago*" } | Stop-Process -Force'
            subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

    def refresh(self):
        self.auto_discover_roms()
        self.detected_games = self.scan_for_games()
        self.setup_ui()
        self.log("Liste des jeux actualisée.")

    def browse_executable(self):
        filename = filedialog.askopenfilename(title="Choisir ArchipelagoLauncher.exe", filetypes=[("Executable", "*.exe")])
        if filename: 
            self.launcher_var.set(filename)
            if not self.patch_dir_var.get():
                self.auto_detect_patch_dir()
                self.refresh()

    def browse_bizhawk(self):
        filename = filedialog.askopenfilename(title="Choisir EmuHawk.exe", filetypes=[("Executable", "*.exe")])
        if filename: self.bizhawk_var.set(filename)

    def browse_patch_dir(self):
        dirname = filedialog.askdirectory(title="Choisir le dossier contenant les patchs (.ap*)")
        if dirname:
            self.patch_dir_var.set(dirname)
            self.refresh()

    def browse_rom(self, rom_name, var):
        filename = filedialog.askopenfilename(title=f"Choisir la ROM pour {rom_name}")
        if filename: var.set(filename)

    def save_and_notify(self):
        self.save_internal()
        self.log("Configuration sauvegardée.", "green")

    def save_internal(self):
        self.config["launcher_path"] = self.launcher_var.get()
        self.config["bizhawk_path"] = self.bizhawk_var.get()
        self.config["patch_dir"] = self.patch_dir_var.get()
        if "roms" not in self.config: self.config["roms"] = {}
        for rom_name, var in self.rom_vars.items(): self.config["roms"][rom_name] = var.get()
        save_config(self.config)

    def test_one_file(self):
        self.save_internal()
        self.sync_host_yaml()
        patch_file = filedialog.askopenfilename(title="Tester un patch", initialdir=self.get_patch_dir(), filetypes=[("Archipelago Patch", "*.ap*")])
        if not patch_file: return
        self.log(f"TEST: {os.path.basename(patch_file)}...", "blue")
        try:
            subprocess.Popen([self.launcher_var.get(), os.path.abspath(patch_file)])
            self.root.after(15000, lambda: (self.cleanup_processes(), self.log("Nettoyage effectué.", "green")))
        except Exception as e: self.log(f"Error: {e}", "red")

    def run_patching(self):
        self.save_internal()
        self.sync_host_yaml()
        launcher = self.launcher_var.get()
        if not launcher or not os.path.exists(launcher): return
        patch_dir = self.get_patch_dir()
        if not os.path.exists(patch_dir): self.log("Dossier patch invalide.", "red"); return
        
        patch_files = [f for f in os.listdir(patch_dir) if os.path.splitext(f)[1].lower().startswith(".ap") and os.path.splitext(f)[1].lower() not in EXCLUDED_EXTENSIONS]
        if not patch_files: self.log("Aucun patch trouvé.", "red"); return
        if not messagebox.askyesno("Confirmation", f"Lancer {len(patch_files)} patch(s) ?"): return
        self.run_btn.config(state="disabled")
        self.log(f"Lancement de {len(patch_files)} patch(s)...", "blue")
        success = 0
        for patch in patch_files:
            try:
                subprocess.Popen([launcher, os.path.abspath(os.path.join(patch_dir, patch))])
                success += 1
            except: pass
        self.log(f"{success} lancés. Nettoyage final dans 30s...", "orange")
        self.root.after(30000, self.final_cleanup_after_all)

    def final_cleanup_after_all(self):
        self.cleanup_processes()
        self.log("Terminé. Vérifiez les ROMs générées.", "green")
        self.run_btn.config(state="normal")
        messagebox.showinfo("Terminé", "Extraction et nettoyage terminés.")

if __name__ == "__main__":
    root = tk.Tk()
    # Load and Discover BEFORE creating the app object
    config = load_config()
    config = discover_roms(config)
    save_config(config) # Optional: save the discovered paths
    
    app = PatcherApp(root)
    root.mainloop()
