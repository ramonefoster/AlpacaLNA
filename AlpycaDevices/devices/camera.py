# camera.py

from falcon import Request, Response, before
from logging import Logger

from shr import PropertyResponse, MethodResponse, PreProcessRequest, get_request_field, to_bool
from exceptions import *
from devices.qhy import QhyCameraDevice
from dummies.qhy import Sdk
import os
from qcam.qCam import * 

logger: Logger = None
camera_device: QhyCameraDevice = None

# -----------------
# DISCOVERY GLOBALS
# -----------------
class CameraMetadata:
    Name = 'QHY Camera'
    Version = '1.0'
    Description = 'ASCOM Alpaca driver for QHY Cameras'
    DeviceType = 'Camera'
    DeviceID = 'f7457d34-4a24-4211-a477-1335a45b73d6'
    Info = 'Python QHY Driver'
    MaxDeviceNumber = 0
    InterfaceVersion = 3

def start_camera_device(log: Logger):
    global logger, camera_device
    logger = log
    # In a real app, you might have device selection logic here
    # --- Initialize Real SDK and Device ---
    try:
        # 1. Initialize the SDK controller from the DLL
        dll_path = os.path.join(os.path.dirname(__file__), 'SDKs\\QHY\\x64\\qhyccd.dll')
        cam_controller = Qcam(dll_path)
        cam_controller.so.InitQHYCCDResource()

        # 2. Scan for cameras (this is a blocking call, so it's fine at startup)
        cameras_found = cam_controller.so.ScanQHYCCD()
        if cameras_found <= 0:
            raise RuntimeError("No QHY camera found by the SDK.")

        # 3. Get the ID of the first camera
        cam_id_buffer = create_string_buffer(32)
        cam_controller.so.GetQHYCCDId(0, cam_id_buffer)
        cam_id = cam_id_buffer.value.decode('utf-8')
        logger.info(f"Found camera with ID: {cam_id}")

        # 4. Pass the controller and ID to the camera.start_camera_device function
        # You might need to modify start_camera_device to accept these parameters
        # or do it directly here:
        camera_device = QhyCameraDevice(logger, cam_controller, cam_id)
        
    except Exception as e:
        logger.error(f"FATAL: Could not initialize camera. {e}", exc_info=True)
        exit()

# --------------------
# FALCON API RESPONDERS
# --------------------

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class DriverVersion:
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(CameraMetadata.Version, req).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class Description:
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(CameraMetadata.Description, req).json

# ... (other static properties like Name, DriverInfo, InterfaceVersion go here)

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class connected:
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(camera_device.connected, req).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        conn = to_bool(get_request_field('Connected', req))
        try:
            camera_device.connected = conn
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, DriverException(0x500, 'Set Connected failed', ex)).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class camerastate:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = PropertyResponse(None, req, NotConnectedException()).json
            return
        resp.text = PropertyResponse(camera_device.camera_state, req).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class cameraxsize:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = PropertyResponse(None, req, NotConnectedException()).json
            return
        resp.text = PropertyResponse(camera_device.camera_xsize, req).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class cameraysize:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = PropertyResponse(None, req, NotConnectedException()).json
            return
        resp.text = PropertyResponse(camera_device.camera_ysize, req).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class binx:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = PropertyResponse(None, req, NotConnectedException()).json
            return
        resp.text = PropertyResponse(camera_device.bin_x, req).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = MethodResponse(req, NotConnectedException()).json
            return
        try:
            value = int(get_request_field('BinX', req))
            camera_device.bin_x = value
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, DriverException(0x500, 'Set BinX failed', ex)).json
            
@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class imageready:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = PropertyResponse(None, req, NotConnectedException()).json
            return
        resp.text = PropertyResponse(camera_device.image_ready, req).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class imagearray:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = PropertyResponse(None, req, NotConnectedException()).json
            return
        try:
            val = camera_device.image_array
            resp.text = PropertyResponse(val, req, is_array=True).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req, DriverException(0x500, 'Get ImageArray failed', ex)).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class canabortexposure:
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(camera_device.can_abort_exposure, req).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class startexposure:
    async def on_put(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = MethodResponse(req, NotConnectedException()).json
            return
        try:
            duration = float(get_request_field('Duration', req))
            light = to_bool(get_request_field('Light', req))
            
            # The method call is synchronous, but it starts an asyncio task
            camera_device.start_exposure(duration, light)
            
            # Respond immediately, as per ASCOM spec for non-blocking exposures
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, DriverException(0x500, 'StartExposure failed', ex)).json

@before(PreProcessRequest(CameraMetadata.MaxDeviceNumber))
class abortexposure:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not camera_device.connected:
            resp.text = MethodResponse(req, NotConnectedException()).json
            return
        try:
            camera_device.abort_exposure()
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, DriverException(0x500, 'AbortExposure failed', ex)).json