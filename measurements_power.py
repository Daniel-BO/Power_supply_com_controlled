import serial
import csv
import time
from datetime import datetime

# === Configuration ===
SERIAL_PORT = '/dev/ttyUSB0'         # Change for your OS, e.g., '/dev/ttyUSB0'
BAUD_RATE = 9600
TIMEOUT = 1                  # seconds
LOG_FILE = 'power_supply_log.csv'
MEASURE_INTERVAL = 1         # seconds between measurements

# === SCPI Commands in hex ===
COMMANDS = {
    'idn': bytes.fromhex('2A49444E3F0A'),
    'set_output_on': bytes.fromhex('3A4F555450204F4E0A0A0A0A'),
    'set_output_off': bytes.fromhex('3A4F555450204F46460A0A'),
    'meas_voltage': bytes.fromhex('3A4D4541533A564F4C543F0A0A0A0A'),
    'meas_current': bytes.fromhex('3A4D4541533A435552523F0A0A'),
    'meas_power': bytes.fromhex('3A4D4541533A504F573F0A0A0A'),
}

def initialize_serial(port, baudrate, timeout):
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Error: {e}")
        return None

def send_command(ser, cmd_bytes):
    ser.write(cmd_bytes)
    time.sleep(0.1)  # Short wait for device to respond
    response = ser.read_all().decode(errors='ignore').strip()
    return response

def apply_voltage_current(ser, voltage, current):
    cmd_str = f":APPL {voltage},{current}\n\n"
    cmd_bytes = cmd_str.encode()
    ser.write(cmd_bytes)
    time.sleep(0.1)

def log_to_csv(timestamp, voltage, current, power):
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, voltage, current, power])

def main():
    ser = initialize_serial(SERIAL_PORT, BAUD_RATE, TIMEOUT)
    if not ser:
        return

    # Create CSV header
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Voltage (V)', 'Current (A)', 'Power (W)'])

    # Example: Set voltage and current, turn on output
    apply_voltage_current(ser, 4, 5)  # Set 5V, 1A
    send_command(ser, COMMANDS['set_output_on'])

    try:
        while True:
            timestamp = datetime.now().isoformat()

            voltage = send_command(ser, COMMANDS['meas_voltage'])
            current = send_command(ser, COMMANDS['meas_current'])
            power = send_command(ser, COMMANDS['meas_power'])

            print(f"[{timestamp}] V: {voltage}, A: {current}, W: {power}")
            log_to_csv(timestamp, voltage, current, power)

            time.sleep(MEASURE_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user.")
        send_command(ser, COMMANDS['set_output_off'])
    finally:
        ser.close()

if __name__ == '__main__':
    main()
