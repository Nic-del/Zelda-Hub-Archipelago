import os
import sys
import threading
import traceback
import shutil
import json
import warnings

# Bypassing Archipelago requirements update check and updates
os.environ["SKIP_REQUIREMENTS_UPDATE"] = "1"

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patcher_config.json")
DEFAULT_PATH = r"C:\Users\Linksweld\Downloads\Archipelago-main\Archipelago-main"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"archipelago_path": DEFAULT_PATH}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
    except Exception:
        pass

config = load_config()
archipelago_path = config.get("archipelago_path", DEFAULT_PATH)

archipelago_loaded = False
worlds = None
Patch = None
AutoPatchRegister = None

def try_load_archipelago(path):
    global archipelago_loaded, worlds, Patch, AutoPatchRegister
    if not path or not os.path.isdir(path):
        return False
    
    if path not in sys.path:
        sys.path.insert(0, path)
        
    try:
        import Utils
        warnings.simplefilter("ignore", DeprecationWarning)
        Utils.user_path.cached_path = r"C:\ProgramData\Archipelago"
        Utils.local_path.cached_path = r"C:\ProgramData\Archipelago"
        Utils.deprecate = lambda message, add_stacklevels=0: None
        Utils.get_options = Utils.get_settings
        
        import worlds
        from worlds.Files import AutoPatchRegister
        import Patch
        archipelago_loaded = True
        return True
    except Exception as e:
        print(f"Error loading Archipelago from {path}: {e}")
        if path in sys.path:
            try:
                sys.path.remove(path)
            except ValueError:
                pass
        return False

# Initialize loading
bundled_error = None
if getattr(sys, 'frozen', False):
    try:
        import Utils
        warnings.simplefilter("ignore", DeprecationWarning)
        Utils.user_path.cached_path = r"C:\ProgramData\Archipelago"
        Utils.local_path.cached_path = r"C:\ProgramData\Archipelago"
        Utils.deprecate = lambda message, add_stacklevels=0: None
        Utils.get_options = Utils.get_settings
        import worlds
        from worlds.Files import AutoPatchRegister
        import Patch
        archipelago_loaded = True
    except Exception as e:
        bundled_error = traceback.format_exc()
        print(f"Error loading bundled Archipelago: {e}")
else:
    if not try_load_archipelago(archipelago_path):
        try_load_archipelago(DEFAULT_PATH)

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set GUI theme and style
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green") # Zelda Green theme

class ZeldaHubPatcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Zelda Hub Patcher - Standing Alone")
        self.geometry("850x800")
        self.minsize(700, 700)
        
        self.selected_patch_path = None
        self.selected_batch_dir = None
        self.selected_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patched_roms")
        os.makedirs(self.selected_output_dir, exist_ok=True)
        
        self.supported_extensions = {".apz5", ".aplttp", ".apladx", ".apooa", ".apoos", ".aptloz", ".apz2", ".aptmc", ".apalbw", ".apalttpr", ".apladxb"}
        
        self.create_widgets()
        self.log("Zelda Hub Patcher initialized.")
        if archipelago_loaded and worlds:
            self.log(f"Custom worlds directory loaded: {worlds.user_folder}")
            if getattr(worlds, "failed_world_loads", None):
                self.log("WARNING: Failed to load some custom worlds:")
                for game, reason in worlds.failed_world_loads.items():
                    self.log(f"  - {game}: {reason}")
        else:
            self.log("WARNING: Archipelago not loaded. Please select your Archipelago folder below.")
            if bundled_error:
                self.log(f"Bundled load error:\n{bundled_error}")
        self.log(f"Available patch formats: " + ", ".join(self.supported_extensions))
        
    def create_widgets(self):
        # Configure Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Row index for Logs frame is now 4
        
        # Header Frame
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e293b", height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="ZELDA HUB PATCHER", 
            font=ctk.CTkFont(family="Outfit", size=24, weight="bold"),
            text_color="#10b981"
        )
        title_label.grid(row=0, column=0, pady=15, padx=20, sticky="w")
        
        # Archipelago Path Settings Frame
        self.arch_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=12)
        self.arch_frame.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.arch_frame.grid_columnconfigure(1, weight=1)
        
        arch_label = ctk.CTkLabel(
            self.arch_frame, 
            text="Archipelago Folder:", 
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#e2e8f0"
        )
        arch_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.arch_entry = ctk.CTkEntry(
            self.arch_frame, 
            fg_color="#1e293b",
            border_color="#334155",
            text_color="#f8fafc"
        )
        self.arch_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        
        self.browse_arch_btn = ctk.CTkButton(
            self.arch_frame, 
            text="Browse", 
            command=self.browse_archipelago_folder,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#0f172a",
            font=ctk.CTkFont(family="Inter", weight="bold")
        )
        self.browse_arch_btn.grid(row=0, column=2, padx=15, pady=15)
        
        self.arch_status_badge = ctk.CTkLabel(
            self.arch_frame, 
            text="Checking...", 
            fg_color="#1e293b",
            text_color="#94a3b8",
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold")
        )
        self.arch_status_badge.grid(row=1, column=0, columnspan=3, padx=15, pady=(5, 15), sticky="w")
        
        if getattr(sys, 'frozen', False):
            self.arch_entry.insert(0, "Built-in / Intégré (Standalone EXE)")
            self.arch_entry.configure(state="disabled")
            self.browse_arch_btn.configure(state="disabled")
            self.arch_status_badge.configure(
                text="Archipelago Loaded (Bundled)",
                fg_color="#064e3b",
                text_color="#34d399"
            )
        else:
            self.arch_entry.insert(0, archipelago_path)
            self.update_archipelago_status()
        
        # Setup Card Frame (Tabbed view for Single/Batch)
        self.setup_tabview = ctk.CTkTabview(self, fg_color="#0f172a", corner_radius=12)
        self.setup_tabview.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        tab_single = self.setup_tabview.add("Single Patch")
        tab_batch = self.setup_tabview.add("Batch Folder Patch")
        
        # Configure Tab 1: Single Patch
        tab_single.grid_columnconfigure(1, weight=1)
        patch_label = ctk.CTkLabel(
            tab_single, 
            text="Patch File:", 
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#e2e8f0"
        )
        patch_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.patch_entry = ctk.CTkEntry(
            tab_single, 
            placeholder_text="Select a patch file...",
            fg_color="#1e293b",
            border_color="#334155",
            text_color="#f8fafc"
        )
        self.patch_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        
        browse_patch_btn = ctk.CTkButton(
            tab_single, 
            text="Browse File", 
            command=self.browse_patch_file,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#0f172a",
            font=ctk.CTkFont(family="Inter", weight="bold")
        )
        browse_patch_btn.grid(row=0, column=2, padx=15, pady=15)
        
        self.info_badge = ctk.CTkLabel(
            tab_single, 
            text="No patch file loaded", 
            fg_color="#1e293b",
            text_color="#94a3b8",
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold")
        )
        self.info_badge.grid(row=1, column=0, columnspan=3, padx=15, pady=(5, 15), sticky="w")
        
        # Configure Tab 2: Batch Folder Patch
        tab_batch.grid_columnconfigure(1, weight=1)
        folder_label = ctk.CTkLabel(
            tab_batch, 
            text="Patch Folder:", 
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#e2e8f0"
        )
        folder_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.folder_entry = ctk.CTkEntry(
            tab_batch, 
            placeholder_text="Select a folder containing patches...",
            fg_color="#1e293b",
            border_color="#334155",
            text_color="#f8fafc"
        )
        self.folder_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        
        browse_folder_btn = ctk.CTkButton(
            tab_batch, 
            text="Browse Folder", 
            command=self.browse_batch_folder,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#0f172a",
            font=ctk.CTkFont(family="Inter", weight="bold")
        )
        browse_folder_btn.grid(row=0, column=2, padx=15, pady=15)
        
        self.batch_badge = ctk.CTkLabel(
            tab_batch, 
            text="No folder loaded", 
            fg_color="#1e293b",
            text_color="#94a3b8",
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold")
        )
        self.batch_badge.grid(row=1, column=0, columnspan=3, padx=15, pady=(5, 15), sticky="w")
        
        # Shared Output Settings Frame (Below Tabs)
        shared_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=12)
        shared_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        shared_frame.grid_columnconfigure(1, weight=1)
        
        out_label = ctk.CTkLabel(
            shared_frame, 
            text="Output Folder:", 
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#e2e8f0"
        )
        out_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        self.out_entry = ctk.CTkEntry(
            shared_frame, 
            placeholder_text="Choose destination folder...",
            fg_color="#1e293b",
            border_color="#334155",
            text_color="#f8fafc"
        )
        self.out_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.out_entry.insert(0, self.selected_output_dir)
        
        browse_out_btn = ctk.CTkButton(
            shared_frame, 
            text="Browse", 
            command=self.browse_output_dir,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#0f172a",
            font=ctk.CTkFont(family="Inter", weight="bold")
        )
        browse_out_btn.grid(row=0, column=2, padx=15, pady=15)
        
        # Logs Window Frame
        logs_frame = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=12)
        logs_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="nsew")
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(1, weight=1)
        
        logs_label = ctk.CTkLabel(
            logs_frame, 
            text="Activity Logs", 
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#e2e8f0"
        )
        logs_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.log_textbox = ctk.CTkTextbox(
            logs_frame, 
            fg_color="#020617", 
            text_color="#38bdf8", 
            border_color="#1e293b",
            border_width=1,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Actions Row Frame (Bottom)
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.patch_btn = ctk.CTkButton(
            actions_frame, 
            text="RUN PATCH PROCESS", 
            command=self.start_patch_thread,
            fg_color="#059669",
            hover_color="#047857",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Outfit", size=15, weight="bold"),
            height=40,
            state="disabled"
        )
        self.patch_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.open_folder_btn = ctk.CTkButton(
            actions_frame, 
            text="OPEN OUTPUT FOLDER", 
            command=self.open_output_folder,
            fg_color="#475569",
            hover_color="#334155",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Outfit", size=15, weight="bold"),
            height=40,
            state="disabled"
        )
        self.open_folder_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Event bindings
        self.setup_tabview.configure(command=self.tab_changed)

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        
    def update_archipelago_status(self):
        global archipelago_loaded
        if archipelago_loaded:
            self.arch_status_badge.configure(
                text="Archipelago Loaded successfully",
                fg_color="#064e3b",
                text_color="#34d399"
            )
        else:
            self.arch_status_badge.configure(
                text="Archipelago NOT FOUND. Select the source folder to patch.",
                fg_color="#7f1d1d",
                text_color="#f87171"
            )
            
    def browse_archipelago_folder(self):
        directory = filedialog.askdirectory(title="Select Archipelago Main Folder")
        if directory:
            self.arch_entry.delete(0, "end")
            self.arch_entry.insert(0, directory)
            self.log(f"Attempting to load Archipelago from: {directory}")
            if try_load_archipelago(directory):
                self.log("Archipelago loaded successfully!")
                global config
                config["archipelago_path"] = directory
                save_config(config)
                self.update_archipelago_status()
                self.tab_changed()
            else:
                self.log("ERROR: Could not load Archipelago from selected directory. Check console/logs.")
                self.update_archipelago_status()

    def tab_changed(self):
        if not archipelago_loaded:
            self.patch_btn.configure(state="disabled")
            return
        active_tab = self.setup_tabview.get()
        if active_tab == "Single Patch":
            if self.selected_patch_path:
                self.patch_btn.configure(state="normal")
            else:
                self.patch_btn.configure(state="disabled")
        else:
            if self.selected_batch_dir:
                self.patch_btn.configure(state="normal")
            else:
                self.patch_btn.configure(state="disabled")
        
    def browse_patch_file(self):
        filetypes = [
            ("All Supported Patches", "*.apz5;*.aplttp;*.apladx;*.apooa;*.apoos;*.aptloz;*.apz2;*.aptmc;*.apalbw;*.apalttpr;*.apladxb"),
            ("Ocarina of Time (.apz5)", "*.apz5"),
            ("A Link to the Past (.aplttp)", "*.aplttp"),
            ("A Link to the Past OWR (.apalttpr)", "*.apalttpr"),
            ("Link's Awakening DX (.apladx)", "*.apladx"),
            ("Link's Awakening DX Beta (.apladxb)", "*.apladxb"),
            ("Oracle of Ages (.apooa)", "*.apooa"),
            ("Oracle of Seasons (.apoos)", "*.apoos"),
            ("Zelda 1 (.aptloz)", "*.aptloz"),
            ("Zelda 2 (.apz2)", "*.apz2"),
            ("Minish Cap (.aptmc)", "*.aptmc"),
            ("A Link Between Worlds (.apalbw)", "*.apalbw"),
            ("All Files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Archipelago Patch File", filetypes=filetypes)
        if filename:
            self.selected_patch_path = filename
            self.patch_entry.delete(0, "end")
            self.patch_entry.insert(0, filename)
            
            ext = os.path.splitext(filename)[1].lower()
            game_names = {
                ".aplttp": "A Link to the Past",
                ".apalttpr": "A Link to the Past OWR",
                ".apladx": "Link's Awakening DX",
                ".apladxb": "Link's Awakening DX Beta",
                ".apz5": "Ocarina of Time",
                ".apooa": "Oracle of Ages",
                ".apoos": "Oracle of Seasons",
                ".aptloz": "The Legend of Zelda 1",
                ".apz2": "Zelda II: The Adventure of Link",
                ".aptmc": "The Minish Cap",
                ".apalbw": "A Link Between Worlds"
            }
            
            game_name = game_names.get(ext, "Unknown Game")
            self.info_badge.configure(
                text=f"Detected: {game_name} ({ext})",
                fg_color="#064e3b",
                text_color="#34d399"
            )
            self.patch_btn.configure(state="normal")
            self.log(f"Loaded patch file: {filename}")
            
    def browse_batch_folder(self):
        directory = filedialog.askdirectory(title="Select Patch Directory")
        if directory:
            self.selected_batch_dir = directory
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, directory)
            
            # Count matching patches
            patches = [f for f in os.listdir(directory) if os.path.splitext(f)[1].lower() in self.supported_extensions]
            count = len(patches)
            
            self.batch_badge.configure(
                text=f"Found {count} supported patches inside folder",
                fg_color="#064e3b" if count > 0 else "#7f1d1d",
                text_color="#34d399" if count > 0 else "#f87171"
            )
            if count > 0:
                self.patch_btn.configure(state="normal")
            else:
                self.patch_btn.configure(state="disabled")
            self.log(f"Loaded batch patch folder: {directory} ({count} patches found)")
            
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Folder")
        if directory:
            self.selected_output_dir = directory
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, directory)
            self.log(f"Output folder changed to: {directory}")

    def open_output_folder(self):
        if os.path.exists(self.selected_output_dir):
            os.startfile(self.selected_output_dir)

    def start_patch_thread(self):
        self.patch_btn.configure(state="disabled")
        self.open_folder_btn.configure(state="disabled")
        threading.Thread(target=self.patch_process_dispatcher, daemon=True).start()
        
    def patch_process_dispatcher(self):
        active_tab = self.setup_tabview.get()
        output_dir = self.out_entry.get().strip()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        if active_tab == "Single Patch":
            patch_path = self.patch_entry.get().strip()
            if not patch_path or not os.path.exists(patch_path):
                self.log("ERROR: Invalid patch file path.")
                messagebox.showerror("Error", "Please specify a valid patch file path.")
                self.patch_btn.configure(state="normal")
                return
            self.patch_single_file(patch_path, output_dir)
        else:
            folder_path = self.folder_entry.get().strip()
            if not folder_path or not os.path.exists(folder_path):
                self.log("ERROR: Invalid patch folder path.")
                messagebox.showerror("Error", "Please specify a valid patch folder path.")
                self.patch_btn.configure(state="normal")
                return
            self.patch_folder_batch(folder_path, output_dir)
            
        self.patch_btn.configure(state="normal")
        self.open_folder_btn.configure(state="normal")

    def patch_single_file(self, patch_path, output_dir):
        try:
            ext = os.path.splitext(patch_path)[1].lower()
            
            if ext == ".apz5":
                self.log("Loading Ocarina of Time patching libraries...")
                from worlds.oot.Rom import Rom, compress_rom_file
                from worlds.oot.N64Patch import apply_patch_file
                from worlds.oot import OOTWorld
                from worlds.oot.Utils import data_path
                
                rom_file_name = OOTWorld.settings.rom_file
                if not os.path.exists(rom_file_name):
                    default_oot_path = r"C:\ProgramData\Archipelago\The Legend of Zelda - Ocarina of Time.z64"
                    if os.path.exists(default_oot_path):
                        rom_file_name = default_oot_path
                    else:
                        raise FileNotFoundError(f"Base OoT ROM not found. Please set it in Archipelago options or copy to: {default_oot_path}")
                
                self.log(f"Using base ROM: {rom_file_name}")
                base_name = os.path.splitext(os.path.basename(patch_path))[0]
                decomp_path = os.path.join(output_dir, base_name + '-decomp.z64')
                comp_path = os.path.join(output_dir, base_name + '.z64')
                
                self.log("Applying OoT ZPF patch...")
                rom = Rom(rom_file_name)
                sub_file = None
                import zipfile
                if zipfile.is_zipfile(patch_path):
                    for name in zipfile.ZipFile(patch_path).namelist():
                        if name.endswith('.zpf'):
                            sub_file = name
                            break
                            
                apply_patch_file(rom, patch_path, sub_file=sub_file)
                
                self.log("Saving decompressed ROM...")
                rom.write_to_file(decomp_path)
                
                self.log("Compressing ROM (this can take a minute)...")
                orig_cwd = os.getcwd()
                compress_dir = data_path("Compress")
                os.chdir(compress_dir)
                try:
                    compress_rom_file(decomp_path, comp_path)
                finally:
                    os.chdir(orig_cwd)
                    
                if os.path.exists(decomp_path):
                    os.remove(decomp_path)
                    
                self.log(f"Success! Patched ROM written to: {comp_path}")
                messagebox.showinfo("Patch Complete", f"Successfully patched Ocarina of Time ROM!\nSaved to: {comp_path}")
                
            else:
                self.log("Loading Archipelago Patch modules...")
                import Patch
                
                self.log("Executing standard patch method...")
                meta, romfile = Patch.create_rom_file(patch_path)
                self.log(f"Patch metadata: {meta}")
                
                # Check target file location and move if necessary
                target_file = os.path.join(output_dir, os.path.basename(romfile))
                if os.path.abspath(romfile) != os.path.abspath(target_file):
                    if os.path.exists(target_file):
                        os.remove(target_file)
                    shutil.move(romfile, target_file)
                    self.log(f"Success! Patched file moved to: {target_file}")
                    messagebox.showinfo("Patch Complete", f"Success!\nPatched file written to: {target_file}")
                else:
                    self.log(f"Success! Patched file written to: {romfile}")
                    messagebox.showinfo("Patch Complete", f"Success!\nPatched file written to: {romfile}")
            
        except Exception as e:
            self.log(f"ERROR patching {os.path.basename(patch_path)}: {str(e)}")
            self.log(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to patch file:\n{str(e)}")

    def patch_folder_batch(self, folder_path, output_dir):
        # Scan folder for supported extensions
        patches = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.splitext(f)[1].lower() in self.supported_extensions]
        total = len(patches)
        
        self.log(f"Starting batch process for folder: {folder_path}")
        self.log(f"Total patch files to execute: {total}")
        
        import Patch
        
        successful_count = 0
        for index, patch_path in enumerate(patches, start=1):
            filename = os.path.basename(patch_path)
            ext = os.path.splitext(patch_path)[1].lower()
            self.log(f"\n[{index}/{total}] Processing: {filename}...")
            
            try:
                if ext == ".apz5":
                    # Custom OoT patching logic (avoids showing messagebox per-file in batch mode)
                    from worlds.oot.Rom import Rom, compress_rom_file
                    from worlds.oot.N64Patch import apply_patch_file
                    from worlds.oot import OOTWorld
                    from worlds.oot.Utils import data_path
                    
                    rom_file_name = OOTWorld.settings.rom_file
                    if not os.path.exists(rom_file_name):
                        default_oot_path = r"C:\ProgramData\Archipelago\The Legend of Zelda - Ocarina of Time.z64"
                        if os.path.exists(default_oot_path):
                            rom_file_name = default_oot_path
                        else:
                            raise FileNotFoundError("Base OoT ROM not found.")
                    
                    base_name = os.path.splitext(filename)[0]
                    decomp_path = os.path.join(output_dir, base_name + '-decomp.z64')
                    comp_path = os.path.join(output_dir, base_name + '.z64')
                    
                    rom = Rom(rom_file_name)
                    sub_file = None
                    import zipfile
                    if zipfile.is_zipfile(patch_path):
                        for name in zipfile.ZipFile(patch_path).namelist():
                            if name.endswith('.zpf'):
                                sub_file = name
                                break
                                
                    apply_patch_file(rom, patch_path, sub_file=sub_file)
                    rom.write_to_file(decomp_path)
                    
                    orig_cwd = os.getcwd()
                    compress_dir = data_path("Compress")
                    os.chdir(compress_dir)
                    try:
                        compress_rom_file(decomp_path, comp_path)
                    finally:
                        os.chdir(orig_cwd)
                        
                    if os.path.exists(decomp_path):
                        os.remove(decomp_path)
                        
                    self.log(f"Successfully generated OoT ROM: {os.path.basename(comp_path)}")
                    successful_count += 1
                    
                else:
                    # Standard patching method
                    meta, romfile = Patch.create_rom_file(patch_path)
                    target_file = os.path.join(output_dir, os.path.basename(romfile))
                    
                    if os.path.abspath(romfile) != os.path.abspath(target_file):
                        if os.path.exists(target_file):
                            os.remove(target_file)
                        shutil.move(romfile, target_file)
                        self.log(f"Successfully generated ROM/Patch: {os.path.basename(target_file)}")
                    else:
                        self.log(f"Successfully generated ROM/Patch: {os.path.basename(romfile)}")
                        
                    successful_count += 1
                    
            except Exception as e:
                self.log(f"FAILED: {filename}. Error: {str(e)}")
                
        self.log(f"\nBatch processing finished. Successfully patched {successful_count}/{total} files.")
        messagebox.showinfo("Batch Complete", f"Successfully patched {successful_count}/{total} files inside the directory!")

if __name__ == "__main__":
    app = ZeldaHubPatcherApp()
    app.mainloop()
