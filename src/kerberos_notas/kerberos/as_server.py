"""
@file as_server.py
@brief Regras do Authentication Server (AS) do Kerberos academico.

@details
Este modulo implementa a parte logica do AS. Ele carrega usuarios, cria
desafios de autenticacao, valida provas HMAC geradas pelo cliente e emite a
resposta AS-REP contendo a chave de sessao Cliente-TGS e o TGT cifrado para o
TGS.

Componentes principais:
- carregar_usuarios
- criar_desafio_as
- autenticar_no_as_com_prova
- gerar_tgt

Papel na arquitetura:
Camada do Servidor de Autenticacao. O servidor TCP em `servidor_as.py` expõe
estas funcoes ao cliente Flask.
"""

import json
import hmac
import secrets
import uuid
from pathlib import Path
from threading import RLock

from kerberos_notas.config import CHAVE_SECRETA_TGS
from kerberos_notas.crypto.crypto_utils import (
    base64_para_bytes,
    bytes_para_base64,
    criptografar_json,
    gerar_chave_simetrica,
)
from kerberos_notas.crypto.kdf import (
    ITERACOES_PBKDF2,
    gerar_prova_as,
)
from kerberos_notas.kerberos.tickets import criar_tgt, timestamp_atual


CAMINHO_USUARIOS = Path(__file__).resolve().parents[3] / "data" / "usuarios.json"
TEMPO_VALIDADE_TGT = 60 * 10
TEMPO_VALIDADE_DESAFIO = 60
DESAFIOS_AS = {}
BLOQUEIO_DESAFIOS_AS = RLock()


