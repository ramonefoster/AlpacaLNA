
# -*- coding: utf-8 -*-
#
# -----------------------------------------------------------------------------
# dome.py - Alpaca API responders for Dome
#
# Author:   Ramon Gargalhone <ramones@ita.br> 
#
# -----------------------------------------------------------------------------

from falcon import Request, Response, HTTPBadRequest, before
from logging import Logger
from shr import PropertyResponse, MethodResponse, PreProcessRequest, \
                get_request_field, to_bool
from exceptions import *        # Nothing but exception classes

from devices.domeDevice import Dome

logger: Logger = None

# ----------------------
# MULTI-INSTANCE SUPPORT
# ----------------------
# If this is > 0 then it means that multiple devices of this type are supported.
# Each responder on_get() and on_put() is called with a devnum parameter to indicate
# which instance of the device (0-based) is being called by the client. Leave this
# set to 0 for the simple case of controlling only one instance of this device type.
#
maxdev = 0                      # Single instance

# -----------
# DEVICE INFO
# -----------
# Static metadata not subject to configuration changes
## EDIT FOR YOUR DEVICE ##
class DomeMetadata:
    """ Metadata describing the Dome Device. Edit for your device"""
    Name = 'OPD Dome'
    Version = '1.0'
    Description = 'Pico dos Dias Observatory Domes'
    DeviceType = 'Dome'
    DeviceID = '528d3b9d-9aa0-4907-ac5a-1cd2eef372ed' # https://guidgenerator.com/online-guid-generator.aspx
    Info = 'Alpaca Sample Device\nImplements IDome\nASCOM Initiative'
    MaxDeviceNumber = maxdev
    InterfaceVersion = 3

# --------------------
# RESOURCE CONTROLLERS
# --------------------

def start_dome_device(logger: logger):
    logger = logger
    global dome
    dome = Dome(logger)

@before(PreProcessRequest(maxdev))
class Action:
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class CommandBlind:
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class CommandBool:
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class CommandString():
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class Description():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(DomeMetadata.Description, req).json

@before(PreProcessRequest(maxdev))
class DriverInfo():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(DomeMetadata.Info, req).json

@before(PreProcessRequest(maxdev))
class InterfaceVersion():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(DomeMetadata.InterfaceVersion, req).json

@before(PreProcessRequest(maxdev))
class DriverVersion():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(DomeMetadata.Version, req).json

@before(PreProcessRequest(maxdev))
class Name():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(DomeMetadata.Name, req).json

@before(PreProcessRequest(maxdev))
class SupportedActions():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse([], req).json  # Not PropertyNotImplemented

