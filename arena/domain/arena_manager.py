from .arena import Arena
from arena.services import ArenaService

class ArenaManager:
    _arenas = {}
    
    @classmethod
    def get_arena(cls, arena_id):
        if arena_id not in cls._arenas:
            cls._arenas[arena_id] = Arena(unique_id=ArenaService.generate_unique_id())
        return cls._arenas[arena_id]
    
    @classmethod
    def remove_arena(cls, arena_id):
        if arena_id in cls._arenas:
            del cls._arenas[arena_id]