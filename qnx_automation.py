#!/usr/bin/env python3
"""
QNX Automation Tool
Connects to QNX device via ADB and Telnet, executes shell commands.
"""

import subprocess
import sys
import time
import argparse
from typing import Optional, List


class QNXAutomation:
    def __init__(self, telnet_ip: str = "192.168.118.2", 
                 telnet_port: int = 23,
                 username: str = "root",
                 password: str = "mQx@r7PLv#Nf"):
        self.telnet_ip = telnet_ip
        self.telnet_port = telnet_port
        self.username = username
        self.password = password
        self.telnet_process: Optional[subprocess.Popen] = None
    
    def adb_root(self) -> bool:
        """Execute 'adb root' command"""
        print("[*] Executing: adb root")
        try:
            result = subprocess.run(
                ["adb", "root"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 or "restarting" in result.stdout.lower():
                print("[+] adb root successful")
                time.sleep(2)  # Wait for adbd to restart
                return True
            else:
                print(f"[-] adb root failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("[-] adb root timed out")
            return False
        except FileNotFoundError:
            print("[-] adb not found. Please ensure Android SDK platform-tools is installed.")
            return False
    
    def adb_shell(self) -> bool:
        """Start adb shell session (prerequisite for telnet)"""
        print("[*] Starting adb shell...")
        # We don't keep this open, just ensure connectivity
        try:
            result = subprocess.run(
                ["adb", "shell", "echo", "connectivity_check"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("[+] adb shell connectivity OK")
                return True
            else:
                print(f"[-] adb shell failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"[-] adb shell error: {e}")
            return False
    
    def connect_telnet(self) -> bool:
        """Connect to QNX via telnet using busybox"""
        print(f"[*] Connecting to telnet {self.telnet_ip}:{self.telnet_port}")
        
        try:
            # Start telnet process via adb shell
            cmd = f"adb shell busybox telnet {self.telnet_ip} {self.telnet_port}"
            self.telnet_process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            time.sleep(2)  # Wait for connection
            
            # Send username
            if self.telnet_process.stdin:
                self.telnet_process.stdin.write(self.username + "\n")
                self.telnet_process.stdin.flush()
            
            time.sleep(1)
            
            # Send password
            if self.telnet_process.stdin:
                self.telnet_process.stdin.write(self.password + "\n")
                self.telnet_process.stdin.flush()
            
            time.sleep(2)
            
            print("[+] Telnet connection established")
            return True
            
        except Exception as e:
            print(f"[-] Telnet connection failed: {e}")
            return False
    
    def execute_command(self, command: str) -> str:
        """Execute a command on the QNX device"""
        if not self.telnet_process or not self.telnet_process.stdin:
            return "Error: Not connected to QNX"
        
        print(f"[*] Executing: {command}")
        
        try:
            self.telnet_process.stdin.write(command + "\n")
            self.telnet_process.stdin.flush()
            
            time.sleep(1)  # Wait for command execution
            
            # Read output (non-blocking approach would be better for production)
            output = ""
            if self.telnet_process.stdout:
                # Try to read available output
                import select
                ready, _, _ = select.select([self.telnet_process.stdout], [], [], 2)
                if ready:
                    output = self.telnet_process.stdout.readline()
            
            return output if output else "Command sent (output may be buffered)"
            
        except Exception as e:
            return f"Error executing command: {e}"
    
    def disconnect(self):
        """Close telnet connection"""
        if self.telnet_process:
            print("[*] Disconnecting...")
            if self.telnet_process.stdin:
                try:
                    self.telnet_process.stdin.write("exit\n")
                    self.telnet_process.stdin.flush()
                except:
                    pass
            self.telnet_process.terminate()
            self.telnet_process.wait(timeout=5)
            self.telnet_process = None
            print("[+] Disconnected")
    
    def run_commands(self, commands: List[str]) -> List[dict]:
        """Run a list of commands and collect results"""
        results = []
        
        if not self.connect_telnet():
            return [{"error": "Failed to connect to QNX"}]
        
        for cmd in commands:
            output = self.execute_command(cmd)
            results.append({
                "command": cmd,
                "output": output
            })
        
        self.disconnect()
        return results


def main():
    parser = argparse.ArgumentParser(
        description="QNX Automation Tool - Connect and execute commands on QNX devices"
    )
    parser.add_argument(
        "--ip", 
        default="192.168.118.2",
        help="QNX device IP address (default: 192.168.118.2)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=23,
        help="Telnet port (default: 23)"
    )
    parser.add_argument(
        "--username", 
        default="root",
        help="Username (default: root)"
    )
    parser.add_argument(
        "--password", 
        default="mQx@r7PLv#Nf",
        help="Password (default: mQx@r7PLv#Nf)"
    )
    parser.add_argument(
        "--command", "-c",
        action="append",
        help="Command to execute (can be specified multiple times)"
    )
    parser.add_argument(
        "--script", "-s",
        help="File containing commands to execute (one per line)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode"
    )
    
    args = parser.parse_args()
    
    # Initialize automation tool
    qnx = QNXAutomation(
        telnet_ip=args.ip,
        telnet_port=args.port,
        username=args.username,
        password=args.password
    )
    
    # Step 1: adb root
    print("=" * 60)
    print("QNX Automation Tool")
    print("=" * 60)
    
    if not qnx.adb_root():
        print("[-] Failed to execute adb root. Exiting.")
        sys.exit(1)
    
    # Step 2: Verify adb shell connectivity
    if not qnx.adb_shell():
        print("[-] adb shell connectivity check failed. Exiting.")
        sys.exit(1)
    
    # Collect commands
    commands = []
    
    if args.command:
        commands.extend(args.command)
    
    if args.script:
        try:
            with open(args.script, 'r') as f:
                commands.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
        except FileNotFoundError:
            print(f"[-] Script file not found: {args.script}")
            sys.exit(1)
    
    if args.interactive or not commands:
        print("\n[!] Interactive mode or no commands specified.")
        print("Commands will be executed after telnet connection.")
        if not args.interactive and not commands:
            print("Enter commands below (empty line to finish):")
            while True:
                cmd = input("> ")
                if not cmd:
                    break
                commands.append(cmd)
    
    # Execute commands
    if commands:
        print(f"\n[*] Executing {len(commands)} command(s)...")
        results = qnx.run_commands(commands)
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        for result in results:
            if "error" in result:
                print(f"ERROR: {result['error']}")
            else:
                print(f"\nCommand: {result['command']}")
                print(f"Output: {result['output']}")
    else:
        # Just test connection
        print("\n[*] Testing connection only...")
        if qnx.connect_telnet():
            print("[+] Connection successful!")
            qnx.disconnect()
        else:
            print("[-] Connection failed!")
            sys.exit(1)
    
    print("\n[+] Done!")


if __name__ == "__main__":
    main()
