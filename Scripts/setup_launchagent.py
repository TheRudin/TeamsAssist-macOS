#!/usr/bin/env python3
import os
import sys
import plistlib
import subprocess

LABEL = "com.teamsassist.status"
PLIST_FILENAME = f"{LABEL}.plist"
LAUNCH_AGENTS_DIR = os.path.expanduser("~/Library/LaunchAgents")
PLIST_PATH = os.path.join(LAUNCH_AGENTS_DIR, PLIST_FILENAME)

def install():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    daemon_script = os.path.join(script_dir, "get_teams_status.py")
    
    if not os.path.exists(daemon_script):
        print(f"Error: Could not find {daemon_script}")
        sys.exit(1)
        
    # Make daemon script executable
    os.chmod(daemon_script, 0o755)
    
    # Configure logs directory in the same folder
    log_out = os.path.join(script_dir, "teams_status.log")
    log_err = os.path.join(script_dir, "teams_status.err")
    
    # Define plist content
    plist_data = {
        "Label": LABEL,
        "ProgramArguments": [
            "/usr/bin/python3",
            daemon_script
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": log_out,
        "StandardErrorPath": log_err,
        "WorkingDirectory": script_dir
    }
    
    # Ensure LaunchAgents directory exists
    os.makedirs(LAUNCH_AGENTS_DIR, exist_ok=True)
    
    # Write plist file
    try:
        with open(PLIST_PATH, "wb") as f:
            plistlib.dump(plist_data, f)
        print(f"Successfully created Launch Agent configuration at {PLIST_PATH}")
    except Exception as e:
        print(f"Error writing plist file: {e}")
        sys.exit(1)
        
    # Unload if already loaded
    subprocess.run(["launchctl", "unload", PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Load and start Launch Agent
    result = subprocess.run(["launchctl", "load", PLIST_PATH], capture_output=True, text=True)
    if result.returncode == 0:
        print("Launch Agent loaded and started successfully!")
        print("The status monitor is now running in the background and will start automatically at login.")
        print(f"Logs will be written to: {log_out}")
    else:
        print(f"Error loading Launch Agent: {result.stderr}")
        print("Try running manually: launchctl load " + PLIST_PATH)

def uninstall():
    if not os.path.exists(PLIST_PATH):
        print(f"Launch Agent plist not found at {PLIST_PATH}. Nothing to uninstall.")
        return
        
    # Unload agent
    result = subprocess.run(["launchctl", "unload", PLIST_PATH], capture_output=True, text=True)
    if result.returncode == 0:
        print("Launch Agent unloaded successfully.")
    else:
        print(f"Warning during unload: {result.stderr.strip()}")
        
    # Remove plist file
    try:
        os.remove(PLIST_PATH)
        print("Removed Launch Agent configuration file.")
    except Exception as e:
        print(f"Error removing plist file: {e}")
        
    print("Uninstall complete.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall()
    else:
        install()

if __name__ == "__main__":
    main()
