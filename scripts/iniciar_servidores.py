"""
@file iniciar_servidores.py
@brief Inicia AS, TGS e Portal de Notas em processos separados.

@details
O script facilita a demonstracao da separacao real por sockets, mantendo cada
componente Kerberos em um processo proprio.
"""

import multiprocessing
import socket
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from kerberos_notas.config import HOST_KERBEROS, PORTA_AS, PORTA_NOTAS, PORTA_TGS
from kerberos_notas.servidores.servidor_as import executar_servidor_as
from kerberos_notas.servidores.servidor_notas import executar_servidor_notas
from kerberos_notas.servidores.servidor_tgs import executar_servidor_tgs
from kerberos_notas.logs import log_evento, log_titulo


def porta_em_uso(host, porta):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexao:
        conexao.settimeout(0.3)
        return conexao.connect_ex((host, porta)) == 0


def validar_portas_livres():
    portas = {
        "AS": PORTA_AS,
        "TGS": PORTA_TGS,
        "PORTAL NOTAS": PORTA_NOTAS,
    }
    ocupadas = [
        {"servico": servico, "host": HOST_KERBEROS, "porta": porta}
        for servico, porta in portas.items()
        if porta_em_uso(HOST_KERBEROS, porta)
    ]

    if ocupadas:
        log_evento(
            "SISTEMA",
            "Portas Kerberos ja estao em uso. Encerre os processos antigos antes de iniciar novamente.",
            {"portas_ocupadas": ocupadas},
        )
        raise SystemExit(1)


def main():
    """@brief Sobe os tres servidores e aguarda ate Ctrl+C."""
    validar_portas_livres()
    processos = [
        multiprocessing.Process(
            target=executar_servidor_as,
            name="servidor-as",
        ),
        multiprocessing.Process(
            target=executar_servidor_tgs,
            name="servidor-tgs",
        ),
        multiprocessing.Process(
            target=executar_servidor_notas,
            name="servidor-notas",
        ),
    ]

    for processo in processos:
        processo.start()

    log_titulo("SISTEMA", "Servidores Kerberos academicos iniciados")
    log_evento(
        "SISTEMA",
        "AS, TGS e Portal de Notas estao rodando em processos separados",
        {"processos": [processo.name for processo in processos]},
    )
    log_evento("SISTEMA", "Pressione Ctrl+C para encerrar os tres servidores")

    try:
        for processo in processos:
            processo.join()
    except KeyboardInterrupt:
        log_evento("SISTEMA", "Encerrando servidores")
        for processo in processos:
            processo.terminate()
        for processo in processos:
            processo.join()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
