from django.urls import reverse

def get_participants_key(reception_id):
    return f'reception_{reception_id}_participants'

def get_user_reception_key(user_name):
    return f'user_{user_name}_reception'

def websocket_reception_url(reception_id):
    return reverse("websocket_reception", kwargs={"reception_id": reception_id})