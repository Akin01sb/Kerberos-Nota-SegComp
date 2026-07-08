from kerberos_notas.notes.repository import adicionar_nota_usuario, listar_notas_usuario


def listar_notas(usuario):
    if not usuario:
        raise ValueError("Usuario nao informado.")

    return listar_notas_usuario(usuario)


def criar_nota(usuario, titulo, conteudo):
    if not usuario:
        raise ValueError("Usuario nao informado.")

    titulo = (titulo or "").strip()
    conteudo = (conteudo or "").strip()

    if not titulo:
        raise ValueError("Titulo da nota nao informado.")

    if not conteudo:
        raise ValueError("Conteudo da nota nao informado.")

    return adicionar_nota_usuario(
        usuario,
        {
            "titulo": titulo,
            "conteudo": conteudo,
        },
    )
