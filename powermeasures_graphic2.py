import serial
import csv
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# === Config ===
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600
TIMEOUT = 1
LOG_FILE = 'power_log.csv'
MEASURE_INTERVAL = 2  # seconds

COMMANDS = {
    'output_on': bytes.fromhex('3A4F555450204F4E0A0A0A0A'),
    'output_off': bytes.fromhex('3A4F555450204F46460A0A'),
    'meas_voltage': bytes.fromhex('3A4D4541533A564F4C543F0A0A0A0A'),
    'meas_current': bytes.fromhex('3A4D4541533A435552523F0A0A'),
    'meas_power': bytes.fromhex('3A4D4541533A504F573F0A0A0A'),
}

class PowerSupplyApp:
    def __init__(self, root):
        self.ser = None
        self.running = False
        self.thread = None
        self.timestamps = []
        self.voltages = []
        self.currents = []
        self.powers = []

        self.root = root
        self.root.title("Power Supply Logger with Live Graph")

        self.voltage_var = tk.StringVar(value="5")
        self.current_var = tk.StringVar(value="1")
        self.protect_var = tk.StringVar(value="6")

        self.build_gui()
        self.setup_plot()

    def build_gui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="n")

        # Input fields
        ttk.Label(frame, text="Voltage (V):").grid(column=0, row=0, sticky='e')
        ttk.Entry(frame, textvariable=self.voltage_var).grid(column=1, row=0)
        ttk.Label(frame, text="Current (A):").grid(column=0, row=1, sticky='e')
        ttk.Entry(frame, textvariable=self.current_var).grid(column=1, row=1)
        ttk.Label(frame, text="Protection Current (A):").grid(column=0, row=2, sticky='e')
        ttk.Entry(frame, textvariable=self.protect_var).grid(column=1, row=2)

        # Buttons
        ttk.Button(frame, text="Connect", command=self.connect_serial).grid(column=0, row=3)
        ttk.Button(frame, text="Apply Settings", command=self.apply_settings).grid(column=1, row=3)
        ttk.Button(frame, text="Output ON", command=self.output_on).grid(column=0, row=4)
        ttk.Button(frame, text="Output OFF", command=self.output_off).grid(column=1, row=4)
        ttk.Button(frame, text="Start Logging", command=self.start_logging).grid(column=0, row=5)
        ttk.Button(frame, text="Stop Logging", command=self.stop_logging).grid(column=1, row=5)

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Live Voltage, Current, Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Values")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=1)
        self.line_v, = self.ax.plot([], [], label="Voltage (V)", color='blue')
        self.line_c, = self.ax.plot([], [], label="Current (A)", color='green')
        self.line_p, = self.ax.plot([], [], label="Power (W)", color='red')
        self.ax.legend()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
            print("Connected to serial.")
        except serial.SerialException as e:
            print(f"Serial error: {e}")

    def send_command(self, cmd):
        if not self.ser:
            print("Serial not connected.")
            return ""
        self.ser.write(cmd)
        time.sleep(0.1)
        return self.ser.read_all().decode(errors='ignore').strip()

    def apply_settings(self):
        voltage = self.voltage_var.get()
        current = self.current_var.get()
        prot = self.protect_var.get()

        apply_cmd = f":APPL {voltage},{current}\n\n".encode()
        protect_cmd = f":CURR:PROT {prot}\n\n".encode()
        self.ser.write(apply_cmd)
        time.sleep(0.1)
        self.ser.write(protect_cmd)
        print("Settings applied.")

    def output_on(self):
        self.send_command(COMMANDS['output_on'])

    def output_off(self):
        self.send_command(COMMANDS['output_off'])

    def start_logging(self):
        if not self.running:
            self.running = True
            with open(LOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Voltage (V)", "Current (A)", "Power (W)"])
            self.thread = threading.Thread(target=self.measure_loop, daemon=True)
            self.thread.start()

    def stop_logging(self):
        self.running = False

    def update_plot(self):
        self.line_v.set_data(self.timestamps, self.voltages)
        self.line_c.set_data(self.timestamps, self.currents)
        self.line_p.set_data(self.timestamps, self.powers)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def measure_loop(self):
        while self.running:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                voltage = self.send_command(COMMANDS['meas_voltage'])
                current = self.send_command(COMMANDS['meas_current'])
                power = self.send_command(COMMANDS['meas_power'])

                self.timestamps.append(timestamp)
                self.voltages.append(float(voltage or 0))
                self.currents.append(float(current or 0))
                self.powers.append(float(power or 0))

                with open(LOG_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, voltage, current, power])

                self.update_plot()
                time.sleep(MEASURE_INTERVAL)
            except Exception as e:
                print(f"Logging error: {e}")
                self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = PowerSupplyApp(root)
    root.mainloop()
