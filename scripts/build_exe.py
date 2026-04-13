import os
import subprocess
import shutil
import sys

def build():
    # Detect current directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_src = os.path.join(project_root, "python_src")
    controller_src = os.path.join(python_src, "controller")
    
    # Target script
    main_script = os.path.join(python_src, "ui_main.py")
    
    # Clean previous build/dist folders
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"[Build] Cleaned up {folder}")
            except Exception as e:
                print(f"[Build] Warning: Could not remove {folder}: {e}")

    # PyInstaller command
    datas = [
        (os.path.join(python_src, "assets"), "assets"),
        (os.path.join(python_src, "controller"), "controller"),
        (os.path.join(python_src, "profiles"), "profiles"),
        (os.path.join(python_src, "clipboard_paste.ps1"), "."),
        (os.path.join(python_src, "maximize_poptracker.ps1"), "."),
        (os.path.join(python_src, "minimize_lua_console.ps1"), "."),
        (os.path.join(python_src, "send_input.ps1"), "."),
    ]
    
    # CustomTkinter needs its resources
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
        datas.append((ctk_path, "customtkinter"))
    except ImportError:
        pass

    # Building for Python 3.14 target
    # We include python_src and controller in --paths so PyInstaller can find local modules
    cmd = ["py", "-3.14", "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--noconfirm",
        "--name=ZeldaMultiLauncherHub",
        f"--workpath={os.path.join(project_root, 'build')}",
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
    ]
    
    for src, dest in datas:
        cmd.append(f"--add-data={src}{os.pathsep}{dest}")
    
    cmd.append(main_script)
    
    print(f"\n[Build] Starting PyInstaller for Python 3.14...\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        print(f"Executable is located in: {os.path.join(project_root, 'dist')}")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")

if __name__ == "__main__":
    build()
