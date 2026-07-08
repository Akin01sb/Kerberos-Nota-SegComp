import copy

import pytest

from kerberos_notas.config import CHAVE_SECRETA_SERVICO_CHAT, CHAVE_SECRETA_TGS
from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    bytes_para_base64,
    criptografar_json,
    descriptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.kerberos.authenticator import criar_autenticador
from kerberos_notas.kerberos.tgs_server import emitir_ticket_servico
from kerberos_notas.kerberos.tickets import criar_tgt, criar_ticket_servico
from kerberos_notas.notes.chat_client import (
    montar_pacote_chat,
    validar_resposta_chat,
)
from kerberos_notas.notes.chat_server import processar_pacote_chat
from kerberos_notas.notes.chat_seguro import (
    ALERTA_IDENTIDADE,
    ALERTA_INTEGRIDADE,
    autenticar_servico_chat,
    criar_mensagem_segura,
    receber_mensagem_segura,
    validar_confirmacao_servico,
    validar_ticket_chat,
)


def montar_ticket_chat(usuario="ana", validade_segundos=600):
    chave_sessao = gerar_chave_simetrica()
    chave_sessao_base64 = bytes_para_base64(chave_sessao)

    ticket = criar_ticket_servico(
        usuario=usuario,
        servico="chat",
        chave_sessao_cliente_servico_base64=chave_sessao_base64,
        validade_segundos=validade_segundos
    )

    ticket_criptografado = criptografar_json(
        CHAVE_SECRETA_SERVICO_CHAT,
        ticket
    )

    return chave_sessao_base64, ticket_criptografado


def montar_ticket_chat_pelo_tgs(usuario="ana"):
    chave_cliente_tgs = gerar_chave_simetrica()
    chave_cliente_tgs_base64 = bytes_para_base64(chave_cliente_tgs)

    tgt = criar_tgt(
        id_cliente=usuario,
        chave_sessao_cliente_tgs_base64=chave_cliente_tgs_base64
    )
    tgt_criptografado = criptografar_json(CHAVE_SECRETA_TGS, tgt)
    autenticador = criar_autenticador(usuario, chave_cliente_tgs_base64)

    resposta_tgs = emitir_ticket_servico(
        usuario=usuario,
        servico="chat",
        tgt_criptografado=tgt_criptografado,
        autenticador_criptografado=autenticador
    )

    dados_cliente = descriptografar_json(
        base64_para_bytes(chave_cliente_tgs_base64),
        resposta_tgs["resposta_cliente"]
    )

    return dados_cliente["chave_sessao_cliente_servico"], resposta_tgs["ticket_servico"]


def test_servico_aceita_ticket_valido_emitido_pelo_tgs():
    _, ticket_criptografado = montar_ticket_chat_pelo_tgs()

    ticket = validar_ticket_chat(ticket_criptografado)

    assert ticket["usuario"] == "ana"
    assert ticket["servico"] == "chat"
    assert ticket["chave_sessao_cliente_servico"]


def test_servico_rejeita_ticket_expirado():
    _, ticket_criptografado = montar_ticket_chat(validade_segundos=-1)

    with pytest.raises(ValueError, match="Ticket de servico expirado"):
        validar_ticket_chat(ticket_criptografado)


def test_servico_rejeita_ticket_invalido():
    ticket_invalido = criptografar_json(
        gerar_chave_simetrica(),
        {"usuario": "ana", "servico": "chat"}
    )

    with pytest.raises(ValueError, match="Ticket de servico invalido"):
        validar_ticket_chat(ticket_invalido)


def test_mensagem_e_criptografada_antes_de_ser_enviada():
    chave_sessao_base64, _ = montar_ticket_chat()

    mensagem = criar_mensagem_segura(
        remetente="ana",
        destinatario="bia",
        conteudo="mensagem secreta",
        chave_sessao_cliente_servico_base64=chave_sessao_base64
    )

    assert "mensagem secreta" not in str(mensagem)

    dados = descriptografar_json(
        base64_para_bytes(chave_sessao_base64),
        mensagem["conteudo_criptografado"]
    )
    assert dados["conteudo"] == "mensagem secreta"


