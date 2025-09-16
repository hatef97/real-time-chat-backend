# naive per-connection limiter using in-memory counters (swap to Redis later)
import time
from collections import deque
from channels.middleware import BaseMiddleware



class SimpleWsRateLimiter(BaseMiddleware):
    def __init__(self, app, max_events=30, per_seconds=10):
        super().__init__(app)
        self.max_events = max_events
        self.per_seconds = per_seconds

    async def __call__(self, scope, receive, send):
        scope["__rates__"] = deque()
        async def limited_receive():
            now = time.monotonic()
            dq = scope["__rates__"]
            while dq and now - dq[0] > self.per_seconds:
                dq.popleft()
            if len(dq) >= self.max_events:
                await send({"type": "websocket.close", "code": 4408})  # policy violation
                return {"type": "websocket.disconnect"}
            msg = await receive()
            if msg.get("type", "").startswith("websocket"):
                dq.append(time.monotonic())
            return msg
        return await super().__call__(scope, limited_receive, send)
