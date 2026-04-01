#!/usr/bin/env python3
"""
QNX Automation Tool
Connects to QNX device via ADB and Telnet, executes shell commands.
Supports interactive mode with real-time output.
"""

import subprocess
import sys
import time
import argparse
import select
import os
from typing import Optional, List


class QNXAutomation:
    def __init__(self, telnet_ip: str = "192.168.118.2", 
                 telnet_port: int = 23,
                 username: str = "root",
                 password: str = "mQx@r7PLv#Nf",
                 verbose: bool = False):
        self.telnet_ip = telnet_ip
        self.telnet_port = telnet_port
        self.username = username
        self.password = password
        self.verbose = verbose
        self.telnet_process: Optional[subprocess.Popen] = None
        self.adb_started = False
    
    def start_adb_server(self) -> bool:
        """Start ADB server if not running"""
        print("[*] Checking ADB server status...")
        try:
            # Check if server is running
            result = subprocess.run(
                ["adb", "start-server"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "starting" in result.stdout.lower() or result.returncode == 0:
                print("[+] ADB server started/running")
                time.sleep(1)
                return True
            else:
                print(f"[-] ADB server issue: {result.stderr}")
                return False
        except Exception as e:
            print(f"[-] ADB server error: {e}")
            return False
    
    def check_adb_devices(self) -> bool:
        """Check if ADB device is connected"""
        print("[*] Checking ADB devices...")
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.strip().split('\n')
            devices = [l for l in lines[1:] if l.strip() and 'device' in l]
            
            if devices:
                print(f"[+] Found {len(devices)} ADB device(s):")
                for dev in devices:
                    print(f"    - {dev.strip()}")
                return True
            else:
                print("[-] No ADB devices found")
                return False
        except Exception as e:
            print(f"[-] ADB devices check error: {e}")
            return False
    
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
            if result.returncode == 0 or "restarting" in result.stdout.lower() or "already" in result.stdout.lower():
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
    
    def connect_telnet_interactive(self) -> bool:
        """Connect to QNX via telnet using busybox in interactive mode"""
        print(f"[*] Connecting to telnet {self.telnet_ip}:{self.telnet_port}")
        
        try:
            # Start telnet process via adb shell
            cmd = f"adb shell busybox telnet {self.telnet_ip} {self.telnet_port}"
            self.telnet_process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            time.sleep(2)  # Wait for connection prompt
            
            # Send username
            if self.telnet_process.stdin:
                if self.verbose:
                    print(f"[*] Sending username: {self.username}")
                self.telnet_process.stdin.write(self.username + "\n")
                self.telnet_process.stdin.flush()
            
            time.sleep(1)
            
            # Send password
            if self.telnet_process.stdin:
                if self.verbose:
                    print("[*] Sending password...")
                self.telnet_process.stdin.write(self.password + "\n")
                self.telnet_process.stdin.flush()
            
            time.sleep(2)
            
            print("[+] Telnet connection established")
            return True
            
        except Exception as e:
            print(f"[-] Telnet connection failed: {e}")
            return False
    
    def execute_command(self, command: str, timeout: float = 5.0) -> str:
        """Execute a command on the QNX device and wait for output"""
        if not self.telnet_process or not self.telnet_process.stdin:
            return "Error: Not connected to QNX"
        
        if self.verbose:
            print(f"[*] Executing: {command}")
        
        try:
            self.telnet_process.stdin.write(command + "\n")
            self.telnet_process.stdin.flush()
            
            # Read output with timeout
            output = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.telnet_process.stdout:
                    ready, _, _ = select.select([self.telnet_process.stdout], [], [], 0.5)
                    if ready:
                        line = self.telnet_process.stdout.readline()
                        if line:
                            output += line
                        else:
                            break
                    else:
                        # No more data available, check if we got something
                        if output.strip():
                            break
                else:
                    break
            
            return output if output.strip() else "Command executed (no output)"
            
        except Exception as e:
            return f"Error executing command: {e}"
    
    def run_interactive_session(self):
        """Run an interactive telnet session"""
        if not self.connect_telnet_interactive():
            print("[-] Failed to establish telnet connection")
            return
        
        print("\n" + "=" * 60)
        print("INTERACTIVE MODE")
        print("=" * 60)
        print("Enter commands to execute on QNX device")
        print("Type 'exit' or press Ctrl+C to quit\n")
        
        try:
            while True:
                try:
                    cmd = input("qnx> ").strip()
                    
                    if cmd.lower() in ['exit', 'quit', 'q']:
                        break
                    
                    if not cmd:
                        continue
                    
                    output = self.execute_command(cmd)
                    print(output)
                    
                except KeyboardInterrupt:
                    print("\n[!] Interrupted by user")
                    break
                    
        except EOFError:
            pass
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Close telnet connection"""
        if self.telnet_process:
            print("\n[*] Disconnecting...")
            try:
                if self.telnet_process.stdin:
                    self.telnet_process.stdin.write("exit\n")
                    self.telnet_process.stdin.flush()
                    time.sleep(0.5)
            except:
                pass
            
            try:
                self.telnet_process.terminate()
                self.telnet_process.wait(timeout=3)
            except:
                self.telnet_process.kill()
            
            self.telnet_process = None
            print("[+] Disconnected")
    
    def run_commands(self, commands: List[str]) -> List[dict]:
        """Run a list of commands and collect results"""
        results = []
        
        if not self.connect_telnet_interactive():
            return [{"error": "Failed to connect to QNX"}]
        
        for idx, cmd in enumerate(commands, 1):
            print(f"\n[{idx}/{len(commands)}] Running: {cmd}")
            output = self.execute_command(cmd)
            results.append({
                "command": cmd,
                "output": output
            })
            print(output)
        
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
    
    # Execute based on mode
    if args.interactive or not commands:
        print("\n[!] Entering interactive mode...")
        qnx.run_interactive_session()
    else:
        # Batch mode - execute commands
        print(f"\n[*] Executing {len(commands)} command(s)...")
        results = qnx.run_commands(commands)
        
        print("\n" + "=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        success_count = 0
        for result in results:
            if "error" in result:
                print(f"ERROR: {result['error']}")
            else:
                success_count += 1
                print(f"[+] {result['command']}: OK")
        
        print(f"\nTotal: {len(results)} | Success: {success_count} | Failed: {len(results) - success_count}")
    
    print("\n[+] Done!")


if __name__ == "__main__":
    main()
