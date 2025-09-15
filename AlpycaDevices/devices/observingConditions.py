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
from devices.observingDevice import ObservingConditions

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
class ObservingCondMetadata:
    """ Metadata describing the Rotator Device. Edit for your device"""
    Name = 'OPD Weather Station'
    Version = '0.2'
    Description = 'Uses OPD weather station'
    DeviceType = 'ObservingConditions'
    DeviceID = '1892ED30-92F3-4236-843E-DA8EEEF2D1CC' # https://guidgenerator.com/online-guid-generator.aspx
    Info = 'Alpaca Device\nObserving Conditions\nASCOM Initiative'
    MaxDeviceNumber = maxdev
    InterfaceVersion = 3        # IRotatorV3

# --------------------
# SIMULATED ROTATOR ()
# --------------------
obsC_dev = None
# At app init not import :-)
def start_obsC_device(logger: logger):
    logger = logger
    global obsC_dev
    obsC_dev = ObservingConditions(logger)

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
        resp.text = PropertyResponse(ObservingCondMetadata.Description, req).json

@before(PreProcessRequest(maxdev))
class driverinfo():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(ObservingCondMetadata.Info, req).json

@before(PreProcessRequest(maxdev))
class interfaceversion():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(ObservingCondMetadata.InterfaceVersion, req).json

@before(PreProcessRequest(maxdev))
class driverversion():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(ObservingCondMetadata.Version, req).json

@before(PreProcessRequest(maxdev))
class name():
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(ObservingCondMetadata.Name, req).json

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
        resp.text = PropertyResponse(obsC_dev.connected, req).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        conn_str = get_request_field('Connected', req)
        conn = to_bool(conn_str)              # Raises 400 Bad Request if str to bool fails

        try:
            # ----------------------
            obsC_dev.connected = conn
            # ----------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, # Put is actually like a method :-(
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class averageperiod:
    """
    (read/write) Gets And sets the time period (hours) over which observations will be averaged.
    Raises:
        InvalidValueException: If the value set is not available for this driver. 
        All drivers must accept 0.0 to specify that an instantaneous value is available.

        NotConnectedException: If the device is not connected

        DriverException: An error occurred that is not described by one of the more specific ASCOM exceptions. 
        Include sufficient detail in the message text to enable the issue to be accurately diagnosed by someone other than yourself. Includes communication errors.

    """
    def on_get(self, req: Request, resp: Response, devnum: int):
        resp.text = PropertyResponse(obsC_dev.average_period, req).json

    def on_put(self, req: Request, resp: Response, devnum: int):
        avg_str = get_request_field('AveragePeriod', req)
        avg = float(avg_str)              # Raises 400 Bad Request if str to bool fails
        if avg < 0.0:
            resp.text = MethodResponse(req, InvalidValueException(f'AveragePeriod {avg} < 0.0')).json
            return
        try:
            # ----------------------
            obsC_dev.average_period = avg
            # ----------------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req, # Put is actually like a method :-(
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class sensordescription:
    """
    Description of the sensor providing the requested property

    Parameters:
        PropertyName (str): The caseless name of the ObservingConditions meterological property for which the sensor description is desired. 
        For example “WindSpeed” (for WindSpeed) shall return a description of the sensor used to measure the wind speed.

    Returns:
        Description of the sensor used to measured the specified property.

    Return type:
        string

    Raises:
        MethodNotImplementedException: If the requested property/sensor is not implemented at all. See Attention section below for conditions.

        InvalidValueException: If PropertyName is not the name of one of the properties of ObservingConditions.

        NotConnectedException: If the device is not connected, and a connection is neeeded to get the descriptive name.

        DriverException: An error occurred that is not described by one of the more specific ASCOM exceptions. 
        Include sufficient detail in the message text to enable the issue to be accurately diagnosed by someone other than yourself. Includes communication errors.

    """
    # def on_get(self, req: Request, resp: Response, devnum: int):
    #     resp.text = PropertyResponse(obsC_dev.average_period, req).json

    def on_get(self, req: Request, resp: Response, devnum: int):
        prop_name = get_request_field('SensorName', req)

        try:
            # ----------------------
            desc = obsC_dev.sensor_description(prop_name)
            if desc == 'Unknown sensor':
                 resp.text = MethodResponse(req, InvalidValueException(), value=desc).json
            elif desc == 'Not implemented':
                resp.text = MethodResponse(req, NotImplementedException(), value=desc).json
            # ----------------------
            else:
                resp.text = MethodResponse(req, value=desc).json
        except Exception as ex:
            resp.text = MethodResponse(req, # Put is actually like a method :-(
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json
            
@before(PreProcessRequest(maxdev))
class refresh:
    """Forces the device to immediately query its attached hardware to refresh sensor values

    Returns:
        Nothing

    Raises:
        MethodNotImplementedException: If refreshing is not supported.

        NotConnectedException: If the device is not connected

        DriverException: An error occurred that is not described by one of the more specific ASCOM exceptions. 
        Include sufficient detail in the message text to enable the issue to be accurately diagnosed by someone other than yourself. Includes communication errors.
    """
    def on_put(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = MethodResponse(req,
                            NotConnectedException()).json
            return
        try:
            # ------------
            obsC_dev.refresh()
            # ------------
            resp.text = MethodResponse(req).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

## PROPERTIES
@before(PreProcessRequest(maxdev))
class cloudcover:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.cloud_cover
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class rainrate:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.rain_rate
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class skybrightness:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.sky_brightness
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class skyquality:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.sky_quality
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class skytemperature:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.sky_temperature
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class starfwhm:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.starfwhm
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class windgust:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            # val = obsC_dev.wind_gust
            # -------------------------------
            resp.text = PropertyResponse(None, req, NotImplementedException()).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class dewpoint:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.dew_point
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class dewpoint:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.dew_point
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class humidity:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.humidity
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json
            
@before(PreProcessRequest(maxdev))
class pressure:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.pressure
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class temperature:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.temperature
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class winddirection:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.wind_direction
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json

@before(PreProcessRequest(maxdev))
class windspeed:
    def on_get(self, req: Request, resp: Response, devnum: int):
        if not obsC_dev.connected:
            resp.text = PropertyResponse(None, req,
                            NotConnectedException()).json
            return
        try:
            # -------------------------------
            val = obsC_dev.wind_speed
            # -------------------------------
            resp.text = PropertyResponse(val, req).json
        except Exception as ex:
            resp.text = PropertyResponse(None, req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json
            
@before(PreProcessRequest(maxdev))
class timesincelastupdate:            
    def on_get(self, req: Request, resp: Response, devnum: int):
        prop_name = get_request_field('SensorName', req)
        if not obsC_dev.connected:
            resp.text = resp.text = MethodResponse(req,
                            NotConnectedException()).json
        try:                
            # -------------------------------
            val = obsC_dev.time_last_update(prop_name)
            if val < 0:
                resp.text = MethodResponse(req, NotImplementedException(), value=val).json
                return
            # -------------------------------
            resp.text = MethodResponse(req, value=val).json
        except Exception as ex:
            resp.text = MethodResponse(req,
                            DriverException(0x500, f'{self.__class__.__name__} failed', ex)).json