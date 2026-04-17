import pyvisa
import time

# Explicitly use the '@py' backend
rm = pyvisa.ResourceManager('@py') 

resources = rm.list_resources()

if not resources:
    print("No resources detected. If using USB, check your permissions (udev rules).")
else:
    print("Detected resources:", resources)

