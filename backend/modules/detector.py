"""Detecta o tipo de input: CPF, CNPJ, email, telefone ou nome."""

import re


def detect_input_type(query: str) -> str:
    query = query.strip()

    # Remove formatação comum
    digits_only = re.sub(r"[.\-/() ]", "", query)

    # Email
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", query):
        return "email"

    # CPF (11 dígitos)
    if re.match(r"^\d{11}$", digits_only):
        return "cpf"

    # CNPJ (14 dígitos)
    if re.match(r"^\d{14}$", digits_only):
        return "cnpj"

    # Telefone (10-11 dígitos, com ou sem +55)
    phone_digits = re.sub(r"[^0-9]", "", query)
    if phone_digits.startswith("55") and len(phone_digits) in (12, 13):
        return "telefone"
    if len(phone_digits) in (10, 11):
        return "telefone"

    # Nome (fallback)
    return "nome"


def format_cpf(cpf: str) -> str:
    d = re.sub(r"\D", "", cpf)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return cpf


def format_cnpj(cnpj: str) -> str:
    d = re.sub(r"\D", "", cnpj)
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return cnpj


def format_phone(phone: str) -> str:
    d = re.sub(r"\D", "", phone)
    if d.startswith("55"):
        d = d[2:]
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return phone


def validate_cpf(cpf: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in range(9, 11):
        val = sum(d[num] * ((i + 1) - num) for num in range(0, i))
        digit = ((val * 10) % 11) % 10
        if d[i] != digit:
            return False
    return True


def validate_cnpj(cnpj: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", cnpj)]
    if len(d) != 14 or len(set(d)) == 1:
        return False
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(d[i] * weights1[i] for i in range(12))
    d1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)
    if d[12] != d1:
        return False
    sum2 = sum(d[i] * weights2[i] for i in range(13))
    d2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)
    return d[13] == d2
