#!/usr/bin/env python3
"""
MAC Address Spoofer
A tool to change/spoof MAC addresses on network interfaces
Requires administrator/root privileges
"""

import subprocess
import re
import random
import argparse
import sys
import platform

class MACSpoofer:
    def __init__(self):
        self.os_type = platform.system()

    def get_current_mac(self, interface):
        """Get the current MAC address of an interface"""
        try:
            if self.os_type == "Windows":
                result = subprocess.check_output(f"getmac /v /fo list", shell=True).decode()
                # Parse Windows output to find MAC for interface
                lines = result.split('\n')
                for i, line in enumerate(lines):
                    if interface.lower() in line.lower():
                        # Look for MAC in nearby lines
                        for j in range(i, min(i+10, len(lines))):
                            mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", lines[j])
                            if mac_match:
                                return mac_match.group(0)
            else:
                result = subprocess.check_output(f"ifconfig {interface}", shell=True).decode()
                mac_search = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result)
                if mac_search:
                    return mac_search.group(0)
        except Exception as e:
            print(f"[-] Error getting MAC address: {e}")
        return None

    def generate_random_mac(self):
        """Generate a random MAC address"""
        # First octet: set locally administered bit, clear multicast bit
        first_octet = random.randint(0, 255) & 0xFE | 0x02
        mac = [first_octet] + [random.randint(0, 255) for _ in range(5)]
        return ':'.join(f"{octet:02x}" for octet in mac)

    def change_mac_windows(self, interface, new_mac):
        """Change MAC address on Windows"""
        try:
            # Remove colons/dashes from MAC
            new_mac_clean = new_mac.replace(':', '').replace('-', '')

            # Get network adapter using PowerShell
            cmd = f'powershell "Get-NetAdapter | Where-Object {{$_.Name -like \'*{interface}*\'}} | Select-Object -First 1 | Format-List Name,MacAddress,InterfaceDescription"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            # Use registry to change MAC (alternative method)
            print(f"[*] Attempting to change MAC address to {new_mac}")
            print(f"[!] On Windows, you may need to:")
            print(f"    1. Open Device Manager")
            print(f"    2. Find your network adapter")
            print(f"    3. Properties > Advanced > Network Address")
            print(f"    4. Set value to: {new_mac_clean}")
            print(f"    5. Disable and re-enable the adapter")

            return True
        except Exception as e:
            print(f"[-] Error changing MAC: {e}")
            return False

    def change_mac_linux(self, interface, new_mac):
        """Change MAC address on Linux"""
        try:
            subprocess.run(["sudo", "ifconfig", interface, "down"], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "hw", "ether", new_mac], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "up"], check=True)
            print(f"[+] MAC address changed to {new_mac}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[-] Error changing MAC: {e}")
            return False

    def change_mac(self, interface, new_mac=None):
        """Change MAC address for given interface"""
        if not new_mac:
            new_mac = self.generate_random_mac()

        print(f"[*] Target interface: {interface}")
        current_mac = self.get_current_mac(interface)
        if current_mac:
            print(f"[*] Current MAC: {current_mac}")

        print(f"[*] New MAC: {new_mac}")

        if self.os_type == "Windows":
            return self.change_mac_windows(interface, new_mac)
        elif self.os_type == "Linux":
            return self.change_mac_linux(interface, new_mac)
        elif self.os_type == "Darwin":  # macOS
            return self.change_mac_linux(interface, new_mac)
        else:
            print(f"[-] Unsupported OS: {self.os_type}")
            return False

    def list_interfaces(self):
        """List all network interfaces"""
        try:
            if self.os_type == "Windows":
                result = subprocess.check_output("netsh interface show interface", shell=True).decode()
                print(result)
            else:
                result = subprocess.check_output("ifconfig -a", shell=True).decode()
                print(result)
        except Exception as e:
            print(f"[-] Error listing interfaces: {e}")

def main():
    parser = argparse.ArgumentParser(description="MAC Address Spoofer")
    parser.add_argument("-i", "--interface", help="Network interface to modify")
    parser.add_argument("-m", "--mac", help="New MAC address (random if not specified)")
    parser.add_argument("-l", "--list", action="store_true", help="List network interfaces")
    parser.add_argument("-r", "--random", action="store_true", help="Generate random MAC")

    args = parser.parse_args()

    spoofer = MACSpoofer()

    if args.list:
        print("[*] Network Interfaces:")
        spoofer.list_interfaces()
        return

    if not args.interface:
        print("[-] Please specify an interface with -i")
        print("[*] Use -l to list available interfaces")
        return

    if args.random or not args.mac:
        new_mac = spoofer.generate_random_mac()
        spoofer.change_mac(args.interface, new_mac)
    else:
        spoofer.change_mac(args.interface, args.mac)

if __name__ == "__main__":
    main()
