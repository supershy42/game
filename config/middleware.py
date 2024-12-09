import jwt
import json
from django.utils.deprecation import MiddlewareMixin
from channels.middleware import BaseMiddleware
from django.http import JsonResponse


class CustomHttpMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.headers.get("Authorization")
        if not token:
            return JsonResponse({"error": "Authentication token missing."}, status=401)

        try:
            payload = jwt.decode(token.split(" ")[1], options={"verify_signature": False})
            request.user_id = payload.get("user_id")
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=401)

class CustomWsMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = get_jwt(scope['headers'])
        if not token:
            return await self.reject_request(send, "Authentication token missing.")
        
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            scope['user_id'] = user_id
            
        except Exception as e:
            return await self.reject_request(send, str(e))
        
        scope['token'] = token
        return await super().__call__(scope, receive, send)
                    
    async def reject_request(self, send, message, status=401):
        headers = [(b"content-type", b"application/json")]
        body = json.dumps({"error": message}).encode('utf-8')

        await send({
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
        
def get_jwt(headers):
    auth_header = dict(headers).get(b'authorization')
    if auth_header:
        auth_header = auth_header.decode()
        prefix, token = auth_header.split(' ')
        if prefix.lower() == 'bearer':
            return token
    return None