import json
import os
import tempfile
from threading import RLock


BLOQUEIO_JSON = RLock()


def carregar_json(caminho, padrao):
    with BLOQUEIO_JSON:
        if not caminho.exists():
            return padrao

        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with BLOQUEIO_JSON:
        descritor, caminho_temporario = tempfile.mkstemp(
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=4)
                arquivo.write("\n")
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(caminho_temporario, caminho)
        except Exception:
            try:
                os.unlink(caminho_temporario)
            except FileNotFoundError:
                pass
            raise
