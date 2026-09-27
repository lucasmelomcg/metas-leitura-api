from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LeituraConcluida
from app.schemas import LeituraCriar, LeituraResposta

router = APIRouter(prefix="/leituras", tags=["Leituras concluídas"])


@router.post(
    "",
    response_model=LeituraResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registra (ou atualiza) a conclusão de um livro",
    description=(
        "Operação idempotente: se o usuário já concluiu este livro, o registro "
        "existente é atualizado com os novos dados (nota, data, etc.)."
    ),
)
def registrar_leitura(dados: LeituraCriar, db: Session = Depends(get_db)):
    if dados.data_conclusao > date.today():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A data de conclusão não pode estar no futuro.",
        )

    leitura = db.scalar(
        select(LeituraConcluida).where(
            LeituraConcluida.usuario_id == dados.usuario_id,
            LeituraConcluida.livro_ref == dados.livro_ref,
        )
    )
    if leitura is None:
        leitura = LeituraConcluida(**dados.model_dump())
        db.add(leitura)
    else:
        for campo, valor in dados.model_dump().items():
            setattr(leitura, campo, valor)

    db.commit()
    db.refresh(leitura)
    return leitura


@router.get(
    "",
    response_model=list[LeituraResposta],
    summary="Lista os livros concluídos por um usuário",
)
def listar_leituras(
    usuario_id: int = Query(gt=0),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    consulta = select(LeituraConcluida).where(LeituraConcluida.usuario_id == usuario_id)
    if ano is not None:
        consulta = consulta.where(extract("year", LeituraConcluida.data_conclusao) == ano)
    return db.scalars(consulta.order_by(LeituraConcluida.data_conclusao.desc())).all()


@router.delete(
    "/{usuario_id}/{livro_ref}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a conclusão de um livro",
)
def remover_leitura(usuario_id: int, livro_ref: str, db: Session = Depends(get_db)):
    leitura = db.scalar(
        select(LeituraConcluida).where(
            LeituraConcluida.usuario_id == usuario_id,
            LeituraConcluida.livro_ref == livro_ref,
        )
    )
    if leitura is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leitura não encontrada.")

    db.delete(leitura)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
