from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app

ANO = date.today().year


def _leitura(**extra):
    dados = {
        "usuario_id": 1,
        "livro_ref": "OL1003040W",
        "titulo": "Dom Casmurro",
        "genero": "Romance",
        "paginas": 268,
        "nota": 5,
    }
    return dados | extra


def test_rotas_exigem_api_key(client):
    sem_chave = TestClient(app)
    assert sem_chave.get("/leituras", params={"usuario_id": 1}).status_code == 401
    assert sem_chave.get("/health").status_code == 200


def test_registrar_leitura_e_idempotente(client):
    primeira = client.post("/leituras", json=_leitura(nota=3))
    segunda = client.post("/leituras", json=_leitura(nota=5))

    assert primeira.status_code == segunda.status_code == 201
    assert primeira.json()["id"] == segunda.json()["id"]

    leituras = client.get("/leituras", params={"usuario_id": 1}).json()
    assert len(leituras) == 1
    assert leituras[0]["nota"] == 5


def test_nao_aceita_conclusao_no_futuro(client):
    amanha = (date.today() + timedelta(days=1)).isoformat()
    resposta = client.post("/leituras", json=_leitura(data_conclusao=amanha))
    assert resposta.status_code == 422


def test_remover_leitura(client):
    client.post("/leituras", json=_leitura())
    assert client.delete("/leituras/1/OL1003040W").status_code == 204
    assert client.delete("/leituras/1/OL1003040W").status_code == 404


def test_ciclo_de_vida_da_meta(client):
    criada = client.post("/metas", json={"usuario_id": 1, "ano": ANO, "meta_livros": 12})
    assert criada.status_code == 201

    duplicada = client.post("/metas", json={"usuario_id": 1, "ano": ANO, "meta_livros": 5})
    assert duplicada.status_code == 409

    alterada = client.put(f"/metas/1/{ANO}", json={"meta_livros": 20, "meta_paginas": 5000})
    assert alterada.json()["meta_livros"] == 20

    assert client.get(f"/metas/1/{ANO}").json()["meta_paginas"] == 5000
    assert client.delete(f"/metas/1/{ANO}").status_code == 204
    assert client.get(f"/metas/1/{ANO}").status_code == 404


def test_sessoes_e_remocao_por_livro(client):
    client.post("/sessoes", json={"usuario_id": 1, "livro_ref": "A", "paginas_lidas": 10})
    client.post("/sessoes", json={"usuario_id": 1, "livro_ref": "B", "paginas_lidas": 20})

    assert client.delete("/sessoes/1/A").status_code == 204

    restantes = client.get("/sessoes", params={"usuario_id": 1}).json()
    assert [s["livro_ref"] for s in restantes] == ["B"]


def test_estatisticas(client):
    hoje = date.today()
    client.post("/metas", json={"usuario_id": 1, "ano": ANO, "meta_livros": 1, "meta_paginas": 100})
    client.post("/leituras", json=_leitura(nota=4))
    client.post("/leituras", json=_leitura(livro_ref="OL2W", titulo="Outro", genero="Fantasia", nota=2))
    for dias_atras in (0, 1, 2):
        client.post(
            "/sessoes",
            json={
                "usuario_id": 1,
                "livro_ref": "OL1003040W",
                "paginas_lidas": 50,
                "data": (hoje - timedelta(days=dias_atras)).isoformat(),
            },
        )

    estatisticas = client.get("/estatisticas/1", params={"ano": ANO}).json()

    assert estatisticas["livros_concluidos"] == 2
    assert estatisticas["media_nota"] == 3.0
    assert estatisticas["sequencia_atual_dias"] == 3
    assert estatisticas["meta"]["situacao"] == "meta_batida"
    assert estatisticas["meta"]["progresso_livros_percentual"] == 100.0
    assert {g["genero"] for g in estatisticas["por_genero"]} == {"Romance", "Fantasia"}
    assert len(estatisticas["por_mes"]) == 12
