import time
from alpaca.focuser import *      
from alpaca.exceptions import *     

F = Focuser('192.168.15.162:5555', 0) 
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