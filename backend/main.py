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

app = FastAPI(title="Labfy OSINT", version="0.2.0")

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
    """Busca via WebSocket com step tracking em tempo real."""
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
        tipo_labels = {"nome": "Nome", "cpf": "CPF", "cnpj": "CNPJ", "email": "Email", "telefone": "Telefone"}
        await websocket.send_json({
            "type": "step",
            "step_id": "detect",
            "label": f"Tipo detectado: {tipo_labels.get(tipo, tipo)}",
            "status": "done",
            "count": 0,
        })

        async def send_step(step_data):
            """Envia step update estruturado."""
            try:
                if isinstance(step_data, dict):
                    await websocket.send_json({"type": "step", **step_data})
                else:
                    # Fallback para string (compatibilidade)
                    await websocket.send_json({"type": "step", "step_id": "info", "label": str(step_data), "status": "done"})
            except Exception:
                pass

        result = await run_search(query, progress_callback=send_step)

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
