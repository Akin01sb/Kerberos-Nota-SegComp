import socketserver

from kerberos_notas.rede.protocolo import enviar_mensagem, receber_mensagem


class ServidorTCPKerberos(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, endereco, processador, nome):
        self.processador = processador
        self.nome = nome
        super().__init__(endereco, ManipuladorKerberos)


class ManipuladorKerberos(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            requisicao = receber_mensagem(self.request)
            acao = requisicao.get("acao", "desconhecida")
            print(f"[{self.server.nome}] {self.client_address[0]} solicitou {acao}.")
            resultado = self.server.processador(requisicao)
            resposta = {"sucesso": True, "resultado": resultado}
        except Exception as erro:
            resposta = {
                "sucesso": False,
                "tipo_erro": type(erro).__name__,
                "erro": str(erro),
            }

        enviar_mensagem(self.request, resposta)


def criar_servidor_tcp(host, porta, processador, nome):
    return ServidorTCPKerberos((host, porta), processador, nome)
