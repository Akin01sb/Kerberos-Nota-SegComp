"""
@file service.py
@brief Regras de negocio do sistema de notas.

@details
Este modulo aplica permissoes de perfil, normaliza notas numericas e chama o
repositorio de notas. Ele nao valida Kerberos diretamente; essa verificacao
ocorre antes, no Portal de Notas.
"""

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
    """
    @brief Retorna o perfil cadastrado para um usuario.

    @param usuario Nome do usuario.
    @return `professor` ou `aluno`.
    @throws ValueError Quando o usuario nao existe.
    """
    usuarios = carregar_usuarios().get("usuarios", {})
    dados_usuario = usuarios.get(usuario)

    if not dados_usuario:
        raise ValueError("Usuario nao encontrado.")

    return dados_usuario.get("perfil", PERFIL_ALUNO)


def listar_alunos():
    """@brief Lista usuarios cadastrados com perfil de aluno."""
    usuarios = carregar_usuarios().get("usuarios", {})
    return sorted(
        usuario
        for usuario, dados in usuarios.items()
        if dados.get("perfil", PERFIL_ALUNO) == PERFIL_ALUNO
    )


def listar_notas(usuario, perfil=None):
    """
    @brief Lista notas visiveis para um usuario.

    @param usuario Usuario autenticado.
    @param perfil Perfil do usuario; professor enxerga todas, aluno apenas as suas.
    @return Lista de notas permitidas para o perfil.
    """
    if not usuario:
        raise ValueError("Usuario nao informado.")

    perfil = perfil or PERFIL_ALUNO
    if perfil == PERFIL_PROFESSOR:
        return listar_todas_notas()

    return listar_notas_usuario(usuario)


def _validar_professor(perfil):
    """
    @brief Garante que apenas professor altere notas.

    @param perfil Perfil informado para a operacao.
    @throws PermissionError Quando o perfil nao e professor.
    """
    if perfil != PERFIL_PROFESSOR:
        raise PermissionError("Acesso negado: aluno nao pode alterar notas.")


def _normalizar_nota(valor):
    """
    @brief Converte uma nota textual ou numerica para float valido.

    @param valor Valor recebido do formulario ou teste.
    @return Nota normalizada entre 0 e 10.
    @throws ValueError Quando o valor nao e numerico ou esta fora da faixa.
    """
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
    """
    @brief Cria uma nota para um aluno.

    @param professor Usuario professor autenticado.
    @param aluno Aluno dono da nota.
    @param disciplina Nome da disciplina.
    @param nota Valor numerico entre 0 e 10.
    @param observacao Texto opcional.
    @param perfil Perfil do usuario que esta executando a acao.
    @return Nota salva no repositorio.
    """
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


def criar_notas(
        professor,
        aluno,
        notas,
        perfil=PERFIL_PROFESSOR
):
    """
    @brief Cria varias notas para um aluno em uma unica operacao.

    @param professor Usuario professor autenticado.
    @param aluno Aluno dono das notas.
    @param notas Lista de dicionarios com disciplina, nota e observacao.
    @param perfil Perfil do usuario que esta executando a acao.
    @return Lista de notas salvas.
    """
    _validar_professor(perfil)
    if not professor:
        raise ValueError("Professor nao informado.")

    aluno = (aluno or "").strip()
    if aluno not in listar_alunos():
        raise ValueError("Aluno nao encontrado.")
    if not isinstance(notas, list) or not notas:
        raise ValueError("Informe pelo menos uma nota.")

    notas_validadas = []
    for item in notas:
        disciplina = (item.get("disciplina") or "").strip()
        if not disciplina:
            raise ValueError("Disciplina nao informada.")
        notas_validadas.append({
            "disciplina": disciplina,
            "nota": _normalizar_nota(item.get("nota")),
            "observacao": (item.get("observacao") or "").strip(),
            "professor": professor,
        })

    return [
        adicionar_nota_usuario(aluno, item)
        for item in notas_validadas
    ]


def editar_nota(
        professor,
        nota_id,
        disciplina,
        nota,
        observacao="",
        perfil=PERFIL_PROFESSOR
):
    """
    @brief Atualiza uma nota existente.

    @param professor Usuario professor autenticado.
    @param nota_id Identificador da nota.
    @param disciplina Novo nome da disciplina.
    @param nota Novo valor numerico.
    @param observacao Nova observacao.
    @param perfil Perfil do usuario que esta executando a acao.
    @return Nota atualizada.
    """
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
    """
    @brief Remove uma nota existente.

    @param nota_id Identificador da nota.
    @param perfil Perfil do usuario que esta executando a acao.
    @return Nota removida.
    """
    _validar_professor(perfil)
    return excluir_nota_por_id(nota_id)
