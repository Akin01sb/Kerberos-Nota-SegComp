"""
@file json_store.py
@brief Leitura e escrita atomica de arquivos JSON.

@details
Fornece funcoes compartilhadas para persistencia simples em JSON. A escrita usa
arquivo temporario e `os.replace`, reduzindo o risco de deixar arquivo parcial
em caso de falha durante a gravacao.
"""

import json
import os
import tempfile
from threading import RLock


BLOQUEIO_JSON = RLock()


def carregar_json(caminho, padrao):
    """
    @brief Carrega JSON de disco com fallback padrao.

    @param caminho Caminho do arquivo.
    @param padrao Valor retornado se o arquivo nao existir.
    @return Conteudo JSON carregado ou valor padrao.
    """
    with BLOQUEIO_JSON:
        if not caminho.exists():
            return padrao

        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)


def salvar_json(caminho, dados):
    """
    @brief Salva JSON de forma atomica.

    @param caminho Caminho final do arquivo.
    @param dados Dados serializaveis em JSON.
    @throws Exception Propaga erros de escrita, serializacao ou substituicao.
    """
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
