from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class DadosNota(BaseModel):
    cnpj_emitente: str | None = Field(None, pattern=r"^\d{14}$")
    valor_total: float | None = Field(None, ge=0)
    data_emissao: date | None = None


class NotaSaida(DadosNota):
    model_config = ConfigDict(from_attributes=True)

    id: int
    arquivo: str
    ferramentas_usadas: list[str]
