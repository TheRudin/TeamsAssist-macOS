#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
import signal

# Default settings in case settings.json is missing or corrupt
DEFAULT_SETTINGS = {
    "ha_token": "<Insert token>",
    "ha_url": "<HA URL>",
    "teams_version": "Auto",
    "check_interval": 2,
    "status_entity": "input_text.teams_status",
    "status_friendly_name": "Microsoft Teams status helper",
    "activity_entity": "input_text.teams_activity",
    "activity_friendly_name": "Microsoft Teams activity helper",
    "monitoring_entity": "binary_sensor.teams_monitoring",
    "monitoring_friendly_name": "Microsoft Teams monitoring",
    "languages": {
        "Available": "Available",
        "Busy": "Busy",
        "OnThePhone": "On the phone",
        "Away": "Away",
        "BeRightBack": "Be right back",
        "DoNotDisturb": "Do not disturb",
        "Presenting": "Presenting",
        "Focusing": "Focusing",
        "InAMeeting": "In a meeting",
        "Offline": "Offline",
        "NotInACall": "Not in a call",
        "InACall": "In a call"
    },
    "icons": {
        "InACall": "mdi:phone-in-talk-outline",
        "NotInACall": "mdi:phone-off",
        "Monitoring": "mdi:api"
    }
}

def load_settings():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(script_dir, "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # Merge with default settings to ensure all keys exist
                merged = DEFAULT_SETTINGS.copy()
                merged.update(settings)
                return merged
        except Exception as e:
            print(f"Error reading settings.json: {e}. Using defaults.")
    return DEFAULT_SETTINGS

def post_to_ha(url, token, entity, state, friendly_name, icon=None):
    if not token or token == "<Insert token>" or not url or url == "<HA URL>":
        print(f"Skipping HA API call for {entity}: Home Assistant URL or Token not configured.")
        return False

    api_url = f"{url.rstrip('/')}/api/states/{entity}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "state": state,
        "attributes": {
            "friendly_name": friendly_name
        }
    }
    if icon:
        payload["attributes"]["icon"] = icon

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status in (200, 201)
    except urllib.error.URLError as e:
        print(f"HA connection error ({entity}): {e}")
    except Exception as e:
        print(f"Error updating Home Assistant ({entity}): {e}")
    return False

def is_teams_running():
    for name in ["MSTeams", "Microsoft Teams"]:
        try:
            # -x is exact match
            subprocess.check_output(["pgrep", "-x", name])
            return True
        except subprocess.CalledProcessError:
            continue
    return False

def is_teams_in_call_pmset():
    try:
        output = subprocess.check_output(["pmset", "-g", "assertions"]).decode("utf-8")
        if "Microsoft Teams Call in progress" in output:
            return True
    except Exception as e:
        print(f"Error running pmset: {e}")
    return False

