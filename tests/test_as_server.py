import json

import pytest

from kerberos_notas.client.routes import autenticar_com_kerberos
from kerberos_notas.config import CHAVE_SECRETA_TGS
from kerberos_notas.crypto.crypto_utils import (
    descriptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.crypto.kdf import (
    derivar_chave_senha,
    gerar_salt,
    gerar_verificador_chave,
)
from kerberos_notas.kerberos import as_server
from kerberos_notas.kerberos.as_server import autenticar_no_as
from kerberos_notas.kerberos.authenticator import criar_autenticador
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico


@pytest.fixture
def usuario_teste(tmp_path, monkeypatch):
    caminho_usuarios = tmp_path / "usuarios.json"
    salt = gerar_salt()
    senha = "senha123"
    chave_cliente = derivar_chave_senha(senha, salt)
    verificador = gerar_verificador_chave(chave_cliente)

    dados = {
        "usuarios": {
            "ana": {
                "salt": salt,
                "verificador": verificador
            }
        }
    }

    caminho_usuarios.write_text(
        json.dumps(dados, indent=4),
        encoding="utf-8"
    )
    monkeypatch.setattr(as_server, "CAMINHO_USUARIOS", caminho_usuarios)

    return {
        "usuario": "ana",
        "senha": senha,
        "salt": salt,
        "chave_cliente": chave_cliente
    }


def abrir_resposta_as(usuario_teste):
    resposta_criptografada = autenticar_no_as(
        usuario_teste["usuario"],
        usuario_teste["senha"]
    )

    return descriptografar_json(
        usuario_teste["chave_cliente"],
        resposta_criptografada
    )


def test_as_autentica_usuario_valido(usuario_teste):
    resposta = abrir_resposta_as(usuario_teste)

    assert resposta["id_tgs"] == "tgs"
    assert resposta["chave_sessao_cliente_tgs"]
    assert resposta["tgt"]


def test_as_rejeita_usuario_inexistente(usuario_teste):
    with pytest.raises(ValueError, match="Usuario nao encontrado"):
        autenticar_no_as("usuario_errado", "senha123")


def test_as_rejeita_senha_invalida(usuario_teste):
    with pytest.raises(ValueError, match="Senha invalida"):
        autenticar_no_as("ana", "senha_errada")


def test_as_gera_tgt_valido_com_dados_necessarios(usuario_teste):
    resposta = abrir_resposta_as(usuario_teste)
    tgt = descriptografar_json(CHAVE_SECRETA_TGS, resposta["tgt"])

    assert tgt["usuario"] == "ana"
    assert tgt["id_cliente"] == "ana"
    assert tgt["chave_sessao_cliente_tgs"] == resposta["chave_sessao_cliente_tgs"]
    assert tgt["timestamp_emissao"] < tgt["timestamp_expiracao"]
    assert tgt["validade_segundos"] > 0
    assert tgt["nonce"]


def test_tgt_nao_fica_legivel_sem_chave_correta(usuario_teste):
    resposta = abrir_resposta_as(usuario_teste)
    tgt_criptografado = resposta["tgt"]
    texto_tgt = str(tgt_criptografado)

    assert "ana" not in texto_tgt
    assert "chave_sessao_cliente_tgs" not in texto_tgt

    with pytest.raises(Exception):
        descriptografar_json(gerar_chave_simetrica(), tgt_criptografado)


def test_tgt_do_as_e_aceito_pelo_tgs(usuario_teste):
    resposta = abrir_resposta_as(usuario_teste)
    autenticador = criar_autenticador(
        "ana",
        resposta["chave_sessao_cliente_tgs"]
    )

    resposta_tgs = emitir_ticket_servico(
        usuario="ana",
        servico="notas",
        tgt_criptografado=resposta["tgt"],
        autenticador_criptografado=autenticador
    )

    assert resposta_tgs["servico"] == "notas"
    assert resposta_tgs["ticket_servico"]
    assert resposta_tgs["resposta_cliente"]


def test_resposta_do_as_pode_seguir_fluxo_do_cliente(usuario_teste):
    resultado = autenticar_com_kerberos("ana", "senha123")

    assert resultado["ticket_servico"]
    assert resultado["chave_sessao_servico"]
