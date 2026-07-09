import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kerberos_notas.storage.json_store import salvar_json


CAMINHO_NOTAS = Path(__file__).resolve().parents[1] / "data" / "notas.json"


def resetar_notas():
    salvar_json(CAMINHO_NOTAS, {"notas": {}})


def main():
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
