import json

import pytest

from kerberos_notas.client.routes import create_app
from kerberos_notas.config import CHAVE_SECRETA_SERVICO_NOTAS
from kerberos_notas.crypto.crypto_utils import (
    bytes_para_base64,
    criptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.kerberos.tickets import criar_ticket_servico
from kerberos_notas.notes import repository
from kerberos_notas.notes.service import criar_nota, listar_notas


@pytest.fixture
def caminho_notas(tmp_path, monkeypatch):
    caminho = tmp_path / "notas.json"
    caminho.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(repository, "CAMINHO_NOTAS", caminho)
    return caminho


def criar_ticket_notas(usuario):
    ticket = criar_ticket_servico(
        usuario=usuario,
        servico="notas",
        chave_sessao_cliente_servico_base64=bytes_para_base64(gerar_chave_simetrica()),
    )
    return criptografar_json(CHAVE_SECRETA_SERVICO_NOTAS, ticket)


def test_servico_cria_e_lista_nota(caminho_notas):
    nota = criar_nota("ana", "Prova", "Estudar Kerberos")

    assert nota["titulo"] == "Prova"
    assert listar_notas("ana") == [nota]

    dados = json.loads(caminho_notas.read_text(encoding="utf-8"))
    assert dados["notas"]["ana"][0]["conteudo"] == "Estudar Kerberos"


def test_rota_notas_salva_e_exibe_nota(caminho_notas):
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario"] = "ana"
            sessao["ticket_servico"] = criar_ticket_notas("ana")

        resposta = cliente.post(
            "/notas",
            data={
                "titulo": "Aula",
                "conteudo": "Fluxo AS TGS Servico",
            },
        )

    assert resposta.status_code == 200
    assert b"Aula" in resposta.data
    assert b"Fluxo AS TGS Servico" in resposta.data

    dados = json.loads(caminho_notas.read_text(encoding="utf-8"))
    assert dados["notas"]["ana"][0]["titulo"] == "Aula"
