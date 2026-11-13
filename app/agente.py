"""Laço do agente: o modelo pede ferramentas, o código executa, até vir a resposta final.

Guardas: limite de passos, só ferramentas da lista branca, e validação da saída
com Pydantic antes de qualquer gravação.
"""
from __future__ import annotations

import json

from .ferramentas import FERRAMENTAS, SCHEMAS
from .llm import Cerebro
from .schemas import DadosNota

INSTRUCAO = (
    "Você extrai dados de notas fiscais e faturas brasileiras. Use as ferramentas para achar "
    "CNPJ do emitente, valor total e data de emissão. Responda só com JSON nas chaves "
    "cnpj_emitente, valor_total e data_emissao. Use null quando não encontrar."
)


class AgenteErro(RuntimeError):
    pass


def extrair(texto: str, cerebro: Cerebro, max_passos: int = 8) -> tuple[DadosNota, list[str]]:
    mensagens: list[dict] = [
        {"role": "system", "content": INSTRUCAO},
        {"role": "user", "content": texto},
    ]
    rastro: list[str] = []
    for _ in range(max_passos):
        resposta = cerebro.responder(mensagens, SCHEMAS)
        chamadas = resposta.get("tool_calls")
        if not chamadas:
            try:
                return DadosNota.model_validate(json.loads(resposta["conteudo"])), rastro
            except (ValueError, KeyError) as e:
                raise AgenteErro(f"Resposta final inválida: {e}") from e
        mensagens.append({"role": "assistant", "tool_calls": chamadas})
        for c in chamadas:
            funcao = FERRAMENTAS.get(c["name"])
            if funcao is None:
                raise AgenteErro(f"Ferramenta fora da lista: {c['name']}")
            resultado = funcao(**c["arguments"])
            rastro.append(c["name"])
            mensagens.append({"role": "tool", "tool_call_id": c["id"], "name": c["name"],
                              "content": json.dumps(resultado)})
    raise AgenteErro("Limite de passos atingido sem resposta final")
