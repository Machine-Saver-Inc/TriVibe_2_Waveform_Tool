import os
import time
import threading
import random
import math
import minimalmodbus
import serial
from serial.tools import list_ports

class MockModbus:
    """Simulates a Modbus Instrument for testing/docker environments without hardware."""
    def __init__(self):
        self.serial = type('obj', (object,), {'close': lambda: None})
        self.address = 1
        self.mode = minimalmodbus.MODE_RTU
        self.precalculate_read_size = True
        self.close_port_after_each_call = True
        self.debug = False
        self._start_time = time.time()
        # Mock storage for writable settings
        self.registers = {
            26: 12345678, # Serial
            277: 10,      # Revision
            366: 16,      # g_range
            382: 100, 383: 1000, # filters_accel_1
            384: 10, 385: 100,   # filters_vel_1
            386: 500, 387: 5000, # filters_accel_2
            388: 50, 389: 500,   # filters_vel_2
        }

    def read_long(self, registeraddress, functioncode=3, signed=False, byteorder=0):
        # Return static serial number
        return self.registers.get(registeraddress, 999999)

    def read_register(self, registeraddress, functioncode=3, signed=False, number_of_decimals=0):
        # Simulate dynamic values
        if registeraddress == 8: return int((time.time() - self._start_time) / 60) # Minutes
        if registeraddress == 9: return int((time.time() - self._start_time) / 3600) # Hours
        if registeraddress == 10: return int((time.time() - self._start_time) / 86400) # Days
        if registeraddress == 31: return int((25.0 + random.uniform(-1, 1)) * 10) # Temp * 10
        
        return self.registers.get(registeraddress, 0)
    
    def read_float(self, registeraddress, functioncode=3, number_of_registers=2, byteorder=3):
        # Simulate Streaming Data (Sine waves)
        t = time.time()
        if registeraddress == 171: return 0.5 + 0.5 * math.sin(t) # Accel X
        if registeraddress == 173: return 0.5 + 0.5 * math.sin(t + 2) # Accel Y
        if registeraddress == 175: return 0.5 + 0.5 * math.sin(t + 4) # Accel Z

        if registeraddress == 177: return 0.2 + 0.1 * math.cos(t) # Vel X
        if registeraddress == 179: return 0.2 + 0.1 * math.cos(t + 2) # Vel Y
        if registeraddress == 181: return 0.2 + 0.1 * math.cos(t + 4) # Vel Z
        return 0.0

    def write_register(self, registeraddress, value, functioncode=16, signed=False, number_of_decimals=0):
        self.registers[registeraddress] = value
        print(f"[MOCK] Wrote {value} to Reg {registeraddress}")

class ModbusService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModbusService, cls).__new__(cls)
            cls._instance.instrument = None
            cls._instance.connection_status = "Disconnected"
            cls._instance.is_mock = False
        return cls._instance

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [{"device": p.device, "description": p.description} for p in ports]

    def connect(self, port: str, slave_id: int = 1):
        with self._lock:
            mode = os.environ.get("MODBUS_MODE", "real").lower()
            if mode == "mock":
                print("Initializing Mock Modbus...")
                self.instrument = MockModbus()
                self.is_mock = True
                self.connection_status = "Connected (Mock)"
                return True

            try:
                # Setup real hardware
                inst = minimalmodbus.Instrument(port, slave_id)
                inst.serial.baudrate = 115200
                inst.serial.bytesize = 8
                inst.serial.parity = serial.PARITY_NONE
                inst.serial.stopbits = 1
                inst.serial.timeout = 0.5
                inst.close_port_after_each_call = True
                inst.clear_buffers_before_each_transaction = True
                
                # Test read to verify connection
                # Reading Serial Number (Reg 26)
                inst.read_long(26, functioncode=3, signed=False, byteorder=0)
                
                self.instrument = inst
                self.is_mock = False
                self.connection_status = "Connected"
                return True
            except Exception as e:
                print(f"Connection Failed: {e}")
                self.instrument = None
                self.connection_status = f"Error: {str(e)}"
                return False

    def disconnect(self):
        with self._lock:
            if self.instrument and hasattr(self.instrument.serial, 'close'):
                self.instrument.serial.close()
            self.instrument = None
            self.connection_status = "Disconnected"

    def read_data(self):
        """Reads all dashboard data in one go (or logically grouped)."""
        with self._lock:
            if not self.instrument:
                return None
            
            try:
                # 1. One-time/Static (We read these every time for simplicity in this demo, 
                # inside a real app we might cache them)
                serial_num = self.instrument.read_long(26, 3, False, 0)
                revision = self.instrument.read_register(277, 0)

                # 2. Polling Data
                uptime_min = self.instrument.read_register(8, 0)
                uptime_hour = self.instrument.read_register(9, 0)
                uptime_day = self.instrument.read_register(10, 0)
                
                temp_raw = self.instrument.read_register(31, 0, signed=True)
                temp_c = temp_raw * 0.1

                # 3. Settings (Current Values)
                g_range = self.instrument.read_register(366, 0)
                f_acc_1_l = self.instrument.read_register(382, 0)
                f_acc_1_h = self.instrument.read_register(383, 0)
                f_vel_1_l = self.instrument.read_register(384, 0)
                f_vel_1_h = self.instrument.read_register(385, 0)
                f_acc_2_l = self.instrument.read_register(386, 0)
                f_acc_2_h = self.instrument.read_register(387, 0)
                f_vel_2_l = self.instrument.read_register(388, 0)
                f_vel_2_h = self.instrument.read_register(389, 0)

                return {
                    "serial_number": serial_num,
                    "revision": revision,
                    "uptime": f"{uptime_day}d {uptime_hour}h {uptime_min}m",
                    "temperature": f"{temp_c:.1f}",
                    "settings": {
                        "g_range": g_range,
                        "filters_accel_1": [f_acc_1_l, f_acc_1_h],
                        "filters_vel_1": [f_vel_1_l, f_vel_1_h],
                        "filters_accel_2": [f_acc_2_l, f_acc_2_h],
                        "filters_vel_2": [f_vel_2_l, f_vel_2_h],
                    }
                }
            except Exception as e:
                print(f"Read Error: {e}")
                return None

    def read_stream_data(self):
        """Reads float values for charts."""
        with self._lock:
            if not self.instrument:
                return None
            try:
                # Byteorder 3 = float big-endian, byte-swap? 
                # MinimalModbus byteorder 3 roughly matches 2 (Float AB CD or CD AB?)
                # user said: Byteorder 3.
                
                # Accel
                ax = self.instrument.read_float(171, 3, 2, 3)
                ay = self.instrument.read_float(173, 3, 2, 3)
                az = self.instrument.read_float(175, 3, 2, 3)
                
                # Vel
                vx = self.instrument.read_float(177, 3, 2, 3)
                vy = self.instrument.read_float(179, 3, 2, 3)
                vz = self.instrument.read_float(181, 3, 2, 3)

                return {
                    "accel": [ax, ay, az],
                    "vel": [vx, vy, vz],
                    "timestamp": time.time()
                }
            except Exception as e:
                print(f"Stream Error: {e}")
                return None

    def write_setting(self, register, value):
        with self._lock:
            if not self.instrument:
                return False
            try:
                self.instrument.write_register(register, value, 0)
                return True
            except Exception as e:
                print(f"Write Error: {e}")
                return False
