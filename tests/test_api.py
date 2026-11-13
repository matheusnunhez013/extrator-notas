from fastapi.testclient import TestClient

from app.main import app

from .conftest import EXEMPLOS

cliente = TestClient(app)


def test_saude():
    assert cliente.get("/saude").json() == {"ok": True}


def test_fluxo_completo_upload_listar_obter():
    conteudo = (EXEMPLOS / "fatura-ficticia-02.txt").read_bytes()
    r = cliente.post("/notas", files={"arquivo": ("fatura.txt", conteudo, "text/plain")})
    assert r.status_code == 201, r.text
    nota = r.json()
    assert nota["valor_total"] == 389.90
    assert nota["data_emissao"] == "2026-02-14"

    lista = cliente.get("/notas", params={"cnpj": "11222333000181"}).json()
    assert any(n["id"] == nota["id"] for n in lista)
    assert cliente.get(f"/notas/{nota['id']}").json()["arquivo"] == "fatura.txt"


def test_formato_nao_suportado():
    r = cliente.post("/notas", files={"arquivo": ("planilha.xlsx", b"x", "application/octet-stream")})
    assert r.status_code == 415


def test_nota_inexistente():
    assert cliente.get("/notas/999999").status_code == 404
