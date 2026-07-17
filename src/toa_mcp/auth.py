"""Bearer-token ASGI middleware (Q5).

Wraps FastMCP's streamable_http_app(). Deliberately not the SDK's OAuth
`auth_server_provider` path — a single shared bearer is what two known clients need.
"""

import hmac

from starlette.types import ASGIApp, Receive, Scope, Send


class BearerTokenMiddleware:
    """Rejects any HTTP request without a matching `Authorization: Bearer <token>`."""

    def __init__(self, app: ASGIApp, token: str, exempt_paths: frozenset[str] = frozenset({"/healthz"})):
        self.app = app
        self._token = token
        self._exempt = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self._exempt:
            await self.app(scope, receive, send)
            return

        if not self._authorized(scope):
            await self._deny(send)
            return

        await self.app(scope, receive, send)

    def _authorized(self, scope: Scope) -> bool:
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                prefix = b"Bearer "
                if not value.startswith(prefix):
                    return False
                # compare_digest to avoid leaking the token via timing
                return hmac.compare_digest(value[len(prefix) :], self._token.encode())
        return False

    async def _deny(self, send: Send) -> None:
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b'Bearer realm="toa-mcp"'),
            ],
        })
        await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
