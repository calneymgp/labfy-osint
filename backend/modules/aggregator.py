"""Orquestra todas as buscas e gera relatório Markdown."""

import asyncio
import re
import httpx
from datetime import datetime

from .detector import (
    detect_input_type, format_cpf, format_cnpj, format_phone,
    validate_cpf, validate_cnpj,
)
from .google_dorking import build_dorks
from .search_engine import search_dorks
from .cnpj_lookup import lookup_cnpj, search_cnpj_by_name
from .whois_lookup import whois_domain, extract_domain_from_email
from .diarios_oficiais import search_diarios, search_dou
from .jusbrasil import search_jusbrasil, search_escavador
from .transparencia import search_ceis, search_ceaf, search_cpf_receita


async def run_search(query: str, progress_callback=None) -> dict:
    """Executa busca completa e retorna resultado estruturado."""
    query = query.strip()
    input_type = detect_input_type(query)

    result = {
        "query": query,
        "tipo": input_type,
        "timestamp": datetime.now().isoformat(),
        "validacao": None,
        "cnpj_data": None,
        "cpf_data": None,
        "whois_data": None,
        "cnpjs_associados": [],
        "diarios": [],
        "dou": [],
        "jusbrasil": [],
        "escavador": [],
        "ceis": [],
        "servidores": [],
        "google_dorks": [],
        "google_results": [],
        "erros": [],
    }

    # Helper to send structured step updates
    async def step(step_id_or_dict, label: str = "", status: str = "done", count: int = 0):
        if not progress_callback:
            return
        try:
            if isinstance(step_id_or_dict, dict):
                await progress_callback(step_id_or_dict)
            else:
                await progress_callback({
                    "step_id": step_id_or_dict,
                    "label": label,
                    "status": status,
                    "count": count,
                })
        except Exception:
            pass

    async with httpx.AsyncClient() as client:

        # --- Validação ---
        if input_type == "cpf":
            is_valid = validate_cpf(query)
            result["validacao"] = {"valido": is_valid}
            await step("validacao", f"Validação CPF — {'válido' if is_valid else 'inválido'}", "done")
        elif input_type == "cnpj":
            is_valid = validate_cnpj(query)
            result["validacao"] = {"valido": is_valid}
            await step("validacao", f"Validação CNPJ — {'válido' if is_valid else 'inválido'}", "done")

        # --- APIs diretas (paralelas, com step tracking) ---
        api_tasks = []

        if input_type == "cpf":
            api_tasks.append(_tracked("cpf_data", "BrasilAPI — CPF",
                search_cpf_receita(query.replace(".", "").replace("-", ""), client), result, step))

        elif input_type == "cnpj":
            api_tasks.append(_tracked("cnpj_data", "BrasilAPI — CNPJ",
                lookup_cnpj(query, client), result, step))

        elif input_type == "email":
            domain = extract_domain_from_email(query)
            if domain:
                api_tasks.append(_tracked("whois_data", f"WHOIS — {domain}",
                    whois_domain(domain, client), result, step))

        if input_type == "nome":
            api_tasks.append(_tracked_list("cnpjs_associados", "Casa dos Dados — CNPJs",
                search_cnpj_by_name(query, client), result, step))
            api_tasks.append(_tracked_list("servidores", "Portal da Transparência — Servidores",
                search_ceaf(query, client), result, step))
            api_tasks.append(_tracked_list("ceis", "CEIS — Sanções",
                search_ceis(query, client), result, step))

        # Universais
        api_tasks.append(_tracked_list("diarios", "Querido Diário — Diários Oficiais",
            search_diarios(query, client), result, step))
        api_tasks.append(_tracked_list("jusbrasil", "JusBrasil — Processos",
            search_jusbrasil(query, client), result, step))
        api_tasks.append(_tracked_list("escavador", "Escavador — Dados Públicos",
            search_escavador(query, client), result, step))

        await asyncio.gather(*api_tasks)

        # --- Dorks via SearXNG ---
        dorks = build_dorks(query, input_type)
        result["google_dorks"] = dorks

        dork_results = await search_dorks(dorks, progress_callback=step)
        result["google_results"] = dork_results

    result["markdown"] = generate_markdown(result)

    # Final step
    await step("complete", "Varredura concluída", "done")

    return result


async def _tracked(key, label, coro, result, step):
    """Executa coroutine com tracking de step."""
    await step(key, label, "running")
    try:
        val = await coro
        result[key] = val
        if val:
            await step(key, label, "done", count=1)
        else:
            await step(key, label, "empty")
    except Exception as e:
        result["erros"].append(f"{key}: {str(e)}")
        await step(key, label, "error")


