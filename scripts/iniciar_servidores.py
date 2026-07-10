"""
@file iniciar_servidores.py
@brief Inicia AS, TGS e Portal de Notas em processos separados.

@details
O script facilita a demonstracao da separacao real por sockets, mantendo cada
componente Kerberos em um processo proprio.
"""

import multiprocessing
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from kerberos_notas.servidores.servidor_as import executar_servidor_as
from kerberos_notas.servidores.servidor_notas import executar_servidor_notas
from kerberos_notas.servidores.servidor_tgs import executar_servidor_tgs


def main():
    """@brief Sobe os tres servidores e aguarda ate Ctrl+C."""
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

    print("[SISTEMA] AS, TGS e Portal de Notas iniciados.")
    print("[SISTEMA] Pressione Ctrl+C para encerrar os tres servidores.")

    try:
        for processo in processos:
            processo.join()
    except KeyboardInterrupt:
        print("\n[SISTEMA] Encerrando servidores...")
        for processo in processos:
            processo.terminate()
        for processo in processos:
            processo.join()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
