from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MetaAnual
from app.schemas import MetaAtualizar, MetaCriar, MetaResposta

router = APIRouter(prefix="/metas", tags=["Metas anuais"])


def _buscar_meta(db: Session, usuario_id: int, ano: int) -> MetaAnual:
    meta = db.scalar(
        select(MetaAnual).where(MetaAnual.usuario_id == usuario_id, MetaAnual.ano == ano)
    )
    if meta is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Nenhuma meta cadastrada para {ano}."
        )
    return meta


@router.post(
    "",
    response_model=MetaResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cria a meta de leitura de um ano",
)
def criar_meta(dados: MetaCriar, db: Session = Depends(get_db)):
    existente = db.scalar(
        select(MetaAnual).where(
            MetaAnual.usuario_id == dados.usuario_id, MetaAnual.ano == dados.ano
        )
    )
    if existente is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Já existe uma meta para {dados.ano}. Use PUT para alterá-la.",
        )

    meta = MetaAnual(**dados.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


@router.get(
    "/{usuario_id}/{ano}",
    response_model=MetaResposta,
    summary="Consulta a meta de leitura de um ano",
)
def obter_meta(usuario_id: int, ano: int, db: Session = Depends(get_db)):
    return _buscar_meta(db, usuario_id, ano)


@router.put(
    "/{usuario_id}/{ano}",
    response_model=MetaResposta,
    summary="Altera a meta de leitura de um ano",
)
def atualizar_meta(
    usuario_id: int, ano: int, dados: MetaAtualizar, db: Session = Depends(get_db)
):
    meta = _buscar_meta(db, usuario_id, ano)
    meta.meta_livros = dados.meta_livros
    meta.meta_paginas = dados.meta_paginas
    db.commit()
    db.refresh(meta)
    return meta


@router.delete(
    "/{usuario_id}/{ano}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a meta de leitura de um ano",
)
def remover_meta(usuario_id: int, ano: int, db: Session = Depends(get_db)):
    db.delete(_buscar_meta(db, usuario_id, ano))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