async def _tracked_list(key, label, coro, result, step):
    """Executa coroutine de lista com tracking de step."""
    await step(key, label, "running")
    try:
        val = await coro
        if val:
            result[key] = val
            await step(key, label, "done", count=len(val))
        else:
            await step(key, label, "empty")
    except Exception as e:
        result["erros"].append(f"{key}: {str(e)}")
        await step(key, label, "error")


def generate_markdown(data: dict) -> str:
    """Gera relatório Markdown completo."""
    lines = []
    tipo_label = {
        "nome": "Nome",
        "cpf": "CPF",
        "cnpj": "CNPJ",
        "email": "Email",
        "telefone": "Telefone",
    }

    lines.append(f"# Relatório OSINT")
    lines.append(f"**Consulta:** `{data['query']}`")
    lines.append(f"**Tipo detectado:** {tipo_label.get(data['tipo'], data['tipo'])}")
    lines.append(f"**Data:** {data['timestamp'][:19].replace('T', ' ')}")
    lines.append("")

    # Validação
    if data["validacao"]:
        status = "Válido" if data["validacao"]["valido"] else "Inválido"
        icon = "✅" if data["validacao"]["valido"] else "❌"
        lines.append(f"> {icon} {tipo_label.get(data['tipo'], '').upper()} {status}")
        lines.append("")

    # Dados CPF
    if data["cpf_data"]:
        d = data["cpf_data"]
        lines.append("## Dados do CPF")
        lines.append(f"| Campo | Valor |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **Nome** | {d.get('nome', 'N/D')} |")
        lines.append(f"| **CPF** | {format_cpf(d.get('cpf', ''))} |")
        lines.append(f"| **Situação** | {d.get('situacao', 'N/D')} |")
        if d.get("data_nascimento"):
            lines.append(f"| **Data Nasc.** | {d['data_nascimento']} |")
        lines.append(f"| **Fonte** | {d.get('fonte', '')} |")
        lines.append("")

    # Dados CNPJ
    if data["cnpj_data"]:
        d = data["cnpj_data"]
        lines.append("## Dados do CNPJ")
        lines.append(f"| Campo | Valor |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **Razão Social** | {d.get('razao_social', 'N/D')} |")
        lines.append(f"| **Nome Fantasia** | {d.get('nome_fantasia', 'N/D')} |")
        lines.append(f"| **CNPJ** | {format_cnpj(d.get('cnpj', ''))} |")
        lines.append(f"| **Situação** | {d.get('situacao', 'N/D')} |")
        lines.append(f"| **Abertura** | {d.get('data_abertura', 'N/D')} |")
        lines.append(f"| **Atividade** | {d.get('atividade_principal', 'N/D')} |")
        addr = f"{d.get('logradouro', '')}, {d.get('numero', '')} {d.get('complemento', '')} - {d.get('bairro', '')} - {d.get('municipio', '')}/{d.get('uf', '')} CEP {d.get('cep', '')}"
        lines.append(f"| **Endereço** | {addr.strip()} |")
        if d.get("telefone"):
            lines.append(f"| **Telefone** | {d['telefone']} |")
        if d.get("telefone2"):
            lines.append(f"| **Telefone 2** | {d['telefone2']} |")
        if d.get("email"):
            lines.append(f"| **Email** | {d['email']} |")
        lines.append(f"| **Fonte** | {d.get('fonte', '')} |")
        lines.append("")

        if d.get("socios"):
            lines.append("### Quadro Societário")
            lines.append("| Nome | Qualificação | CPF/CNPJ |")
            lines.append("|------|-------------|----------|")
            for s in d["socios"]:
                lines.append(f"| {s.get('nome', '')} | {s.get('qualificacao', '')} | {s.get('cpf_cnpj', '')} |")
            lines.append("")

    # CNPJs associados
    if data["cnpjs_associados"]:
        lines.append("## CNPJs Associados")
        lines.append("| CNPJ | Razão Social | Fantasia | Cidade | Situação |")
        lines.append("|------|-------------|----------|--------|----------|")
        for c in data["cnpjs_associados"]:
            lines.append(f"| {c.get('cnpj', '')} | {c.get('razao_social', '')} | {c.get('nome_fantasia', '')} | {c.get('municipio', '')}/{c.get('uf', '')} | {c.get('situacao', '')} |")
        lines.append("")

    # Servidores Federais
    if data["servidores"]:
        lines.append("## Servidores Federais")
        lines.append("| Nome | CPF | Órgão | Cargo |")
        lines.append("|------|-----|-------|-------|")
        for s in data["servidores"]:
            lines.append(f"| {s.get('nome', '')} | {s.get('cpf', '')} | {s.get('orgao', '')} | {s.get('cargo', '')} |")
        lines.append("")

    # CEIS
    if data["ceis"]:
        lines.append("## Sanções (CEIS)")
        lines.append("| Nome | CPF/CNPJ | Sanção | Órgão |")
        lines.append("|------|----------|--------|-------|")
        for c in data["ceis"]:
            lines.append(f"| {c.get('nome', '')} | {c.get('cnpj_cpf', '')} | {c.get('tipo_sancao', '')} | {c.get('orgao', '')} |")
        lines.append("")

    # WHOIS
    if data["whois_data"]:
        w = data["whois_data"]
        lines.append("## WHOIS do Domínio")
        lines.append(f"| Campo | Valor |")
        lines.append(f"|-------|-------|")
        for k, v in w.items():
            if k != "fonte" and v:
                label = k.replace("_", " ").title()
                if isinstance(v, list):
                    v = ", ".join(str(i) for i in v)
                lines.append(f"| **{label}** | {v} |")
        lines.append(f"| **Fonte** | {w.get('fonte', '')} |")
        lines.append("")

    # JusBrasil
    if data["jusbrasil"]:
        lines.append("## JusBrasil — Processos e Publicações")
        for item in data["jusbrasil"]:
            title = item.get("titulo", "Sem título")
            url = item.get("url", "")
            trecho = item.get("trecho", "")
            lines.append(f"### [{title}]({url})")
            if trecho:
                lines.append(f"> {trecho[:300]}...")
            lines.append("")

    # Escavador
    if data["escavador"]:
        lines.append("## Escavador — Dados Públicos")
        for item in data["escavador"]:
            title = item.get("titulo", "Sem título")
            url = item.get("url", "")
            trecho = item.get("trecho", "")
            lines.append(f"- **[{title}]({url})**")
            if trecho:
                lines.append(f"  > {trecho[:200]}")
        lines.append("")

    # Diários Oficiais
    if data["diarios"]:
        lines.append("## Diários Oficiais (Municipais)")
        for item in data["diarios"]:
            lines.append(f"### {item.get('municipio', '')} ({item.get('uf', '')}) — {item.get('data', '')}")
            if item.get("url"):
                lines.append(f"[PDF Original]({item['url']})")
            for t in item.get("trechos", []):
                lines.append(f"> {t[:300]}")
            lines.append("")

    # DOU
    if data["dou"]:
        lines.append("## Diário Oficial da União")
        for item in data["dou"]:
            lines.append(f"- **[{item.get('titulo', '')}]({item.get('url', '')})** — {item.get('data', '')}")
        lines.append("")

    # Google Results
    if data["google_results"]:
        lines.append("## Resultados de Busca (Google Dorking)")
        for group in data["google_results"]:
            lines.append(f"### {group['source']}")
            lines.append(f"*Dork:* `{group['dork']}`")
            lines.append("")
            for r in group["results"]:
                lines.append(f"- **[{r.get('title', '')}]({r.get('url', '')})**")
                if r.get("snippet"):
                    lines.append(f"  > {r['snippet'][:200]}")
            lines.append("")

    # Google Dorks não executados
    executed = {g["source"] for g in data.get("google_results", [])}
    remaining = [d for d in data.get("google_dorks", []) if d["source"] not in executed]
    if remaining:
        lines.append("## Dorks Adicionais (buscar manualmente)")
        for d in remaining:
            lines.append(f"- **{d['source']}:** `{d['dork']}`")
            lines.append(f"  {d['description']}")
        lines.append("")

    # Erros
    if data["erros"]:
        lines.append("---")
        lines.append("## Log de Erros")
        for e in data["erros"]:
            lines.append(f"- {e}")
        lines.append("")

    total = (
        len(data.get("jusbrasil", [])) +
        len(data.get("escavador", [])) +
        len(data.get("diarios", [])) +
        len(data.get("dou", [])) +
        len(data.get("servidores", [])) +
        len(data.get("ceis", [])) +
        sum(len(g.get("results", [])) for g in data.get("google_results", []))
    )

    lines.append("---")
    lines.append(f"*Total de resultados encontrados: {total} | Fontes consultadas: {_count_sources(data)} | Labfy OSINT*")

    return "\n".join(lines)


def _count_sources(data: dict) -> int:
    count = 0
    if data.get("cpf_data"): count += 1
    if data.get("cnpj_data"): count += 1
    if data.get("whois_data"): count += 1
    if data.get("cnpjs_associados"): count += 1
    if data.get("diarios"): count += 1
    if data.get("dou"): count += 1
    if data.get("jusbrasil"): count += 1
    if data.get("escavador"): count += 1
    if data.get("ceis"): count += 1
    if data.get("servidores"): count += 1
    if data.get("google_results"): count += len(data["google_results"])
    return count
