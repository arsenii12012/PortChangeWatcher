#!/usr/bin/env python3

#Port Change Watcher
#-------------------
#Monitors a target host for new open ports and sends alerts to Telegram.

#Author: Arsenii12012

#License: MIT

import socket
import argparse
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor

# Your Telegram bot token and chat ID here
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_ID"

def scan_port(host, port, timeout=1):
    """Check if a port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def load_state(file_path):
    """Load previous scan results from JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_state(file_path, state):
    """Save scan results to JSON file."""
    with open(file_path, "w") as f:
        json.dump(state, f, indent=2)

def send_telegram_message(token, chat_id, text):
    """Send a Telegram message."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": text})
        if not response.ok:
            print(f"[!] Telegram API error: {response.text}")
    except Exception as e:
        print(f"[!] Failed to send Telegram message: {e}")

def scan_host(host, ports):
    """Scan multiple ports in parallel."""
    results = {}
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(scan_port, host, p): p for p in ports}
        for future in futures:
            port = futures[future]
            try:
                results[port] = future.result()
            except Exception:
                results[port] = False
    return results

def main():
    parser = argparse.ArgumentParser(description="Port Change Watcher")
    parser.add_argument("host", help="Target host to scan")
    parser.add_argument("--ports", default="1-1024",
                        help="Ports to scan (e.g., 22,80,443 or 1-65535)")
    parser.add_argument("--state-file", default="port_state.json",
                        help="File to store scan state")
    parser.add_argument("--interval", type=int, default=60,
                        help="Interval between scans in seconds")
    args = parser.parse_args()

    # Parse ports list
    ports = []
    for part in args.ports.split(","):
        if "-" in part:
            start, end = part.split("-")
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(part))

    prev_state = load_state(args.state_file)
    print(f"[*] Starting scan on {args.host}, monitoring {len(ports)} ports every {args.interval}s")

    while True:
        scan_results = scan_host(args.host, ports)
        open_ports = [p for p, is_open in scan_results.items() if is_open]

        prev_open_ports = prev_state.get(args.host, [])
        new_ports = [p for p in open_ports if p not in prev_open_ports]
        closed_ports = [p for p in prev_open_ports if p not in open_ports]

        if new_ports or closed_ports:
            msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Host: {args.host}\n"
            if new_ports:
                msg += f"  [+] New open ports: {new_ports}\n"
            if closed_ports:
                msg += f"  [-] Closed ports: {closed_ports}\n"
            print(msg.strip())

            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

            prev_state[args.host] = open_ports
            save_state(args.state_file, prev_state)

        time.sleep(args.interval)

if __name__ == "__main__":
    main()
