from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, UploadFile

from . import db
from .agente import AgenteErro, extrair
from .llm import Cerebro, cerebro_do_ambiente
from .ocr import FormatoNaoSuportado, texto_do_arquivo
from .schemas import NotaSaida

app = FastAPI(title="Extrator de notas", version="0.1.0")
_Sessao = db.criar_sessao()


def sessao():
    with _Sessao() as s:
        yield s


def cerebro() -> Cerebro:
    return cerebro_do_ambiente()


Sessao = Annotated[db.Session, Depends(sessao)]
CerebroDep = Annotated[Cerebro, Depends(cerebro)]


@app.get("/saude")
def saude() -> dict:
    return {"ok": True}


@app.post("/notas", response_model=NotaSaida, status_code=201)
async def criar_nota(arquivo: UploadFile, s: Sessao, c: CerebroDep):
    try:
        texto = texto_do_arquivo(arquivo.filename or "", await arquivo.read())
    except FormatoNaoSuportado as e:
        raise HTTPException(415, str(e)) from e
    try:
        dados, rastro = extrair(texto, c)
    except AgenteErro as e:
        raise HTTPException(422, str(e)) from e
    nota = db.Nota(arquivo=arquivo.filename, ferramentas_usadas=rastro, **dados.model_dump())
    s.add(nota)
    s.commit()
    return nota


@app.get("/notas", response_model=list[NotaSaida])
def listar(s: Sessao, cnpj: str | None = None):
    q = s.query(db.Nota)
    if cnpj:
        q = q.filter(db.Nota.cnpj_emitente == cnpj)
    return q.order_by(db.Nota.id.desc()).limit(100).all()


@app.get("/notas/{nota_id}", response_model=NotaSaida)
def obter(nota_id: int, s: Sessao):
    nota = s.get(db.Nota, nota_id)
    if nota is None:
        raise HTTPException(404, "Nota não encontrada")
    return nota
