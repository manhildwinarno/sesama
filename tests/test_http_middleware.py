"""python tests/test_http_middleware.py: Streamlit gzip ASGI ordering regression."""
import asyncio
from streamlit.web.server.starlette.starlette_gzip_middleware import MediaAwareGZipMiddleware

async def check():
    for encoding in (b'gzip', b'identity'):
        messages = []
        async def app(scope, receive, send):
            await send({'type':'http.response.start', 'status':200,
                        'headers':[(b'content-type',b'text/javascript'), (b'content-encoding',b'gzip')]})
            await send({'type':'http.response.body', 'body':b'asset'})
        async def send(message):
            messages.append(message)
        async def receive():
            return {'type':'http.request', 'body':b''}
        await MediaAwareGZipMiddleware(app)({'type':'http', 'headers':[(b'accept-encoding',encoding)]}, receive, send)
        assert [m['type'] for m in messages] == ['http.response.start', 'http.response.body'], messages

asyncio.run(check())
print('PASS: encoded static response sends ASGI start before body with gzip and identity clients.')
