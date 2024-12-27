from enum import Enum

class CloseCode(Enum):
    INVALID_TOKEN = 4000
    INVALID_RECEPTION = 4001
    INVALID_USER = 4002
    INVALID_ACCESS = 4003
    ARENA_FULL = 4004
    ARENA_STARTED = 5000
    
    def __int__(self):
        return self.value
    