def test_mensagem_valida_passa_na_verificacao_de_hmac():
    chave_sessao_base64, ticket_criptografado = montar_ticket_chat()
    mensagem = criar_mensagem_segura(
        "ana",
        "bia",
        "oi bia",
        chave_sessao_base64
    )

    mensagem_aberta = receber_mensagem_segura(ticket_criptografado, mensagem)

    assert mensagem_aberta["remetente"] == "ana"
    assert mensagem_aberta["destinatario"] == "bia"
    assert mensagem_aberta["conteudo"] == "oi bia"


def test_mensagem_adulterada_e_detectada_pelo_hmac():
    chave_sessao_base64, ticket_criptografado = montar_ticket_chat()
    mensagem = criar_mensagem_segura(
        "ana",
        "bia",
        "oi bia",
        chave_sessao_base64
    )
    mensagem_adulterada = copy.deepcopy(mensagem)
    mensagem_adulterada["destinatario"] = "carla"

    with pytest.raises(ValueError, match=ALERTA_INTEGRIDADE):
        receber_mensagem_segura(ticket_criptografado, mensagem_adulterada)


def test_usuario_diferente_do_ticket_e_rejeitado():
    chave_sessao_base64, ticket_criptografado = montar_ticket_chat(usuario="ana")
    mensagem = criar_mensagem_segura(
        "bia",
        "ana",
        "tentativa indevida",
        chave_sessao_base64
    )

    with pytest.raises(ValueError, match=ALERTA_IDENTIDADE):
        receber_mensagem_segura(ticket_criptografado, mensagem)


def test_autenticacao_mutua_funciona_com_chave_correta():
    chave_sessao_base64, ticket_criptografado = montar_ticket_chat()
    autenticador = criar_autenticador("ana", chave_sessao_base64, nonce="nonce123")

    confirmacao = autenticar_servico_chat(ticket_criptografado, autenticador)
    dados_confirmacao = validar_confirmacao_servico(
        chave_sessao_base64,
        confirmacao,
        nonce_esperado="nonce123"
    )

    assert dados_confirmacao["usuario"] == "ana"
    assert dados_confirmacao["status"] == "canal_autenticado"


def test_autenticacao_mutua_falha_com_chave_incorreta():
    chave_sessao_base64, ticket_criptografado = montar_ticket_chat()
    autenticador = criar_autenticador("ana", chave_sessao_base64, nonce="nonce123")
    confirmacao = autenticar_servico_chat(ticket_criptografado, autenticador)
    chave_errada = bytes_para_base64(gerar_chave_simetrica())

    with pytest.raises(ValueError, match="Confirmacao do servico invalida"):
        validar_confirmacao_servico(
            chave_errada,
            confirmacao,
            nonce_esperado="nonce123"
        )


def test_fluxo_cliente_servidor_do_chat_funciona():
    chave_sessao_base64, ticket_criptografado = montar_ticket_chat_pelo_tgs()
    pacote = montar_pacote_chat(
        remetente="ana",
        destinatario="bia",
        conteudo="oi pelo chat",
        ticket_servico_criptografado=ticket_criptografado,
        chave_sessao_cliente_servico_base64=chave_sessao_base64,
        nonce_autenticador="nonce-fluxo"
    )

    resposta = processar_pacote_chat(pacote)
    confirmacao = validar_resposta_chat(
        chave_sessao_base64,
        resposta,
        nonce_autenticador="nonce-fluxo"
    )

    assert resposta["ok"] is True
    assert resposta["mensagem"]["conteudo"] == "oi pelo chat"
    assert confirmacao["status"] == "canal_autenticado"
