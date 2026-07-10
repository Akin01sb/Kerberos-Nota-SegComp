"""Testes do fluxo Kerberos usando AS, TGS e Notas por sockets TCP."""

import json
import threading

import pytest

from kerberos_notas.client.routes import (
    autenticar_com_kerberos,
    create_app,
    executar_operacao_kerberos,
)
from kerberos_notas.crypto.kdf import (
    derivar_chave_senha,
    gerar_prova_as,
    gerar_salt,
    gerar_verificador_chave,
    obter_chave_autenticacao_as,
)
from kerberos_notas.kerberos import as_server
from kerberos_notas.notes import repository
from kerberos_notas.rede.cliente_tcp import ClienteKerberosTCP
from kerberos_notas.servidores.servidor_as import criar_servidor_as
from kerberos_notas.servidores.servidor_notas import criar_servidor_notas
from kerberos_notas.servidores.servidor_tgs import criar_servidor_tgs


@pytest.fixture
def ambiente_tcp(tmp_path, monkeypatch):
    """Prepara usuarios, notas e tres servidores TCP em portas livres."""
    usuarios = {}
    for usuario, senha, perfil in (
        ("professor_tcp", "prof123", "professor"),
        ("aluno_tcp", "aluno123", "aluno"),
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

    caminho_notas = tmp_path / "notas.json"
    caminho_notas.write_text('{"notas": {}}', encoding="utf-8")
    monkeypatch.setattr(repository, "CAMINHO_NOTAS", caminho_notas)

    servidores = [
        criar_servidor_as(porta=0),
        criar_servidor_tgs(porta=0),
        criar_servidor_notas(porta=0),
    ]
    requisicoes_as = []
    processador_as = servidores[0].processador

    def registrar_requisicao_as(requisicao):
        """Registra mensagens recebidas pelo AS para verificar ausencia de senha."""
        requisicoes_as.append(dict(requisicao))
        return processador_as(requisicao)

    servidores[0].processador = registrar_requisicao_as
    threads = []
    for servidor in servidores:
        thread = threading.Thread(
            target=servidor.serve_forever,
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    cliente = ClienteKerberosTCP(
        porta_as=servidores[0].server_address[1],
        porta_tgs=servidores[1].server_address[1],
        porta_notas=servidores[2].server_address[1],
    )

    yield {
        "cliente": cliente,
        "requisicoes_as": requisicoes_as,
    }

    for servidor in servidores:
        servidor.shutdown()
        servidor.server_close()
    for thread in threads:
        thread.join(timeout=2)


def test_fluxo_completo_passa_por_tres_servidores_tcp(ambiente_tcp):
    cliente = ambiente_tcp["cliente"]
    sessao = autenticar_com_kerberos(
        "professor_tcp",
        "prof123",
        usar_rede=True,
        cliente_tcp=cliente,
    )

    nota = executar_operacao_kerberos(
        sessao,
        "criar_nota",
        {
            "aluno": "aluno_tcp",
            "disciplina": "Seguranca Computacional",
            "nota": "9.5",
            "observacao": "Criada pelo fluxo TCP",
        },
    )
    nota_editada = executar_operacao_kerberos(
        sessao,
        "editar_nota",
        {
            "nota_id": nota["id"],
            "disciplina": "Criptografia",
            "nota": "10",
            "observacao": "Editada pelo fluxo TCP",
        },
    )
    lote = executar_operacao_kerberos(
        sessao,
        "criar_notas",
        {
            "aluno": "aluno_tcp",
            "notas": [
                {
                    "disciplina": "Redes",
                    "nota": "8",
                    "observacao": "Primeira nota do lote",
                },
                {
                    "disciplina": "Programacao",
                    "nota": "9",
                    "observacao": "Segunda nota do lote",
                },
            ],
        },
    )
    painel = executar_operacao_kerberos(sessao, "carregar_painel")

    assert sessao["portal_autenticado"] is True
    assert sessao["perfil"] == "professor"
    assert nota_editada["disciplina"] == "Criptografia"
    assert len(lote) == 2
    assert any(item["id"] == nota["id"] for item in painel["notas"])

    sessao_aluno = autenticar_com_kerberos(
        "aluno_tcp",
        "aluno123",
        usar_rede=True,
        cliente_tcp=cliente,
    )
    painel_aluno = executar_operacao_kerberos(
        sessao_aluno,
        "carregar_painel",
    )
    ids_esperados = {nota["id"], *(item["id"] for item in lote)}
    assert {item["id"] for item in painel_aluno["notas"]} == ids_esperados

    with pytest.raises(PermissionError):
        executar_operacao_kerberos(
            sessao_aluno,
            "criar_nota",
            {
                "aluno": "aluno_tcp",
                "disciplina": "Operacao proibida",
                "nota": "10",
            },
        )

    executar_operacao_kerberos(
        sessao,
        "excluir_nota",
        {"nota_id": nota["id"]},
    )
    for item in lote:
        executar_operacao_kerberos(
            sessao,
            "excluir_nota",
            {"nota_id": item["id"]},
        )
    painel_final = executar_operacao_kerberos(sessao, "carregar_painel")
    assert all(item["id"] != nota["id"] for item in painel_final["notas"])


def test_senha_nao_atravessa_a_rede(ambiente_tcp):
    autenticar_com_kerberos(
        "professor_tcp",
        "prof123",
        usar_rede=True,
        cliente_tcp=ambiente_tcp["cliente"],
    )

    requisicoes = ambiente_tcp["requisicoes_as"]
    assert [item["acao"] for item in requisicoes] == [
        "obter_parametros",
        "autenticar",
    ]
    assert all("senha" not in item for item in requisicoes)
    assert "prof123" not in json.dumps(requisicoes)


def test_as_tcp_rejeita_senha_invalida(ambiente_tcp):
    with pytest.raises(ValueError, match="Senha invalida"):
        autenticar_com_kerberos(
            "professor_tcp",
            "senha-errada",
            usar_rede=True,
            cliente_tcp=ambiente_tcp["cliente"],
        )


def test_desafio_do_as_nao_pode_ser_reutilizado(ambiente_tcp):
    cliente = ambiente_tcp["cliente"]
    parametros = cliente.solicitar_parametros_as("professor_tcp")
    chave_derivada = derivar_chave_senha(
        "prof123",
        parametros["salt"],
    )
    chave_as = obter_chave_autenticacao_as(chave_derivada)
    prova = gerar_prova_as(
        chave_as,
        "professor_tcp",
        parametros["desafio"],
    )

    cliente.enviar_prova_as(
        "professor_tcp",
        parametros["desafio"],
        prova,
    )
    with pytest.raises(ValueError, match="Desafio de autenticacao invalido"):
        cliente.enviar_prova_as(
            "professor_tcp",
            parametros["desafio"],
            prova,
        )


def test_aplicacao_web_pode_usar_os_servidores_tcp(ambiente_tcp):
    app = create_app(
        usar_rede=True,
        cliente_tcp=ambiente_tcp["cliente"],
    )
    app.config["TESTING"] = True

    with app.test_client() as navegador:
        resposta = navegador.post(
            "/login",
            data={
                "usuario": "professor_tcp",
                "senha": "prof123",
            },
            follow_redirects=True,
        )
        resposta_lote = navegador.post(
            "/notas",
            data={
                "aluno": "aluno_tcp",
                "disciplina": ["Redes", "Criptografia"],
                "nota": ["8.5", "9.5"],
                "observacao": ["Primeira", "Segunda"],
            },
            follow_redirects=True,
        )

    assert resposta.status_code == 200
    assert b"Painel de Professor" in resposta.data
    assert resposta_lote.status_code == 200
    assert b"Redes" in resposta_lote.data
    assert b"Criptografia" in resposta_lote.data
