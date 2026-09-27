from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, extract, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SessaoLeitura
from app.schemas import SessaoCriar, SessaoResposta

router = APIRouter(prefix="/sessoes", tags=["Sessões de leitura"])


@router.post(
    "",
    response_model=SessaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registra páginas lidas em um dia",
)
def registrar_sessao(dados: SessaoCriar, db: Session = Depends(get_db)):
    if dados.data > date.today():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A data da sessão não pode estar no futuro.",
        )

    sessao = SessaoLeitura(**dados.model_dump())
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return sessao


@router.get(
    "",
    response_model=list[SessaoResposta],
    summary="Lista as sessões de leitura de um usuário",
)
def listar_sessoes(
    usuario_id: int = Query(gt=0),
    livro_ref: str | None = Query(default=None),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    consulta = select(SessaoLeitura).where(SessaoLeitura.usuario_id == usuario_id)
    if livro_ref is not None:
        consulta = consulta.where(SessaoLeitura.livro_ref == livro_ref)
    if ano is not None:
        consulta = consulta.where(extract("year", SessaoLeitura.data) == ano)
    return db.scalars(consulta.order_by(SessaoLeitura.data.desc())).all()


@router.delete(
    "/{usuario_id}/{livro_ref}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove todas as sessões de um livro",
    description="Usado quando o livro é removido da estante do usuário.",
)
def remover_sessoes(usuario_id: int, livro_ref: str, db: Session = Depends(get_db)):
    db.execute(
        delete(SessaoLeitura).where(
            SessaoLeitura.usuario_id == usuario_id,
            SessaoLeitura.livro_ref == livro_ref,
        )
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
