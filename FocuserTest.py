import time
from alpaca.focuser import *      # Multiple Classes including Enumerations
from alpaca.exceptions import *     # Or just the exceptions you want to catch

F = Focuser('192.168.15.162:5555', 0) # Local Omni Simulator
try:
    F.Connected = True
    print(f'Connected to {F.Name}')
    print(F.Description)
    print(f'Focuser position: {F.Position}')
    F.Move(F.Position+500)    # 2 hrs east of meridian
    while(F.IsMoving):
        print(f"Pos: {F.Position}")
        time.sleep(.5)               # What do a few seconds matter?
    print('... Movimentacao completa.')
    print(f'POSICAO={F.Position} ')    
except Exception as e:              # Should catch specific InvalidOperationException
    print(f'Slew failed: {str(e)}')
finally:                            # Assure that you disconnect
    print("Disconnecting...")
    F.Connected = False