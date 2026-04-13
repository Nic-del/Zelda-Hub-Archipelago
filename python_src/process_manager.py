import os
import subprocess
import time
import sys

try:
    import psutil
except ImportError:
    psutil = None

class ProcessManager:
    """
    Centralized utility for process management (PID tracking, killing, priority).
    """
    
    @staticmethod
    def kill_process_tree(pid):
        """Kills a process and all its children using taskkill /T on Windows."""
        if not pid: return
        print(f"[ProcessManager] Force killing process tree for PID {pid}...")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                               capture_output=True, check=False)
            else:
                # Fallback for non-windows if needed
                if psutil:
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()
                else:
                    os.kill(pid, 9)
        except Exception as e:
            print(f"[ProcessManager] Error killing process {pid}: {e}")

    @staticmethod
    def kill_by_name(image_name):
        """Kills all processes matching a specific image name."""
        if not image_name: return
        print(f"[ProcessManager] Killing processes by name: {image_name}")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/IM", image_name], 
                               capture_output=True, check=False)
            elif psutil:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() == image_name.lower():
                        proc.kill()
        except Exception as e:
            print(f"[ProcessManager] Error killing {image_name}: {e}")

    @staticmethod
    def is_running(pid):
        """Checks if a process ID is still active."""
        if not pid: return False
        if psutil:
            try:
                return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
            except:
                return False
        return False

    @staticmethod
    def wait_for_exit(pid, timeout=5.0):
        """Waits for a process to exit within a timeout."""
        if not pid: return True
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not ProcessManager.is_running(pid):
                return True
            time.sleep(0.2)
        return False

    @staticmethod
    def set_priority(pid, priority_class):
        """Sets process priority (Windows specific classes via psutil)."""
        if not psutil or not pid: return False
        try:
            p = psutil.Process(pid)
            p.nice(priority_class)
            return True
        except Exception as e:
            print(f"[ProcessManager] Priority error for PID {pid}: {e}")
            return False
