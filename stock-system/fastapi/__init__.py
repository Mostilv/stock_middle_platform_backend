from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _Status:
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_204_NO_CONTENT = 204
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_500_INTERNAL_SERVER_ERROR = 500


status = _Status()


class Depends:
    def __init__(self, dependency: Callable[..., Any]) -> None:
        self.dependency = dependency


class Request:
    def __init__(self, app: "FastAPI") -> None:
        self.app = app
        self.state = getattr(app, "state", None)


@dataclass
class ParameterSpec:
    default: Any
    alias: Optional[str] = None


def Query(default: Any = None, description: str | None = None, alias: str | None = None, **_: Any) -> ParameterSpec:
    return ParameterSpec(default=default, alias=alias)


def Path(default: Any = None, description: str | None = None, alias: str | None = None, **_: Any) -> ParameterSpec:
    return ParameterSpec(default=default, alias=alias)


def Header(default: Any = None, alias: str | None = None, **_: Any) -> ParameterSpec:
    return ParameterSpec(default=default, alias=alias)


@dataclass
class Route:
    path: str
    method: str
    endpoint: Callable[..., Awaitable[Any]]
    dependencies: List[Depends]
    tags: List[str]
    name: Optional[str]


class APIRouter:
    def __init__(
        self,
        *,
        prefix: str = "",
        dependencies: Optional[List[Depends]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        self.prefix = prefix
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.routes: List[Route] = []

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Awaitable[Any]],
        *,
        methods: List[str],
        dependencies: Optional[List[Depends]] = None,
        tags: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> None:
        deps = self.dependencies + (dependencies or [])
        route = Route(path, methods[0].upper(), endpoint, deps, self.tags + (tags or []), name)
        self.routes.append(route)

    def get(
        self,
        path: str,
        *,
        dependencies: Optional[List[Depends]] = None,
        tags: Optional[List[str]] = None,
        name: Optional[str] = None,
        **_: Any,
    ):
        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self.add_api_route(path, func, methods=["GET"], dependencies=dependencies, tags=tags, name=name)
            return func

        return decorator

    def post(
        self,
        path: str,
        *,
        dependencies: Optional[List[Depends]] = None,
        tags: Optional[List[str]] = None,
        name: Optional[str] = None,
        **_: Any,
    ):
        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self.add_api_route(path, func, methods=["POST"], dependencies=dependencies, tags=tags, name=name)
            return func

        return decorator


class RouterState:
    def __init__(self) -> None:
        self.routes: List[Route] = []
        self.on_startup: List[Callable[[], Awaitable[None]]] = []
        self.on_shutdown: List[Callable[[], Awaitable[None]]] = []


class FastAPI:
    def __init__(self, *, title: str = "FastAPI", version: str = "0.1.0") -> None:
        self.title = title
        self.version = version
        self.router = RouterState()
        self.state = type("State", (), {})()

    def include_router(self, router: APIRouter) -> None:
        for route in router.routes:
            full_path = (router.prefix or "") + route.path
            self.router.routes.append(
                Route(full_path, route.method, route.endpoint, route.dependencies, route.tags, route.name)
            )

    def add_api_route(self, path: str, endpoint: Callable[..., Awaitable[Any]], *, methods: List[str]) -> None:
        self.router.routes.append(Route(path, methods[0].upper(), endpoint, [], [], None))

    def on_event(self, event_type: str) -> Callable[[Callable[..., Awaitable[None]]], Callable[..., Awaitable[None]]]:
        if event_type not in {"startup", "shutdown"}:
            raise ValueError("Unsupported event type")

        def decorator(func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
            if event_type == "startup":
                self.router.on_startup.append(func)
            else:
                self.router.on_shutdown.append(func)
            return func

        return decorator


class Response:
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Any:
        return self._body


async def _resolve_dependency(
    dep: Depends,
    request_state: Dict[str, Any],
    *,
    app: "FastAPI",
    path_params: Dict[str, Any],
    query_params: Dict[str, Any],
    headers: Dict[str, Any],
    json_body: Any,
) -> Any:
    callable_ = dep.dependency
    signature = inspect.signature(callable_)
    header_lookup = {k.lower(): v for k, v in headers.items()}
    values: Dict[str, Any] = {}
    request_obj = Request(app)
    for name, param in signature.parameters.items():
        if name in path_params:
            values[name] = path_params[name]
            continue
        annotation = param.annotation
        if annotation is Request or getattr(annotation, "__name__", "") == "Request" or name == "request":
            values[name] = request_obj
            continue
        default = param.default
        if isinstance(default, ParameterSpec):
            alias = default.alias or name
            alias_lower = alias.lower()
            header_value = header_lookup.get(alias_lower)
            if header_value is None:
                header_value = headers.get(alias) or headers.get(alias_lower)
            if header_value is not None:
                values[name] = header_value
            else:
                values[name] = query_params.get(alias, default.default)
        elif isinstance(default, Depends):
            dep_value = await _resolve_dependency(
                default,
                request_state,
                app=app,
                path_params=path_params,
                query_params=query_params,
                headers=headers,
                json_body=json_body,
            )
            values[name] = dep_value
        elif json_body is not None and param.default is inspect._empty:
            if hasattr(annotation, "from_dict"):
                values[name] = annotation.from_dict(json_body)
            else:
                values[name] = json_body
        else:
            values[name] = query_params.get(name, None if default is inspect._empty else default)
    result = callable_(**values)
    if inspect.isawaitable(result):
        result = await result
    if inspect.isasyncgen(result):
        value = await result.__anext__()
        request_state.setdefault("async_generators", []).append(result)
        return value
    if inspect.isgenerator(result):
        value = next(result)
        request_state.setdefault("generators", []).append(result)
        return value
    return result


async def _cleanup_dependencies(state: Dict[str, Any]) -> None:
    for agen in state.get("async_generators", []):
        await agen.aclose()
    for gen in state.get("generators", []):
        try:
            gen.close()
        except Exception:
            pass


async def call_endpoint(
    route: Route,
    app: FastAPI,
    *,
    path_params: Dict[str, Any],
    query_params: Dict[str, Any],
    headers: Dict[str, Any],
    json_body: Any,
) -> Response:
    state: Dict[str, Any] = {}
    header_lookup = {k.lower(): v for k, v in headers.items()}
    try:
        values: Dict[str, Any] = {}
        for dep in route.dependencies:
            await _resolve_dependency(
                dep,
                state,
                app=app,
                path_params=path_params,
                query_params=query_params,
                headers=headers,
                json_body=json_body,
            )
        signature = inspect.signature(route.endpoint)
        request_obj = Request(app)
        for name, param in signature.parameters.items():
            if name in values:
                continue
            if name in path_params:
                values[name] = path_params[name]
                continue
            annotation = param.annotation
            if annotation is Request or getattr(annotation, "__name__", "") == "Request" or name == "request":
                values[name] = request_obj
                continue
            default = param.default
            if isinstance(default, ParameterSpec):
                alias = default.alias or name
                alias_lower = alias.lower()
                if alias_lower in header_lookup:
                    values[name] = header_lookup.get(alias_lower, default.default)
                else:
                    values[name] = query_params.get(alias, default.default)
            elif isinstance(default, Depends):
                dep_value = await _resolve_dependency(
                    default,
                    state,
                    app=app,
                    path_params=path_params,
                    query_params=query_params,
                    headers=headers,
                    json_body=json_body,
                )
                values[name] = dep_value
            elif json_body is not None and param.default is inspect._empty:
                if hasattr(annotation, "from_dict"):
                    values[name] = annotation.from_dict(json_body)
                else:
                    values[name] = json_body
            else:
                values[name] = query_params.get(name, None if default is inspect._empty else default)
        result = route.endpoint(**values)
        if inspect.isawaitable(result):
            result = await result
        await _cleanup_dependencies(state)
        return Response(status.HTTP_200_OK, result if result is not None else {})
    except HTTPException as exc:
        await _cleanup_dependencies(state)
        return Response(exc.status_code, {"detail": exc.detail})


__all__ = [
    "FastAPI",
    "APIRouter",
    "Depends",
    "HTTPException",
    "Request",
    "status",
    "Query",
    "Path",
    "Header",
    "call_endpoint",
    "Response",
]
