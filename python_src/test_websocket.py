import socket
import json
import os
import sys
import time

def check_port(host, port, name):
    print(f"[*] Checking {name} on {host}:{port}...")
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[+] {name} is listening on {host}:{port}")
            return True
    except (socket.timeout, ConnectionRefusedError):
        print(f"[-] {name} is NOT responding on {host}:{port}")
        return False
    except Exception as e:
        print(f"[!] Error checking {name}: {e}")
        return False


def test_obs_websocket():
    print("\n--- Testing OBS WebSocket ---")

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    host, port, password = "localhost", 4455, ""

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                obs_settings = config.get("obs_settings", {})
                host = obs_settings.get("host", "localhost")
                port = obs_settings.get("port", 4455)
                password = obs_settings.get("password", "")
                print(f"[*] Loaded config: {host}:{port}")
        except Exception as e:
            print(f"[!] Could not load config.json: {e}")
            print("[!] Using default OBS connection settings.")

    if not check_port(host, port, "OBS"):
        print("[!] Tip: Open OBS → Tools → WebSocket Server Settings")
        print("[!] Ensure 'Enable WebSocket Server' is checked.")
        return

    try:
        from obswebsocket import obsws
        from obswebsocket import requests
        print("[+] obs-websocket-py library found.")
    except ImportError:
        print("[-] obs-websocket-py NOT installed.")
        print("Install with:")
        print("pip install obs-websocket-py")
        return

    try:
        print("[*] Connecting to OBS...")
        ws = obsws(host, port, password)
        ws.connect()

        print("[+] Connected to OBS.")

        # Get OBS version
        version = ws.call(requests.GetVersion())

        print("[+] OBS Version:", version.getObsVersion())
        print("[+] WebSocket Version:", version.getObsWebSocketVersion())

        ws.disconnect()
        print("[+] Connection closed.")

    except Exception as e:
        print(f"[-] Connection failed: {e}")
        print("[!] Verify password and WebSocket settings in OBS.")


def test_poptracker_websocket():
    print("\n--- Testing PopTracker WebSocket ---")

    check_port("localhost", 8080, "PopTracker Web")
    check_port("localhost", 42069, "PopTracker Bridge")

    print("[!] Tip: PopTracker must be open with a pack loaded.")


if __name__ == "__main__":
    test_obs_websocket()
    test_poptracker_websocket()

    print("\nVerification complete.")
    input("\nPress Enter to exit...")