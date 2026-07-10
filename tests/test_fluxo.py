import json

import pytest

from kerberos_notas.client.routes import autenticar_com_kerberos, create_app
from kerberos_notas.crypto.kdf import (
    derivar_chave_senha,
    gerar_salt,
    gerar_verificador_chave,
)
from kerberos_notas.kerberos import as_server
from kerberos_notas.notes import repository


@pytest.fixture
def ambiente_completo(tmp_path, monkeypatch):
    usuarios = {}
    for usuario, senha, perfil in (
        ("professor_demo", "prof123", "professor"),
        ("aluno_demo", "aluno123", "aluno"),
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


def test_fluxo_as_tgs_portal_com_autenticacao_mutua(ambiente_completo):
    resultado = autenticar_com_kerberos(
        "professor_demo",
        "prof123",
        usar_rede=False,
    )

    assert resultado["perfil"] == "professor"
    assert resultado["portal_autenticado"] is True
    assert resultado["ticket_servico"]["ciphertext"]
    assert any("TGT emitido" in etapa for etapa in resultado["logs"])
    assert any(
        "autenticacao mutua concluida" in etapa.lower()
        for etapa in resultado["logs"]
    )
    assert all("prof123" not in etapa for etapa in resultado["logs"])


def test_fluxo_web_professor_lanca_e_aluno_consulta(ambiente_completo):
    app = create_app(usar_rede=False)
    app.config["TESTING"] = True

    with app.test_client() as professor:
        resposta = professor.post(
            "/login",
            data={"usuario": "professor_demo", "senha": "prof123"},
            follow_redirects=True,
        )
        assert resposta.status_code == 200
        assert b"Painel de Professor" in resposta.data

        resposta = professor.post(
            "/notas",
            data={
                "aluno": "aluno_demo",
                "disciplina": "Seguranca Computacional",
                "nota": "9.5",
                "observacao": "Fluxo Kerberos completo",
            },
            follow_redirects=True,
        )
        assert b"Seguranca Computacional" in resposta.data

    with app.test_client() as aluno:
        resposta = aluno.post(
            "/login",
            data={"usuario": "aluno_demo", "senha": "aluno123"},
            follow_redirects=True,
        )

        assert resposta.status_code == 200
        assert b"Painel de Aluno" in resposta.data
        assert b"Seguranca Computacional" in resposta.data
        assert b"Lan\xc3\xa7ar nota" not in resposta.data

        bloqueio = aluno.post(
            "/notas",
            data={
                "aluno": "aluno_demo",
                "disciplina": "Ataque",
                "nota": "10",
            },
        )
        assert bloqueio.status_code == 403
