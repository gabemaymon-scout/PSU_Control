import tkinter as tk
import pyvisa
import serial
import time

# ---------------- CONFIG ----------------
DEVICES = [
    {
        "id": "USB0::62700::5200::SPS43ABQ800042::0::INSTR",
        "voltage": 12.0,
        "name": "SP240 12V",
        "type": "siglent",
        "channel": 1
    },
    {
        "id": "USB0::62700::5200::SPS43ABD800066::0::INSTR",
        "voltage": 28.0,
        "name": "28V PS",
        "type": "siglent",
        "channel": 1
    },
    {
        "id": "/dev/ttyACM0",
        "voltage": 5.0,
        "name": "IRU 5V COM",
        "type": "konrad"
    }
]

# ================= GUI CLASS =================
class PowerSupplyGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Multi-PSU Control")
        self.root.geometry("520x320")

        self.rm = pyvisa.ResourceManager('@py')

        self.psus = {}
        self.indicators = {}
        self.current_labels = {}   # ⭐ NEW

        self.create_widgets()
        self.connect_devices()
        self.start_current_monitor()

    # ---------------- GUI ----------------
    def create_widgets(self):
        for device in DEVICES:
            frame = tk.Frame(self.root)
            frame.pack(pady=10, fill='x', padx=20)

            canvas = tk.Canvas(frame, width=20, height=20, highlightthickness=0)
            canvas.grid(row=0, column=0, padx=10)

            oval = canvas.create_oval(2, 2, 18, 18, fill="red")
            self.indicators[device["id"]] = (canvas, oval)

            tk.Label(frame, text=device['name'],
                     width=14, anchor='w').grid(row=0, column=1)

            tk.Button(frame, text="ON", width=8, bg="#e1f5fe",
                      command=lambda d=device: self.output_on(d)
            ).grid(row=0, column=2, padx=5)

            tk.Button(frame, text="OFF", width=8, bg="#ffebee",
                      command=lambda d=device: self.output_off(d)
            ).grid(row=0, column=3, padx=5)

            # ⭐ CURRENT DISPLAY LABEL
            current_label = tk.Label(frame, text="0.000 A",
                                     width=10, anchor='e',
                                     font=("Arial", 10, "bold"))
            current_label.grid(row=0, column=4, padx=10)

            self.current_labels[device["id"]] = current_label

    # ---------------- CONNECTION ----------------
    def connect_devices(self):
        for device in DEVICES:
            try:
                if device["type"] == "siglent":
                    psu = self.rm.open_resource(device["id"])
                    psu.write_termination = '\n'
                    psu.read_termination = '\n'
                    psu.timeout = 5000

                    psu.write("*CLS")
                    idn = psu.query("*IDN?")
                    print(f"SUCCESS: {device['name']} connected: {idn.strip()}")

                    psu.write(f"VOLT {device['voltage']}")
                    self.psus[device["id"]] = psu

                elif device["type"] == "konrad":
                    psu = serial.Serial(
                        port=device["id"],
                        baudrate=115200,
                        timeout=1
                    )
                    time.sleep(1)
                    psu.reset_input_buffer()

                    psu.write(f"VSET1:{device['voltage']}\n".encode())
                    print(f"SUCCESS: {device['name']} connected")

                    self.psus[device["id"]] = psu

            except Exception as e:
                print(f"ERROR: Failed to connect {device['name']}: {e}")

    # ---------------- CURRENT MONITOR ----------------
    def start_current_monitor(self):
        self.read_current()
        self.root.after(5000, self.start_current_monitor)

    def read_current(self):
        for device in DEVICES:
            psu = self.psus.get(device["id"])
            label = self.current_labels.get(device["id"])

            if not psu or not label:
                continue

            try:
                # ===== SIGLENT =====
                if device["type"] == "siglent":
                    ch = device.get("channel", 1)
                    current = psu.query(f"MEASure:CURRent? CH{ch}")
                    current = float(current.strip())

                # ===== KONRAD =====
                elif device["type"] == "konrad":
                    psu.write(b"IOUT1?\n")
                    current = float(psu.readline().decode().strip())

                # Update GUI label
                label.config(text=f"{current:.3f} A")

                print(f"{device['name']} Current: {current:.3f} A")

            except Exception as e:
                label.config(text="ERR")
                print(f"Current read failed ({device['name']}): {e}")

    # ---------------- CONTROL ----------------
    def output_on(self, device):
        psu = self.psus.get(device["id"])
        if not psu:
            return

        try:
            if device["type"] == "siglent":
                psu.write(f"VOLT {device['voltage']}")
                psu.write("OUTP ON")
            elif device["type"] == "konrad":
                psu.write(f"VSET1:{device['voltage']}\n".encode())
                psu.write(b"OUT1\n")

            self.set_indicator(device["id"], True)
            print(f"{device['name']} Output ON")

        except Exception as e:
            print(f"ON command failed for {device['name']}: {e}")

    def output_off(self, device):
        psu = self.psus.get(device["id"])
        if not psu:
            return

        try:
            if device["type"] == "siglent":
                psu.write("OUTP OFF")
            elif device["type"] == "konrad":
                psu.write(b"OUT0\n")

            self.set_indicator(device["id"], False)
            print(f"{device['name']} Output OFF")

        except Exception as e:
            print(f"OFF command failed for {device['name']}: {e}")

    # ---------------- INDICATOR ----------------
    def set_indicator(self, device_id, state):
        canvas, oval = self.indicators[device_id]
        canvas.itemconfig(oval, fill="green" if state else "red")


# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = PowerSupplyGUI(root)
    root.mainloop()

