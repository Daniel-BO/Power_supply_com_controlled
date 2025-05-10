
import serial
import serial.tools.list_ports
import csv
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import pandas as pd

# === SCPI Commands in HEX ===
COMMANDS = {
    'output_on': bytes.fromhex('3A4F555450204F4E0A0A0A0A'),
    'output_off': bytes.fromhex('3A4F555450204F46460A0A'),
    'meas_voltage': bytes.fromhex('3A4D4541533A564F4C543F0A0A0A0A'),
    'meas_current': bytes.fromhex('3A4D4541533A435552523F0A0A'),
    'meas_power': bytes.fromhex('3A4D4541533A504F573F0A0A0A'),
    'outp_query': bytes.fromhex('3A4F5554503F0A0A0A'),
    'volt_prot_stat': bytes.fromhex('3A564F4C543A50524F543A535441543F0A0A0A0A'),
    'curr_prot_query': bytes.fromhex('3A435552523A50524F543F0A0A0A0A'),
    'oper_status': bytes.fromhex('3A535441543A4F5045523A454E41423F0A0A0A0A'),
}

MEASURE_INTERVAL = 2  # seconds
LOG_FILE = 'power_log.csv'


class PowerSupplyApp:
    def __init__(self, root):
        self.root = root
        self.ser = None
        self.running = False
        self.thread = None
        self.timestamps, self.voltages, self.currents, self.powers = [], [], [], []

        self.voltage_var = tk.StringVar(value="5")
        self.current_var = tk.StringVar(value="1")
        self.protect_var = tk.StringVar(value="6")
        self.port_var = tk.StringVar()
        self.status_text = tk.StringVar(value="Disconnected")

        self.build_gui()
        self.setup_plot()

    def build_gui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="n")

        # Port selector
        ttk.Label(frame, text="Serial Port:").grid(column=0, row=0, sticky="e")
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=15)
        self.port_combo['values'] = self.list_serial_ports()
        self.port_combo.grid(column=1, row=0, pady=2)

        # Voltage/current/protection entries
        ttk.Label(frame, text="Voltage (V):").grid(column=0, row=1, sticky='e')
        ttk.Entry(frame, textvariable=self.voltage_var).grid(column=1, row=1)

        ttk.Label(frame, text="Current (A):").grid(column=0, row=2, sticky='e')
        ttk.Entry(frame, textvariable=self.current_var).grid(column=1, row=2)

        ttk.Label(frame, text="Protection Current (A):").grid(column=0, row=3, sticky='e')
        ttk.Entry(frame, textvariable=self.protect_var).grid(column=1, row=3)

        # Buttons
        ttk.Button(frame, text="Refresh Ports", command=self.refresh_ports).grid(column=0, row=4)
        ttk.Button(frame, text="Connect", command=self.connect_serial).grid(column=1, row=4)
        ttk.Button(frame, text="Apply Settings", command=self.apply_settings).grid(column=0, row=5)
        ttk.Button(frame, text="Output ON", command=self.output_on).grid(column=1, row=5)
        ttk.Button(frame, text="Output OFF", command=self.output_off).grid(column=0, row=6)
        ttk.Button(frame, text="Start Logging", command=self.start_logging).grid(column=1, row=6)
        ttk.Button(frame, text="Stop Logging", command=self.stop_logging).grid(column=0, row=7)
        ttk.Button(frame, text="Export to Excel", command=self.export_to_excel).grid(column=1, row=7)

        # Status queries
        ttk.Label(frame, text="Status Queries:").grid(column=0, row=8, pady=(10, 2), sticky='w')
        ttk.Button(frame, text="Output Status", command=lambda: self.query_status("outp_query")).grid(column=0, row=9)
        ttk.Button(frame, text="Voltage Prot.", command=lambda: self.query_status("volt_prot_stat")).grid(column=1, row=9)
        ttk.Button(frame, text="Current Prot.", command=lambda: self.query_status("curr_prot_query")).grid(column=0, row=10)
        ttk.Button(frame, text="Oper. Status", command=lambda: self.query_status("oper_status")).grid(column=1, row=10)

        # Status label
        ttk.Label(frame, textvariable=self.status_text, foreground="blue").grid(column=0, row=11, columnspan=2, pady=5)

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Live Voltage, Current, Power")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Values")
        self.ax.grid(True)

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.fig.autofmt_xdate()

        right_frame = ttk.Frame(self.root)
        right_frame.grid(row=0, column=1, padx=10, pady=10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        toolbar.update()

        self.line_v, = self.ax.plot([], [], label="Voltage (V)", color='blue')
        self.line_c, = self.ax.plot([], [], label="Current (A)", color='green')
        self.line_p, = self.ax.plot([], [], label="Power (W)", color='red')
        self.ax.legend()

    def list_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def refresh_ports(self):
        ports = self.list_serial_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])

    def connect_serial(self):
        port = self.port_var.get()
        try:
            self.ser = serial.Serial(port, 9600, timeout=1)
            self.status_text.set(f"Connected to {port}")
        except Exception as e:
            self.status_text.set(f"Connection failed: {e}")

    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            self.ser.write(cmd)
            time.sleep(0.1)
            return self.ser.read_all().decode(errors='ignore').strip()
        else:
            self.status_text.set("Serial not connected.")
            return ""

    def apply_settings(self):
        voltage = self.voltage_var.get()
        current = self.current_var.get()
        protection = self.protect_var.get()

        self.ser.write(f":APPL {voltage},{current}".encode())
        time.sleep(0.1)
        self.ser.write(f":CURR:PROT {protection}".encode())
        self.status_text.set("Settings applied.")

    def output_on(self):
        self.send_command(COMMANDS['output_on'])
        self.status_text.set("Output turned ON.")

    def output_off(self):
        self.send_command(COMMANDS['output_off'])
        self.status_text.set("Output turned OFF.")

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
                timestamp = datetime.now()
                voltage = self.send_command(COMMANDS['meas_voltage'])
                current = self.send_command(COMMANDS['meas_current'])
                power = self.send_command(COMMANDS['meas_power'])

                self.timestamps.append(timestamp)
                self.voltages.append(float(voltage or 0))
                self.currents.append(float(current or 0))
                self.powers.append(float(power or 0))

                with open(LOG_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp.strftime('%Y-%m-%d %H:%M:%S'), voltage, current, power])

                self.update_plot()
                time.sleep(MEASURE_INTERVAL)
            except Exception as e:
                self.status_text.set(f"Logging error: {e}")
                self.running = False

    def export_to_excel(self):
        try:
            df = pd.read_csv(LOG_FILE)
            filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if filepath:
                df.to_excel(filepath, index=False)
                messagebox.showinfo("Export Successful", f"Data exported to:{filepath}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def query_status(self, key):
        response = self.send_command(COMMANDS[key])
        self.status_text.set(f"{key.replace('_', ' ').capitalize()}: {response}")


# Run the app
root = tk.Tk()
root.title("SCPI Power Supply Logger")
app = PowerSupplyApp(root)
root.mainloop()
