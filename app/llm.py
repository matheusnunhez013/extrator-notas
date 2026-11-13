"""Provedores de "cérebro" para o agente.

- RoteiroLocal: sem rede e sem custo. Chama as ferramentas numa ordem fixa. Serve
  para testes, CI e para rodar a demo sem chave de API.
- ClienteCompativelOpenAI: qualquer endpoint /chat/completions com suporte a tools
  (DeepSeek, OpenAI etc.), configurado por variáveis de ambiente.

Os dois devolvem o mesmo formato: {"tool_calls": [...]} ou {"conteudo": "..."}.
"""
from __future__ import annotations

import json
import os
from typing import Protocol

import httpx


class Cerebro(Protocol):
    def responder(self, mensagens: list[dict], ferramentas: list[dict]) -> dict: ...


class RoteiroLocal:
    ORDEM = ("extrair_cnpj", "extrair_valor_total", "extrair_data_emissao")

    def responder(self, mensagens: list[dict], ferramentas: list[dict]) -> dict:
        texto = next(m["content"] for m in mensagens if m["role"] == "user")
        ja_chamadas = {m["name"] for m in mensagens if m["role"] == "tool"}
        for i, nome in enumerate(self.ORDEM):
            if nome not in ja_chamadas:
                return {
                    "tool_calls": [
                        {"id": f"local-{i}", "name": nome, "arguments": {"texto": texto}}
                    ]
                }
        resultados = {m["name"]: json.loads(m["content"]) for m in mensagens if m["role"] == "tool"}
        return {
            "conteudo": json.dumps(
                {
                    "cnpj_emitente": resultados["extrair_cnpj"],
                    "valor_total": resultados["extrair_valor_total"],
                    "data_emissao": resultados["extrair_data_emissao"],
                }
            )
        }


class ClienteCompativelOpenAI:
    def __init__(self, base_url: str, api_key: str, modelo: str, timeout: float = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.modelo = modelo
        self.timeout = timeout

    def responder(self, mensagens: list[dict], ferramentas: list[dict]) -> dict:
        corpo = {"model": self.modelo, "messages": _para_formato_openai(mensagens),
                 "tools": ferramentas, "temperature": 0}
        r = httpx.post(f"{self.base_url}/chat/completions", json=corpo, timeout=self.timeout,
                       headers={"Authorization": f"Bearer {self.api_key}"})
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        if msg.get("tool_calls"):
            return {"tool_calls": [
                {"id": c["id"], "name": c["function"]["name"],
                 "arguments": json.loads(c["function"]["arguments"] or "{}")}
                for c in msg["tool_calls"]
            ]}
        return {"conteudo": msg.get("content") or ""}


def _para_formato_openai(mensagens: list[dict]) -> list[dict]:
    saida = []
    for m in mensagens:
        if m["role"] == "assistant" and m.get("tool_calls"):
            saida.append({"role": "assistant", "content": None, "tool_calls": [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                for c in m["tool_calls"]
            ]})
        elif m["role"] == "tool":
            saida.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
        else:
            saida.append({"role": m["role"], "content": m["content"]})
    return saida


def cerebro_do_ambiente() -> Cerebro:
    base, chave, modelo = (os.getenv(k, "") for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"))
    if base and chave and modelo:
        return ClienteCompativelOpenAI(base, chave, modelo)
    return RoteiroLocal()
