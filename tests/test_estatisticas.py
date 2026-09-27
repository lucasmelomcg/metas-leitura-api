from datetime import date, timedelta

from app.models import MetaAnual
from app.schemas import SituacaoMeta
from app.services.estatisticas import calcular_progresso_meta, calcular_sequencias

HOJE = date(2026, 7, 1)


def test_sequencias_vazias():
    assert calcular_sequencias(set(), HOJE) == (0, 0)


def test_sequencia_atual_continua_se_leu_ontem():
    datas = {HOJE - timedelta(days=d) for d in (1, 2, 3)}
    assert calcular_sequencias(datas, HOJE) == (3, 3)


def test_sequencia_atual_quebrada_e_maior_sequencia():
    datas = {date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4), HOJE}
    assert calcular_sequencias(datas, HOJE) == (1, 4)


def test_situacao_atrasado_e_ritmo_necessario():
    meta = MetaAnual(ano=2026, meta_livros=24, meta_paginas=None)
    progresso = calcular_progresso_meta(meta, livros_concluidos=5, paginas_lidas=0, hoje=HOJE)

    assert progresso.situacao == SituacaoMeta.atrasado
    assert progresso.livros_restantes == 19
    assert progresso.ritmo_necessario_livros_por_mes == round(19 / 6, 2)


def test_situacao_adiantado():
    meta = MetaAnual(ano=2026, meta_livros=12, meta_paginas=None)
    progresso = calcular_progresso_meta(meta, livros_concluidos=9, paginas_lidas=0, hoje=HOJE)
    assert progresso.situacao == SituacaoMeta.adiantado


def test_meta_de_ano_futuro_nao_iniciada():
    meta = MetaAnual(ano=2027, meta_livros=12, meta_paginas=3000)
    progresso = calcular_progresso_meta(meta, livros_concluidos=0, paginas_lidas=0, hoje=HOJE)

    assert progresso.situacao == SituacaoMeta.nao_iniciada
    assert progresso.progresso_paginas_percentual == 0.0
