from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from app.database import Base, engine
from app.routers import estatisticas, leituras, metas, sessoes
from app.security import verificar_api_key

DESCRICAO = """
API secundária do projeto **Estante de Leitura**.

Guarda o histórico de leitura dos usuários e calcula metas e estatísticas:

* **Leituras concluídas**: livros que o usuário terminou.
* **Sessões de leitura**: páginas lidas por dia, usadas para calcular a sequência de dias lendo.
* **Metas anuais**: quantos livros (e páginas) o usuário quer ler no ano.
* **Estatísticas**: progresso da meta, ritmo necessário, livros por mês e por gênero.

É consumida pela **Estante API** (API principal). Todas as rotas, exceto `/health`,
exigem o cabeçalho `X-API-Key`.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Metas de Leitura API",
    description=DESCRICAO,
    version="1.0.0",
    lifespan=lifespan,
)

protegida = [Depends(verificar_api_key)]
app.include_router(leituras.router, dependencies=protegida)
app.include_router(sessoes.router, dependencies=protegida)
app.include_router(metas.router, dependencies=protegida)
app.include_router(estatisticas.router, dependencies=protegida)


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Saúde"], summary="Verifica se a API está no ar")
def health():
    return {"status": "ok"}