def get_last_lines_from_file(file_path, max_bytes=50000):
    try:
        with open(file_path, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            seek_pos = max(0, file_size - max_bytes)
            f.seek(seek_pos)
            data = f.read()
            return data.decode('utf-8', errors='ignore').splitlines()
    except Exception as e:
        return []

def parse_classic_status(lines, languages):
    mapping = {
        "Available": "Available",
        "Busy": "Busy",
        "OnThePhone": "OnThePhone",
        "Away": "Away",
        "BeRightBack": "BeRightBack",
        "DoNotDisturb": "DoNotDisturb",
        "Presenting": "Presenting",
        "Focusing": "Focusing",
        "InAMeeting": "InAMeeting",
        "Offline": "Offline"
    }
    for line in reversed(lines):
        for log_val, state_key in mapping.items():
            if f"Setting the taskbar overlay icon - {log_val}" in line or \
               f"StatusIndicatorStateService: Added {log_val}" in line or \
               f"current state: {log_val} -> NewActivity" in line:
                return languages.get(state_key, log_val)
    return None

def parse_classic_activity(lines, languages, icons):
    for line in reversed(lines):
        if any(p in line for p in ["Pausing daemon App updates", "SfB:TeamsActiveCall", "isOngoing: true"]):
            return languages.get("InACall", "In a call"), icons.get("InACall", "mdi:phone-in-talk-outline")
        if any(p in line for p in ["Resuming daemon App updates", "SfB:TeamsNoCall", "isOngoing: false"]):
            return languages.get("NotInACall", "Not in a call"), icons.get("NotInACall", "mdi:phone-off")
    return None

# Global signal handler for clean exit
running = True
def handle_signal(signum, frame):
    global running
    print(f"Received signal {signum}. Shutting down...")
    running = False

def main():
    global running
    # Register shutdown signals
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    settings = load_settings()
    
    # Check if manual status override parameters are used
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status" and len(sys.argv) > 2:
            status_val = sys.argv[2]
            print(f"Manually setting status to {status_val}...")
            post_to_ha(
                settings["ha_url"], 
                settings["ha_token"], 
                settings["status_entity"], 
                status_val, 
                settings["status_friendly_name"],
                icon="mdi:microsoft-teams"
            )
            return
        elif sys.argv[1] == "--activity" and len(sys.argv) > 2:
            act_val = sys.argv[2]
            print(f"Manually setting activity to {act_val}...")
            icon_key = "InACall" if act_val == settings["languages"].get("InACall", "In a call") else "NotInACall"
            post_to_ha(
                settings["ha_url"], 
                settings["ha_token"], 
                settings["activity_entity"], 
                act_val, 
                settings["activity_friendly_name"],
                icon=settings["icons"].get(icon_key)
            )
            return
        else:
            print("Usage: python3 get_teams_status.py [--status <state> | --activity <state>]")
            sys.exit(1)

    print("Microsoft Teams Status Monitor started.")
    
    # Update monitoring status to on
    post_to_ha(
        settings["ha_url"],
        settings["ha_token"],
        settings["monitoring_entity"],
        "on",
        settings["monitoring_friendly_name"],
        icon=settings["icons"].get("Monitoring")
    )

    current_status = None
    current_activity = None
    
    classic_log_path = os.path.expanduser("~/Library/Application Support/Microsoft/Teams/logs.txt")

    try:
        while running:
            # Reload settings dynamically in case they changed
            settings = load_settings()
            
            languages = settings["languages"]
            icons = settings["icons"]
            
            teams_running = is_teams_running()
            
            status = None
            activity = None
            activity_icon = icons.get("NotInACall", "mdi:phone-off")

            if teams_running:
                # Decide version parsing mode
                mode = settings["teams_version"].lower()
                if mode == "auto":
                    # If classic log file exists, check it first
                    if os.path.exists(classic_log_path):
                        mode = "old"
                    else:
                        mode = "new"
                
                if mode == "old" and os.path.exists(classic_log_path):
                    lines = get_last_lines_from_file(classic_log_path)
                    status = parse_classic_status(lines, languages)
                    parsed_act = parse_classic_activity(lines, languages, icons)
                    if parsed_act:
                        activity, activity_icon = parsed_act
                else:
                    # New Teams mode uses pmset
                    in_call = is_teams_in_call_pmset()
                    if in_call:
                        status = languages.get("InAMeeting", "In a meeting")
                        activity = languages.get("InACall", "In a call")
                        activity_icon = icons.get("InACall", "mdi:phone-in-talk-outline")
                    else:
                        status = languages.get("Available", "Available")
                        activity = languages.get("NotInACall", "Not in a call")
                        activity_icon = icons.get("NotInACall", "mdi:phone-off")
            else:
                # Teams is not running
                status = languages.get("Offline", "Offline")
                activity = languages.get("NotInACall", "Not in a call")
                activity_icon = icons.get("NotInACall", "mdi:phone-off")

            # Post updates if state changed
            if status and status != current_status:
                print(f"Status changed to: {status}")
                success = post_to_ha(
                    settings["ha_url"], 
                    settings["ha_token"], 
                    settings["status_entity"], 
                    status, 
                    settings["status_friendly_name"],
                    icon="mdi:microsoft-teams"
                )
                if success or current_status is None:
                    current_status = status
            
            if activity and activity != current_activity:
                print(f"Activity changed to: {activity}")
                success = post_to_ha(
                    settings["ha_url"], 
                    settings["ha_token"], 
                    settings["activity_entity"], 
                    activity, 
                    settings["activity_friendly_name"],
                    icon=activity_icon
                )
                if success or current_activity is None:
                    current_activity = activity
            
            # Wait for next check
            time.sleep(settings["check_interval"])
            
    finally:
        # Update monitoring status to off on exit
        print("Stopping monitor...")
        post_to_ha(
            settings["ha_url"],
            settings["ha_token"],
            settings["monitoring_entity"],
            "off",
            settings["monitoring_friendly_name"],
            icon=settings["icons"].get("Monitoring")
        )

if __name__ == "__main__":
    main()
