from __future__ import annotations

import os
from datetime import UTC, date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

__all__ = ["Base", "Nota", "Session", "criar_sessao"]

URL = os.getenv("DATABASE_URL", "sqlite:///./notas.db")


class Base(DeclarativeBase):
    pass


class Nota(Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True)
    arquivo: Mapped[str] = mapped_column(String(255))
    cnpj_emitente: Mapped[str | None] = mapped_column(String(14), index=True)
    valor_total: Mapped[float | None] = mapped_column(Float)
    data_emissao: Mapped[date | None] = mapped_column(Date)
    ferramentas_usadas: Mapped[list] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


def criar_sessao(url: str = URL):
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=args)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
