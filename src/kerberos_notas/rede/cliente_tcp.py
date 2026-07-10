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
    def __init__(
            self,
            host=HOST_KERBEROS,
            porta_as=PORTA_AS,
            porta_tgs=PORTA_TGS,
            porta_notas=PORTA_NOTAS,
            timeout=TIMEOUT_REDE
    ):
        self.host = host
        self.porta_as = porta_as
        self.porta_tgs = porta_tgs
        self.porta_notas = porta_notas
        self.timeout = timeout

    def _solicitar(self, porta, requisicao):
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
        return self._solicitar(
            self.porta_as,
            {"acao": "obter_parametros", "usuario": usuario},
        )

    def enviar_prova_as(self, usuario, desafio, prova):
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
        return self._solicitar(
            self.porta_notas,
            {
                "acao": "executar_operacao",
                "ticket_servico": ticket_servico,
                "autenticador": autenticador,
                "requisicao": requisicao,
            },
        )
