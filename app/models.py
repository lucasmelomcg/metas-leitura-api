from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class LeituraConcluida(Base):
    """Um livro que o usuário terminou de ler."""

    __tablename__ = "leituras_concluidas"
    __table_args__ = (UniqueConstraint("usuario_id", "livro_ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, index=True)
    livro_ref: Mapped[str] = mapped_column(String(50))
    titulo: Mapped[str] = mapped_column(String(300))
    genero: Mapped[str] = mapped_column(String(50), default="Outros")
    paginas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_conclusao: Mapped[date] = mapped_column(Date)


class SessaoLeitura(Base):
    """Páginas lidas de um livro em um determinado dia."""

    __tablename__ = "sessoes_leitura"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, index=True)
    livro_ref: Mapped[str] = mapped_column(String(50))
    paginas_lidas: Mapped[int] = mapped_column(Integer)
    data: Mapped[date] = mapped_column(Date)


class MetaAnual(Base):
    """Meta de leitura de um usuário para um ano."""

    __tablename__ = "metas_anuais"
    __table_args__ = (UniqueConstraint("usuario_id", "ano"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, index=True)
    ano: Mapped[int] = mapped_column(Integer)
    meta_livros: Mapped[int] = mapped_column(Integer)
    meta_paginas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_agora, onupdate=_agora
    )
