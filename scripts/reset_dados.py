"""
@file reset_dados.py
@brief Remove notas cadastradas preservando usuarios.

@details
Usado em demonstracoes e testes manuais para voltar `data/notas.json` ao estado
vazio sem apagar credenciais e perfis cadastrados.
"""

import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kerberos_notas.storage.json_store import salvar_json


CAMINHO_NOTAS = Path(__file__).resolve().parents[1] / "data" / "notas.json"


def resetar_notas():
    """@brief Regrava o arquivo de notas com estrutura vazia."""
    salvar_json(CAMINHO_NOTAS, {"notas": {}})


def main():
    """@brief Confirma com o usuario e executa a limpeza das notas."""
    resposta = input(
        "Apagar todas as notas? Os usuarios serao preservados. [s/N]: "
    ).strip().lower()

    if resposta != "s":
        print("Operacao cancelada.")
        return

    resetar_notas()
    print("Notas removidas com sucesso.")


if __name__ == "__main__":
    main()
