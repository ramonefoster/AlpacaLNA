import time
from alpaca.focuser import *      
from alpaca.exceptions import *     
from alpaca import discovery

svrs = discovery.search_ipv4()  # Note there is an IPv6 function as well
print(svrs)
F = Focuser('127.0.0.1:5555', 0) 
try:
    F.Connected = True
    print(f'Connected to {F.Name}')
    print(F.Description)
    print(f'Focuser position: {F.Position}')
    F.Move(F.Position+500)    
    while(F.IsMoving):
        print(f"Pos: {F.Position}")
        time.sleep(.5)               
    print('... Movimentacao completa.')
    print(f'POSICAO={F.Position} ')    
except Exception as e:              
    print(f'Movimentacao falhou: {str(e)}')
finally:                            
    print("Disconnecting...")
    F.Connected = False