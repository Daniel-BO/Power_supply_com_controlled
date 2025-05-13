# Power_supply_com_controlled

The main purpose of this repository is to use by scripts the power supply for test duties


RS485 FT232 USB dongle to power supply RS485 port

HCP1020A Power supply 100w/40V/10A

Commands are send via serial port always with 9600 bauds

SCPI Commands:

----------------------------------------------------
Commands not change : 

to send a *IDN? is in hex command 2A 49 44 4E 3F 0A

example:

-> 2A 49 44 4E 3F 0A

<- HENGHUI Ltd.,HCP1020A,17,V003,860000



to measure the current during a test:

:MEAS:CURR?

3A 4D 45 41 53 3A 43 55 52 52 3F 0A 0A

Query current protection

:CURR:PROT?

3A 43 55 52 52 3A 50 52 4F 54 3F 0A 0A 0A 0A


to measure the power during a test

:VOLT:PROT:STAT?

3A 56 4F 4C 54 3A 50 52 4F 54 3A 53 54 41 54 3F 0A 0A 0A 0A


to measure voltage that is settled:

:VOLT?

3A 56 4F 4C 54 3F 0A 0A 0A 0A


:MEAS:POW?

3A 4D 45 41 53 3A 50 4F 57 3F 0A 0A 0A

to measure the voltage during the test:

:MEAS?

3A 4D 45 41 53 3F 0A 0A


to off the output:

:OUTP OFF

3A 4F 55 54 50 20 4F 46 46 0A 0A

to on the output:

:OUTP ON

3A 4F 55 54 50 20 4F 4E 0A 0A 0A 0A

:OUTP?

3A 4F 55 54 50 3F 0A 0A 0A

1 is on 0 is off 

the operativility of the power supply:

:STAT:OPER:ENAB?

3A 53 54 41 54 3A 4F 50 45 52 3A 45 4E 41 42 3F 0A 0A 0A 0A

+0   means ok
by the way if you execute the command lock the front panel to not move the dial


------------------------------------------------------------------------------------------
Set commands change according the input 

to set a current protection to 6A

Set a voltage an a current
The APPLy command is used to control or query the power supply voltage and current values.

:APPL 5,1

example:

3A 41 50 50 4C 20 35 2C 31 0A 0A

:APPL 3,1

example:


3A 41 50 50 4C 20 33 2C 31 0A 0A

:CURR:PROT 6

3a 43 55 52 52 3a 50 52 4f 54 3f 0a 0a 0a 0a

to set a voltage without activate the output:

:VOLT 3

3A 56 4F 4C 54 20 33 0A 0A 0A 0A












