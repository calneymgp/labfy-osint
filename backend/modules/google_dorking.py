"""Gera Google Dorks para busca OSINT."""

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
        digits = re.sub(r"\D", "", query)
        formatted = _format_cpf(digits)
        # Busca com CPF formatado e raw — ambos aparecem em documentos
        dorks.extend([
            {
                "source": "Google (CPF geral)",
                "dork": f'"{formatted}" OR "{digits}"',
                "description": "Busca geral por este CPF em toda a web",
            },
            {
                "source": "JusBrasil (CPF)",
                "dork": f'site:jusbrasil.com.br "{formatted}" OR "{digits}"',
                "description": "Processos judiciais com este CPF",
            },
            {
                "source": "Gov.br (PDFs com CPF)",
                "dork": f'site:gov.br "{formatted}" OR "{digits}"',
                "description": "Documentos governamentais com este CPF",
            },
            {
                "source": "Diários Oficiais (CPF)",
                "dork": f'"{formatted}" diário oficial',
                "description": "Publicações oficiais com este CPF",
            },
            {
                "source": "Escavador (CPF)",
                "dork": f'site:escavador.com "{formatted}"',
                "description": "Dados públicos no Escavador",
            },
            {
                "source": "Licitações (CPF)",
                "dork": f'"{formatted}" licitação OR pregão OR contrato',
                "description": "Licitações e contratos públicos",
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
