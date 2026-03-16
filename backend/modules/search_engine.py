"""Motor de busca multi-engine: SearXNG (principal) → DuckDuckGo (fallback)."""

import asyncio
import logging
import os
import httpx
from duckduckgo_search import DDGS

log = logging.getLogger(__name__)

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")


async def _searxng_search(query: str, max_results: int = 8, engines: str = "") -> list[dict]:
    """Busca via SearXNG local (meta-search: Google + Bing + DDG + Brave + Qwant)."""
    results = []
    try:
        params = {
            "q": query,
            "format": "json",
            "language": "pt-BR",
            "pageno": 1,
        }
        if engines:
            params["engines"] = engines

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SEARXNG_URL}/search",
                params=params,
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                seen_urls = set()
                for r in data.get("results", []):
                    url = r.get("url", "")
                    title = r.get("title", "")
                    # Filtra resultados sem URL real ou com gibberish
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
    """Busca síncrona no DuckDuckGo (fallback)."""
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


async def search_web(query: str, max_results: int = 8) -> list[dict]:
    """Busca com fallback: SearXNG (google,bing) → SearXNG (all) → DDG."""
    # Para dorks com site:/filetype:, usar engines que suportam
    has_operators = any(op in query for op in ["site:", "filetype:", "inurl:", "intitle:"])
    if has_operators:
        results = await _searxng_search(query, max_results, engines="google,bing,brave")
    else:
        results = await _searxng_search(query, max_results)

    if not results:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _ddg_search, query, max_results)
    return results


async def search_dorks(dorks: list[dict], progress_callback=None) -> list[dict]:
    """Executa dorks via SearXNG (sem rate limit) com delay mínimo."""
    results = []

    for i, dork_info in enumerate(dorks):
        if progress_callback:
            try:
                await progress_callback(
                    f"[{i+1}/{len(dorks)}] Buscando: {dork_info['source']}..."
                )
            except Exception:
                pass

        items = await search_web(dork_info["dork"], max_results=5)
        if items:
            results.append({
                "source": dork_info["source"],
                "description": dork_info["description"],
                "dork": dork_info["dork"],
                "results": items,
            })

        # Delay mínimo entre buscas (SearXNG local não tem rate limit agressivo)
        if i < len(dorks) - 1:
            await asyncio.sleep(1)

    return results
