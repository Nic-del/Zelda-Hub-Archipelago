import os
import sys
import shutil
import zipfile
import subprocess
import time

# Codes de couleur ANSI pour un affichage console premium
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"

def safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        cleaned = (message
                   .replace("\u2713", "OK")
                   .replace("\u2717", "X")
                   .replace("📁", "[DIR]")
                   .replace("📄", "[FILE]")
                   .replace(">>", ">>")
                   .replace("»", ">>"))
        # Remove or ignore any remaining non-ASCII characters if needed
        cleaned = cleaned.encode('ascii', errors='replace').decode('ascii').replace('?', ' ')
        print(cleaned)

def print_header(title):
    safe_print(f"\n{BOLD}{MAGENTA}{'=' * 60}{RESET}")
    safe_print(f"{BOLD}{CYAN} {title.center(58)} {RESET}")
    safe_print(f"{BOLD}{MAGENTA}{'=' * 60}{RESET}\n")

def print_step(step_name):
    safe_print(f"{BOLD}{YELLOW}>> {step_name}...{RESET}")

def print_success(message):
    safe_print(f"{BOLD}{GREEN}[\u2713] {message}{RESET}")

def print_warning(message):
    safe_print(f"{BOLD}{YELLOW}[!] {message}{RESET}")

def print_error(message):
    safe_print(f"{BOLD}{RED}[\u2717] {message}{RESET}")

def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def get_dir_size(path, ignore_func=None):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        # Apply ignore function if provided to exclude ignored paths
        if ignore_func:
            ignored = ignore_func(dirpath, filenames)
            filenames = [f for f in filenames if f not in ignored]
            dirnames[:] = [d for d in dirnames if d not in ignored]
        
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
    return total_size

