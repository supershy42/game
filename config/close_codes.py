from enum import Enum

class CloseCode(Enum):
    NO_RECEPTION = 4000
    NO_USER = 4001
    ALREADY_IN_ROOM = 4002
    GAME_STARTED = 5000
    
    def __int__(self):
        return self.value
    