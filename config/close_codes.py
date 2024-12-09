from enum import Enum

class CloseCode(Enum):
    INVALID_TOKEN = 4000
    NO_RECEPTION = 4001
    NO_USER = 4002
    ALREADY_IN_ROOM = 4003
    GAME_STARTED = 5000
    
    def __int__(self):
        return self.value
    