import serial
import serial.tools.list_ports
from logging import Logger

from threading import Lock
import re
import math
import time
from config import Config, save_toml
from exceptions import *

class Dome():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Dome'
        self.logger = logger
        
        self._altitude = 0.0
        self._azimuth = 0.0
        self._at_park = False
        self._at_home = False
        self._shutter_status = 1
        self._home_az = 0 #degree
        self._park_az = Config.park_az #degree
        # Status Shutter:       0 = "The shutter or roof is open", 
        #                       1 = "The shutter or roof is closed", 
        #                       2 = "The shutter or roof is opening", 
        #                       3 = "The shutter or roof is closing" 
        #                       4 = "The shutter or roof has encountered a problem"
        self._slaved = False
        self._slewing = False

        self._can_find_home = Config.can_find_home
        self._can_park = Config.can_park
        self._can_set_alt = Config.can_set_alt
        self._can_set_az = Config.can_set_az
        self._can_set_park = Config.can_set_park
        self._can_set_shutter = Config.can_set_shutter
        self._can_slave = Config.can_slave
        self._can_sync = Config.can_sync

        self._connected = False
        self._serial = None
        self._timeout = 2
        self._port = Config.com_port
        self._baudrate = Config.com_baudrate
    
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
        if connected and self._port in self._ports():
            self._lock.release()
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,                
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
            self._write("MEADE DOMO INIT")
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
    
    def barcode_to_azimuth(self, dome_lcb):
        if dome_lcb >= 855 and dome_lcb <= 982:
            return 2 * (dome_lcb - 855)
        elif dome_lcb < 855:
            return 2 * (dome_lcb - 675)
    
    def status(self):
        self._lock.acquire()

        try:
            ack = self._write("MEADE PROG STATUS")

            if not ack or '*' not in ack:
                self.logger.error(f'[Reading] Invalid ACK: {ack}')
                return

            parts = ack.split('*')
            if len(parts) != 2:
                self.logger.error(f'[Reading] Malformed ACK: {ack}')
                return

            try:
                dome_lcb = int(parts[0].strip())
            except ValueError:
                self.logger.error(f'[Reading] Invalid LCB: {parts[0]}')
                return

            raw_bits = parts[1].strip()
            status_bits = ''.join(c for c in raw_bits if c in '01')

            if len(status_bits) < 16:
                self.logger.error(f'[Reading] Incomplete bitfield: {raw_bits}')
                return

            try:
                self._slewing = bool(int(status_bits[3]))

                shutter = int(status_bits[6])
                if shutter == 1:
                    self._shutter_status = 0
                elif shutter == 0:
                    self._shutter_status = 1

            except Exception as e:
                self.logger.error(f'[Parsing Bits] {e} | bits={status_bits}')
                return

            self._azimuth = self.barcode_to_azimuth(dome_lcb)
            self._at_home = (self._home_az == self._azimuth)

        finally:
            self._lock.release()
    
    @property
    def altitude(self) -> float:
        return
    
    @altitude.setter
    def altitude(self) -> float:
        self._lock.acquire()
        if not self._can_set_alt:
            self._lock.release()
            raise RuntimeError("Does not support vertical (altitude) control ")
        self._lock.release()
        return
    
    @property
    def azimuth(self) -> float:
        self.status()
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
        self.status()
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
    def slewing(self):
        self.status()
        self._lock.acquire()
        res = self._slewing
        self._lock.release()
        return res
    
    @property
    def slaved(self):
        self._lock.acquire()
        res = self._slaved
        self._lock.release()
        return res
    @slaved.setter
    def slaved(self, slave: bool):
        self._slaved = slave
        return
    
    def at_park(self) -> bool:
        return False  
    
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
        self.logger.debug(f'[Slew] pos={str(azimuth)}')               
        if self._slaved:
            raise RuntimeError('Slaved')
        if not self._can_set_az:
            raise RuntimeError('Dome does not support rotational (azimuth) control')
        
        azimuth = float(azimuth)
        if azimuth == 360:
            azimuth = 0
        if azimuth >= 0 and azimuth < 252:
            tag = 855 + math.ceil((azimuth) / 2)  
        elif azimuth >= 252 and azimuth < 360:
            tag = 675 + math.ceil((azimuth) / 2)

        self._slewing = 'ACK' in self._write("MEADE DOMO MOVER = " + str(tag))
        self._lock.acquire()
        print('[SlewToAzimuth]', self._slewing)
        self._lock.release() 
    
    def close_shutter(self)-> None:
        if not self._can_set_shutter:
            raise RuntimeError('Cannot set Shutter')
        
        ret = 'ACK' in self._write(f"MEADE TRAPEIRA FECHAR")
        if not ret:
            ret = 'ACK' in self._write(f"MEADE TRAPEIRA FECHAR")
            if not ret:    
                self._shutter_status = 4        
                raise RuntimeError('Dome close FAIL!')            
        self._lock.acquire()
        self._shutter_status = 3
        self._lock.release()
    
    def set_park(self):
        if not self._can_set_park:
            raise RuntimeError('Cannot set Park')
        
        save_toml('device', 'park_az', self._azimuth)
        self.logger.info(f'[SetPark] pos={str(self._azimuth)}')

    def park(self) -> None:
        if not self._can_park:
            raise RuntimeError('Cannot Park')
        if self._slaved:
            raise SlavedException()
        if self._at_park:
            raise ParkedException()

        self._lock.acquire()
        self._at_park = True
        self._lock.release()
        self.slew_to_azimuth(self._home_az)

    def open_shutter(self)-> None:
        if not self._can_set_shutter:
            raise RuntimeError('Cannot set Shutter')
        
        ret = 'ACK' in self._write(f"MEADE TRAPEIRA ABRIR")
        if not ret:
            ret = 'ACK' in self._write(f"MEADE TRAPEIRA ABRIR")
            if not ret:    
                self._shutter_status = 4        
                raise RuntimeError('Dome close FAIL!')            
        self._lock.acquire()
        self._shutter_status = 2
        self._lock.release()

    def abort(self) -> None:        
        print('[AbortSlew] Aborting...')
        resp = 'ACK' in self._write("MEADE DOMO PARAR")
        self._write("MEADE PROG PARAR")
        if not resp:
            resp = 'ACK' in self._write("MEADE DOMO PARAR")        
        if not resp:
            raise RuntimeError('Dome Abort FAIL!')
        self._lock.acquire()
        self._slewing = False
        self._lock.release()
    
    def flat_on(self) -> None:
        """
        Sends the serial command to turn the flat lamp ON.
        """
        self.logger.info('[FlatLamp] Turning ON')
        
        cmd_to_send = "MEADE FLAT_WEAK LIGAR" 

        resp = 'ACK' in self._write(cmd_to_send)
        print("LAMP RESPONSE", resp)
        if not resp:
            self.logger.warning('[FlatLamp] First attempt failed, trying again.')
            resp = 'ACK' in self._write(cmd_to_send)
            if not resp:    
                self.logger.error('[FlatLamp] Failed to turn ON')
                raise RuntimeError('Flat Lamp ON command failed')
        else:
            self.logger.info('[FlatLamp] Successfully turned ON')

    def flat_off(self) -> None:
        """
        Sends the serial command to turn the flat lamp OFF.
        """
        self.logger.info('[FlatLamp] Turning OFF')

        cmd_to_send = "MEADE FLAT_WEAK DESLIGAR"

        resp = 'ACK' in self._write(cmd_to_send)
        print("LAMP RESPONSE", resp)
        if not resp:
            self.logger.warning('[FlatLamp] First attempt failed, trying again.')
            resp = 'ACK' in self._write(cmd_to_send)
            if not resp:    
                self.logger.error('[FlatLamp] Failed to turn OFF')
                raise RuntimeError('Flat Lamp OFF command failed')
        else:
            self.logger.info('[FlatLamp] Successfully turned OFF')
    
    def _write(self, cmd):
        if self._serial.is_open:
            try:                 
                cmd = (cmd + '\r\n').encode('ascii')
                self._serial.write(cmd)
                time.sleep(.2)
                ack = self._serial.readline().decode('latin-1').rstrip() 
                        
                return ack
            except Exception as e:
                print("Error writing COM: "+ str(e))
                return "Error"
        else:
            return "Not Open"