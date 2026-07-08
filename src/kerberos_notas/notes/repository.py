from pathlib import Path
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


def adicionar_nota_usuario(usuario, nota):
    dados = carregar_notas()
    notas_usuario = dados["notas"].setdefault(usuario, [])

    nota_salva = {
        "id": uuid4().hex,
        "titulo": nota["titulo"],
        "conteudo": nota["conteudo"],
    }
    notas_usuario.append(nota_salva)

    salvar_notas(dados)
    return nota_salva
