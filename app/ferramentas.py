"""Ferramentas que o agente pode chamar (tool calling).

Cada ferramenta é uma função pura e testável, descrita num schema JSON no formato
usado pelas APIs compatíveis com a OpenAI. O agente decide qual chamar; o código
executa e devolve o resultado.
"""
from __future__ import annotations

import re
from datetime import date

_RE_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
_RE_VALOR = re.compile(r"R\$\s*([\d.]+,\d{2})")
_RE_DATA_BR = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_RE_DATA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_PALAVRAS_TOTAL = ("valor total", "total a pagar", "total da nota", "total")


def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def validar_cnpj(cnpj: str) -> bool:
    """Confere os dois dígitos verificadores de um CNPJ."""
    d = _so_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False

    def dv(base: str, pesos: list[int]) -> str:
        resto = sum(int(n) * p for n, p in zip(base, pesos)) % 11
        return "0" if resto < 2 else str(11 - resto)

    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [6] + p1
    return d[12] == dv(d[:12], p1) and d[13] == dv(d[:13], p2)


def extrair_cnpj(texto: str) -> str | None:
    """Primeiro CNPJ válido do texto, só com dígitos."""
    for achado in _RE_CNPJ.findall(texto):
        if validar_cnpj(achado):
            return _so_digitos(achado)
    return None


def _para_float(valor_br: str) -> float:
    return float(valor_br.replace(".", "").replace(",", "."))


def extrair_valor_total(texto: str) -> float | None:
    """Valor da linha de total; se não houver, o maior valor em R$ do documento."""
    for linha in texto.splitlines():
        baixa = linha.lower()
        if any(p in baixa for p in _PALAVRAS_TOTAL):
            achados = _RE_VALOR.findall(linha)
            if achados:
                return _para_float(achados[-1])
    valores = [_para_float(v) for v in _RE_VALOR.findall(texto)]
    return max(valores) if valores else None


def extrair_data_emissao(texto: str) -> str | None:
    """Data de emissão em ISO (AAAA-MM-DD). Aceita DD/MM/AAAA e AAAA-MM-DD."""
    for m in _RE_DATA_BR.finditer(texto):
        dia, mes, ano = map(int, m.groups())
        try:
            return date(ano, mes, dia).isoformat()
        except ValueError:
            continue
    for m in _RE_DATA_ISO.finditer(texto):
        ano, mes, dia = map(int, m.groups())
        try:
            return date(ano, mes, dia).isoformat()
        except ValueError:
            continue
    return None


FERRAMENTAS = {
    "extrair_cnpj": extrair_cnpj,
    "extrair_valor_total": extrair_valor_total,
    "extrair_data_emissao": extrair_data_emissao,
}


def _schema(nome: str, descricao: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": nome,
            "description": descricao,
            "parameters": {
                "type": "object",
                "properties": {"texto": {"type": "string", "description": "Texto do documento"}},
                "required": ["texto"],
            },
        },
    }


SCHEMAS = [
    _schema("extrair_cnpj", "Encontra o CNPJ do emitente e valida os dígitos verificadores."),
    _schema("extrair_valor_total", "Encontra o valor total do documento em reais."),
    _schema("extrair_data_emissao", "Encontra a data de emissão e devolve em AAAA-MM-DD."),
]
