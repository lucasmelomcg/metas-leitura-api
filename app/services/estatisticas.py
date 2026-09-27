import calendar
import math
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.models import LeituraConcluida, MetaAnual, SessaoLeitura
from app.schemas import (
    Estatisticas,
    ProgressoMeta,
    ResumoGenero,
    ResumoMes,
    SituacaoMeta,
)


def calcular_sequencias(datas: set[date], hoje: date) -> tuple[int, int]:
    """Retorna (sequência atual, maior sequência) de dias consecutivos com leitura.

    A sequência atual continua valendo se o usuário leu ontem mas ainda não leu hoje.
    """
    if not datas:
        return 0, 0

    ordenadas = sorted(datas)
    maior = corrente = 1
    for anterior, data in zip(ordenadas, ordenadas[1:]):
        corrente = corrente + 1 if (data - anterior).days == 1 else 1
        maior = max(maior, corrente)

    dia = hoje if hoje in datas else hoje - timedelta(days=1)
    atual = 0
    while dia in datas:
        atual += 1
        dia -= timedelta(days=1)

    return atual, maior


def calcular_progresso_meta(
    meta: MetaAnual, livros_concluidos: int, paginas_lidas: int, hoje: date
) -> ProgressoMeta:
    ano = meta.ano
    dias_no_ano = 366 if calendar.isleap(ano) else 365

    if ano < hoje.year:
        fracao_do_ano, meses_restantes = 1.0, 0
    elif ano > hoje.year:
        fracao_do_ano, meses_restantes = 0.0, 12
    else:
        fracao_do_ano = hoje.timetuple().tm_yday / dias_no_ano
        meses_restantes = 12 - hoje.month + 1

    esperados = meta.meta_livros * fracao_do_ano
    restantes = max(meta.meta_livros - livros_concluidos, 0)

    if livros_concluidos >= meta.meta_livros:
        situacao = SituacaoMeta.meta_batida
    elif ano > hoje.year:
        situacao = SituacaoMeta.nao_iniciada
    elif livros_concluidos >= esperados + 1:
        situacao = SituacaoMeta.adiantado
    elif livros_concluidos >= math.floor(esperados):
        situacao = SituacaoMeta.no_ritmo
    else:
        situacao = SituacaoMeta.atrasado

    progresso_paginas = None
    if meta.meta_paginas:
        progresso_paginas = round(min(paginas_lidas / meta.meta_paginas, 1) * 100, 1)

    return ProgressoMeta(
        meta_livros=meta.meta_livros,
        meta_paginas=meta.meta_paginas,
        progresso_livros_percentual=round(
            min(livros_concluidos / meta.meta_livros, 1) * 100, 1
        ),
        progresso_paginas_percentual=progresso_paginas,
        livros_restantes=restantes,
        livros_esperados_ate_hoje=round(esperados, 1),
        ritmo_necessario_livros_por_mes=(
            round(restantes / meses_restantes, 2) if meses_restantes else 0.0
        ),
        situacao=situacao,
    )


def calcular_estatisticas(
    db: Session, usuario_id: int, ano: int, hoje: date | None = None
) -> Estatisticas:
    hoje = hoje or date.today()

    leituras = db.scalars(
        select(LeituraConcluida).where(
            LeituraConcluida.usuario_id == usuario_id,
            extract("year", LeituraConcluida.data_conclusao) == ano,
        )
    ).all()
    sessoes = db.scalars(
        select(SessaoLeitura).where(SessaoLeitura.usuario_id == usuario_id)
    ).all()
    sessoes_do_ano = [s for s in sessoes if s.data.year == ano]

    livros_por_mes = Counter(leitura.data_conclusao.month for leitura in leituras)
    paginas_por_mes: Counter[int] = Counter()
    for sessao in sessoes_do_ano:
        paginas_por_mes[sessao.data.month] += sessao.paginas_lidas

    por_genero = Counter(leitura.genero for leitura in leituras)
    notas = [leitura.nota for leitura in leituras if leitura.nota is not None]
    paginas_lidas = sum(paginas_por_mes.values())

    sequencia_atual, maior_sequencia = calcular_sequencias(
        {sessao.data for sessao in sessoes}, hoje
    )

    meta = db.scalar(
        select(MetaAnual).where(MetaAnual.usuario_id == usuario_id, MetaAnual.ano == ano)
    )

    return Estatisticas(
        usuario_id=usuario_id,
        ano=ano,
        livros_concluidos=len(leituras),
        paginas_lidas=paginas_lidas,
        media_nota=round(sum(notas) / len(notas), 2) if notas else None,
        sequencia_atual_dias=sequencia_atual,
        maior_sequencia_dias=maior_sequencia,
        meta=(
            calcular_progresso_meta(meta, len(leituras), paginas_lidas, hoje)
            if meta
            else None
        ),
        por_mes=[
            ResumoMes(mes=mes, livros=livros_por_mes[mes], paginas=paginas_por_mes[mes])
            for mes in range(1, 13)
        ],
        por_genero=[
            ResumoGenero(genero=genero, livros=quantidade)
            for genero, quantidade in por_genero.most_common()
        ],
    )
