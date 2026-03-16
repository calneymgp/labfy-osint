"""WHOIS lookup para domínios e busca reversa por email/nome."""

import httpx
import re


async def whois_domain(domain: str, client: httpx.AsyncClient) -> dict | None:
    """Consulta WHOIS de um domínio via API pública."""
    try:
        resp = await client.get(
            f"https://brasilapi.com.br/api/registrobr/v1/{domain}",
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "fonte": "Registro.br via BrasilAPI",
                "dominio": domain,
                "status": data.get("status_code", ""),
                "data_criacao": data.get("created", ""),
                "data_expiracao": data.get("expires", ""),
                "responsavel": data.get("responsible", ""),
                "pais": data.get("country", ""),
                "nameservers": data.get("nameservers", []),
            }
    except Exception:
        pass

    # Fallback: whois via ip-api
    try:
        import whois
        w = whois.whois(domain)
        if w and w.domain_name:
            return {
                "fonte": "WHOIS direto",
                "dominio": domain,
                "registrante": w.get("name", ""),
                "organizacao": w.get("org", ""),
                "email_registrante": w.get("emails", []),
                "data_criacao": str(w.get("creation_date", "")),
                "data_expiracao": str(w.get("expiration_date", "")),
                "nameservers": w.get("name_servers", []),
            }
    except Exception:
        pass

    return None


def extract_domain_from_email(email: str) -> str | None:
    """Extrai domínio de um email."""
    match = re.match(r"^[^@]+@([^@]+)$", email.strip())
    if match:
        domain = match.group(1).lower()
        # Ignora provedores genéricos
        generic = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com",
                    "yahoo.com.br", "hotmail.com.br", "live.com", "icloud.com",
                    "protonmail.com", "uol.com.br", "bol.com.br", "terra.com.br",
                    "ig.com.br", "globo.com", "zipmail.com.br"}
        if domain not in generic:
            return domain
    return None
