"""Motor de busca: DDG para exact match, SearXNG para genérico."""

import asyncio
import logging
import os
import httpx
from duckduckgo_search import DDGS

log = logging.getLogger(__name__)

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")


async def _searxng_search(query: str, max_results: int = 8) -> list[dict]:
    """Busca via SearXNG (bom para queries genéricas, ruim para exact match)."""
    results = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SEARXNG_URL}/search",
                params={"q": query, "format": "json", "language": "pt-BR", "pageno": 1},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                seen_urls = set()
                for r in data.get("results", []):
                    url = r.get("url", "")
                    title = r.get("title", "")
                    if not url or not title or len(title) < 5:
                        continue
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": r.get("content", ""),
                    })
                    if len(results) >= max_results:
                        break
    except Exception as e:
        log.warning(f"SearXNG failed: {str(e)[:80]}")
    return results


def _ddg_search(query: str, max_results: int = 8) -> list[dict]:
    """Busca no DuckDuckGo (suporta site: e exact match com aspas)."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region="br-pt", max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        log.warning(f"DDG failed: {str(e)[:80]}")
    return results


def _needs_exact_match(query: str) -> bool:
    """Detecta se a query precisa de exact match (tem aspas ou operadores)."""
    return '"' in query or "site:" in query or "filetype:" in query


async def search_web(query: str, max_results: int = 8) -> list[dict]:
    """Busca inteligente: DDG para exact match, SearXNG para genérico."""
    if _needs_exact_match(query):
        # DDG respeita aspas e site: — usar como primário
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _ddg_search, query, max_results)
        if results:
            return results
        # Fallback SearXNG (sem aspas)
        clean_query = query.replace('"', '').replace("site:", "")
        return await _searxng_search(clean_query, max_results)
    else:
        # Queries genéricas — SearXNG é melhor (múltiplas engines)
        results = await _searxng_search(query, max_results)
        if results:
            return results
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _ddg_search, query, max_results)


async def search_dorks(dorks: list[dict], progress_callback=None) -> list[dict]:
    """Executa dorks com engine apropriada e delay para rate limit."""
    results = []
    ddg_count = 0  # Track DDG usage for rate limiting

    for i, dork_info in enumerate(dorks):
        step_id = f"dork_{i}"
        source = dork_info["source"]

        if progress_callback:
            try:
                await progress_callback({
                    "step_id": step_id,
                    "label": f"Buscando — {source}",
                    "status": "running",
                    "count": 0,
                })
            except Exception:
                pass

        query = dork_info["dork"]
        uses_ddg = _needs_exact_match(query)

        # Rate limit DDG: wait longer between DDG queries
        if uses_ddg and ddg_count > 0:
            await asyncio.sleep(8)
        elif i > 0:
            await asyncio.sleep(1)

        items = await search_web(query, max_results=5)

        if uses_ddg:
            ddg_count += 1

        if progress_callback:
            try:
                await progress_callback({
                    "step_id": step_id,
                    "label": f"{'DDG' if uses_ddg else 'SearXNG'} — {source}",
                    "status": "done" if items else "empty",
                    "count": len(items),
                })
            except Exception:
                pass

        if items:
            results.append({
                "source": dork_info["source"],
                "description": dork_info["description"],
                "dork": dork_info["dork"],
                "results": items,
            })

    return results
