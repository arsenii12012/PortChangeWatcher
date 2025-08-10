#!/usr/bin/env python3

"""
Port Change Watcher
-------------------
Monitors a target host for new open ports and sends alerts to Telegram.

Author: Arsenii12012
License: MIT
"""

import socket
import argparse
import json
import time
import requests
import signal
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration - should be moved to config file or environment variables
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_ID"
DEFAULT_TIMEOUT = 1.0
MAX_WORKERS = 100
DEFAULT_INTERVAL = 60

def scan_port(host, port, timeout=DEFAULT_TIMEOUT):
    """Check if a port is open with proper error handling."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return (port, s.connect_ex((host, port)) == 0)
    except socket.error as e:
        return (port, False)
    except Exception as e:
        print(f"[!] Unexpected error scanning port {port}: {e}")
        return (port, False)

def load_state(file_path):
    """Load previous scan results from JSON file with validation."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid state file format")
            return data
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[!] Error loading state file: {e}")
        return {}

def save_state(file_path, state):
    """Save scan results to JSON file with atomic write."""
    try:
        temp_file = file_path + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, file_path)
    except Exception as e:
        print(f"[!] Failed to save state: {e}")

def send_telegram_message(token, chat_id, text):
    """Send a Telegram message with retry logic."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[!] Telegram API error: {e}")
        return False

def scan_host(host, ports):
    """Scan multiple ports in parallel with improved error handling."""
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scan_port, host, p): p for p in ports}
        for future in as_completed(futures):
            try:
                port, status = future.result()
                results[port] = status
            except Exception as e:
                print(f"[!] Error processing port scan: {e}")
    return results

def parse_ports(port_spec):
    """Parse port specification string into list of ports."""
    ports = set()
    for part in port_spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end or start < 1 or end > 65535:
                    raise ValueError
                ports.update(range(start, end + 1))
            except ValueError:
                print(f"[!] Invalid port range: {part}")
        else:
            try:
                port = int(part)
                if port < 1 or port > 65535:
                    raise ValueError
                ports.add(port)
            except ValueError:
                print(f"[!] Invalid port number: {part}")
    return sorted(ports)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n[!] Received interrupt signal. Shutting down...")
    exit(0)

def main():
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(
        description="Monitor network ports for changes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("host", help="Target host to scan")
    parser.add_argument("--ports", default="1-1024",
                       help="Ports to scan (e.g., '22,80,443' or '1-1000')")
    parser.add_argument("--state-file", default="port_state.json",
                       help="File to store scan state")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                       help="Interval between scans in seconds")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                       help="Port connection timeout in seconds")
    args = parser.parse_args()

    # Parse and validate ports
    ports = parse_ports(args.ports)
    if not ports:
        print("[!] No valid ports specified")
        return 1

    # Load initial state
    prev_state = load_state(args.state_file)
    print(f"[*] Starting scan on {args.host}, monitoring {len(ports)} ports")
    print(f"[*] Scan interval: {args.interval}s, Timeout: {args.timeout}s")

    while True:
        start_time = time.time()
        
        try:
            scan_results = scan_host(args.host, ports)
            open_ports = [p for p, is_open in scan_results.items() if is_open]

            prev_open_ports = prev_state.get(args.host, [])
            new_ports = [p for p in open_ports if p not in prev_open_ports]
            closed_ports = [p for p in prev_open_ports if p not in open_ports]

            if new_ports or closed_ports:
                msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Host: {args.host}\n"
                if new_ports:
                    msg += f"  [+] New open ports: {sorted(new_ports)}\n"
                if closed_ports:
                    msg += f"  [-] Closed ports: {sorted(closed_ports)}\n"
                print(msg.strip())
                
                # Try to send Telegram message up to 3 times
                for attempt in range(3):
                    if send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg):
                        break
                    if attempt < 2:
                        time.sleep(5)

                prev_state[args.host] = open_ports
                save_state(args.state_file, prev_state)

        except Exception as e:
            print(f"[!] Scan error: {e}")

        # Calculate sleep time accounting for scan duration
        elapsed = time.time() - start_time
        sleep_time = max(0, args.interval - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
