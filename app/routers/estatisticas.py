from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import Estatisticas
from app.services.estatisticas import calcular_estatisticas

router = APIRouter(prefix="/estatisticas", tags=["Estatísticas"])


@router.get(
    "/{usuario_id}",
    response_model=Estatisticas,
    summary="Estatísticas de leitura e progresso da meta no ano",
    description=(
        "Consolida livros concluídos, páginas lidas, livros por mês e por gênero, "
        "média das notas, sequência de dias lendo e a situação da meta anual "
        "(meta batida, adiantado, no ritmo ou atrasado)."
    ),
)
def obter_estatisticas(
    usuario_id: int,
    ano: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    return calcular_estatisticas(db, usuario_id, ano)