def carregar_usuarios() -> dict:
    """
    ***************************************************************************
    Funcao: carregar_usuarios

    @brief Carrega usuarios cadastrados para validacao pelo AS.

    Descricao:
    Le `data/usuarios.json` e retorna sua estrutura. O arquivo contem salt,
    verificador e perfil de cada usuario, mas nao contem senha em texto claro.

    Parametros:
    Nao recebe parametros explicitos.

    Valor retornado:
    @return Dicionario com a chave `usuarios`.

    Assertiva de entrada:
    @pre O caminho de usuarios pode existir ou nao.

    Assertiva de saida:
    @post Retorna usuarios cadastrados ou estrutura vazia se o arquivo nao existir.

    Excecoes:
    @throws json.JSONDecodeError Pode ocorrer se o JSON estiver invalido.
    @throws OSError Pode propagar erro de leitura do arquivo.

    Observacoes:
    Esta funcao apoia o AS e tambem a camada de notas para descobrir perfis.
    ***************************************************************************
    """
    if not CAMINHO_USUARIOS.exists():
        return {"usuarios": {}}

    with open(CAMINHO_USUARIOS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def obter_dados_usuario(nome_usuario: str) -> dict:
    """
    ***************************************************************************
    Funcao: obter_dados_usuario

    @brief Recupera os dados persistidos de um usuario.

    Descricao:
    Busca o usuario no arquivo carregado e retorna os campos necessarios ao AS,
    como salt e verificador. Se o usuario nao existir, a autenticacao inicial
    deve falhar.

    Parametros:
    @param nome_usuario Identificador textual do usuario.

    Valor retornado:
    @return Dicionario com os dados do usuario.

    Assertiva de entrada:
    @pre O nome do usuario deve ser uma string cadastrada.

    Assertiva de saida:
    @post Retorna os dados do usuario existente.

    Excecoes:
    @throws ValueError Quando o usuario nao esta cadastrado.
    @throws Exception Pode propagar erros de leitura do JSON.

    Observacoes:
    A funcao nao valida senha; ela apenas localiza os dados usados no desafio.
    ***************************************************************************
    """
    usuarios = carregar_usuarios().get("usuarios", {})
    if nome_usuario not in usuarios:
        raise ValueError("Usuario nao encontrado.")
    return usuarios[nome_usuario]


def criar_desafio_as(nome_usuario: str) -> dict:
    """
    ***************************************************************************
    Funcao: criar_desafio_as

    @brief Cria os parametros AS-REQ para o cliente responder.

    Descricao:
    Remove desafios expirados, gera um desafio aleatorio, associa esse desafio
    ao usuario e retorna salt, numero de iteracoes da KDF e desafio. O cliente
    usa esses dados para derivar a chave localmente e produzir a prova HMAC.

    Parametros:
    @param nome_usuario Usuario que iniciou a autenticacao.

    Valor retornado:
    @return Dicionario com usuario, salt, iteracoes_kdf e desafio.

    Assertiva de entrada:
    @pre O usuario deve existir em `data/usuarios.json`.

    Assertiva de saida:
    @post Um desafio de uso unico fica registrado em memoria por ate 60 segundos.

    Excecoes:
    @throws ValueError Quando o usuario nao esta cadastrado.
    @throws Exception Pode propagar erros de leitura ou aleatoriedade.

    Observacoes:
    Esta funcao representa a primeira metade da comunicacao com o AS no fluxo
    academico: o cliente ainda nao recebe TGT, apenas parametros para provar
    conhecimento da senha.
    ***************************************************************************
    """
    dados_usuario = obter_dados_usuario(nome_usuario)
    agora = timestamp_atual()

    with BLOQUEIO_DESAFIOS_AS:
        expirados = [
            desafio
            for desafio, dados in DESAFIOS_AS.items()
            if dados["timestamp"] < agora - TEMPO_VALIDADE_DESAFIO
        ]
        for desafio in expirados:
            DESAFIOS_AS.pop(desafio, None)

        desafio = secrets.token_hex(32)
        DESAFIOS_AS[desafio] = {
            "usuario": nome_usuario,
            "timestamp": agora,
        }
    return {
        "usuario": nome_usuario,
        "salt": dados_usuario["salt"],
        "iteracoes_kdf": ITERACOES_PBKDF2,
        "desafio": desafio,
    }


def _emitir_resposta_as(
        nome_usuario: str,
        chave_cliente: bytes,
        validade_segundos: int
) -> dict:
    """
    ***************************************************************************
    Funcao: _emitir_resposta_as

    @brief Monta a resposta cifrada do AS apos autenticacao bem-sucedida.

    Descricao:
    Gera a chave de sessao Cliente-TGS, cria o TGT, cifra o TGT com a chave
    secreta do TGS e cifra a resposta final com a chave de longo prazo do
    cliente.

    Parametros:
    @param nome_usuario Usuario autenticado.
    @param chave_cliente Chave de longo prazo reproduzida pelo cliente.
    @param validade_segundos Tempo de validade do TGT.

    Valor retornado:
    @return Pacote AES-GCM contendo chave Cliente-TGS e TGT.

    Assertiva de entrada:
    @pre A prova do usuario ja deve ter sido validada.
    @pre A chave do cliente deve ter tamanho aceito pelo AES-GCM.

    Assertiva de saida:
    @post Retorna AS-REP cifrado e um TGT transportavel pelo cliente.

    Excecoes:
    @throws ValueError Quando a validade do TGT for invalida.
    @throws Exception Pode propagar erros de cifragem ou aleatoriedade.

    Observacoes:
    O cliente transporta o TGT, mas nao consegue abri-lo porque ele e cifrado
    com a chave secreta do TGS.
    ***************************************************************************
    """
    chave_sessao_cliente_tgs = gerar_chave_simetrica()
    chave_sessao_cliente_tgs_base64 = bytes_para_base64(chave_sessao_cliente_tgs)

    tgt = gerar_tgt(
        nome_usuario=nome_usuario,
        chave_sessao_cliente_tgs_base64=chave_sessao_cliente_tgs_base64,
        validade_segundos=validade_segundos,
    )
    tgt_criptografado = criptografar_json(CHAVE_SECRETA_TGS, tgt)
    resposta_para_cliente = {
        "id_tgs": "tgs",
        "chave_sessao_cliente_tgs": chave_sessao_cliente_tgs_base64,
        "tgt": tgt_criptografado,
        "timestamp_emissao": tgt["timestamp_emissao"],
        "timestamp_expiracao": tgt["timestamp_expiracao"],
        "validade_segundos": tgt["validade_segundos"],
        "nonce_tgt": tgt["nonce"],
    }
    return criptografar_json(chave_cliente, resposta_para_cliente)


def autenticar_no_as_com_prova(
        nome_usuario: str,
        desafio: str,
        prova: str,
        validade_segundos: int = TEMPO_VALIDADE_TGT
) -> dict:
    """
    ***************************************************************************
    Funcao: autenticar_no_as_com_prova

    @brief Valida a prova HMAC e emite a resposta do AS.

    Descricao:
    Consome um desafio previamente criado, verifica se pertence ao usuario,
    confere expiracao e compara a prova HMAC recebida com a prova esperada. Se
    a validacao passar, emite a resposta do AS com TGT e chave Cliente-TGS.

    Parametros:
    @param nome_usuario Usuario que responde ao desafio.
    @param desafio Desafio emitido por criar_desafio_as.
    @param prova Prova HMAC-SHA256 codificada em Base64.
    @param validade_segundos Validade desejada para o TGT.

    Valor retornado:
    @return Pacote cifrado para o cliente com os dados da autenticacao.

    Assertiva de entrada:
    @pre O desafio deve existir, estar valido e pertencer ao usuario.
    @pre A prova deve ter sido calculada com a chave derivada da senha correta.

    Assertiva de saida:
    @post O desafio e removido da memoria e nao pode ser reutilizado.
    @post Em caso de sucesso, um TGT e emitido.

    Excecoes:
    @throws ValueError Para desafio invalido, expirado ou prova incorreta.
    @throws Exception Pode propagar erros de cifragem e leitura de usuarios.

    Observacoes:
    Esta funcao substitui o envio direto de senha ao AS. O AS valida posse da
    senha por desafio e HMAC.
    ***************************************************************************
    """
    with BLOQUEIO_DESAFIOS_AS:
        dados_desafio = DESAFIOS_AS.pop(desafio, None)
    if not dados_desafio or dados_desafio["usuario"] != nome_usuario:
        raise ValueError("Desafio de autenticacao invalido.")

    if dados_desafio["timestamp"] < timestamp_atual() - TEMPO_VALIDADE_DESAFIO:
        raise ValueError("Desafio de autenticacao expirado.")

    dados_usuario = obter_dados_usuario(nome_usuario)
    chave_autenticacao = base64_para_bytes(dados_usuario["verificador"])
    prova_esperada = gerar_prova_as(
        chave_autenticacao,
        nome_usuario,
        desafio,
    )
    if not hmac.compare_digest(prova_esperada, prova):
        raise ValueError("Senha invalida.")

    return _emitir_resposta_as(
        nome_usuario,
        chave_autenticacao,
        validade_segundos,
    )


def gerar_tgt(
        nome_usuario: str,
        chave_sessao_cliente_tgs_base64: str,
        validade_segundos: int = TEMPO_VALIDADE_TGT
) -> dict:
    """
    ***************************************************************************
    Funcao: gerar_tgt

    @brief Cria a estrutura do Ticket Granting Ticket.

    Descricao:
    Usa a funcao comum de tickets para montar o TGT e acrescenta campos usados
    pelo AS, como usuario, expiracao e nonce. O TGT sera cifrado pela resposta
    do AS antes de ser entregue ao cliente.

    Parametros:
    @param nome_usuario Usuario autenticado.
    @param chave_sessao_cliente_tgs_base64 Chave Cliente-TGS em Base64.
    @param validade_segundos Tempo de validade do ticket.

    Valor retornado:
    @return Dicionario com os campos do TGT em claro antes da cifragem.

    Assertiva de entrada:
    @pre A validade deve ser positiva.
    @pre A chave de sessao deve estar codificada em Base64.

    Assertiva de saida:
    @post Retorna TGT contendo identidade, chave de sessao, validade e nonce.

    Excecoes:
    @throws ValueError Quando a validade for menor ou igual a zero.

    Observacoes:
    A funcao apenas monta a estrutura; a protecao criptografica ocorre em
    _emitir_resposta_as.
    ***************************************************************************
    """
    if validade_segundos <= 0:
        raise ValueError("Validade do TGT invalida.")

    tgt = criar_tgt(
        id_cliente=nome_usuario,
        chave_sessao_cliente_tgs_base64=chave_sessao_cliente_tgs_base64,
        id_tgs="tgs"
    )

    # Campos extras documentam validade e nonce antes da cifragem do TGT.
    tgt["usuario"] = nome_usuario
    tgt["validade_segundos"] = validade_segundos
    tgt["timestamp_expiracao"] = tgt["timestamp_emissao"] + validade_segundos
    tgt["nonce"] = uuid.uuid4().hex

    return tgt
