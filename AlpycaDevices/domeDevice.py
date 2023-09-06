import serial
import serial.tools.list_ports
from logging import Logger

from threading import Lock
import re
import math
import time

class Dome():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger
        
        self._altitude = 0.0
        self._azimuth = 0.0
        self._at_park = False
        self._at_home = False
        self._shutter_status = 1
        self._home_az = 0 #degree
        # Status Shutter:       0 = "The shutter or roof is open", 
        #                       1 = "The shutter or roof is closed", 
        #                       2 = "The shutter or roof is opening", 
        #                       3 = "The shutter or roof is closing" 
        #                       4 = "The shutter or roof has encountered a problem"
        self._slaved = False
        self._slewing = False

        self._can_find_home = True
        self._can_park = False
        self._can_set_alt = False
        self._can_set_az = True
        self._can_set_park = False
        self._can_set_shutter = True
        self._can_slave = False
        self._can_sync = False

        self._connected = False
        self._serial = None
        self._timeout = 1
    
    def _ports(self):
        self.list = serial.tools.list_ports.comports()
        coms = []
        for element in self.list:
            coms.append(element.device)

        return(coms)

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
        if connected and 'COM3' in self._ports():
            self._lock.release()
            self._serial = serial.Serial(
                port='COM3',
                baudrate='9600',                
                timeout=self._timeout
            )
            self._serial.close()
            if not self._serial.is_open:
                try: 
                    self._serial.open()
                    self._serial.flush() 
                    time.sleep(1)                   
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
        if self._serial.is_open:
            try:
                self._serial.close()
            except:
                raise RuntimeError('Cannot disconnect')
        self._lock.release()
    
    def barcode_to_azimuth(self, stat_buf):
        """converts barcode number to azimuth"""
        if len(stat_buf)>20:                       
            if not type(re.search(r'\d+', stat_buf[0:12])) == type(None):
                dome_lcb = int(re.search(r'\d+', stat_buf[0:12]).group())
            else:
                dome_lcb = 851
            if dome_lcb >= 801 and dome_lcb < 851:
                return (dome_lcb - 670)*2
            if dome_lcb >= 851 and dome_lcb <= 982:
                return (dome_lcb - 851)*2
        else:
            return -1
    
    def status(self):
        self._lock.acquire()
        ack = self._write("MEADE PROG STATUS\r")
        if '*' in ack:
            self._azimuth = self.barcode_to_azimuth(ack) 
            if self._home_az != self._azimuth:
                self._at_home = False
            else:
                self._at_home = True
            self._slewing = bool(int(ack[16])) 
            shutter = int(ack[19])
            if shutter == 1:
                self._shutter_status = 0
            elif shutter == 0:
                self._shutter_status = 1
        self._lock.release()
    
    @property
    def altitude(self) -> float:
        self._lock.acquire()
        if not self._can_set_alt:
            self._lock.release()
            raise RuntimeError("Does not support vertical (altitude) control ")
        self._lock.release()
        return
    
    @property
    def azimuth(self) -> float:
        self._lock.acquire()
        if not self._can_set_az:
            self._lock.release()
            raise RuntimeError("Does not support vertical (altitude) control ")
        if self._azimuth == -1:
            raise RuntimeError("Reading azimuth error")
        self._lock.release()
        return self._azimuth
    
    @property
    def at_home(self) -> bool:
        self._lock.acquire()
        res = self._at_home
        self._lock.release()
        return res
    
    @property
    def can_find_home(self)-> bool:
        self._lock.acquire()
        res = self._can_find_home
        self._lock.release()
        return res
    
    @property
    def can_set_az(self)-> bool:
        self._lock.acquire()
        res = self._can_set_az
        self._lock.release()
        return res
    
    @property
    def can_park(self)-> bool:
        self._lock.acquire()
        res = self._can_park
        self._lock.release()
        return res
    
    @property
    def can_set_park(self)-> bool:
        self._lock.acquire()
        res = self._can_set_park
        self._lock.release()
        return res
    
    @property
    def shutter_status(self)-> bool:
        self.status()
        self._lock.acquire()
        res = self._shutter_status
        self._lock.release()
        return res
    
    @property
    def can_set_alt(self)-> bool:
        self._lock.acquire()
        res = self._can_set_alt
        self._lock.release()
        return res
    
    @property
    def can_slave(self)-> bool:
        self._lock.acquire()
        res = self._can_slave
        self._lock.release()
        return res
    
    @property
    def can_sync(self)-> bool:
        self._lock.acquire()
        res = self._can_sync
        self._lock.release()
        return res
    
    @property
    def can_set_shutter(self)-> bool:
        self._lock.acquire()
        res = self._can_set_shutter
        self._lock.release()
        return res
    
    @property
    def slewing(self)-> bool:
        self.status()
        self._lock.acquire()
        res = self._slewing
        self._lock.release()
        return res
    
    @property
    def slaved(self)-> bool:
        self._lock.acquire()
        res = self._slaved
        self._lock.release()
        return res
    @property.setter
    def slaved(self, slave: bool):
        if slave:
            raise RuntimeError("Not implemented")
    
    @property
    def at_park(self) -> bool:
        raise RuntimeError("Does does not support parking")
    
    def sync_to_az(self, az: float) -> None:
        raise RuntimeError('Shutter does not support azimuth synchronization')
    
    def set_park(self) -> None:
        raise RuntimeError('Dome does not support the setting of the park position')
    
    def park(self) -> None:
        raise RuntimeError('Dome does not support park')
    
    def find_home(self) -> None:
        self.abort()
        self.status()
        while self._slewing:
            time.sleep(1)
        print('[Homing]')
        self.slew_to_azimuth(self._home_az)
    
    def slew_to_altitude(self, alt: float):
        raise RuntimeError('Dome does not support Altitude Slew')

    def slew_to_azimuth(self, azimuth: float):
        self.logger.debug(f'[Move] pos={str(azimuth)}')               
        if self._slaved:
            raise RuntimeError('Slaved')
        if not self._can_set_az:
            raise RuntimeError('Dome does not support rotational (azimuth) control')
        
        azimuth = float(azimuth)
        if azimuth >= 0 and azimuth < 250:
            tag = 857 + math.ceil((azimuth) / 2)  
        elif azimuth >= 250 and azimuth < 360:
            tag = 676 + math.ceil((azimuth) / 2)

        self._slewing = 'ACK' in self._write("MEADE DOMO MOVER = " + str(tag) + "\r")
        self._lock.acquire()
        print('[SlewToAzimuth]', self._slewing)
        self._lock.release() 
    
    def close_shutter(self)-> None:
        if not self._can_set_shutter:
            raise RuntimeError('Cannot set Shutter')
        
        ret = 'ACK' in self._write(f"MEADE TRAPEIRA FECHAR\r")
        if not ret:
            ret = 'ACK' in self._write(f"MEADE TRAPEIRA FECHAR\r")
            if not ret:    
                self._shutter_status = 4        
                raise RuntimeError('Dome close FAIL!')            
        self._lock.acquire()
        self._shutter_status = 3
        self._lock.release()
    
    def open_shutter(self)-> None:
        if not self._can_set_shutter:
            raise RuntimeError('Cannot set Shutter')
        
        ret = 'ACK' in self._write(f"MEADE TRAPEIRA ABRIR\r")
        if not ret:
            ret = 'ACK' in self._write(f"MEADE TRAPEIRA ABRIR\r")
            if not ret:    
                self._shutter_status = 4        
                raise RuntimeError('Dome close FAIL!')            
        self._lock.acquire()
        self._shutter_status = 2
        self._lock.release()


    def abort(self) -> None:        
        print('[AbortSlew] Aborting...')
        resp = 'ACK' in self._write("MEADE DOMO PARAR\r")
        if not resp:
            resp = 'ACK' in self._write("MEADE DOMO PARAR\r")        
        if not resp:
            raise RuntimeError('Dome Abort FAIL!')
        self._lock.acquire()
        self._slewing = False
        self._lock.release()
    
    def _write(self, cmd):
        if self._serial.is_open:
            try:    
                time.sleep(.05)            
                self._serial.write(bytes(cmd, 'utf-8'))
                ack = self._serial.readline().decode('utf-8').rstrip()                            
                return ack
            except Exception as e:
                print("Error writing COM: "+ str(e))
                return "Error"
        else:
            return "Not Open"