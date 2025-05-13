from power_control_HCP1020A import  PowerSupply

ps = PowerSupply("config_HCP1020A.json")

# Comandos fijos

print("[RX]", ps.send_command("IDN"))

# Activar salida
ps.send_command("OUTP_ON")

#Establecer voltaje y corriente (ej. 5V, 1A)
ps.send_command(":APPL {},{}", 1, 1)

# # Establecer solo voltaje sin activar salida
# ps.send_command(":VOLT {}", 3)

# # Establecer protección de corriente a 6A
# ps.send_command(":CURR:PROT {}", 6)

# Leer voltaje

print("[RX]", ps.send_command("VOLT_Q"))
print("[RX]", ps.send_command("MEAS_CURR"))
print("[RX]", ps.send_command("MEAS_POW"))

# desactiva salida
ps.send_command("OUTP_OFF")

ps.close()
