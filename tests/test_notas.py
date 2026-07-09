import json

import pytest

from kerberos_notas.client.routes import create_app
from kerberos_notas.config import CHAVE_SECRETA_SERVICO_NOTAS
from kerberos_notas.crypto.crypto_utils import (
    bytes_para_base64,
    criptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.crypto.kdf import (
    derivar_chave_senha,
    gerar_salt,
    gerar_verificador_chave,
)
from kerberos_notas.kerberos import as_server
from kerberos_notas.kerberos.authenticator import abrir_autenticador, criar_autenticador
from kerberos_notas.kerberos.tickets import criar_ticket_servico
from kerberos_notas.notes import repository
from kerberos_notas.notes.portal_notas import (
    autenticar_portal_notas,
    validar_confirmacao_portal,
)
from kerberos_notas.notes.service import (
    criar_nota,
    editar_nota,
    excluir_nota,
    listar_notas,
)


@pytest.fixture
def dados_portal(tmp_path, monkeypatch):
    caminho_notas = tmp_path / "notas.json"
    caminho_notas.write_text('{"notas": {}}', encoding="utf-8")
    monkeypatch.setattr(repository, "CAMINHO_NOTAS", caminho_notas)

    usuarios = {}
    for usuario, senha, perfil in (
        ("prof", "senha-prof", "professor"),
        ("ana", "senha-ana", "aluno"),
        ("bia", "senha-bia", "aluno"),
    ):
        salt = gerar_salt()
        chave = derivar_chave_senha(senha, salt)
        usuarios[usuario] = {
            "salt": salt,
            "verificador": gerar_verificador_chave(chave),
            "perfil": perfil,
        }

    caminho_usuarios = tmp_path / "usuarios.json"
    caminho_usuarios.write_text(
        json.dumps({"usuarios": usuarios}),
        encoding="utf-8",
    )
    monkeypatch.setattr(as_server, "CAMINHO_USUARIOS", caminho_usuarios)

    return caminho_notas


def criar_ticket_notas(usuario):
    chave_base64 = bytes_para_base64(gerar_chave_simetrica())
    ticket = criar_ticket_servico(
        usuario=usuario,
        servico="notas",
        chave_sessao_cliente_servico_base64=chave_base64,
    )
    return (
        criptografar_json(CHAVE_SECRETA_SERVICO_NOTAS, ticket),
        chave_base64,
    )


def criar_sessao_web(app, cliente, usuario, perfil):
    ticket, chave = criar_ticket_notas(usuario)
    id_sessao = f"sessao-{usuario}"
    app.extensions["sessoes_kerberos"][id_sessao] = {
        "usuario": usuario,
        "perfil": perfil,
        "ticket_servico": ticket,
        "chave_sessao_servico": chave,
        "portal_autenticado": True,
        "logs": [],
    }
    with cliente.session_transaction() as sessao:
        sessao["id_sessao_kerberos"] = id_sessao


def test_professor_cria_lista_e_edita_nota(dados_portal):
    nota = criar_nota("prof", "ana", "Seguranca", 8.5, "Bom trabalho")

    assert nota["aluno"] == "ana"
    assert listar_notas("prof", "professor") == [nota]

    atualizada = editar_nota(
        "prof",
        nota["id"],
        "Seguranca Computacional",
        9,
        "Revisada",
    )

    assert atualizada["nota"] == 9
    assert listar_notas("ana", "aluno")[0]["observacao"] == "Revisada"


def test_aluno_visualiza_apenas_as_proprias_notas(dados_portal):
    criar_nota("prof", "ana", "Criptografia", 9)
    criar_nota("prof", "bia", "Redes", 7)

    notas_ana = listar_notas("ana", "aluno")

    assert len(notas_ana) == 1
    assert notas_ana[0]["aluno"] == "ana"
    assert notas_ana[0]["disciplina"] == "Criptografia"


def test_aluno_nao_pode_criar_nota(dados_portal):
    with pytest.raises(PermissionError, match="aluno nao pode alterar"):
        criar_nota("ana", "ana", "Redes", 10, perfil="aluno")


def test_aluno_nao_pode_editar_nota(dados_portal):
    nota = criar_nota("prof", "ana", "Redes", 8)

    with pytest.raises(PermissionError, match="aluno nao pode alterar"):
        editar_nota("ana", nota["id"], "Redes", 10, perfil="aluno")


def test_professor_pode_excluir_nota(dados_portal):
    nota = criar_nota("prof", "ana", "Redes", 8)

    excluir_nota(nota["id"], perfil="professor")

    assert listar_notas("ana", "aluno") == []


def test_portal_realiza_autenticacao_mutua(dados_portal):
    ticket, chave = criar_ticket_notas("ana")
    autenticador = criar_autenticador("ana", chave, nonce="nonce-notas")

    confirmacao = autenticar_portal_notas(ticket, autenticador)
    resposta = validar_confirmacao_portal(
        chave,
        confirmacao,
        timestamp_esperado=abrir_autenticador(chave, autenticador)["timestamp"],
        nonce_esperado="nonce-notas",
    )

    assert resposta["status"] == "portal_autenticado"


def test_portal_rejeita_autenticador_com_chave_errada(dados_portal):
    ticket, _ = criar_ticket_notas("ana")
    chave_errada = bytes_para_base64(gerar_chave_simetrica())
    autenticador = criar_autenticador("ana", chave_errada)

    with pytest.raises(ValueError, match="Autenticador Cliente-Servico invalido"):
        autenticar_portal_notas(ticket, autenticador)


def test_portal_rejeita_ticket_adulterado(dados_portal):
    ticket, chave = criar_ticket_notas("ana")
    ticket["ciphertext"] = ticket["ciphertext"][:-2] + "AA"
    autenticador = criar_autenticador("ana", chave)

    with pytest.raises(ValueError, match="Ticket de servico invalido"):
        autenticar_portal_notas(ticket, autenticador)


def test_rota_professor_salva_e_exibe_nota(dados_portal):
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        criar_sessao_web(app, cliente, "prof", "professor")
        resposta = cliente.post(
            "/notas",
            data={
                "aluno": "ana",
                "disciplina": "Seguranca",
                "nota": "8.5",
                "observacao": "Fluxo AS TGS Portal",
            },
            follow_redirects=True,
        )

    assert resposta.status_code == 200
    assert b"Seguranca" in resposta.data
    assert b"Fluxo AS TGS Portal" in resposta.data


def test_rota_impede_aluno_de_lancar_nota(dados_portal):
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        criar_sessao_web(app, cliente, "ana", "aluno")
        resposta = cliente.post(
            "/notas",
            data={
                "aluno": "ana",
                "disciplina": "Seguranca",
                "nota": "10",
            },
        )

    assert resposta.status_code == 403
    assert listar_notas("ana", "aluno") == []


def test_rota_recusa_acesso_sem_service_ticket(dados_portal):
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as cliente:
        resposta = cliente.get("/notas")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")
