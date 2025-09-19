#!/usr/bin/env python3
"""
Simple keyboard control script for robot via serial communication.
Works on macOS with simpler key detection.
"""

import serial
import time
import sys
import threading

class SimpleKeyboardController:
    def __init__(self, port='/dev/cu.usbserial-0001', baudrate=115200):
        """
        Initialize the keyboard controller for macOS.
        
        Args:
            port (str): Serial port (typically /dev/cu.usbserial-* on macOS)
            baudrate (int): Serial communication speed
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        
    def find_serial_port(self):
        """Try to find available serial ports on macOS."""
        import glob
        
        # Common patterns for ESP32/Arduino on macOS
        patterns = [
            '/dev/cu.usbserial-*',
            '/dev/cu.SLAB_USBtoUART*',
            '/dev/cu.wchusbserial*',
            '/dev/cu.usbmodem*'
        ]
        
        ports = []
        for pattern in patterns:
            ports.extend(glob.glob(pattern))
        
        if ports:
            print(f"Found serial ports: {ports}")
            return ports[0]  # Return first found port
        return None
        
    def connect(self):
        """Establish serial connection to the microcontroller."""
        # Try to auto-detect port if default doesn't work
        if not self.test_port(self.port):
            auto_port = self.find_serial_port()
            if auto_port:
                self.port = auto_port
                print(f"Auto-detected port: {self.port}")
            
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for connection to establish
            print(f"✓ Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"✗ Failed to connect to {self.port}: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure your ESP32/Arduino is connected via USB")
            print("2. Check that no other programs are using the serial port")
            print("3. Try running: ls /dev/cu.* to see available ports")
            return False
    
    def test_port(self, port):
        """Test if a port exists and is accessible."""
        try:
            test_conn = serial.Serial(port, self.baudrate, timeout=0.1)
            test_conn.close()
            return True
        except:
            return False
    
    def disconnect(self):
        """Close the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("✓ Disconnected from serial port")
    
    def send_command(self, command):
        """Send a command to the microcontroller."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command.encode())
                self.serial_conn.flush()
                return True
            except serial.SerialException as e:
                print(f"✗ Error sending command: {e}")
                return False
        return False
    
    def run(self):
        """Main run loop with simple input()."""
        if not self.connect():
            return
        
        try:
            print("\n" + "="*40)
            print("🤖 ROBOT KEYBOARD CONTROL")
            print("="*40)
            print("Controls:")
            print("  w - Forward")
            print("  s - Backward") 
            print("  a - Turn Left")
            print("  d - Turn Right")
            print("  x - Stop")
            print("  q - Quit")
            print("\nType a command and press Enter:")
            print("="*40)
            
            self.running = True
            
            while self.running:
                try:
                    command = input("🎮 Command: ").strip().lower()
                    
                    if command == 'q' or command == 'quit':
                        print("🛑 Stopping robot and quitting...")
                        self.send_command('x')
                        break
                    elif command in ['w', 's', 'a', 'd', 'x']:
                        if self.send_command(command):
                            action_map = {
                                'w': '⬆️  Forward',
                                's': '⬇️  Backward',
                                'a': '⬅️  Turn Left',
                                'd': '➡️  Turn Right',
                                'x': '🛑 Stop'
                            }
                            print(f"✓ Sent: {action_map[command]}")
                        else:
                            print("✗ Failed to send command")
                    elif command == '':
                        continue  # Empty input, just continue
                    else:
                        print(f"✗ Unknown command: '{command}'. Use w/s/a/d/x/q")
                        
                except EOFError:
                    print("\n🛑 EOF received, stopping...")
                    break
                except KeyboardInterrupt:
                    print("\n🛑 Interrupted by user")
                    break
                    
        finally:
            self.send_command('x')  # Stop robot
            self.disconnect()
            self.running = False

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Robot Keyboard Controller')
    parser.add_argument('--port', '-p', default='/dev/cu.usbserial-0001', 
                       help='Serial port (default: auto-detect)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200,
                       help='Baudrate (default: 115200)')
    
    args = parser.parse_args()
    
    controller = SimpleKeyboardController(args.port, args.baudrate)
    controller.run()

if __name__ == '__main__':
    main()