@before(PreProcessRequest(maxdev))
class connected:
    """Retrieves or sets the connected state of the device

    * Set True to connect to the device hardware. Set False to disconnect
      from the device hardware. Client can also read the property to check
      whether it is connected. This reports the current hardware state.
    * Multiple calls setting Connected to true or false must not cause
      an error.

    """
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(dome.connected, req).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        conn_str = get_request_field('Connected', req)
        conn = to_bool(conn_str)              # Raises 400 Bad Request if str to bool fails

        try:
            # ----------------------
            dome.connected = conn
            # ----------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, # Put is actually like a method :-(
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class altitude:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.altitude
            # ----------------------
            resp.text = PropertyResponse(None, req,
                            NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Altitude failed', ex)).json

@before(PreProcessRequest(maxdev))
class athome:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.at_home
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Athome failed', ex)).json

@before(PreProcessRequest(maxdev))
class atpark:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.at_park
            # ----------------------
            resp.text = PropertyResponse(None, req,
                            NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Atpark failed', ex)).json

@before(PreProcessRequest(maxdev))
class azimuth:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.azimuth
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Azimuth failed', ex)).json

@before(PreProcessRequest(maxdev))
class canfindhome:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_find_home
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Canfindhome failed', ex)).json

@before(PreProcessRequest(maxdev))
class canpark:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_park
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Canpark failed', ex)).json

@before(PreProcessRequest(maxdev))
class cansetaltitude:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome._can_set_alt
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Cansetaltitude failed', ex)).json

@before(PreProcessRequest(maxdev))
class cansetazimuth:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_set_az
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Cansetazimuth failed', ex)).json

@before(PreProcessRequest(maxdev))
class cansetpark:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_set_park
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Cansetpark failed', ex)).json

@before(PreProcessRequest(maxdev))
class cansetshutter:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_set_shutter
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Cansetshutter failed', ex)).json

@before(PreProcessRequest(maxdev))
class canslave:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_slave
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Canslave failed', ex)).json

@before(PreProcessRequest(maxdev))
class cansyncazimuth:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.can_sync
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Cansyncazimuth failed', ex)).json

@before(PreProcessRequest(maxdev))
class shutterstatus:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.shutter_status
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Shutterstatus failed', ex)).json

@before(PreProcessRequest(maxdev))
class slaved:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.slaved
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Slaved failed', ex)).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        slavedstr = get_request_field('Slaved', req)      # Raises 400 bad request if missing
        slaved = to_bool(slavedstr)                       # Same here

        try:
            # -----------------------------
            dome.slaved(slaved)
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Slaved failed', ex)).json

@before(PreProcessRequest(maxdev))
class slewing:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # ----------------------
            val = dome.slewing
            # ----------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, 'Dome.Slewing failed', ex)).json

@before(PreProcessRequest(maxdev))
class abortslew:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -----------------------------
            dome.abort()
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Abortslew failed', ex)).json

@before(PreProcessRequest(maxdev))
class closeshutter:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -----------------------------
            dome.close_shutter()
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Closeshutter failed', ex)).json

@before(PreProcessRequest(maxdev))
class findhome:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -----------------------------
            dome.find_home()
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Findhome failed', ex)).json

@before(PreProcessRequest(maxdev))
class openshutter:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -----------------------------
            dome.open_shutter()
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Openshutter failed', ex)).json

@before(PreProcessRequest(maxdev))
class park:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -----------------------------
            dome.park()
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Park failed', ex)).json

@before(PreProcessRequest(maxdev))
class setpark:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -----------------------------
            dome.set_park()
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Setpark failed', ex)).json

@before(PreProcessRequest(maxdev))
class slewtoaltitude:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        altitudestr = get_request_field('Altitude', req)      # Raises 400 bad request if missing
        try:
            altitude = float(altitudestr)
        except:
            resp.text = MethodResponse(req,
                            InvalidValueException(f'Altitude " + altitudestr + " not a valid number.')).json
            return
        ### RANGE CHECK AS NEEDED ###       # Raise Alpaca InvalidValueException with details!
        try:
            # -----------------------------
            # dome.slew_to_altitude(altitude)
            # -----------------------------
            resp.text = PropertyResponse(None, req,
                            NotImplementedException()).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Slewtoaltitude failed', ex)).json

@before(PreProcessRequest(maxdev))
class slewtoazimuth:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        azimuthstr = get_request_field('Azimuth', req)      # Raises 400 bad request if missing
        try:
            azimuth = float(azimuthstr)
        except:
            resp.text = MethodResponse(req,
                            InvalidValueException(f'Azimuth " + azimuthstr + " not a valid number.')).json
            return
        ### RANGE CHECK AS NEEDED ###       # Raise Alpaca InvalidValueException with details!
        try:
            # -----------------------------
            if azimuth < 0 or azimuth> 360:
                resp.text = MethodResponse(req,
                            InvalidValueException(f'Azimuth " + azimuthstr + " not a valid number.')).json
                return
            dome.slew_to_azimuth(azimuth)
            # -----------------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Slewtoazimuth failed', ex)).json

@before(PreProcessRequest(maxdev))
class synctoazimuth:
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not dome.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        azimuthstr = get_request_field('Azimuth', req)      # Raises 400 bad request if missing
        try:
            azimuth = int(azimuthstr)
        except:
            resp.text = MethodResponse(req,
                            InvalidValueException(f'Azimuth " + azimuthstr + " not a valid number.')).json
            return
        ### RANGE CHECK AS NEEDED ###       # Raise Alpaca InvalidValueException with details!
        try:
            # -----------------------------
            # dome.slew_to_azimuth(azimuth)
            # -----------------------------
            resp.text = PropertyResponse(None, req,
                            NotImplementedException()).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, 'Dome.Synctoazimuth failed', ex)).json

