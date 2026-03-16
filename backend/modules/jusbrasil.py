"""Scraping de resultados do JusBrasil (consulta pública)."""

import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


async def search_jusbrasil(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca processos e publicações no JusBrasil."""
    results = []
    url = f"https://www.jusbrasil.com.br/jurisprudencia/busca?q={quote_plus(query)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    try:
        resp = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")

            for item in soup.select('[class*="SearchResult"], [class*="search-result"], article')[:10]:
                title_el = item.select_one("h2, h3, [class*='title'], a")
                link_el = item.select_one("a[href]")
                snippet_el = item.select_one("[class*='snippet'], [class*='description'], p")

                if title_el:
                    href = ""
                    if link_el:
                        href = link_el.get("href", "")
                        if href.startswith("/"):
                            href = f"https://www.jusbrasil.com.br{href}"

                    results.append({
                        "fonte": "JusBrasil",
                        "titulo": title_el.get_text(strip=True)[:200],
                        "url": href,
                        "trecho": snippet_el.get_text(strip=True)[:500] if snippet_el else "",
                    })
    except Exception:
        pass

    # Também busca em tópicos/artigos
    try:
        url2 = f"https://www.jusbrasil.com.br/busca?q={quote_plus(query)}"
        resp2 = await client.get(url2, headers=headers, timeout=15, follow_redirects=True)
        if resp2.status_code == 200:
            soup2 = BeautifulSoup(resp2.text, "lxml")
            for item in soup2.select("a[href*='/artigos/'], a[href*='/noticias/'], a[href*='/topicos/']")[:5]:
                title = item.get_text(strip=True)
                href = item.get("href", "")
                if href.startswith("/"):
                    href = f"https://www.jusbrasil.com.br{href}"
                if title and len(title) > 10:
                    results.append({
                        "fonte": "JusBrasil (artigos/notícias)",
                        "titulo": title[:200],
                        "url": href,
                        "trecho": "",
                    })
    except Exception:
        pass

    return results


async def search_escavador(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca no Escavador (dados públicos de pessoas e empresas)."""
    results = []
    url = f"https://www.escavador.com/busca?q={quote_plus(query)}&type=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    try:
        resp = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select('[class*="result"], [class*="card"], article')[:10]:
                title_el = item.select_one("h2, h3, h4, a[class*='name']")
                link_el = item.select_one("a[href]")
                detail_el = item.select_one("[class*='detail'], [class*='info'], p")

                if title_el:
                    href = ""
                    if link_el:
                        href = link_el.get("href", "")
                        if href.startswith("/"):
                            href = f"https://www.escavador.com{href}"

                    results.append({
                        "fonte": "Escavador",
                        "titulo": title_el.get_text(strip=True)[:200],
                        "url": href,
                        "trecho": detail_el.get_text(strip=True)[:500] if detail_el else "",
                    })
    except Exception:
        pass

    return results
