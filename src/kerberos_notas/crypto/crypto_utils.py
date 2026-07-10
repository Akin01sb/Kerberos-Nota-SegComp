"""
@file crypto_utils.py
@brief Primitivas simetricas e serializacao segura de JSON.

@details
Este modulo concentra as funcoes de apoio criptografico usadas pelo AS, TGS,
cliente e Servico de Notas. Ele gera chaves AES de 32 bytes, converte dados
entre bytes e Base64 e cifra/decifra dicionarios JSON com AES-GCM.

Componentes principais:
- gerar_chave_simetrica
- bytes_para_base64
- base64_para_bytes
- criptografar_json
- descriptografar_json

Papel na arquitetura:
Camada de criptografia simetrica compartilhada por tickets, autenticadores,
respostas do AS/TGS e operacoes protegidas do Portal de Notas.
"""

import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

TAMANHO_NONCE = 12
TAMANHO_CHAVE_AES = 32


def gerar_chave_simetrica() -> bytes:
    """
    ***************************************************************************
    Funcao: gerar_chave_simetrica

    @brief Gera uma chave simetrica de 256 bits.

    Descricao:
    Usa `os.urandom` para produzir 32 bytes aleatorios. Essas chaves sao usadas
    como chaves de sessao Cliente-TGS e Cliente-Servico durante o fluxo
    Kerberos academico.

    Parametros:
    Nao recebe parametros explicitos.

    Valor retornado:
    @return Bytes aleatorios com tamanho adequado para AES-256.

    Assertiva de entrada:
    @pre O sistema operacional deve disponibilizar gerador seguro de bytes.

    Assertiva de saida:
    @post Retorna uma chave nova, independente das anteriores.

    Excecoes:
    @throws Exception Pode propagar erros do gerador de aleatoriedade.

    Observacoes:
    A chave gerada nao e persistida por esta funcao; o chamador decide como
    transporta-la ou protege-la.
    ***************************************************************************
    """
    return os.urandom(TAMANHO_CHAVE_AES)


def bytes_para_base64(dados: bytes) -> str:
    """
    ***************************************************************************
    Funcao: bytes_para_base64

    @brief Codifica bytes em Base64 textual.

    Descricao:
    Converte bytes criptograficos para string Base64, permitindo armazenar e
    transportar chaves, nonces e ciphertexts em JSON.

    Parametros:
    @param dados Sequencia de bytes a ser codificada.

    Valor retornado:
    @return String Base64.

    Assertiva de entrada:
    @pre O parametro deve ser bytes.

    Assertiva de saida:
    @post Retorna texto ASCII seguro para JSON.

    Excecoes:
    @throws Exception Pode propagar erros de codificacao Base64.

    Observacoes:
    Base64 nao criptografa; apenas representa bytes em texto.
    ***************************************************************************
    """
    return base64.b64encode(dados).decode("utf-8")


def base64_para_bytes(dados_base64: str) -> bytes:
    """
    ***************************************************************************
    Funcao: base64_para_bytes

    @brief Decodifica texto Base64 para bytes.

    Descricao:
    Reverte a representacao textual usada em mensagens JSON para recuperar
    chaves, nonces e ciphertexts em bytes.

    Parametros:
    @param dados_base64 String Base64 a ser decodificada.

    Valor retornado:
    @return Bytes decodificados.

    Assertiva de entrada:
    @pre A entrada deve ser Base64 valido.

    Assertiva de saida:
    @post Retorna a sequencia de bytes original.

    Excecoes:
    @throws Exception Pode propagar erro quando a entrada nao for Base64 valido.

    Observacoes:
    A funcao nao valida semanticamente se os bytes representam chave ou nonce.
    ***************************************************************************
    """
    return base64.b64decode(dados_base64)


def criptografar_json(chave: bytes, dados: dict) -> dict:
    """
    ***************************************************************************
    Funcao: criptografar_json

    @brief Cifra um dicionario JSON com AES-GCM.

    Descricao:
    Serializa um dicionario em JSON, gera um nonce de 12 bytes e cifra os dados
    com AES-GCM. O retorno contem nonce e ciphertext em Base64, formato usado
    nos tickets, autenticadores e respostas do protocolo.

    Parametros:
    @param chave Chave AES de 32 bytes.
    @param dados Dicionario serializavel em JSON.

    Valor retornado:
    @return Dicionario com `nonce` e `ciphertext` em Base64.

    Assertiva de entrada:
    @pre A chave deve ter tamanho aceito pelo AES-GCM.
    @pre Os dados devem ser serializaveis em JSON.

    Assertiva de saida:
    @post Retorna pacote cifrado e autenticado.

    Excecoes:
    @throws TypeError Pode ocorrer se os dados nao forem serializaveis.
    @throws Exception Pode propagar erros da biblioteca criptografica.

    Observacoes:
    AES-GCM fornece confidencialidade e deteccao de adulteracao. Nao ha dados
    autenticados adicionais associados nesta implementacao.
    ***************************************************************************
    """
    aesgcm = AESGCM(chave)
    nonce = os.urandom(TAMANHO_NONCE)

    dados_json = json.dumps(dados).encode("utf-8")

    ciphertext = aesgcm.encrypt(
        nonce,
        dados_json,
        None
    )

    return {
        "nonce": bytes_para_base64(nonce),
        "ciphertext": bytes_para_base64(ciphertext)
    }


def descriptografar_json(chave: bytes, pacote: dict) -> dict:
    """
    ***************************************************************************
    Funcao: descriptografar_json

    @brief Abre um pacote JSON cifrado por criptografar_json.

    Descricao:
    Decodifica nonce e ciphertext de Base64, executa a abertura AES-GCM e
    converte o JSON resultante para dicionario Python. Se o pacote tiver sido
    adulterado ou a chave estiver incorreta, a biblioteca criptografica falha.

    Parametros:
    @param chave Chave AES usada para abrir o pacote.
    @param pacote Dicionario contendo `nonce` e `ciphertext`.

    Valor retornado:
    @return Dicionario original descriptografado.

    Assertiva de entrada:
    @pre O pacote deve conter campos `nonce` e `ciphertext` em Base64.
    @pre A chave deve corresponder a usada na cifragem.

    Assertiva de saida:
    @post Retorna os dados originais se autenticacao AES-GCM for valida.

    Excecoes:
    @throws Exception Pode propagar erro de Base64, JSON ou tag AES-GCM invalida.

    Observacoes:
    Esta funcao e usada para abrir TGTs, Service Tickets, autenticadores,
    confirmacoes de autenticacao mutua e requisicoes protegidas.
    ***************************************************************************
    """
    aesgcm = AESGCM(chave)
    nonce = base64_para_bytes(pacote["nonce"])
    ciphertext = base64_para_bytes(pacote["ciphertext"])

    dados_json = aesgcm.decrypt(
        nonce,
        ciphertext,
        None
    )

    return json.loads(dados_json.decode("utf-8"))
