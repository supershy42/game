import jwt
import datetime
from config.settings import WS_SECRET_KEY, WS_ALGORITHM

def create_ws_token(user_id, reception_id, expiration_minutes=30):
    payload = {
        "user_id": user_id,
        "reception_id": reception_id,
        "exp": datetime.timezone.now() + datetime.timedelta(minutes=expiration_minutes)
    }
    token = jwt.encode(payload, WS_SECRET_KEY, algorithm=WS_ALGORITHM)
    return token

def verify_ws_token(token):
    try:
        payload = jwt.decode(token, WS_SECRET_KEY, algorithms=[WS_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None