from channels.layers import get_channel_layer

async def broadcast_event(group_name, type, event=""):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        group_name,
        {
            'type': type,
            'message': event
        }
    )