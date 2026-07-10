"""
@file authenticator.py
@brief Criacao e abertura dos autenticadores Kerberos.

@details
Autenticadores sao mensagens cifradas com chaves de sessao. Eles carregam
usuario, timestamp e nonce, e tambem podem prender a mensagem a uma acao e ao
hash de uma requisicao protegida.
"""

import uuid

from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    criptografar_json,
    descriptografar_json,
)
from kerberos_notas.kerberos.tickets import timestamp_atual


def criar_autenticador(
        usuario: str,
        chave_sessao_base64: str,
        nonce: str | None = None,
        acao: str | None = None,
        hash_requisicao: str | None = None
) -> dict:
    """
    @brief Cria autenticador cifrado com uma chave de sessao.

    @param usuario Usuario que apresenta o ticket.
    @param chave_sessao_base64 Chave de sessao em Base64.
    @param nonce Valor unico contra replay; se ausente, e gerado.
    @param acao Operacao esperada no servico, quando aplicavel.
    @param hash_requisicao Hash da requisicao protegida, quando aplicavel.
    @return Pacote AES-GCM contendo os dados do autenticador.
    """
    chave_sessao = base64_para_bytes(chave_sessao_base64)

    dados = {
        "usuario": usuario,
        "timestamp": timestamp_atual(),
        "nonce": nonce or uuid.uuid4().hex
    }

    if acao:
        dados["acao"] = acao

    if hash_requisicao:
        dados["hash_requisicao"] = hash_requisicao

    return criptografar_json(chave_sessao, dados)


def abrir_autenticador(chave_sessao_base64: str, autenticador_criptografado: dict) -> dict:
    """
    @brief Descriptografa um autenticador usando a chave de sessao esperada.

    @param chave_sessao_base64 Chave de sessao em Base64.
    @param autenticador_criptografado Pacote cifrado recebido do cliente.
    @return Dados internos do autenticador.
    @throws Exception Quando a chave ou o pacote nao validam no AES-GCM.
    """
    chave_sessao = base64_para_bytes(chave_sessao_base64)
    return descriptografar_json(chave_sessao, autenticador_criptografado)
