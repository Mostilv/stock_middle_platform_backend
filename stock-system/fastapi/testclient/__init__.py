from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from .. import Response, call_endpoint


class TestResponse:
    def __init__(self, response: Response) -> None:
        self.status_code = response.status_code
        self._payload = response.json()

    def json(self) -> Any:
        return self._payload

    @property
    def text(self) -> str:
        return str(self._payload)


class TestClient:
    def __init__(self, app) -> None:
        self.app = app
        self._entered = False

    def __enter__(self) -> "TestClient":
        asyncio.run(self._run_startup())
        self._entered = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        asyncio.run(self._run_shutdown())
        self._entered = False

    async def _run_startup(self) -> None:
        for handler in self.app.router.on_startup:
            await handler()

    async def _run_shutdown(self) -> None:
        for handler in self.app.router.on_shutdown:
            await handler()

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> TestResponse:
        method = method.upper()
        params = params or {}
        headers = headers or {}
        parsed = urlparse(url)
        path = parsed.path
        query_params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        query_params.update(params)
        for route in self.app.router.routes:
            if route.method != method:
                continue
            match, path_params = self._match_path(route.path, path)
            if not match:
                continue
            response = asyncio.run(
                call_endpoint(
                    route,
                    self.app,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    json_body=json,
                )
            )
            return TestResponse(response)
        return TestResponse(Response(404, {"detail": "Not Found"}))

    def get(self, url: str, *, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> TestResponse:
        return self.request("GET", url, params=params, headers=headers)

    def post(
        self,
        url: str,
        *,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> TestResponse:
        return self.request("POST", url, json=json, params=params, headers=headers)

    @staticmethod
    def _match_path(pattern: str, actual: str) -> tuple[bool, Dict[str, str]]:
        pattern_parts = [part for part in pattern.strip("/").split("/") if part]
        actual_parts = [part for part in actual.strip("/").split("/") if part]
        if len(pattern_parts) != len(actual_parts):
            return False, {}
        params: Dict[str, str] = {}
        for expected, value in zip(pattern_parts, actual_parts):
            if expected.startswith("{") and expected.endswith("}"):
                params[expected[1:-1]] = value
            elif expected != value:
                return False, {}
        return True, params


__all__ = ["TestClient", "TestResponse"]
