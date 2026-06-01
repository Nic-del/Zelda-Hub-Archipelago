import webview
import sys
import json
import os
import threading
import http.server
import socketserver
import time
import subprocess
import socket

def wait_for_port(port, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except:
            time.sleep(1)
    return False

def start_local_server(path, port):
    os.chdir(path)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[WebTracker] Hosting {path} on port {port}")
        httpd.serve_forever()

def run_npm_server(path):
    print(f"[WebTracker] NPM mode detected in {path}")
    os.chdir(path)
    
    # Check for node_modules
    if not os.path.exists(os.path.join(path, "node_modules")):
        print("[WebTracker] node_modules missing. Running npm install...")
        subprocess.run(["npm", "install"], shell=True, cwd=path, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    
    print("[WebTracker] Starting npm server on port 5176...")
    # Run npm start (which is 'vite' for the SS tracker)
    return subprocess.Popen(["npm", "start", "--", "--port", "5176"], shell=True, cwd=path, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)

def main():
    if len(sys.argv) < 2:
        print("Usage: python web_tracker_host.py <URL or Path> [x y w h] [IP PORT SLOT MDP]")
        return

    input_source = sys.argv[1]
    input_source = os.path.abspath(input_source)
    x, y, w, h = None, None, 1280, 720
    
    # Defaults for Archipelago parameters
    ap_params = {"ip": "", "port": "", "slot": "", "mdp": ""}

    # Parse geometry
    if len(sys.argv) >= 6:
        try:
            x = None if sys.argv[2] == "None" else int(sys.argv[2])
            y = None if sys.argv[3] == "None" else int(sys.argv[3])
            w = int(sys.argv[4])
            h = int(sys.argv[5])
        except:
            pass

    # Parse Archipelago params (passed after geometry)
    if len(sys.argv) >= 10:
        ap_params["ip"] = sys.argv[6]
        ap_params["port"] = sys.argv[7]
        ap_params["slot"] = sys.argv[8]
        ap_params["mdp"] = sys.argv[9]

    url = input_source
    npm_proc = None

    if os.path.isdir(input_source):
        # 1. Check for package.json (NPM mode) - Highest priority as requested
        if os.path.exists(os.path.join(input_source, "package.json")):
            npm_proc = run_npm_server(input_source)
            server_port = 5176
            if wait_for_port(server_port):
                url = f"http://localhost:{server_port}"
            else:
                print(f"[WebTracker] Error: NPM server failed to start on port {server_port}")
                # Fallback to dist if npm fails
                dist_path = os.path.join(input_source, "dist")
                if not os.path.exists(dist_path): dist_path = os.path.join(input_source, "build")
                
                if os.path.exists(dist_path) and os.path.exists(os.path.join(dist_path, "index.html")):
                    print(f"[WebTracker] NPM failed. Falling back to pre-built folder: {dist_path}")
                    threading.Thread(target=start_local_server, args=(dist_path, server_port), daemon=True).start()
                    url = f"http://localhost:{server_port}"
                    wait_for_port(server_port)
                else:
                    return
        
        # 2. Check for pre-built dist/build if no package.json or as fallback
        else:
            dist_path = os.path.join(input_source, "dist")
            if not os.path.exists(dist_path):
                dist_path = os.path.join(input_source, "build")
                
            if os.path.exists(dist_path) and os.path.exists(os.path.join(dist_path, "index.html")):
                print(f"[WebTracker] Pre-built folder found at {dist_path}. Hosting as static site.")
                host_dir = dist_path
                server_port = 5176
                threading.Thread(target=start_local_server, args=(host_dir, server_port), daemon=True).start()
                url = f"http://localhost:{server_port}"
                wait_for_port(server_port)
            else:
                # Fallback for simple trackers
                server_port = 5176
                threading.Thread(target=start_local_server, args=(input_source, server_port), daemon=True).start()
                url = f"http://localhost:{server_port}"
                wait_for_port(server_port)

    # Inject parameters into URL (Vite style used by the SS tracker)
    if ap_params["ip"]:
        sep = "#/?" if "localhost" in url else "?"
        if "#" in url and "localhost" not in url: sep = "&"
        
        param_str = f"ip={ap_params['ip']}&port={ap_params['port']}&slot={ap_params['slot']}&autolaunch=true"
        if ap_params["mdp"] and ap_params["mdp"] != "None":
            param_str += f"&mdp={ap_params['mdp']}"
        
        url = f"{url}{sep}{param_str}"

    print(f"[WebTracker] Opening window with URL: {url}")

    # Check config for maximization
    do_maximize = True
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                do_maximize = json.load(f).get("maximize_poptracker", True)
    except: pass

    # Window creation
    window = webview.create_window(
        'Zelda Hub - Web Tracker', 
        url, 
        x=x, 
        y=y, 
        width=w, 
        height=h,
        background_color='#000000',
        transparent=True,
        maximized=do_maximize
    )
    
    try:
        webview.start()
    finally:
        if npm_proc:
            print("[WebTracker] Shutting down NPM server...")
            # On Windows, we need to be aggressive with taskkill to kill the vite child process
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(npm_proc.pid)], shell=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)

if __name__ == "__main__":
    main()
