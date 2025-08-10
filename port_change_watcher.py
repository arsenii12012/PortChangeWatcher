Port Change Watcher
-------------------
Monitors open ports on a target host and sends notifications via your own Telegram bot.

Author: Arsenii12012
License: MIT


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
        with socket.socket() as s:
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
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def parse_ports(ports_str):
    ports = []
    for part in ports_str.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(part))
    return ports

def main():
    print("=== Port Change Watcher ===")
    host = input("Enter target host (IP or domain): ").strip()
    ports_str = input("Enter ports to scan (e.g. 22,80,443 or 1-1024): ").strip()
    interval_str = input("Enter scan interval in seconds (default 60): ").strip()
    interval = int(interval_str) if interval_str.isdigit() else 60

    ports = parse_ports(ports_str)
    print(f"Monitoring {host} ports: {ports}")
    print(f"Scan interval: {interval} seconds")

    state = load_state()
    prev_open = state.get(host, [])

    while True:
        open_ports = []
        for p in ports:
            if scan_port(host, p):
                open_ports.append(p)

        new_ports = [p for p in open_ports if p not in prev_open]
        closed_ports = [p for p in prev_open if p not in open_ports]

        if new_ports or closed_ports:
            msg = f"Port changes on {host}:\n"
            if new_ports:
                msg += f"New open ports: {new_ports}\n"
            if closed_ports:
                msg += f"Closed ports: {closed_ports}\n"
            print(msg)
            send_telegram_message(msg)
            prev_open = open_ports
            state[host] = prev_open
            save_state(state)

        time.sleep(interval)

if __name__ == "__main__":
    main()
