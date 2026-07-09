from kerberos_notas.kerberos.as_server import carregar_usuarios
from kerberos_notas.notes.repository import (
    adicionar_nota_usuario,
    atualizar_nota_por_id,
    buscar_nota_por_id,
    excluir_nota_por_id,
    listar_notas_usuario,
    listar_todas_notas,
)


PERFIL_PROFESSOR = "professor"
PERFIL_ALUNO = "aluno"


def obter_perfil_usuario(usuario):
    usuarios = carregar_usuarios().get("usuarios", {})
    dados_usuario = usuarios.get(usuario)

    if not dados_usuario:
        raise ValueError("Usuario nao encontrado.")

    return dados_usuario.get("perfil", PERFIL_ALUNO)


def listar_alunos():
    usuarios = carregar_usuarios().get("usuarios", {})
    return sorted(
        usuario
        for usuario, dados in usuarios.items()
        if dados.get("perfil", PERFIL_ALUNO) == PERFIL_ALUNO
    )


def listar_notas(usuario, perfil=None):
    if not usuario:
        raise ValueError("Usuario nao informado.")

    perfil = perfil or PERFIL_ALUNO
    if perfil == PERFIL_PROFESSOR:
        return listar_todas_notas()

    return listar_notas_usuario(usuario)


def _validar_professor(perfil):
    if perfil != PERFIL_PROFESSOR:
        raise PermissionError("Acesso negado: aluno nao pode alterar notas.")


def _normalizar_nota(valor):
    try:
        nota = float(str(valor).replace(",", "."))
    except (TypeError, ValueError) as erro:
        raise ValueError("Informe uma nota numerica.") from erro

    if not 0 <= nota <= 10:
        raise ValueError("A nota deve estar entre 0 e 10.")

    return nota


def criar_nota(
        professor,
        aluno,
        disciplina,
        nota,
        observacao="",
        perfil=PERFIL_PROFESSOR
):
    _validar_professor(perfil)

    if not professor:
        raise ValueError("Professor nao informado.")

    aluno = (aluno or "").strip()
    disciplina = (disciplina or "").strip()
    observacao = (observacao or "").strip()

    if aluno not in listar_alunos():
        raise ValueError("Aluno nao encontrado.")

    if not disciplina:
        raise ValueError("Disciplina nao informada.")

    return adicionar_nota_usuario(aluno, {
        "disciplina": disciplina,
        "nota": _normalizar_nota(nota),
        "observacao": observacao,
        "professor": professor,
    })


def editar_nota(
        professor,
        nota_id,
        disciplina,
        nota,
        observacao="",
        perfil=PERFIL_PROFESSOR
):
    _validar_professor(perfil)

    if not buscar_nota_por_id(nota_id):
        raise ValueError("Nota nao encontrada.")

    disciplina = (disciplina or "").strip()
    if not disciplina:
        raise ValueError("Disciplina nao informada.")

    return atualizar_nota_por_id(nota_id, {
        "disciplina": disciplina,
        "nota": _normalizar_nota(nota),
        "observacao": (observacao or "").strip(),
        "professor": professor,
    })


def excluir_nota(nota_id, perfil=PERFIL_PROFESSOR):
    _validar_professor(perfil)
    return excluir_nota_por_id(nota_id)
