import requests
import serial
import serial.tools.list_ports
from logging import Logger

from threading import Lock
from threading import Timer
import json
import time

class Focuser():
    def __init__(self, logger: Logger):  
        self._lock = Lock()
        self.name: str = 'LNA Focuser'
        self.logger = logger
        
        self._step_size: float = 1.0
        
        self._reverse = False
        self._absolute = True
        self._max_step = 7000
        self._max_increment = 100
        self._is_moving = False
        self._connected = False
        
        self._temp_comp = False 
        self._temp_comp_available = False
        self._temp = 0.0 
        self._steps_per_sec = 1

        self._position = 0
        self._tgt_position = 0
        self._stopped = True

        self._serial = None
        self._timeout = 1

        self._timer: Timer = None
        self._interval: float = 1.0 / self._steps_per_sec
    
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
        try:
            response = requests.get('http://your_server_ip:port/check_connection')
            if response.status_code == 200:
                self._connected = True
            else:
                self._connected = False
        except Exception as e:
            self._connected = False
        self._lock.release()            
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
    
    def start(self, from_run: bool = False) -> None:
        print('[start]')
        self._lock.acquire()
        print('[start] got lock')
        if from_run or self._stopped:
            self._stopped = False
            print('[start] new timer')
            self._timer = Timer(self._interval, self._run)
            print('[start] now start the timer')
            self._timer.start()
            print('[start] timer started')
            self._lock.release()
            print('[start] lock released')
        else:
            self._lock.release()
            print('[start] lock released')
    
    def _run(self) -> None:
        print('[_run] (tmr expired) get lock')
        self.position
        self._lock.acquire()
        delta = self._tgt_position - self._position
        self._lock.release()
        print(f'[_run] final delta={str(delta)}')
        if delta != 0:
            self.position
            self._lock.acquire()
            self._is_moving = True
            self._lock.release()
        else:
            self._lock.acquire()
            self._is_moving = False
            self._stopped = True
            self._lock.release()
        print('[_run] lock released')
        if self._is_moving:
            print('[_run] more motion needed, start another timer interval')
            self.start(from_run = True)
    
    @property
    def temp(self):
        self._lock.acquire()
        res = self._temp
        self._lock.release()
        return res
    
    @property
    def temp_comp_available(self):
        self._lock.acquire()
        res = self._temp_comp_available
        self._lock.release()
        return res
    
    @property
    def temp_comp(self):
        self._lock.acquire()
        res = self._temp_comp
        self._lock.release()
        return res
    @temp_comp.setter
    def temp_comp(self, temp: bool):
        self._lock.acquire()
        if not self._temp_comp_available and temp:
            self._temp_comp = False
        elif self._temp_comp_available:        
            self._temp_comp = temp
        self._lock.release()
        res = self._temp_comp
        if self._temp_comp:
            self.logger.info(f'[temp_comp] {str(res)}')
        else:
            self.logger.info(f'[temp_comp] {str(res)}')

    @property
    def position(self) -> int:
        max_retries = 3  
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get('http://your_server_ip:port/get_position')
                data = json.loads(response.text)
                self._lock.acquire()
                if 'status' in data and 'message' in data:
                    self._position = int(data['message'])
                else:
                    raise RuntimeError('Invalid response format')                
                self.logger.debug(f'[position] {str(self._position)}')
                self._lock.release()
                print(f"[position] {self._position}")
                return self._position
            except ValueError as e:
                # Handle the ValueError (or other exceptions) here
                self.logger.error(f'Error reading position: {e}')
                retries += 1  
                self._lock.release()        
        return -1        
    
    @property
    def is_moving(self) -> bool:
        self._lock.acquire()
        # self._is_moving = self._write("R\n")
        res = self._is_moving
        self._lock.release()
        self.logger.debug(f'[is_moving] {str(res)}')
        return res
    
    @property
    def absolute(self) -> bool:  
        self._lock.acquire()      
        res = self._absolute
        self._lock.release()
        self.logger.debug(f'[absolute] {str(res)}')
        return res

    @property
    def max_increment(self) -> bool:
        self._lock.acquire()
        res = self._max_increment
        self._lock.release()
        self.logger.debug(f'[max_increment] {str(res)}')
        return res

    @property
    def max_step(self) -> bool:
        self._lock.acquire()
        res = self._max_step
        self._lock.release()
        self.logger.debug(f'[max_step] {str(res)}')
        return res

    @property
    def step_size(self) -> bool:
        self._lock.acquire()
        res = self._step_size
        self._lock.release()
        self.logger.debug(f'[step_size] {str(res)}')
        return res

    def move(self, position: int):
        self.logger.debug(f'[Move] pos={str(position)}')
        self._lock.acquire()        
        if self._is_moving:
            self._lock.release()
            raise RuntimeError('Cannot start a move while the focuser is moving')
        if position > self._max_step:
            raise RuntimeError('Invalid Steps')
        if self._temp_comp:
            raise RuntimeError('Invalid TempComp')
        self._tgt_position = position 
        resp = requests.get(f'http://your_server_ip:port/move?M{position}')        
        c = 0
        while not resp.status_code == 200:
            if c >= 5:
                self._is_moving = True
            c += 1     
            resp = requests.get(f'http://your_server_ip:port/move?M{position}')   
        self._is_moving = bool(resp) 
        print('[move]', self._is_moving)
        self._lock.release() 
        self.start() 

    def stop(self) -> None:
        self._lock.acquire()
        print('[stop] Stopping...')
        self._stopped = True
        self._is_moving = False
        if self._timer is not None:
            self._timer.cancel()
        self._timer = None
        self._lock.release()      
    
    def Halt(self) -> None:
        self.logger.debug('[Halt]')
        requests.get(f'http://your_server_ip:port/stop')
        self.stop()        
