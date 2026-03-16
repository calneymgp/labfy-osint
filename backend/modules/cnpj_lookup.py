"""Consulta CNPJ na ReceitaWS (API pública gratuita) e BrasilAPI."""

import httpx
import re


async def lookup_cnpj(cnpj: str, client: httpx.AsyncClient) -> dict | None:
    """Consulta dados de CNPJ via APIs públicas."""
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14:
        return None

    # Tenta BrasilAPI primeiro (mais confiável, sem rate limit agressivo)
    result = await _brasilapi(digits, client)
    if result:
        return result

    # Fallback: ReceitaWS
    result = await _receitaws(digits, client)
    if result:
        return result

    return None


async def _brasilapi(cnpj: str, client: httpx.AsyncClient) -> dict | None:
    try:
        resp = await client.get(
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            socios = []
            for s in data.get("qsa", []):
                socios.append({
                    "nome": s.get("nome_socio", ""),
                    "qualificacao": s.get("qualificacao_socio", ""),
                    "cpf_cnpj": s.get("cnpj_cpf_do_socio", ""),
                })
            return {
                "fonte": "BrasilAPI",
                "cnpj": cnpj,
                "razao_social": data.get("razao_social", ""),
                "nome_fantasia": data.get("nome_fantasia", ""),
                "situacao": data.get("descricao_situacao_cadastral", ""),
                "data_abertura": data.get("data_inicio_atividade", ""),
                "natureza_juridica": data.get("natureza_juridica", ""),
                "atividade_principal": data.get("cnae_fiscal_descricao", ""),
                "logradouro": data.get("logradouro", ""),
                "numero": data.get("numero", ""),
                "complemento": data.get("complemento", ""),
                "bairro": data.get("bairro", ""),
                "municipio": data.get("municipio", ""),
                "uf": data.get("uf", ""),
                "cep": data.get("cep", ""),
                "telefone": data.get("ddd_telefone_1", ""),
                "telefone2": data.get("ddd_telefone_2", ""),
                "email": data.get("email", ""),
                "socios": socios,
            }
    except Exception:
        pass
    return None


async def _receitaws(cnpj: str, client: httpx.AsyncClient) -> dict | None:
    try:
        resp = await client.get(
            f"https://receitaws.com.br/v1/cnpj/{cnpj}",
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ERROR":
                return None
            socios = []
            for s in data.get("qsa", []):
                socios.append({
                    "nome": s.get("nome", ""),
                    "qualificacao": s.get("qual", ""),
                })
            return {
                "fonte": "ReceitaWS",
                "cnpj": cnpj,
                "razao_social": data.get("nome", ""),
                "nome_fantasia": data.get("fantasia", ""),
                "situacao": data.get("situacao", ""),
                "data_abertura": data.get("abertura", ""),
                "natureza_juridica": data.get("natureza_juridica", ""),
                "atividade_principal": (data.get("atividade_principal", [{}])[0].get("text", "")
                                        if data.get("atividade_principal") else ""),
                "logradouro": data.get("logradouro", ""),
                "numero": data.get("numero", ""),
                "complemento": data.get("complemento", ""),
                "bairro": data.get("bairro", ""),
                "municipio": data.get("municipio", ""),
                "uf": data.get("uf", ""),
                "cep": data.get("cep", ""),
                "telefone": data.get("telefone", ""),
                "email": data.get("email", ""),
                "socios": socios,
            }
    except Exception:
        pass
    return None


async def search_cnpj_by_name(name: str, client: httpx.AsyncClient) -> list[dict]:
    """Busca CNPJs associados a um nome via CasaDosDados (open)."""
    results = []
    try:
        resp = await client.post(
            "https://api.casadosdados.com.br/v2/public/cnpj/search",
            json={
                "query": {"termo": [name]},
                "range": {"inicio": "2000-01-01", "fim": "2026-12-31"},
                "extras": {"somente_mei": False, "excluir_mei": False, "com_contato_telefonico": False},
                "page": 1,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", {}).get("cnpj", [])[:10]:
                results.append({
                    "cnpj": item.get("cnpj", ""),
                    "razao_social": item.get("razao_social", ""),
                    "nome_fantasia": item.get("nome_fantasia", ""),
                    "municipio": item.get("municipio", ""),
                    "uf": item.get("uf", ""),
                    "situacao": item.get("situacao_cadastral", ""),
                })
    except Exception:
        pass
    return results
