"""Labfy OSINT — API Principal."""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from modules.aggregator import run_search
from modules.detector import detect_input_type

app = FastAPI(title="Labfy OSINT", version="0.1.0")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class SearchRequest(BaseModel):
    query: str


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "labfy-osint"}


@app.post("/api/search")
async def search(req: SearchRequest):
    """Busca síncrona — retorna tudo de uma vez."""
    query = req.query.strip()
    if not query or len(query) < 3:
        return JSONResponse(
            status_code=400,
            content={"error": "Query deve ter pelo menos 3 caracteres"},
        )

    result = await run_search(query)
    return {
        "query": result["query"],
        "tipo": result["tipo"],
        "timestamp": result["timestamp"],
        "markdown": result["markdown"],
        "stats": {
            "fontes": _count_sections(result),
            "erros": len(result.get("erros", [])),
        },
    }


@app.get("/api/detect")
async def detect(q: str):
    """Detecta tipo do input."""
    return {"query": q, "tipo": detect_input_type(q)}


@app.websocket("/ws/search")
async def ws_search(websocket: WebSocket):
    """Busca via WebSocket com progresso em tempo real."""
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        req = json.loads(data)
        query = req.get("query", "").strip()

        if not query or len(query) < 3:
            await websocket.send_json({"type": "error", "message": "Query muito curta"})
            await websocket.close()
            return

        tipo = detect_input_type(query)
        await websocket.send_json({"type": "info", "message": f"Tipo detectado: {tipo}"})
        await websocket.send_json({"type": "progress", "message": "Iniciando varredura..."})

        async def send_progress(msg):
            try:
                await websocket.send_json({"type": "progress", "message": msg})
            except Exception:
                pass

        result = await run_search(query, progress_callback=send_progress)

        await websocket.send_json({
            "type": "result",
            "markdown": result["markdown"],
            "stats": {
                "fontes": _count_sections(result),
                "erros": len(result.get("erros", [])),
            },
        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


def _count_sections(result: dict) -> int:
    count = 0
    for key in ["cpf_data", "cnpj_data", "whois_data"]:
        if result.get(key):
            count += 1
    for key in ["cnpjs_associados", "diarios", "dou", "jusbrasil", "escavador", "ceis", "servidores", "google_results"]:
        if result.get(key):
            count += 1
    return count


# Frontend estático
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
