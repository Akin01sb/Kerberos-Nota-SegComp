"""
@file cliente_tcp.py
@brief Cliente TCP usado pelo Flask para conversar com AS, TGS e Notas.

@details
A classe encapsula as chamadas remotas do fluxo Kerberos. Cada metodo monta uma
mensagem JSON, envia para a porta correta e traduz erros remotos em excecoes
locais.
"""

import socket

from kerberos_notas.config import (
    HOST_KERBEROS,
    PORTA_AS,
    PORTA_NOTAS,
    PORTA_TGS,
    TIMEOUT_REDE,
)
from kerberos_notas.rede.protocolo import enviar_mensagem, receber_mensagem


class ClienteKerberosTCP:
    """@brief Fachada TCP para os tres servidores Kerberos."""

    def __init__(
            self,
            host=HOST_KERBEROS,
            porta_as=PORTA_AS,
            porta_tgs=PORTA_TGS,
            porta_notas=PORTA_NOTAS,
            timeout=TIMEOUT_REDE
    ):
        """
        @brief Configura enderecos e timeout das conexoes.

        @param host Host comum dos servidores.
        @param porta_as Porta do AS.
        @param porta_tgs Porta do TGS.
        @param porta_notas Porta do servico de notas.
        @param timeout Timeout de conexao e leitura.
        """
        self.host = host
        self.porta_as = porta_as
        self.porta_tgs = porta_tgs
        self.porta_notas = porta_notas
        self.timeout = timeout

    def _solicitar(self, porta, requisicao):
        """
        @brief Envia uma requisicao para uma porta Kerberos e retorna o resultado.

        @param porta Porta TCP do servidor.
        @param requisicao Dicionario JSON da chamada remota.
        @return Campo `resultado` da resposta remota.
        @throws ConnectionError Quando nao ha servidor disponivel.
        @throws PermissionError Quando o servidor remoto negou permissao.
        @throws ValueError Para demais erros remotos.
        """
        try:
            with socket.create_connection(
                (self.host, porta),
                timeout=self.timeout,
            ) as conexao:
                conexao.settimeout(self.timeout)
                enviar_mensagem(conexao, requisicao)
                resposta = receber_mensagem(conexao)
        except OSError as erro:
            raise ConnectionError(
                f"Nao foi possivel conectar ao servico na porta {porta}."
            ) from erro

        if resposta.get("sucesso"):
            return resposta["resultado"]

        mensagem = resposta.get("erro", "Erro remoto sem detalhes.")
        if resposta.get("tipo_erro") == "PermissionError":
            raise PermissionError(mensagem)
        raise ValueError(mensagem)

    def solicitar_parametros_as(self, usuario):
        """@brief Pede salt, iteracoes da KDF e desafio ao AS."""
        return self._solicitar(
            self.porta_as,
            {"acao": "obter_parametros", "usuario": usuario},
        )

    def enviar_prova_as(self, usuario, desafio, prova):
        """@brief Envia ao AS a prova HMAC calculada pelo cliente."""
        return self._solicitar(
            self.porta_as,
            {
                "acao": "autenticar",
                "usuario": usuario,
                "desafio": desafio,
                "prova": prova,
            },
        )

    def solicitar_ticket_servico(
            self,
            usuario,
            servico,
            tgt,
            autenticador
    ):
        """@brief Solicita ao TGS um Service Ticket para o servico informado."""
        return self._solicitar(
            self.porta_tgs,
            {
                "acao": "emitir_ticket",
                "usuario": usuario,
                "servico": servico,
                "tgt": tgt,
                "autenticador": autenticador,
            },
        )

    def autenticar_portal(self, ticket_servico, autenticador):
        """@brief Envia Service Ticket e autenticador para autenticacao mutua."""
        return self._solicitar(
            self.porta_notas,
            {
                "acao": "autenticar_portal",
                "ticket_servico": ticket_servico,
                "autenticador": autenticador,
            },
        )

    def executar_operacao(
            self,
            ticket_servico,
            autenticador,
            requisicao
    ):
        """@brief Executa uma operacao protegida no Portal de Notas."""
        return self._solicitar(
            self.porta_notas,
            {
                "acao": "executar_operacao",
                "ticket_servico": ticket_servico,
                "autenticador": autenticador,
                "requisicao": requisicao,
            },
        )
