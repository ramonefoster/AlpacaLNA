# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# rotator.py - Endpoints for members of ASCOM Alpaca ObservingConditions Device
#
# based on the AlpycaDevice Alpaca skeleton/template device driver
#
# Author:   Ramon Gargalhone <ramones@ita.br>
#
# Python Compatibility: Requires Python 3.7 or later
# GitHub: https://github.com/ASCOMInitiative/AlpycaDevice
#
# -----------------------------------------------------------------------------

from falcon import Request, Response, HTTPBadRequest, before
from logging import Logger
from shr import PropertyResponse, MethodResponse, PreProcessRequest, \
                get_request_field, to_bool
from exceptions import *        # Nothing but exception classes
from safetyDev import SafetyMonitor

logger: Logger = None
#logger = None                   # Safe on Python 3.7 but no intellisense in VSCode etc.

# ----------------------
# MULTI-INSTANCE SUPPORT
# ----------------------
# If this is > 0 then it means that multiple devices of this type are supported.
# Each responder on_get() and on_put() is called with a devnum parameter to indicate
# which instance of the device (0-based) is being called by the client. Leave this
# set to 0 for the simple case of controlling only one instance of this device type.
#
maxdev = 0                      # Single instance

# -------------------
# ROTATOR DEVICE INFO
# -------------------
# Static metadata not subject to configuration changes
class SafetyMonitorMetadata:
    """ Metadata describing the Rotator Device. Edit for your device"""
    Name = 'OPD Safety Monitor'
    Version = '0.2'
    Description = 'Uses OPD weather station to define safety conditions'
    DeviceType = 'SafetyMonitor'
    DeviceID = '1892ED30-92F3-4236-843E-DA8EEEF2D1CC' # https://guidgenerator.com/online-guid-generator.aspx
    Info = 'Alpaca Device\nObserving Conditions\nASCOM Initiative'
    MaxDeviceNumber = maxdev
    InterfaceVersion = 3        # IRotatorV3

# --------------------
# SIMULATED ROTATOR ()
# --------------------
safe_monitor = None
# At app init not import :-)
def start_safe_monitorice(logger: logger):
    logger = logger
    global safe_monitor
    safe_monitor = SafetyMonitor(logger)

# --------------------
# RESOURCE CONTROLLERS
# --------------------

@before(PreProcessRequest(maxdev))
class action:
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class commandblind:
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class commandbool:
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

@before(PreProcessRequest(maxdev))
class commandstring():
    def on_put(self, req: Request, resp: Response, devnum: int):
        resp.text = MethodResponse(req, NotImplementedException()).json

# Connected, though common, is implemented in rotator.py
@before(PreProcessRequest(maxdev))
class description():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(SafetyMonitorMetadata.Description, req).json

@before(PreProcessRequest(maxdev))
class driverinfo():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(SafetyMonitorMetadata.Info, req).json

@before(PreProcessRequest(maxdev))
class interfaceversion():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(SafetyMonitorMetadata.InterfaceVersion, req).json

@before(PreProcessRequest(maxdev))
class driverversion():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(SafetyMonitorMetadata.Version, req).json

@before(PreProcessRequest(maxdev))
class name():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(SafetyMonitorMetadata.Name, req).json

@before(PreProcessRequest(maxdev))
class supportedactions():
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
        resp.text = PropertyResponse(safe_monitor.connected, req).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        conn_str = get_request_field('Connected', req)
        conn = to_bool(conn_str)              # Raises 400 Bad Request if str to bool fails

        try:
            # ----------------------
            safe_monitor.connected = conn
            # ----------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, # Put is actually like a method :-(
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json


## PROPERTIES
@before(PreProcessRequest(maxdev))
class issafe:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not safe_monitor.connected:
            resp.text = PropertyResponse(False, req).json
            return
        try:
            # -------------------------------
            val = safe_monitor.is_safe
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json