def make_release():
    print_header("Zelda Multi-Launcher Hub - Release Builder")
    
    # 1. Détection des chemins du projet
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(scripts_dir)
    
    dist_dir = os.path.join(project_root, "dist")
    exe_name = "ZeldaMultiLauncherHub.exe"
    exe_path = os.path.join(dist_dir, exe_name)
    build_script = os.path.join(scripts_dir, "build_exe.py")
    
    # 2. Vérification / Proposition de compilation de l'exécutable
    if not os.path.exists(exe_path):
        print_warning(f"L'exécutable '{exe_name}' n'a pas été trouvé dans {dist_dir}.")
        if sys.stdin.isatty():
            response = input(f"{BOLD}Voulez-vous compiler l'exécutable maintenant avec build_exe.py ? (o/n) [défaut: o]: {RESET}").strip().lower()
        else:
            print_warning("Session non-interactive détectée. Lancement de la compilation automatique.")
            response = 'o'
        if response != 'n':
            if os.path.exists(build_script):
                print_step("Compilation de l'exécutable en cours")
                try:
                    # Tenter de lancer avec la version de Python adéquate
                    subprocess.run(["py", "-3.14", build_script], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run([sys.executable, build_script], check=True)
                    except subprocess.CalledProcessError as e:
                        print_error(f"Erreur lors de la compilation de l'exécutable : {e}")
                        sys.exit(1)
                
                if os.path.exists(exe_path):
                    print_success("Exécutable compilé avec succès !")
                else:
                    print_error("Compilation terminée mais l'exécutable est introuvable.")
                    sys.exit(1)
            else:
                print_error(f"Le script de compilation '{build_script}' est introuvable. Impossible de compiler.")
                sys.exit(1)
        else:
            print_error("Compilation annulée par l'utilisateur. Impossible de continuer sans exécutable.")
            sys.exit(1)
    else:
        # L'exécutable existe, demander si l'utilisateur souhaite le recompiler
        if sys.stdin.isatty():
            response = input(f"{BOLD}Un exécutable existant a été trouvé. Voulez-vous le recompiler ? (o/n) [défaut: n]: {RESET}").strip().lower()
        else:
            print_warning("Session non-interactive détectée. Recompilation automatique de l'exécutable.")
            response = 'o'
        if response == 'o':
            if os.path.exists(build_script):
                print_step("Recompilation de l'exécutable")
                try:
                    subprocess.run(["py", "-3.14", build_script], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run([sys.executable, build_script], check=True)
                    except subprocess.CalledProcessError as e:
                        print_error(f"Erreur lors de la compilation de l'exécutable : {e}")
                        sys.exit(1)
                
                if os.path.exists(exe_path):
                    print_success("Exécutable recompilé avec succès !")
                else:
                    print_error("La recompilation a échoué.")
                    sys.exit(1)
            else:
                print_warning("Script de compilation introuvable. Utilisation de l'exécutable existant.")

    # 3. Préparation des répertoires de release
    release_parent = os.path.join(project_root, "release")
    release_folder_name = "Zelda-Hub-Release"
    release_dir = os.path.join(release_parent, release_folder_name)
    zip_path = os.path.join(release_parent, f"{release_folder_name}.zip")
    
    print_step(f"Nettoyage et préparation du dossier de destination : {release_dir}")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    os.makedirs(release_dir, exist_ok=True)
    print_success("Dossiers de destination créés.")
    
    # 4. Définition des dossiers et fichiers à copier et règles d'exclusion
    # Exclure les fichiers de développement, caches, logs et git
    ignored_patterns = shutil.ignore_patterns(
        '.git', '.gitignore', '.gitattributes',
        '__pycache__', '*.pyc', '*.pyo', '*.pyd',
        '.vscode', '.idea', '.pytest_cache',
        '.electron_data', 'logs', 'node_modules',
        'package-lock.json'
    )
    
    items_to_copy = [
        ("App", "dossier"),
        ("Extractor", "dossier"),
        ("Emulator", "dossier"),
        ("PatchFile", "dossier"),
        ("Patcher", "dossier"),
        ("Rom", "dossier"),
        ("README.md", "fichier")
    ]
    
    copied_summary = []
    
    # Copie de l'exécutable à la racine du dossier de release
    print_step(f"Copie de l'exécutable à la racine : {exe_name}")
    shutil.copy2(exe_path, os.path.join(release_dir, exe_name))
    exe_size = os.path.getsize(exe_path)
    copied_summary.append((exe_name, exe_size, "fichier"))
    print_success(f"Copie réussie. Taille : {format_size(exe_size)}")
    
    # Copie des autres éléments requis
    for item_name, item_type in items_to_copy:
        src_path = os.path.join(project_root, item_name)
        dest_path = os.path.join(release_dir, item_name)
        
        if not os.path.exists(src_path):
            print_warning(f"L'élément source '{item_name}' n'existe pas. Ignoré.")
            continue
            
        print_step(f"Copie de l'élément : {item_name} ({item_type})")
        
        if item_type == "dossier":
            shutil.copytree(src_path, dest_path, ignore=ignored_patterns)
            if item_name == "Extractor":
                patcher_release_dir = os.path.join(dest_path, "Patcher")
                if os.path.exists(patcher_release_dir):
                    for filename in os.listdir(patcher_release_dir):
                        file_p = os.path.join(patcher_release_dir, filename)
                        if filename != "ZeldaHubPatcher.exe":
                            try:
                                if os.path.isdir(file_p):
                                    shutil.rmtree(file_p)
                                else:
                                    os.remove(file_p)
                            except Exception as e:
                                print_warning(f"Impossible de supprimer {filename}: {e}")
            size = get_dir_size(dest_path)
            copied_summary.append((item_name, size, "dossier"))
            print_success(f"Dossier '{item_name}' copié avec succès ! Taille : {format_size(size)}")
        else:
            shutil.copy2(src_path, dest_path)
            size = os.path.getsize(src_path)
            copied_summary.append((item_name, size, "fichier"))
            print_success(f"Fichier '{item_name}' copié avec succès ! Taille : {format_size(size)}")
            
    # 5. Création de l'archive ZIP
    print_step(f"Génération de l'archive ZIP : {os.path.basename(zip_path)}")
    
    start_time = time.time()
    total_files = 0
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Stocker dans le zip avec un chemin relatif par rapport au dossier de release parent
                arcname = os.path.relpath(file_path, release_parent)
                zip_file.write(file_path, arcname)
                total_files += 1
                
    elapsed_time = time.time() - start_time
    zip_size = os.path.getsize(zip_path)
    print_success(f"Archive ZIP créée avec succès en {elapsed_time:.2f}s ! Taille : {format_size(zip_size)} (contient {total_files} fichiers)")
    
    # 6. Rapport final
    print_header("Rapport de Release Premium")
    safe_print(f"{BOLD}{CYAN}Dossier de Release : {RESET}{release_dir}")
    safe_print(f"{BOLD}{CYAN}Archive ZIP        : {RESET}{zip_path}")
    safe_print(f"{BOLD}{CYAN}Contenu inclus     :{RESET}")
    
    total_release_size = 0
    for name, size, itype in copied_summary:
        total_release_size += size
        icon = "📁" if itype == "dossier" else "📄"
        safe_print(f"  {icon} {name:<25} : {format_size(size)}")
        
    safe_print(f"\n{BOLD}{CYAN}Taille totale du dossier : {RESET}{format_size(total_release_size)}")
    safe_print(f"{BOLD}{CYAN}Taille compressée (ZIP)  : {RESET}{format_size(zip_size)}")
    
    # Estimation de la taille économisée grâce aux exclusions
    total_raw_size = exe_size
    for item_name, item_type in items_to_copy:
        src_path = os.path.join(project_root, item_name)
        if os.path.exists(src_path):
            if item_type == "dossier":
                total_raw_size += get_dir_size(src_path)
            else:
                total_raw_size += os.path.getsize(src_path)
                
    saved_size = total_raw_size - total_release_size
    if saved_size > 0:
        safe_print(f"{BOLD}{GREEN}Espace économisé (filtres) : {RESET}{format_size(saved_size)}")
        
    safe_print(f"\n{BOLD}{GREEN}La release est prête à être partagée !{RESET}\n")

if __name__ == "__main__":
    try:
        # Forcer la prise en charge des couleurs ANSI sous Windows
        if sys.platform == "win32":
            os.system("")
        make_release()
    except KeyboardInterrupt:
        print_error("\nOpération interrompue par l'utilisateur.")
        sys.exit(1)
