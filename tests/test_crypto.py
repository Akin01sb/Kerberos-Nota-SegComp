"""Testes das primitivas criptograficas e da KDF usada pelo projeto."""

import base64

import pytest
from cryptography.exceptions import InvalidTag

from kerberos_notas.crypto.crypto_utils import (
    criptografar_json,
    descriptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.crypto.kdf import (
    derivar_chave_senha,
    gerar_salt,
    gerar_verificador_chave,
    verificar_senha,
)


def test_aes_gcm_criptografa_e_descriptografa_json():
    chave = gerar_chave_simetrica()
    dados = {"mensagem": "conteudo protegido", "valor": 10}

    pacote = criptografar_json(chave, dados)

    assert descriptografar_json(chave, pacote) == dados
    assert "conteudo protegido" not in str(pacote)


def test_aes_gcm_rejeita_chave_errada():
    pacote = criptografar_json(gerar_chave_simetrica(), {"segredo": "nota"})

    with pytest.raises(InvalidTag):
        descriptografar_json(gerar_chave_simetrica(), pacote)


def test_aes_gcm_detecta_ciphertext_adulterado():
    chave = gerar_chave_simetrica()
    pacote = criptografar_json(chave, {"segredo": "nota"})
    adulterado = dict(pacote)
    ciphertext = bytearray(base64.b64decode(adulterado["ciphertext"]))
    ciphertext[0] ^= 1
    adulterado["ciphertext"] = base64.b64encode(ciphertext).decode("ascii")

    with pytest.raises(InvalidTag):
        descriptografar_json(chave, adulterado)


def test_aes_gcm_usa_nonces_diferentes():
    chave = gerar_chave_simetrica()

    primeiro = criptografar_json(chave, {"valor": 1})
    segundo = criptografar_json(chave, {"valor": 1})

    assert primeiro["nonce"] != segundo["nonce"]
    assert primeiro["ciphertext"] != segundo["ciphertext"]


def test_kdf_e_deterministica_com_mesma_senha_e_salt():
    salt = gerar_salt()

    assert derivar_chave_senha("senha", salt) == derivar_chave_senha("senha", salt)


def test_kdf_produz_chaves_diferentes_com_salts_diferentes():
    assert derivar_chave_senha("senha", gerar_salt()) != derivar_chave_senha(
        "senha",
        gerar_salt(),
    )


def test_verificacao_de_senha_rejeita_senha_errada():
    salt = gerar_salt()
    chave = derivar_chave_senha("senha-correta", salt)
    verificador = gerar_verificador_chave(chave)

    assert verificar_senha("senha-correta", salt, verificador)
    assert not verificar_senha("senha-errada", salt, verificador)
