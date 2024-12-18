import jwt
import json
from django.utils.deprecation import MiddlewareMixin
from channels.middleware import BaseMiddleware
from django.http import JsonResponse


class CustomHttpMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token_line = request.headers.get("Authorization")
        if not token_line:
            return JsonResponse({"error": "Authentication token missing."}, status=401)

        try:
            token = token_line.split(" ")[1]
            request.token = token
            payload = jwt.decode(token, options={"verify_signature": False})
            request.user_id = payload.get("user_id")
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=401)

class CustomWsMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = get_jwt(scope['headers'])
        # token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM0MTg1NDM5LCJpYXQiOjE3MzQxODUxMzksImp0aSI6IjkxODQ5ODdkODI5NjQ0MzVhZDZkNGFjYTZlODAxYTgxIiwidXNlcl9pZCI6MX0.kqOvvPqz4LiYbNGtCO4uqd2H_h3Xr6pN_DLe5lmm0T4'
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