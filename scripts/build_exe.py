import os
import subprocess
import shutil
import sys

def build_one(use_console, project_root, python_src, controller_src, main_script, datas):
    # Determine the name and flag
    name = "ZeldaMultiLauncherHub_Debug" if use_console else "ZeldaMultiLauncherHub"
    console_flag = "--console" if use_console else "--noconsole"
    
    print(f"\n=======================================================")
    print(f" Compilation de {name} ({'Avec Console' if use_console else 'Sans Console'})")
    print(f"=======================================================\n")
    
    # Clean previous build folder
    build_folder = os.path.join(project_root, "build")
    if os.path.exists(build_folder):
        try:
            shutil.rmtree(build_folder)
            print(f"[Build] Nettoyage du dossier build")
        except Exception as e:
            print(f"[Build] Attention: Impossible de supprimer {build_folder}: {e}")
            
    # Clean existing executable file in dist to ensure it is rebuilt
    exe_file = os.path.join(project_root, "dist", f"{name}.exe")
    if os.path.exists(exe_file):
        try:
            os.remove(exe_file)
            print(f"[Build] Supprimé l'ancien exécutable : {exe_file}")
        except Exception as e:
            print(f"[Build] Attention: Impossible de supprimer {exe_file}: {e}")

    base_cmd = [
        console_flag,
        "--onefile",
        "--noconfirm",
        f"--name={name}",
        f"--workpath={build_folder}",
        f"--distpath={os.path.join(project_root, 'dist')}",
        f"--specpath={project_root}",
        f"--paths={python_src}",
        f"--paths={controller_src}",
        "--hidden-import=pygame",
        "--hidden-import=psutil",
        "--hidden-import=keyboard",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=win32gui",
        "--hidden-import=win32process",
        "--hidden-import=win32con",
        "--hidden-import=obswebsocket",
        "--hidden-import=controller_manager",
        "--hidden-import=device_detector",
        "--hidden-import=profile_manager",
        "--hidden-import=input_mapper",
        "--hidden-import=config_exporter",
        "--collect-all=customtkinter",
        "--collect-all=pygame",
        "--collect-all=obswebsocket",
        "--collect-all=websocket",
    ]
    
    for src, dest in datas:
        base_cmd.append(f"--add-data={src}{os.pathsep}{dest}")
    
    base_cmd.append(main_script)
    
    # Try compiling with py -3.14 first
    cmd = ["py", "-3.14", "-m", "PyInstaller"] + base_cmd
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[Build] Succès de la compilation de {name} !")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"\n[Build] py -3.14 non disponible ou a échoué. Tentative avec l'interpréteur Python actuel...")
        fallback_cmd = [sys.executable, "-m", "PyInstaller"] + base_cmd
        try:
            subprocess.run(fallback_cmd, check=True)
            print(f"\n[Build] Succès de la compilation de {name} avec le Python actuel !")
        except subprocess.CalledProcessError as e:
            print(f"\n[Build] Échec de la compilation de {name} : {e}")
            return False
    return True

def build():
    # Detect current directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_src = os.path.join(project_root, "python_src")
    controller_src = os.path.join(python_src, "controller")
    main_script = os.path.join(python_src, "ui_main.py")
    
    # Ensure dist exists
    os.makedirs(os.path.join(project_root, "dist"), exist_ok=True)
    
    # PyInstaller command datas
    datas = [
        (os.path.join(python_src, "assets"), "assets"),
        (os.path.join(python_src, "controller"), "controller"),
        (os.path.join(python_src, "clipboard_paste.ps1"), "."),
        (os.path.join(python_src, "maximize_poptracker.ps1"), "."),
        (os.path.join(python_src, "minimize_lua_console.ps1"), "."),
        (os.path.join(python_src, "send_input.ps1"), "."),
        (os.path.join(python_src, "games_metadata.json"), "."),
        (os.path.join(python_src, "center_broadcast.ps1"), "."),
        (os.path.join(python_src, "web_tracker_host.py"), "."),
        (os.path.join(python_src, "ui_controller.py"), "."),
        (os.path.join(python_src, "ui_setup.py"), "."),
    ]
    
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
        datas.append((ctk_path, "customtkinter"))
    except ImportError:
        pass

    # Parse arguments
    compile_console = "--console" in sys.argv or "-c" in sys.argv
    compile_noconsole = "--noconsole" in sys.argv or "-nc" in sys.argv
    
    # Determine what to build
    targets = []
    if compile_console and not compile_noconsole:
        targets = [True] # Console only
    elif compile_noconsole and not compile_console:
        targets = [False] # Standard only
    else:
        # Default: build BOTH
        targets = [False, True] # False = noconsole, True = console

    success = True
    for target in targets:
        if not build_one(target, project_root, python_src, controller_src, main_script, datas):
            success = False
            
    if success:
        print("\n[Build] Toutes les compilations demandées ont été effectuées avec succès !")
        print(f"Les exécutables se trouvent dans : {os.path.join(project_root, 'dist')}")
    else:
        print("\n[Build] Une ou plusieurs compilations ont échoué.")

if __name__ == "__main__":
    build()
