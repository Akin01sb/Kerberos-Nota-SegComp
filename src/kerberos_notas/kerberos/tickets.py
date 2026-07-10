"""
@file tickets.py
@brief Estruturas de tickets e funcoes de validade temporal.

@details
O modulo cria o TGT usado pelo AS/TGS e o Service Ticket usado pelo TGS/Portal
de Notas. Ele tambem concentra as verificacoes simples de expiracao por tempo
de emissao ou timestamp absoluto.
"""

import time
import uuid

TEMPO_VALIDADE_TICKET = 60 * 10
TEMPO_VALIDADE_TICKET_SERVICO = 60 * 10


def timestamp_atual() -> int:
    """@brief Retorna o timestamp Unix atual em segundos."""
    return int(time.time())


def ticket_expirou(timestamp_emissao: int, validade_segundos: int) -> bool:
    """
    @brief Verifica expiracao calculada a partir da emissao do ticket.

    @param timestamp_emissao Momento em que o ticket foi criado.
    @param validade_segundos Janela de validade em segundos.
    @return True quando o ticket ja passou da validade.
    """
    agora = timestamp_atual()

    return agora > timestamp_emissao + validade_segundos


def ticket_expirou_por_timestamp(timestamp_expiracao: int) -> bool:
    """
    @brief Verifica expiracao usando um timestamp absoluto.

    @param timestamp_expiracao Momento maximo aceito para o ticket.
    @return True quando o horario atual ultrapassou a expiracao.
    """
    return timestamp_atual() > timestamp_expiracao


def criar_tgt(
        id_cliente: str,
        chave_sessao_cliente_tgs_base64: str,
        id_tgs: str = "tgs"
) -> dict:
    """
    @brief Cria o Ticket Granting Ticket em claro antes da cifragem.

    @param id_cliente Usuario autenticado pelo AS.
    @param chave_sessao_cliente_tgs_base64 Chave de sessao Cliente-TGS.
    @param id_tgs Identificador logico do TGS.
    @return Dicionario do TGT a ser cifrado com a chave secreta do TGS.

    O cliente transporta esse ticket, mas nao consegue abri-lo depois que o AS
    cifra o conteudo com a chave secreta compartilhada com o TGS.
    """

    return {
        "id_cliente": id_cliente,
        "id_tgs": id_tgs,
        "chave_sessao_cliente_tgs": chave_sessao_cliente_tgs_base64,
        "timestamp_emissao": timestamp_atual(),
        "validade_segundos": TEMPO_VALIDADE_TICKET
    }


def criar_ticket_servico(
        usuario: str,
        servico: str,
        chave_sessao_cliente_servico_base64: str,
        validade_segundos: int = TEMPO_VALIDADE_TICKET_SERVICO
) -> dict:
    """
    @brief Cria o Service Ticket em claro antes da cifragem.

    @param usuario Usuario dono do ticket.
    @param servico Nome do servico protegido, como `notas`.
    @param chave_sessao_cliente_servico_base64 Chave de sessao Cliente-Servico.
    @param validade_segundos Janela de validade do ticket.
    @return Dicionario do ticket que sera cifrado com a chave do servico.
    """
    timestamp_emissao = timestamp_atual()

    return {
        "usuario": usuario,
        "servico": servico,
        "chave_sessao_cliente_servico": chave_sessao_cliente_servico_base64,
        "timestamp_emissao": timestamp_emissao,
        "timestamp_expiracao": timestamp_emissao + validade_segundos,
        "nonce": uuid.uuid4().hex
    }
