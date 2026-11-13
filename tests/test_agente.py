import json

import pytest

from app.agente import AgenteErro, extrair
from app.llm import RoteiroLocal, _para_formato_openai

from .conftest import EXEMPLOS


def test_agente_local_extrai_nota_ficticia():
    texto = (EXEMPLOS / "nota-ficticia-01.txt").read_text(encoding="utf-8")
    dados, rastro = extrair(texto, RoteiroLocal())
    assert dados.cnpj_emitente == "11222333000181"
    assert dados.valor_total == 1250.00
    assert str(dados.data_emissao) == "2026-03-05"
    assert rastro == ["extrair_cnpj", "extrair_valor_total", "extrair_data_emissao"]


class CerebroMalicioso:
    def responder(self, mensagens, ferramentas):
        return {"tool_calls": [{"id": "x", "name": "apagar_banco", "arguments": {}}]}


class CerebroEmLoop:
    def responder(self, mensagens, ferramentas):
        return {"tool_calls": [{"id": "x", "name": "extrair_cnpj", "arguments": {"texto": ""}}]}


class CerebroSaidaInvalida:
    def responder(self, mensagens, ferramentas):
        return {"conteudo": json.dumps({"cnpj_emitente": "123", "valor_total": -5})}


@pytest.mark.parametrize("cerebro", [CerebroMalicioso(), CerebroEmLoop(), CerebroSaidaInvalida()])
def test_guardas_do_agente(cerebro):
    with pytest.raises(AgenteErro):
        extrair("qualquer texto", cerebro, max_passos=3)


def test_conversao_para_formato_openai():
    msgs = [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "tool_calls": [{"id": "a", "name": "f", "arguments": {"texto": "t"}}]},
        {"role": "tool", "tool_call_id": "a", "name": "f", "content": "null"},
    ]
    saida = _para_formato_openai(msgs)
    assert saida[1]["tool_calls"][0]["function"]["arguments"] == '{"texto": "t"}'
    assert saida[2] == {"role": "tool", "tool_call_id": "a", "content": "null"}
