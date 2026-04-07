import tkinter as tk
import pyvisa
import serial
import time

# ---------------- CONFIG ----------------
DEVICES = [
    # -------- SIGLENT 12V --------
    {
        "id": "USB0::0xF4EC::0x1450::SPS43ABQ800042::INSTR",
        "voltage": 12.0,
        "name": "SP240 12V",
        "type": "siglent"
    },

    # -------- SIGLENT 28V --------
    {
        "id": "USB0::0xF4EC::0x1450::SPS43ABD800066::INSTR",
        "voltage": 28.0,
        "name": "28V PS",
        "type": "siglent"
    },

    # -------- KONRAD SERIAL PSU --------
    {
        "id": "/dev/ttyACM1",
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
        self.root.geometry("420x260")

        self.rm = pyvisa.ResourceManager()
        self.psus = {}
        self.indicators = {}

        self.create_widgets()
        self.connect_devices()

    # ---------------- GUI ----------------
    def create_widgets(self):
        for device in DEVICES:
            frame = tk.Frame(self.root)
            frame.pack(pady=10)

            canvas = tk.Canvas(frame, width=20, height=20,
                               highlightthickness=0)
            canvas.grid(row=0, column=0, padx=5)

            oval = canvas.create_oval(2, 2, 18, 18, fill="red")
            self.indicators[device["id"]] = (canvas, oval)

            tk.Button(
                frame,
                text=f"{device['name']} ON",
                width=14,
                command=lambda d=device: self.output_on(d)
            ).grid(row=0, column=1, padx=5)

            tk.Button(
                frame,
                text=f"{device['name']} OFF",
                width=14,
                command=lambda d=device: self.output_off(d)
            ).grid(row=0, column=2, padx=5)

    # ---------------- CONNECTION ----------------
    def connect_devices(self):

        for device in DEVICES:
            try:

                # ===== SIGLENT VISA =====
                if device["type"] == "siglent":
                    psu = self.rm.open_resource(device["id"])
                    psu.write_termination = '\n'
                    psu.read_termination = '\n'
                    psu.timeout = 5000

                    psu.write("*CLS")
                    idn = psu.query("*IDN?")
                    print(f"{device['name']} connected: {idn.strip()}")

                    # preset voltage
                    psu.write(f"VOLT {device['voltage']}")

                    self.psus[device["id"]] = psu

                # ===== KONRAD SERIAL =====
                elif device["type"] == "konrad":

                    psu = serial.Serial(
                        port=device["id"],
                        baudrate=115200,
                        timeout=1
                    )

                    time.sleep(1)

                    psu.reset_input_buffer()
                    psu.reset_output_buffer()

                    # set voltage
                    cmd = f"VSET1:{device['voltage']}\n"
                    psu.write(cmd.encode())

                    # try IDN (optional)
                    psu.write(b"*IDN?\n")
                    time.sleep(0.2)
                    idn = psu.readline().decode(errors="ignore").strip()

                    print(f"{device['name']} connected: {idn}")

                    self.psus[device["id"]] = psu

            except Exception as e:
                print(f"Failed to connect {device['name']}: {e}")

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

        except Exception as e:
            print(f"ON failed ({device['name']}): {e}")

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

        except Exception as e:
            print(f"OFF failed ({device['name']}): {e}")

    # ---------------- INDICATOR ----------------
    def set_indicator(self, device_id, state):
        canvas, oval = self.indicators[device_id]
        canvas.itemconfig(oval, fill="green" if state else "red")


# ================= MAIN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = PowerSupplyGUI(root)
    root.mainloop()
