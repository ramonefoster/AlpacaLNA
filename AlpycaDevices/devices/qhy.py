# qhy_camera_device.py

import asyncio
from datetime import datetime, timezone
from logging import Logger
from threading import Lock
import numpy as np

# --- REAL SDK IMPORTS ---
# Import the Qcam class and the ctypes types from your SDK file
from qcam.qCam import * 
from ctypes import byref, c_uint32, c_double, c_char_p

# Local exception classes (should be in your project)
from exceptions import *

# --- ASCOM CONSTANTS ---
class CameraState:
    IDLE = 0
    EXPOSING = 1
    READING = 2
    DOWNLOADING = 3
    ERROR = 4

class QhyCameraDevice:
    # The __init__ method now takes the main SDK object and the camera ID string
    def __init__(self, logger: Logger, cam_controller: Qcam, cam_id: str):
        self.logger = logger
        self._lock = Lock()

        # --- REAL SDK OBJECTS ---
        self.cam = cam_controller            # The main Qcam object from qcam.py
        self.cam_id_bytes = cam_id.encode('utf-8') # The SDK uses bytes for the ID
        self.handle = None                   # The handle to the open camera, a key identifier

        # ASCOM Properties
        self.name = cam_id
        self._connected = False
        self._state = CameraState.IDLE
        self._binning = 1
        
        # We will populate these from the real SDK upon connection
        self._ccd_info = {} 
        self._last_image_buffer = None

        self.last_exposure_start_time: datetime = None
        self.last_exposure_duration_s = 0.0
        self.last_image: np.ndarray = None
        self._exposure_task: asyncio.Task = None

    @property
    def connected(self):
        with self._lock:
            return self._connected

    @connected.setter
    def connected(self, connected: bool):
        with self._lock:
            if connected == self._connected:
                return
            
            if connected:
                self.logger.info(f"Connecting to camera: {self.name}")
                # --- REAL SDK ---
                # Open the camera using its ID to get a handle
                self.handle = self.cam.so.OpenQHYCCD(self.cam_id_bytes)
                if not self.handle:
                    raise ConnectionError(f"Failed to open camera {self.name}")

                # Set to single frame mode, the most common for capture
                self.cam.so.SetQHYCCDStreamMode(self.handle, self.cam.stream_single_mode)
                
                # Initialize the camera
                if self.cam.so.InitQHYCCD(self.handle) != self.cam.QHYCCD_SUCCESS:
                    self.cam.so.CloseQHYCCD(self.handle) # Clean up on failure
                    raise ConnectionError(f"Failed to initialize camera {self.name}")

                # Get and cache chip info
                self._get_and_cache_chip_info()
                
                self._connected = True
                self.logger.info("Camera connected successfully.")
            else:
                self.logger.info(f"Disconnecting from camera: {self.name}")
                if self._exposure_task and not self._exposure_task.done():
                    self.abort_exposure()
                
                # --- REAL SDK ---
                # Close the camera handle
                if self.handle:
                    self.cam.so.CloseQHYCCD(self.handle)
                    self.handle = None
                
                self._connected = False
                self.logger.info("Camera disconnected.")

    def _get_and_cache_chip_info(self):
        """Helper to get hardware info and store it."""
        w, h = c_double(), c_double()
        iw, ih = c_uint32(), c_uint32()
        pw, ph = c_double(), c_double()
        bpp = c_uint32()

        self.cam.so.GetQHYCCDChipInfo(self.handle, byref(w), byref(h), byref(iw), byref(ih), byref(pw), byref(ph), byref(bpp))
        
        self._ccd_info = {
            'chip_width': w.value, 'chip_height': h.value,
            'image_width': iw.value, 'image_height': ih.value,
            'pixel_width': pw.value, 'pixel_height': ph.value,
            'bits_per_pixel': bpp.value
        }
        self.logger.info(f"Chip Info: {self._ccd_info}")
        
        # Prepare a buffer for the image data based on its size
        mem_size = self.cam.so.GetQHYCCDMemLength(self.handle)
        # Assuming 16-bit images for now, as that's most common for FITS
        self._last_image_buffer = (c_uint16 * int(mem_size / 2))()


    async def _exposure_and_readout_task(self, duration_s: float):
        """This is the core task that handles the real hardware exposure sequence."""
        try:
            self._state = CameraState.EXPOSING
            self.logger.info(f"Starting {duration_s}s exposure on hardware...")
            
            # 1. Start the exposure (this is a non-blocking call)
            await asyncio.to_thread(self.cam.so.ExpQHYCCDSingleFrame, self.handle)
            self.logger.info("Exposure started, now waiting for completion...")

            # 2. Poll the camera to see when the image is ready
            # This is a common pattern for hardware control. We repeatedly ask "are you done yet?"
            while self._state == CameraState.EXPOSING:
                # This is the blocking call to get the image data
                ret = await asyncio.to_thread(
                    self.cam.so.GetQHYCCDSingleFrame, self.handle,
                    byref(c_uint32()), byref(c_uint32()), byref(c_uint32()), byref(c_uint32()),
                    byref(self._last_image_buffer)
                )

                if ret == self.cam.QHYCCD_SUCCESS:
                    self.logger.info("Image data successfully retrieved.")
                    self._state = CameraState.DOWNLOADING # Technically we have it now
                    break # Exit the polling loop
                elif ret == 0x2001: # Error code meaning "still exposing"
                    await asyncio.sleep(0.5) # Wait before polling again
                else: # Any other error code
                    raise DriverException(f"Failed to get frame, SDK error code: {ret}")

            # 3. Convert the C-style buffer to a NumPy array
            w = self._ccd_info['image_width']
            h = self._ccd_info['image_height']
            
            image_array = np.ctypeslib.as_array(self._last_image_buffer)
            image_array = image_array[0:(w*h)] # Trim any extra buffer data
            
            # Reshape into a 2D image and transpose for Alpaca standard
            self.last_image = np.reshape(image_array, (h, w)).transpose()
            self.logger.info(f"Image processed, shape: {self.last_image.shape}")
            
        except asyncio.CancelledError:
            self.logger.warning("Exposure task was cancelled.")
            await asyncio.to_thread(self.cam.so.CancelQHYCCDExposure, self.handle)
        except Exception as e:
            self._state = CameraState.ERROR
            self.logger.error(f"Exposure failed: {e}", exc_info=True)
        finally:
            if self._state != CameraState.ERROR:
                self._state = CameraState.IDLE

    # --- ASCOM Properties and Methods ---
    @property
    def camera_state(self) -> int: return self._state
    @property
    def camera_xsize(self) -> int: return self._ccd_info.get('image_width', 0)
    @property
    def camera_ysize(self) -> int: return self._ccd_info.get('image_height', 0)
    @property
    def can_abort_exposure(self) -> bool: return True
    @property
    def max_adu(self) -> int: return 65535 # For a 16-bit camera

    @property
    def image_ready(self) -> bool:
        return self._state == CameraState.IDLE and self.last_image is not None

    @property
    def image_array(self) -> list:
        if self.last_image is None: raise ValueNotSetException()
        return self.last_image.tolist()

    def start_exposure(self, duration: float, light: bool):
        if self._state != CameraState.IDLE: raise InvalidOperationException("Camera is busy")
        
        self.last_image = None
        self.last_exposure_duration_s = duration
        self.last_exposure_start_time = datetime.now(timezone.utc)
        
        # --- REAL SDK ---
        # Set camera parameters before starting exposure
        self.cam.so.SetQHYCCDParam(self.handle, self.cam.CONTROL_EXPOSURE, c_double(duration * 1_000_000))
        # You would set Gain, Offset, etc. here as well
        # self.cam.so.SetQHYCCDParam(self.handle, self.cam.CONTROL_GAIN, c_double(gain_value))
        
        # Start the background task that manages the hardware
        self._exposure_task = asyncio.create_task(self._exposure_and_readout_task(duration))
    
    def abort_exposure(self):
        if self._state != CameraState.EXPOSING:
            return
        
        self.logger.warning("Abort requested by user.")
        if self._exposure_task and not self._exposure_task.done():
            self._exposure_task.cancel() # This will trigger the CancelledError in the task