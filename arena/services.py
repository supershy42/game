
def get_arena_group_name(arena_id):
    return f"arena_{arena_id}"

def arena_websocket_url(arena_id):
    return f"/ws/arena/{arena_id}/"