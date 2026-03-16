"""Gera Google Dorks e executa buscas via httpx (fallback scraping)."""

import httpx
from urllib.parse import quote_plus


def build_dorks(query: str, input_type: str) -> list[dict]:
    """Gera lista de dorks baseado no tipo de input."""
    dorks = []

    if input_type == "nome":
        dorks.extend([
            {
                "source": "JusBrasil",
                "dork": f'site:jusbrasil.com.br "{query}"',
                "description": "Processos judiciais no JusBrasil",
            },
            {
                "source": "JusBrasil (com email)",
                "dork": f'site:jusbrasil.com.br "{query}" email',
                "description": "Processos com menção a email",
            },
            {
                "source": "Diários Oficiais",
                "dork": f'site:diariooficial.com "{query}"',
                "description": "Publicações em diários oficiais",
            },
            {
                "source": "Gov.br (PDFs)",
                "dork": f'filetype:pdf site:gov.br "{query}" CPF telefone',
                "description": "Documentos governamentais em PDF",
            },
            {
                "source": "Licitações",
                "dork": f'site:comprasnet.gov.br "{query}"',
                "description": "Licitações e contratos públicos",
            },
            {
                "source": "LinkedIn",
                "dork": f'site:linkedin.com/in "{query}"',
                "description": "Perfil profissional no LinkedIn",
            },
            {
                "source": "Escavador",
                "dork": f'site:escavador.com "{query}"',
                "description": "Dados públicos no Escavador",
            },
            {
                "source": "CVM",
                "dork": f'site:cvm.gov.br "{query}"',
                "description": "Registros na CVM",
            },
            {
                "source": "Transparência",
                "dork": f'site:portaltransparencia.gov.br "{query}"',
                "description": "Portal da Transparência",
            },
        ])

    elif input_type == "cpf":
        dorks.extend([
            {
                "source": "Gov.br (PDFs com CPF)",
                "dork": f'filetype:pdf site:gov.br "{query}"',
                "description": "Documentos governamentais com este CPF",
            },
            {
                "source": "JusBrasil (CPF)",
                "dork": f'site:jusbrasil.com.br "{query}"',
                "description": "Processos judiciais com este CPF",
            },
            {
                "source": "Diários Oficiais (CPF)",
                "dork": f'site:diariooficial.com "{query}"',
                "description": "Publicações oficiais com este CPF",
            },
            {
                "source": "Licitações (CPF)",
                "dork": f'site:comprasnet.gov.br "{query}"',
                "description": "Licitações vinculadas a este CPF",
            },
        ])

    elif input_type == "cnpj":
        dorks.extend([
            {
                "source": "Receita Federal",
                "dork": f'site:receita.fazenda.gov.br "{query}"',
                "description": "Dados na Receita Federal",
            },
            {
                "source": "JusBrasil (CNPJ)",
                "dork": f'site:jusbrasil.com.br "{query}"',
                "description": "Processos judiciais com este CNPJ",
            },
            {
                "source": "Gov.br (CNPJ)",
                "dork": f'filetype:pdf site:gov.br "{query}"',
                "description": "Documentos governamentais com este CNPJ",
            },
            {
                "source": "CVM (CNPJ)",
                "dork": f'site:cvm.gov.br "{query}"',
                "description": "Registros CVM para este CNPJ",
            },
        ])

    elif input_type == "email":
        dorks.extend([
            {
                "source": "Google (email)",
                "dork": f'"{query}"',
                "description": "Menções públicas deste email",
            },
            {
                "source": "JusBrasil (email)",
                "dork": f'site:jusbrasil.com.br "{query}"',
                "description": "Processos com este email",
            },
            {
                "source": "LinkedIn (email)",
                "dork": f'site:linkedin.com "{query}"',
                "description": "LinkedIn associado a este email",
            },
            {
                "source": "GitHub (email)",
                "dork": f'site:github.com "{query}"',
                "description": "Perfil GitHub com este email",
            },
        ])

    elif input_type == "telefone":
        dorks.extend([
            {
                "source": "Google (telefone)",
                "dork": f'"{query}"',
                "description": "Menções públicas deste telefone",
            },
            {
                "source": "JusBrasil (telefone)",
                "dork": f'site:jusbrasil.com.br "{query}"',
                "description": "Processos com este telefone",
            },
            {
                "source": "Reclame Aqui",
                "dork": f'site:reclameaqui.com.br "{query}"',
                "description": "Reclamações com este telefone",
            },
        ])

    return dorks


async def search_google(dork: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca no Google via scraping básico. Retorna lista de resultados."""
    url = f"https://www.google.com/search?q={quote_plus(dork)}&num=10&hl=pt-BR"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }

    results = []
    try:
        resp = await client.get(url, headers=headers, timeout=15, follow_redirects=True)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for g in soup.select("div.g"):
                link_el = g.select_one("a[href]")
                title_el = g.select_one("h3")
                snippet_el = g.select_one("div[data-sncf]") or g.select_one(".VwiC3b")
                if link_el and title_el:
                    href = link_el["href"]
                    if href.startswith("/url?q="):
                        href = href.split("/url?q=")[1].split("&")[0]
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": href,
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
    except Exception:
        pass

    return results
