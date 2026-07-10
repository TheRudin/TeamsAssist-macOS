#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

# Self-install websocket-client dependency if not present
try:
    import websocket
except ImportError:
    print("Installing required library: websocket-client...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"], stdout=subprocess.DEVNULL)
        import websocket
    except Exception as e:
        print(f"Error: Failed to install websocket-client. Please install it manually: pip install websocket-client ({e})")
        sys.exit(1)

def http_post(url, data, is_json=True):
    headers = {}
    if is_json:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data).encode("utf-8")
    else:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        payload = urllib.parse.urlencode(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Try to read error body if available
        try:
            err_body = e.read().decode("utf-8")
            return {"error": e.code, "message": err_body}
        except:
            return {"error": e.code, "message": str(e)}
    except Exception as e:
        return {"error": "connection_failed", "message": str(e)}

def generate_token(ha_url, username, password):
    ha_url = ha_url.rstrip("/")
    login_flow_url = f"{ha_url}/auth/login_flow"
    token_url = f"{ha_url}/auth/token"
    
    # 1. Start login flow
    print("Initiating login flow with Home Assistant...")
    flow_init = http_post(login_flow_url, {
        "client_id": "http://localhost/",
        "redirect_uri": "http://localhost/",
        "handler": ["homeassistant", None]
    })
    
    if "error" in flow_init:
        print(f"Failed to start login flow: {flow_init['message']}")
        return None
        
    flow_id = flow_init.get("flow_id")
    if not flow_id:
        print(f"Error: No flow ID returned from Home Assistant: {flow_init}")
        return None
        
    # 2. Submit username and password
    print("Submitting credentials...")
    step_submit = http_post(f"{login_flow_url}/{flow_id}", {
        "username": username,
        "password": password
    })
    
    if "error" in step_submit:
        print(f"Authentication failed: {step_submit['message']}")
        return None
        
    # Handle multi-factor auth (MFA) step if active
    if step_submit.get("type") == "form" and step_submit.get("step_id") == "mfa":
        print("Home Assistant requested Multi-Factor Authentication (2FA).")
        mfa_code = input("Enter your 2FA verification code: ").strip()
        step_submit = http_post(f"{login_flow_url}/{flow_id}", {
            "code": mfa_code
        })
        if "error" in step_submit:
            print(f"2FA verification failed: {step_submit['message']}")
            return None

    # Verify authorization code is returned
    auth_code = step_submit.get("result")
    if not auth_code or step_submit.get("type") != "create_entry":
        print(f"Authentication did not complete. Response: {step_submit}")
        return None
        
    # 3. Exchange auth code for short-lived access token
    print("Exchanging auth code for access token...")
    token_resp = http_post(token_url, {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": "http://localhost/"
    }, is_json=False)
    
    if "error" in token_resp:
        print(f"Token exchange failed: {token_resp['message']}")
        return None
        
    short_lived_token = token_resp.get("access_token")
    if not short_lived_token:
        print(f"Error: Access token missing in exchange response: {token_resp}")
        return None
        
    # 4. Connect to WebSocket API to generate Long-Lived Access Token
    print("Connecting to WebSocket API to generate Long-Lived Access Token...")
    ws_url = ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
    
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
        
        # Expect auth_required message
        greeting = json.loads(ws.recv())
        if greeting.get("type") != "auth_required":
            print(f"Unexpected WebSocket greeting: {greeting}")
            ws.close()
            return None
            
        # Send authentication payload
        ws.send(json.dumps({
            "type": "auth",
            "access_token": short_lived_token
        }))
        
        auth_result = json.loads(ws.recv())
        if auth_result.get("type") != "auth_ok":
            print(f"WebSocket authentication failed: {auth_result}")
            ws.close()
            return None
            
        # Send long_lived_access_token command (10-year lifespan = 3650 days)
        print("Requesting 10-year Long-Lived Access Token...")
        ws.send(json.dumps({
            "id": 1,
            "type": "auth/long_lived_access_token",
            "client_name": "TeamsAssist-macOS-CLI",
            "lifespan": 3650
        }))
        
        token_result = json.loads(ws.recv())
        ws.close()
        
        if token_result.get("success") and "result" in token_result:
            return token_result["result"]
        else:
            print(f"Failed to generate long-lived token: {token_result}")
            return None
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return None

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 create_token.py <ha_url> <username> <password>")
        print("Example: python3 create_token.py http://homeassistant.local:8123 admin my_secure_password")
        sys.exit(1)
        
    ha_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    token = generate_token(ha_url, username, password)
    if token:
        print("\n" + "="*80)
        print("SUCCESS! Long-Lived Access Token generated successfully:")
        print("="*80)
        print(token)
        print("="*80)
        print("Copy this token and paste it into your Scripts/settings.json file.")
    else:
        print("\nFailed to generate token. Please check your credentials, URL and connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()
