 #Port Change Watcher
#Monitors open ports on a target host and sends notifications via your own Telegram bot. 

#Author: Arsenii12012
#License: MIT


import socket
import time
import json
import requests

# === INSERT YOUR TELEGRAM BOT TOKEN AND CHAT ID BELOW ===
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
# ========================================================

STATE_FILE = "port_state.json"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] Failed to send Telegram message: {e}")

def scan_port(host, port, timeout=1):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[!] Failed to save state: {e}")

def parse_ports(ports_str):
    ports = []
    for part in ports_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    start, end = end, start
                ports.extend(range(start, end + 1))
            except ValueError:
                print(f"[!] Invalid port range: {part}")
        else:
            try:
                ports.append(int(part))
            except ValueError:
                print(f"[!] Invalid port: {part}")
    return ports

def main():
    print("=== Port Change Watcher ===")

