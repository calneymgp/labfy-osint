"""Consultas ao Portal da Transparência e fontes governamentais."""

import httpx


async def search_ceis(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca no CEIS (Cadastro de Empresas Inidôneas e Suspensas)."""
    results = []
    try:
        resp = await client.get(
            "https://portaldatransparencia.gov.br/api-de-dados/ceis",
            params={"nomeFantasia": query, "pagina": 1, "tamanhoPagina": 10},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data if isinstance(data, list) else []:
                results.append({
                    "fonte": "CEIS - Portal da Transparência",
                    "nome": item.get("nomeFantasia", "") or item.get("razaoSocial", ""),
                    "cnpj_cpf": item.get("numeroCNPJCPF", ""),
                    "tipo_sancao": item.get("tipoSancao", ""),
                    "orgao": item.get("orgaoSancionador", ""),
                    "data_inicio": item.get("dataInicioSancao", ""),
                    "data_fim": item.get("dataFimSancao", ""),
                })
    except Exception:
        pass
    return results


async def search_ceaf(query: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca no CEAF (servidores federais)."""
    results = []
    try:
        resp = await client.get(
            "https://portaldatransparencia.gov.br/api-de-dados/servidores",
            params={"nome": query, "pagina": 1, "tamanhoPagina": 10},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data if isinstance(data, list) else []:
                results.append({
                    "fonte": "Servidores Federais - Portal da Transparência",
                    "nome": item.get("nome", ""),
                    "cpf": item.get("cpf", ""),
                    "orgao": item.get("orgaoServidorExercicio", ""),
                    "cargo": item.get("cargoEfetivo", ""),
                    "funcao": item.get("funcao", ""),
                })
    except Exception:
        pass
    return results


async def search_cpf_receita(cpf: str, client: httpx.AsyncClient) -> dict | None:
    """Consulta situação cadastral de CPF."""
    # Não existe API pública oficial para CPF. Tentamos via nubankapi/brasilapi
    try:
        resp = await client.get(
            f"https://brasilapi.com.br/api/cpf/v1/{cpf}",
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "fonte": "BrasilAPI",
                "cpf": cpf,
                "nome": data.get("nome", ""),
                "situacao": data.get("situacao", ""),
                "data_nascimento": data.get("data_nascimento", ""),
            }
    except Exception:
        pass
    return None
