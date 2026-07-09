from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from kerberos_notas.storage.json_store import carregar_json, salvar_json


CAMINHO_NOTAS = Path(__file__).resolve().parents[3] / "data" / "notas.json"


def _normalizar_dados(dados):
    if not isinstance(dados, dict):
        return {"notas": {}}

    if "notas" not in dados:
        return {"notas": {}}

    if not isinstance(dados["notas"], dict):
        return {"notas": {}}

    return dados


def carregar_notas():
    dados = carregar_json(CAMINHO_NOTAS, {"notas": {}})
    return _normalizar_dados(dados)


def salvar_notas(dados):
    salvar_json(CAMINHO_NOTAS, _normalizar_dados(dados))


def listar_notas_usuario(usuario):
    dados = carregar_notas()
    return list(dados["notas"].get(usuario, []))


def listar_todas_notas():
    dados = carregar_notas()
    notas = []

    for aluno, notas_aluno in dados["notas"].items():
        for nota in notas_aluno:
            nota_com_aluno = dict(nota)
            nota_com_aluno.setdefault("aluno", aluno)
            notas.append(nota_com_aluno)

    return notas


def adicionar_nota_usuario(usuario, nota):
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
    dados = carregar_notas()

    for aluno, notas_aluno in dados["notas"].items():
        for nota in notas_aluno:
            if nota.get("id") == nota_id:
                nota_encontrada = dict(nota)
                nota_encontrada.setdefault("aluno", aluno)
                return nota_encontrada

    return None


def atualizar_nota_por_id(nota_id, campos):
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
    dados = carregar_notas()

    for notas_aluno in dados["notas"].values():
        for indice, nota in enumerate(notas_aluno):
            if nota.get("id") == nota_id:
                nota_excluida = notas_aluno.pop(indice)
                salvar_notas(dados)
                return nota_excluida

    raise ValueError("Nota nao encontrada.")
