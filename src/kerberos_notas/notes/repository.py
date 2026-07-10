"""
@file repository.py
@brief Persistencia das notas em arquivo JSON.

@details
O repositorio guarda notas em `data/notas.json`, agrupadas por aluno. Um lock
protege as operacoes de leitura/escrita durante requisicoes simultaneas.
"""

from pathlib import Path
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from kerberos_notas.storage.json_store import carregar_json, salvar_json


CAMINHO_NOTAS = Path(__file__).resolve().parents[3] / "data" / "notas.json"
BLOQUEIO_NOTAS = RLock()


def _normalizar_dados(dados):
    """
    @brief Garante que a estrutura raiz de notas esteja no formato esperado.

    @param dados Conteudo carregado do JSON.
    @return Dicionario com a chave `notas`.
    """
    if not isinstance(dados, dict):
        return {"notas": {}}

    if "notas" not in dados:
        return {"notas": {}}

    if not isinstance(dados["notas"], dict):
        return {"notas": {}}

    return dados


def carregar_notas():
    """@brief Carrega o arquivo de notas ou retorna estrutura vazia."""
    dados = carregar_json(CAMINHO_NOTAS, {"notas": {}})
    return _normalizar_dados(dados)


def salvar_notas(dados):
    """@brief Salva o arquivo de notas apos normalizar a estrutura."""
    salvar_json(CAMINHO_NOTAS, _normalizar_dados(dados))


def listar_notas_usuario(usuario):
    """
    @brief Lista as notas de um aluno especifico.

    @param usuario Aluno dono das notas.
    @return Lista de notas do aluno.
    """
    with BLOQUEIO_NOTAS:
        dados = carregar_notas()
        return list(dados["notas"].get(usuario, []))


def listar_todas_notas():
    """@brief Retorna todas as notas, incluindo o aluno em cada item."""
    with BLOQUEIO_NOTAS:
        dados = carregar_notas()
        notas = []

        for aluno, notas_aluno in dados["notas"].items():
            for nota in notas_aluno:
                nota_com_aluno = dict(nota)
                nota_com_aluno.setdefault("aluno", aluno)
                notas.append(nota_com_aluno)

        return notas


def adicionar_nota_usuario(usuario, nota):
    """
    @brief Adiciona uma nota ao aluno informado.

    @param usuario Aluno dono da nota.
    @param nota Dados ja validados pela camada de servico.
    @return Nota salva com id e timestamps.
    """
    with BLOQUEIO_NOTAS:
        dados = carregar_notas()
        notas_usuario = dados["notas"].setdefault(usuario, [])
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")

        nota_salva = {
            "id": uuid4().hex,
            "aluno": usuario,
            "disciplina": nota["disciplina"],
            "nota": nota["nota"],
            "observacao": nota.get("observacao", ""),
            "professor": nota["professor"],
            "criado_em": agora,
            "atualizado_em": agora,
        }
        notas_usuario.append(nota_salva)

        salvar_notas(dados)
        return nota_salva


def buscar_nota_por_id(nota_id):
    """
    @brief Procura uma nota pelo identificador global.

    @param nota_id Identificador da nota.
    @return Copia da nota encontrada ou None.
    """
    with BLOQUEIO_NOTAS:
        dados = carregar_notas()

        for aluno, notas_aluno in dados["notas"].items():
            for nota in notas_aluno:
                if nota.get("id") == nota_id:
                    nota_encontrada = dict(nota)
                    nota_encontrada.setdefault("aluno", aluno)
                    return nota_encontrada

        return None


def atualizar_nota_por_id(nota_id, campos):
    """
    @brief Atualiza campos de uma nota existente.

    @param nota_id Identificador da nota.
    @param campos Campos validados para sobrescrever.
    @return Copia da nota atualizada.
    @throws ValueError Quando a nota nao existe.
    """
    with BLOQUEIO_NOTAS:
        dados = carregar_notas()

        for aluno, notas_aluno in dados["notas"].items():
            for nota in notas_aluno:
                if nota.get("id") == nota_id:
                    nota.update(campos)
                    nota["aluno"] = aluno
                    nota["atualizado_em"] = datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    )
                    salvar_notas(dados)
                    return dict(nota)

        raise ValueError("Nota nao encontrada.")


def excluir_nota_por_id(nota_id):
    """
    @brief Remove uma nota pelo identificador.

    @param nota_id Identificador da nota.
    @return Nota removida.
    @throws ValueError Quando a nota nao existe.
    """
    with BLOQUEIO_NOTAS:
        dados = carregar_notas()

        for notas_aluno in dados["notas"].values():
            for indice, nota in enumerate(notas_aluno):
                if nota.get("id") == nota_id:
                    nota_excluida = notas_aluno.pop(indice)
                    salvar_notas(dados)
                    return nota_excluida

        raise ValueError("Nota nao encontrada.")
