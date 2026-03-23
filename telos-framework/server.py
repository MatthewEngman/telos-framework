"""Thin FastAPI shell around the Telos MILP runtime (canvas + WebSocket)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from telos import DockerActuator, TelosRuntime

ROOT = Path(__file__).resolve().parent

app = FastAPI()
os_runtime = TelosRuntime()
os_runtime.attach_actuator(DockerActuator())


@app.get("/")
async def get_ui():
    return HTMLResponse((ROOT / "index.html").read_text(encoding="utf-8"))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[Telos OS] Canvas connected.")

    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                raise

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if "schema" not in data or not data["schema"]:
                continue

            t0 = time.perf_counter()
            result = os_runtime.tick(data["schema"], data.get("parameters") or {})
            ms = (time.perf_counter() - t0) * 1000.0

            if result["status"] == "HEALTHY":
                await websocket.send_text(
                    json.dumps(
                        {
                            "status": "HEALTHY",
                            "ms": ms,
                            "router": result["router"],
                            "db": result["db"],
                            "memory": result.get("memory", {}),
                        }
                    )
                )
            else:
                detail = result.get("detail")
                payload: dict = {"status": "FATAL CONFLICT"}
                if detail is not None:
                    payload["detail"] = detail
                await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        print("[Telos OS] Canvas disconnected.")
    except Exception as e:
        print(f"[Telos OS] WebSocket error: {e}")


if __name__ == "__main__":
    use_reload = os.environ.get("TELOS_RELOAD", "").lower() in ("1", "true", "yes")
    port = int(os.environ.get("TELOS_PORT", "8000"))
    print(f"\n[Telos SDK] Canvas at http://127.0.0.1:{port}\n")
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=port,
        reload=use_reload,
        ws_ping_interval=20.0,
        ws_ping_timeout=20.0,
    )
