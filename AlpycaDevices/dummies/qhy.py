# pyqhyccd_mock.py
import time
import numpy as np

# --- Mock Enums and Structs ---
class Control:
    CamBin1x1mode = "CamBin1x1mode"
    CamBin2x2mode = "CamBin2x2mode"
    CamIsColor = "CamIsColor"
    CamColor = "CamColor"
    Exposure = "Exposure"
    Gain = "Gain"
    Offset = "Offset"
    Cooler = "Cooler"
    CurTemp = "CurTemp"
    CurPWM = "CurPWM"
    OutputDataActualBits = "OutputDataActualBits"

class StreamMode:
    SingleFrameMode = 0

class CCDChipInfo:
    def __init__(self):
        self.image_width = 5496
        self.image_height = 3672
        self.pixel_width = 3.76
        self.pixel_height = 3.76

class CCDChipArea:
    def __init__(self, start_x=0, start_y=0, width=5496, height=3672):
        self.start_x = start_x
        self.start_y = start_y
        self.width = width
        self.height = height

class ImageData:
    def __init__(self, data, width, height, bpp, channels):
        self.data = data
        self.width = width
        self.height = height
        self.bits_per_pixel = bpp
        self.channels = channels

# --- Mock Device Class ---
class MockCamera:
    """A mock QHY camera class that simulates hardware interaction."""
    def __init__(self, id_):
        self._id = id_
        self._is_open = False
        self._controls = {
            Control.Exposure: 1000,
            Control.Gain: 10,
            Control.Offset: 120,
            Control.CurTemp: -5.0,
            Control.CurPWM: 50.0,
            Control.OutputDataActualBits: 16.0,
        }
        self._roi = CCDChipArea()
        self._is_exposing = False
        self._abort_exposure = False

    def id(self):
        return self._id

    def open(self):
        self._is_open = True
        print(f"MockCamera {self._id}: Opened")

    def close(self):
        self._is_open = False
        print(f"MockCamera {self._id}: Closed")

    def is_open(self):
        return self._is_open

    def init(self):
        print(f"MockCamera {self._id}: Initialized")

    def get_ccd_info(self):
        return CCDChipInfo()

    def get_effective_area(self):
        return self._roi

    def is_control_available(self, control):
        return True # Simulate all controls are available

    def set_stream_mode(self, mode): pass
    def set_readout_mode(self, mode): pass
    def set_bin_mode(self, bin_x, bin_y): pass
    def set_roi(self, area): self._roi = area

    def set_parameter(self, control, value):
        self._controls[control] = value

    def get_parameter(self, control):
        return self._controls.get(control, 0.0)
        
    def get_parameter_min_max_step(self, control):
        if control == Control.Exposure:
            return (1000, 3600 * 1_000_000, 1) # 1ms to 1hr in us
        if control == Control.Gain:
            return (0, 100, 1)
        if control == Control.Offset:
            return (0, 255, 1)
        return (0, 0, 0)

    def get_image_size(self):
        return self._roi.width * self._roi.height * 2 # Assume 16bpp

    def start_single_frame_exposure(self):
        """Simulates a blocking exposure call."""
        if self._is_exposing:
            raise RuntimeError("Already exposing")
        self._is_exposing = True
        self._abort_exposure = False
        
        duration_us = self.get_parameter(Control.Exposure)
        end_time = time.time() + (duration_us / 1_000_000.0)
        
        while time.time() < end_time:
            if self._abort_exposure:
                print("MockCamera: Exposure aborted during wait.")
                self._is_exposing = False
                raise InterruptedError("Exposure aborted")
            time.sleep(0.1) # Check for abort periodically
            
        self._is_exposing = False

    def get_single_frame(self, buffer_size):
        width = self._roi.width
        height = self._roi.height
        img_data = np.random.randint(200, 800, size=(width * height), dtype=np.uint16)
        return ImageData(img_data.tobytes(), width, height, 16, 1)

    def abort_exposure_and_readout(self):
        if self._is_exposing:
            self._abort_exposure = True
        print("MockCamera: Abort signal received.")

# --- Mock SDK Class ---
class Sdk:
    """Simulates the main SDK entry point."""
    def __init__(self):
        print("Initializing Mock QHYCCD SDK...")
        self._cameras = [MockCamera("QHY268M-1234A")]
    
    def cameras(self):
        yield from self._cameras