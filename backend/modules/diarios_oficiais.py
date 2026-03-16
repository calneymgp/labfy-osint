"""Busca em Diários Oficiais via API do Querido Diário (open source)."""

import httpx


async def search_diarios(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca publicações em diários oficiais municipais."""
    results = []

    try:
        resp = await client.get(
            "https://queridodiario.ok.org.br/api/gazettes",
            params={
                "querystring": query,
                "excerpt_size": 500,
                "number_of_excerpts": 3,
                "size": 10,
                "sort_by": "relevance",
            },
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("gazettes", []):
                excerpts = item.get("excerpts", [])
                results.append({
                    "fonte": "Querido Diário",
                    "municipio": item.get("territory_name", ""),
                    "uf": item.get("state_code", ""),
                    "data": item.get("date", ""),
                    "edicao": item.get("edition", ""),
                    "url": item.get("url", ""),
                    "trechos": excerpts,
                })
    except Exception:
        pass

    return results


async def search_dou(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca no Diário Oficial da União via imprensa nacional."""
    results = []

    try:
        resp = await client.get(
            "https://www.in.gov.br/servicos/diario-oficial-da-uniao/pesquisa",
            params={"q": query},
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            },
        )
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select(".resultados-item, .resultado-busca")[:10]:
                title_el = item.select_one("h5, .titulo, a")
                date_el = item.select_one(".data, .date, time")
                link_el = item.select_one("a[href]")
                if title_el:
                    results.append({
                        "fonte": "DOU - Imprensa Nacional",
                        "titulo": title_el.get_text(strip=True),
                        "data": date_el.get_text(strip=True) if date_el else "",
                        "url": f"https://www.in.gov.br{link_el['href']}" if link_el and link_el.get("href", "").startswith("/") else (link_el["href"] if link_el else ""),
                    })
    except Exception:
        pass

    return results
