from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .formulas import DEFAULT_DATA, compute_results, normalize_data

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class ConnectionManager:
    def __init__(self) -> None:
        self.active: Set[WebSocket] = set()
        self.lock = asyncio.Lock()
        self.data: Dict[str, Any] = dict(DEFAULT_DATA)

    def _build_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = normalize_data(data)
        results = compute_results(normalized)
        return {"data": normalized, "results": results}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.active.add(websocket)
            payload = self._build_payload(self.data)
            self.data = payload["data"]
        await websocket.send_json(payload)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self.lock:
            self.active.discard(websocket)

    async def update_data(self, new_data: Dict[str, Any]) -> None:
        async with self.lock:
            self.data.update(new_data)
            payload = self._build_payload(self.data)
            self.data = payload["data"]
        await self.broadcast(payload)

    async def broadcast(
        self,
        payload: Dict[str, Any],
        sockets: Optional[Iterable[WebSocket]] = None,
    ) -> None:
        async with self.lock:
            targets = list(sockets) if sockets is not None else list(self.active)

        for websocket in targets:
            try:
                await websocket.send_json(payload)
            except Exception:
                await self.disconnect(websocket)


manager = ConnectionManager()


@app.get("/", response_class=RedirectResponse)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/form")


@app.get("/form", response_class=HTMLResponse)
async def form_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("form.html", {"request": request})


@app.get("/print", response_class=HTMLResponse)
async def print_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("print.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                continue
            data = message.get("data")
            if isinstance(data, dict):
                await manager.update_data(data)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
