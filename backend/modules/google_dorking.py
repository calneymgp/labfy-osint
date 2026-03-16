"""Gera queries de busca otimizadas para SearXNG (sem operador site:)."""

import re


def _format_cpf(cpf: str) -> str:
    d = re.sub(r"\D", "", cpf)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return cpf


def _format_cnpj(cnpj: str) -> str:
    d = re.sub(r"\D", "", cnpj)
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return cnpj


def _cpf_digits(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def _cnpj_digits(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj)


def build_dorks(query: str, input_type: str) -> list[dict]:
    """Gera queries otimizadas por tipo de input.

    NOTA: SearXNG não suporta operador site: — usamos nomes de domínio
    como termos de busca para direcionar resultados.
    """
    dorks = []

    if input_type == "nome":
        dorks.extend([
            {
                "source": "JusBrasil",
                "dork": f'jusbrasil.com.br "{query}" processo',
                "description": "Processos judiciais no JusBrasil",
            },
            {
                "source": "JusBrasil (email/tel)",
                "dork": f'jusbrasil "{query}" email telefone',
                "description": "Processos com contato",
            },
            {
                "source": "Escavador",
                "dork": f'escavador.com "{query}"',
                "description": "Dados públicos no Escavador",
            },
            {
                "source": "Diários Oficiais",
                "dork": f'diário oficial "{query}"',
                "description": "Publicações em diários oficiais",
            },
            {
                "source": "Gov.br",
                "dork": f'gov.br "{query}" CPF telefone',
                "description": "Documentos governamentais",
            },
            {
                "source": "Licitações",
                "dork": f'licitação pregão "{query}"',
                "description": "Licitações e contratos públicos",
            },
            {
                "source": "LinkedIn",
                "dork": f'linkedin.com/in "{query}"',
                "description": "Perfil profissional no LinkedIn",
            },
            {
                "source": "CVM",
                "dork": f'cvm.gov.br "{query}"',
                "description": "Registros na CVM",
            },
            {
                "source": "Transparência",
                "dork": f'portaltransparencia.gov.br "{query}"',
                "description": "Portal da Transparência",
            },
        ])

    elif input_type == "cpf":
        digits = _cpf_digits(query)
        formatted = _format_cpf(digits)
        # DDG suporta site: e exact match — usar formato completo
        dorks.extend([
            {
                "source": "Google (CPF)",
                "dork": f'"{formatted}"',
                "description": "Busca geral por este CPF",
            },
            {
                "source": "JusBrasil (CPF)",
                "dork": f'site:jusbrasil.com.br "{formatted}"',
                "description": "Processos judiciais com este CPF",
            },
            {
                "source": "Gov.br (CPF)",
                "dork": f'site:gov.br "{formatted}"',
                "description": "Documentos governamentais com este CPF",
            },
            {
                "source": "Diários Oficiais (CPF)",
                "dork": f'site:diariooficial.com "{formatted}"',
                "description": "Publicações oficiais com este CPF",
            },
        ])

    elif input_type == "cnpj":
        digits = _cnpj_digits(query)
        formatted = _format_cnpj(digits)
        dorks.extend([
            {
                "source": "Google (CNPJ)",
                "dork": f'"{formatted}"',
                "description": "Busca geral por este CNPJ",
            },
            {
                "source": "JusBrasil (CNPJ)",
                "dork": f'site:jusbrasil.com.br "{formatted}"',
                "description": "Processos judiciais com este CNPJ",
            },
            {
                "source": "Gov.br (CNPJ)",
                "dork": f'site:gov.br "{formatted}"',
                "description": "Documentos governamentais",
            },
            {
                "source": "CVM (CNPJ)",
                "dork": f'site:cvm.gov.br "{formatted}"',
                "description": "Registros na CVM",
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
                "description": "LinkedIn associado",
            },
            {
                "source": "GitHub (email)",
                "dork": f'site:github.com "{query}"',
                "description": "Perfil GitHub",
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
                "description": "Reclamações",
            },
        ])

    return dorks


def build_direct_links(query: str, input_type: str) -> list[dict]:
    """Gera links diretos para consulta manual em sites protegidos."""
    links = []
    encoded = query.replace(" ", "+")

    if input_type in ("nome", "cpf", "cnpj"):
        links.append({
            "source": "JusBrasil — Consulta Processual",
            "url": f"https://www.jusbrasil.com.br/consulta-processual/busca?q={encoded}",
            "description": "Buscar processos diretamente no JusBrasil",
        })
        links.append({
            "source": "Escavador — Busca",
            "url": f"https://www.escavador.com/busca?q={encoded}&type=1",
            "description": "Buscar dados públicos no Escavador",
        })

    if input_type == "cpf":
        digits = _cpf_digits(query)
        formatted = _format_cpf(digits)
        links.append({
            "source": "JusBrasil — CPF",
            "url": f"https://www.jusbrasil.com.br/consulta-processual/busca?q={formatted}",
            "description": "Consultar processos por CPF no JusBrasil",
        })

    if input_type == "cnpj":
        digits = _cnpj_digits(query)
        links.append({
            "source": "Receita Federal — CNPJ",
            "url": f"https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/cnpjreva_solicitacao.asp",
            "description": "Consulta oficial do CNPJ na Receita Federal",
        })
        links.append({
            "source": "CasaDosdados — CNPJ",
            "url": f"https://casadosdados.com.br/solucao/cnpj/{digits}",
            "description": "Dados empresariais completos",
        })

    if input_type == "nome":
        links.append({
            "source": "Google Dorking Manual",
            "url": f'https://www.google.com/search?q="{encoded}"+CPF+email+telefone',
            "description": "Busca avançada no Google com termos OSINT",
        })

    return links
