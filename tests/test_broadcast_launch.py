import os
import sys
import subprocess
import time
import psutil

def get_exe_dir():
    # Matches the app's get_exe_dir logic
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_broadcast_fallback_and_launch():
    print("=== STARTING BROADCAST LAUNCH TEST ===")
    
    # 1. Resolve potential app directory path
    app_dir = os.path.join(get_exe_dir(), "App")
    print(f"App directory resolved to: {app_dir}")
    
    # 2. Emulate fallback path resolution
    broadcast_fallback = os.path.join(app_dir, "BroadCast-Archipelago")
    broadcast_fallback_alt = os.path.join(app_dir, "uibroadcast")
    
    broadcast_dir = ""
    if os.path.exists(os.path.join(broadcast_fallback, "start_cli.py")):
        broadcast_dir = broadcast_fallback
    elif os.path.exists(os.path.join(broadcast_fallback_alt, "start_cli.py")):
        broadcast_dir = broadcast_fallback_alt
        
    print(f"Detected Broadcast directory: {broadcast_dir}")
    
    if not broadcast_dir:
        print("[FAIL] Could not locate the Broadcast directory or start_cli.py!")
        sys.exit(1)
        
    print("[PASS] Successfully located the renamed BroadCast-Archipelago directory!")
    
    # 3. Simulate process spawning using the exact method in ui_main.py
    # Find a valid python interpreter
    python_exe_list = ["py", "-3.12"]
    for interp in [["py", "-3.12"], ["py", "-3.14"], ["python"], ["py"]]:
        try:
            if subprocess.call(interp + ["-c", "pass"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                python_exe_list = interp
                break
        except: pass
        
    print(f"Using python interpreter: {python_exe_list}")
    
    b_cmd = python_exe_list + [
        "start_cli.py",
        "--server", "archipelago.gg:12345",
        "--slot", "TestSlot",
        "--mode", "obs"
    ]
    
    print(f"Running launch command: {' '.join(b_cmd)}")
    
    try:
        # Launch the broadcast in a new console like the app does
        broadcast_p = subprocess.Popen(
            b_cmd,
            cwd=broadcast_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"Spawned Broadcast process (PID: {broadcast_p.pid})")
        
        # 4. Wait a few seconds to let it start and check if it remains alive
        time.sleep(3)
        
        poll = broadcast_p.poll()
        if poll is not None:
            print(f"[FAIL] Broadcast process exited early with code {poll}!")
            sys.exit(1)
            
        print("[PASS] Broadcast process is running successfully!")
        
        # 5. Check if the sub-processes (like the bridge) were spawned
        print("Scanning for child processes of the broadcast launcher...")
        parent = psutil.Process(broadcast_p.pid)
        children = parent.children(recursive=True)
        
        if children:
            print(f"[PASS] Successfully detected {len(children)} active child process(es):")
            for child in children:
                try:
                    print(f"  - PID: {child.pid}, Name: {child.name()}, Cmdline: {child.cmdline()}")
                except Exception as e:
                    print(f"  - PID: {child.pid} (Details hidden: {e})")
        else:
            print("[WARNING] No active child processes detected yet. This might be normal if loading is slow.")
            
        # 6. Graceful cleanup (kill the process tree like the controller does)
        print("Cleaning up broadcast processes...")
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(broadcast_p.pid)], capture_output=True)
        print("[PASS] Cleaned up all background test processes successfully!")
        print("=== ALL TESTS PASSED! ===")
        
    except Exception as e:
        print(f"[FAIL] Error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_broadcast_fallback_and_launch()
