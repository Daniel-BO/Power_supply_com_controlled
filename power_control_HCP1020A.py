import json
import serial
import time
from datetime import datetime

class PowerSupply:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.serial_port = self.connect_serial()
        self.fixed_commands = {
            "IDN": bytes.fromhex("2A49444E3F0A"),
            "MEAS_CURR": bytes.fromhex("3A4D4541533A435552523F0A0A"),
            "CURR_PROT_Q": bytes.fromhex("3A435552523A50524F543F0A0A0A0A"),
            "VOLT_PROT_STAT": bytes.fromhex("3A564F4C543A50524F543A535441543F0A0A0A0A"),
            "VOLT_Q": bytes.fromhex("3A564F4C543F0A0A0A0A"),
            "MEAS_POW": bytes.fromhex("3A4D4541533A504F573F0A0A0A"),
            "MEAS": bytes.fromhex("3A4D4541533F0A0A"),
            "OUTP_ON": bytes.fromhex("3A4F555450204F4E0A0A0A0A"),
            "OUTP_OFF": bytes.fromhex("3A4F555450204F46460A0A"),
            "OUTP_Q": bytes.fromhex("3A4F5554503F0A0A0A"),
            "STAT_OPER_ENAB_Q": bytes.fromhex("3A535441543A4F5045523A454E41423F0A0A0A0A")
        }

    def load_config(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def connect_serial(self):
        try:
            return serial.Serial(
                port=self.config["port"],
                baudrate=self.config["baudrate"],
                parity=self.config["parity"],
                stopbits=self.config["stopbits"],
                bytesize=self.config["bytesize"],
                timeout=self.config["timeout"]
            )
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")
            return None


    def send_command(self, name_or_command, *args):
        if name_or_command in self.fixed_commands:
            hex_str = self.fixed_commands[name_or_command]
            self.serial_port.write(hex_str)
            time.sleep(0.1)  # Short wait for device to respond
            response = self.serial_port.read_all().decode(errors='ignore').strip()  
        else:
            command_str = name_or_command.format(*args) + '\n' + '\n'
            byte_data = command_str.encode()
            self.serial_port.write(byte_data)
            time.sleep(0.1)  # Short wait for device to respond
            response = self.serial_port.read_all().decode(errors='ignore').strip() 
        return response

    def close(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
