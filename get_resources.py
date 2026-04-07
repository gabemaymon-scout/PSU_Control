import pyvisa
import time

VOLTAGE = 0

rm = pyvisa.ResourceManager()  # NI-VISA backend
resources = rm.list_resources()
print("Detected resources:", resources)