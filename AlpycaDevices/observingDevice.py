from logging import Logger
from datetime import datetime, timezone
from threading import Lock, Timer, Thread
from dateutil import parser
import time
import requests
from config import Config
from exceptions import *

class ObservingConditions():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Observing Conditions'
        self.logger = logger
        
        self._api_url = Config.api_url
        self._status = {}
        self._wind_speed: float = 0.0
        self._wind_direction: float = 0.0
        self._temperature: float = 0.0
        self._humidity: float = 0.0
        self._dew_point: float = 0.0
        self._pressure: float = 0.0
        self._connected: bool = False
        self._last_update = 3600
        self._average_period = 12 # hours

        self._sensor_descriptions = {
            'CloudCover': 'Not implemented',
            'DewPoint': 'Dew Point calculated from temperature and humidity',
            'Humidity': 'Relative Humidity from weather station',
            'Pressure': 'Atmospheric Pressure from weather station',
            'RainRate': 'Not implemented',
            'SkyBrightness': 'Not implemented',
            'SkyQuality': 'Not implemented',
            'SkyTemperature': 'Not implemented',
            'StarFWHM': 'Not implemented',
            'Temperature': 'Temperature from weather station',
            'WindDirection': 'Wind Direction from weather station',
            'WindGust': 'Not implemented',
            'WindSpeed': 'Wind Speed from weather station'
        }
        self._loop_thread = Thread(target=self.get_status, daemon=True)
    
    def get_status(self):
        while self._connected:
            try: 
                response = requests.get(self._api_url, timeout=5, verify=False)
                if response.status_code == 200:                
                    self._lock.acquire()

                    self._status = response.json()
                    # get time from station in str iso format
                    now = datetime.now(timezone.utc)
                    target = parser.isoparse(self._status.get('datetime'))
                    self._last_update = (now - target).total_seconds()

                    self._lock.release()
                else:
                    raise RuntimeError(f'Error fetching data: {response.status_code}')                
            except:
                raise RuntimeError('Cannot Connect')
            # wait 60 seconds to next update
            time.sleep(30)

    def refresh(self):
        "Forces the device to immediately query its attached hardware to refresh sensor values"
        if self._connected:
            self.get_status()

    @property
    def connected(self):
        self._lock.acquire()
        res = self._connected
        self._lock.release()
        return res
    @connected.setter
    def connected(self, connected: bool):
        self._lock.acquire()
        self._connected = connected
        if connected:
            self._lock.release()            
            try: 
                response = requests.get(self._api_url, timeout=5, verify=False)
                if response.status_code == 200:
                    self._status = response.json()
                    self._lock.acquire()
                    self._connected = True
                    self._lock.release()
                    self._loop_thread.start()
                    self._last_update = 0
                else:
                    raise RuntimeError(f'Error fetching data: {response.status_code}')                
            except:
                raise RuntimeError('Cannot Connect')
        elif not connected:
            self._lock.release()
            self.disconnect()
        if self._connected:
            self.logger.info('[connected]')
        else:
            self.logger.info('[disconnected]')
    
    def disconnect(self):
        self._lock.acquire()
        self._connected = False
        self._lock.release()
        if self._loop_thread.is_alive():
            self._loop_thread.join(timeout=1)
    
    @property
    def average_period(self):
        return self._average_period
    @average_period.setter
    def average_period(self, period: float):
        self._lock.acquire()
        self._average_period = period
        self._lock.release()

    def sensor_description(self, sensor: str) -> str:
        "Description of the sensor providing the requested property"
        description = self._sensor_descriptions.get(sensor, 'Unknown sensor')
        if description == 'Unknown sensor':
            raise InvalidValueException()
        elif description == 'Not implemented':
            raise NotImplementedException()
        return description
    
    @property
    def cloud_cover(self) -> float:
        raise NotImplementedException()
    
    @property
    def dew_point(self) -> float:
        "Atmospheric dew point temperature (deg C) at the observatory"
        try:
            self._lock.acquire()
            temp = float(self._status.get('temperature', 0))
            hum = float(self._status.get('humidity', 0))
            self._dew_point = temp - ((100 - hum) / 5)
            self._lock.release()
        except:
            self._lock.release()
            raise RuntimeError('Error calculating dew point')
        return self._dew_point
    
    @property
    def humidity(self) -> float:
        "Atmospheric relative humidity (0.0 - 100.0 percent) at the observatory"
        self._lock.acquire()
        res = float(self._status.get('humidity', 0))
        self._humidity = res
        self._lock.release()
        return res
    
    @property
    def pressure(self) -> float:
        "Atmospheric pressure (hPa) at the observatory altitude"
        self._lock.acquire()
        res = float(self._status.get('bar', 0))
        self._pressure = res * 1.33322 # convert mmHg to hPa
        self._lock.release()
        return res
    
    @property
    def rain_rate(self) -> float:
        raise NotImplementedException()
    
    @property
    def sky_brightness(self) -> float:
        raise NotImplementedException()
    
    @property
    def sky_quality(self) -> float:
        raise NotImplementedException()
    
    @property
    def sky_temperature(self) -> float:
        raise NotImplementedException()
    
    @property
    def star_fwhm(self) -> float:
        raise NotImplementedException()
    
    @property
    def temperature(self) -> float:
        "Atmospheric temperature (deg C) at the observatory"
        self._lock.acquire()
        res = float(self._status.get('temperature', 0))
        self._temperature = res
        self._lock.release()
        return res
    
    @property
    def wind_direction(self) -> float:
        "Direction (deg) from which the wind is blowing at the observatory"
        self._lock.acquire()
        res = float(self._status.get('wind_angle', 0))
        self._wind_direction = res
        self._lock.release()
        return res
    
    @property
    def wind_gust(self) -> float:
        raise NotImplementedException()
    
    @property
    def wind_speed(self) -> float:
        "Wind speed (m/s) at the observatory"
        self._lock.acquire()
        res = float(self._status.get('wind_speed', 0))
        self._wind_speed = res / 3.6 #Convert km/h to m/s
        self._lock.release()
        return res
    
    @property
    def time_last_update(self, item) -> float:
        return self._last_update