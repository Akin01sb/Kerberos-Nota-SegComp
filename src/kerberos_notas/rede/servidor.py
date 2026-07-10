"""
@file servidor.py
@brief Infraestrutura TCP compartilhada pelos servidores Kerberos.

@details
O modulo cria servidores TCP com threads por conexao. Cada servidor recebe um
processador especifico de negocio, como AS, TGS ou Portal de Notas.
"""

import socketserver

from kerberos_notas.logs import log_erro, log_evento, log_ok
from kerberos_notas.rede.protocolo import enviar_mensagem, receber_mensagem


class ServidorTCPKerberos(socketserver.ThreadingTCPServer):
    """
    @brief Servidor TCP reutilizavel para os componentes Kerberos.

    @param endereco Par host/porta do socket.
    @param processador Funcao que trata uma requisicao JSON.
    @param nome Nome exibido nos logs do terminal.
    """

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, endereco, processador, nome):
        self.processador = processador
        self.nome = nome
        super().__init__(endereco, ManipuladorKerberos)


class ManipuladorKerberos(socketserver.BaseRequestHandler):
    """@brief Manipulador de uma conexao TCP recebida."""

    def handle(self):
        """@brief Recebe uma requisicao, executa o processador e envia resposta."""
        componente = (
            "PORTAL NOTAS"
            if self.server.nome == "NOTAS"
            else self.server.nome
        )
        try:
            requisicao = receber_mensagem(self.request)
            acao = requisicao.get("acao", "desconhecida")
            log_evento(
                componente,
                "Requisicao TCP recebida",
                {
                    "cliente": self.client_address[0],
                    "acao": acao,
                    "requisicao": requisicao,
                },
            )
            resultado = self.server.processador(requisicao)
            resposta = {"sucesso": True, "resultado": resultado}
            log_ok(
                componente,
                "Requisicao TCP processada com sucesso",
                {
                    "acao": acao,
                    "resposta": resposta,
                },
            )
        except Exception as erro:
            resposta = {
                "sucesso": False,
                "tipo_erro": type(erro).__name__,
                "erro": str(erro),
            }
            log_erro(
                componente,
                "Erro ao processar requisicao TCP",
                resposta,
            )

        log_evento(
            componente,
            "Enviando resposta TCP",
            {"resposta": resposta},
        )
        enviar_mensagem(self.request, resposta)


def criar_servidor_tcp(host, porta, processador, nome):
    """
    @brief Cria um servidor TCP Kerberos para um componente especifico.

    @param host Interface de rede.
    @param porta Porta TCP.
    @param processador Funcao de negocio chamada por requisicao.
    @param nome Nome logico do servidor.
    @return Instancia de ServidorTCPKerberos.
    """
    return ServidorTCPKerberos((host, porta), processador, nome)
