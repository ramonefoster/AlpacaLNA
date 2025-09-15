from logging import Logger
from threading import Lock, Thread
import time
import requests
from config import Config

import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suprime o warning específico
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

class SafetyMonitor():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Safety Monitor'
        self.logger = logger
        
        self._connected: bool = False
        self._api_url = Config.api_url
        self._status = {}
        self._is_safe = False
        self._loop_thread = Thread(target=self.get_status, daemon=True)
    
    def get_status(self):
        while self._connected:
            try: 
                response = requests.get(self._api_url, timeout=5, verify=False)
                if response.status_code == 200:                
                    self._lock.acquire()
                    self._status = response.json()
                    temp = float(self._status.get('temperature', 50))
                    hum = float(self._status.get('humidity', 100))
                    wind_speed = float(self._status.get('wind_speed', 50))
                    leaf = float(self._status.get('leaf', 10))
                    dew = temp - ((100 - hum) / 5)
                    if hum < Config.max_humidity:
                        self._is_safe = True
                    elif wind_speed < Config.max_wind:
                        self._is_safe = True
                    elif temp > Config.min_temp and temp < Config.max_temp:
                        self._is_safe = True
                    elif leaf < Config.max_leaf:
                        self._is_safe = True
                    elif dew < Config.risk_dew:
                        self._is_safe = True
                    else:
                        self._is_safe = False
                    self._lock.release()
                else:
                    raise RuntimeError(f'Error fetching data: {response.status_code}')                
            except:
                raise RuntimeError('Cannot Connect')
            # wait 60 seconds to next update
            time.sleep(60)

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
    def is_safe(self) -> bool:
        return self._is_safe
    
    