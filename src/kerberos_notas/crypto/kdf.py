"""
@file kdf.py
@brief Funcoes de derivacao de chave e prova criptografica baseada em senha.

@details
Este modulo implementa a KDF usada no cadastro e na autenticacao do Portal de
Notas. A senha informada pelo usuario e combinada com um salt e processada por
PBKDF2-HMAC-SHA256 para produzir uma chave de 32 bytes. O modulo tambem gera o
verificador armazenado no arquivo de usuarios e a prova HMAC usada pelo cliente
para responder ao desafio do AS sem enviar a senha pela rede.

Componentes principais:
- gerar_salt
- derivar_chave_senha
- gerar_verificador_chave
- obter_chave_autenticacao_as
- gerar_prova_as
- verificar_senha

Papel na arquitetura:
Camada de criptografia compartilhada pelo cliente, scripts de cadastro e AS.
"""

import os
import base64
import hashlib
import hmac

TAMANHO_SALT = 16
TAMANHO_CHAVE = 32
ITERACOES_PBKDF2 = 200_000


def gerar_salt() -> str:
    """
    ***************************************************************************
    Funcao: gerar_salt

    @brief Gera um salt aleatorio para a derivacao da chave do usuario.

    Descricao:
    Cria 16 bytes aleatorios usando o gerador criptografico do sistema
    operacional e codifica o resultado em Base64 para armazenamento em JSON.
    O salt impede que senhas iguais gerem a mesma chave derivada.

    Parametros:
    Nao recebe parametros explicitos.

    Valor retornado:
    @return String Base64 contendo o salt aleatorio.

    Assertiva de entrada:
    @pre O sistema operacional deve disponibilizar fonte segura de aleatoriedade.

    Assertiva de saida:
    @post Retorna um salt Base64 adequado para PBKDF2.

    Excecoes:
    @throws Exception Pode propagar erros de aleatoriedade ou codificacao Base64.

    Observacoes:
    O salt e armazenado junto ao usuario, mas nao e secreto.
    ***************************************************************************
    """
    salt = os.urandom(TAMANHO_SALT)
    return base64.b64encode(salt).decode("utf-8")


def derivar_chave_senha(senha: str, salt_base64: str) -> bytes:
    """
    ***************************************************************************
    Funcao: derivar_chave_senha

    @brief Deriva a chave simetrica do cliente a partir da senha.

    Descricao:
    Aplica PBKDF2-HMAC-SHA256 sobre a senha informada pelo usuario e o salt
    armazenado no cadastro. O resultado tem 32 bytes e e usado como base para o
    segredo de longo prazo empregado no fluxo de autenticacao com o AS.

    Parametros:
    @param senha Senha digitada pelo usuario.
    @param salt_base64 Salt do usuario codificado em Base64.

    Valor retornado:
    @return Chave derivada em bytes.

    Assertiva de entrada:
    @pre A senha deve ser uma string.
    @pre O salt deve estar em Base64 valido.

    Assertiva de saida:
    @post Retorna uma chave de 32 bytes derivada por PBKDF2-HMAC-SHA256.

    Excecoes:
    @throws ValueError Pode ocorrer se o salt Base64 for invalido.
    @throws Exception Pode propagar erros da biblioteca hashlib.

    Observacoes:
    Esta funcao representa a etapa de KDF exigida pelo trabalho. A senha nao e
    enviada ao AS no fluxo TCP; ela e processada localmente pelo cliente.
    ***************************************************************************
    """
    salt = base64.b64decode(salt_base64)

    chave = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        ITERACOES_PBKDF2,
        dklen=TAMANHO_CHAVE,
    )

    return chave


def gerar_verificador_chave(chave: bytes) -> str:
    """
    ***************************************************************************
    Funcao: gerar_verificador_chave

    @brief Gera o verificador persistido para uma chave derivada.

    Descricao:
    Calcula SHA-256 da chave derivada e codifica o resultado em Base64. Esse
    valor e salvo em `data/usuarios.json` para representar o segredo de longo
    prazo associado ao usuario sem armazenar a senha em texto claro.

    Parametros:
    @param chave Chave derivada pela KDF.

    Valor retornado:
    @return Verificador Base64 associado a chave derivada.

    Assertiva de entrada:
    @pre A chave deve ser bytes obtidos por derivacao PBKDF2.

    Assertiva de saida:
    @post Retorna um verificador que pode ser comparado ou usado no desafio AS.

    Excecoes:
    @throws Exception Pode propagar erros de hashing ou codificacao.

    Observacoes:
    O verificador nao e senha em texto claro, mas e sensivel e deve ser tratado
    como segredo do ambiente academico.
    ***************************************************************************
    """
    hash_chave = hashlib.sha256(chave).digest()
    return base64.b64encode(hash_chave).decode("utf-8")


def obter_chave_autenticacao_as(chave_derivada: bytes) -> bytes:
    """
    ***************************************************************************
    Funcao: obter_chave_autenticacao_as

    @brief Converte a chave derivada no segredo usado na prova com o AS.

    Descricao:
    Calcula SHA-256 da chave derivada. O resultado em bytes corresponde ao valor
    que o AS consegue recuperar a partir do verificador salvo, permitindo que o
    cliente gere uma prova HMAC do desafio sem transmitir a senha.

    Parametros:
    @param chave_derivada Chave retornada por derivar_chave_senha.

    Valor retornado:
    @return Chave de autenticacao do AS em bytes.

    Assertiva de entrada:
    @pre A chave derivada deve ser bytes.

    Assertiva de saida:
    @post Retorna bytes usados como chave de HMAC no desafio do AS.

    Excecoes:
    @throws Exception Pode propagar erros de hashing.

    Observacoes:
    Esta transformacao separa a chave bruta derivada da senha do valor usado
    diretamente na etapa AS-REQ/AS-REP do protocolo academico.
    ***************************************************************************
    """
    return hashlib.sha256(chave_derivada).digest()


def gerar_prova_as(
        chave_autenticacao: bytes,
        usuario: str,
        desafio: str
) -> str:
    """
    ***************************************************************************
    Funcao: gerar_prova_as

    @brief Gera a prova HMAC-SHA256 enviada ao AS.

    Descricao:
    Monta a mensagem `usuario:desafio` e calcula HMAC-SHA256 usando a chave de
    autenticacao derivada da senha. O resultado e codificado em Base64 e enviado
    ao AS para provar que o cliente conhece a senha sem transmiti-la.

    Parametros:
    @param chave_autenticacao Chave em bytes usada no HMAC.
    @param usuario Nome do usuario autenticado.
    @param desafio Desafio aleatorio criado pelo AS.

    Valor retornado:
    @return Prova HMAC codificada em Base64.

    Assertiva de entrada:
    @pre A chave deve ser bytes validos para HMAC.
    @pre Usuario e desafio devem ser strings nao vazias.

    Assertiva de saida:
    @post Retorna uma prova verificavel pelo AS para o desafio informado.

    Excecoes:
    @throws Exception Pode propagar erros de HMAC ou codificacao.

    Observacoes:
    Esta funcao representa a resposta criptografica do cliente ao desafio do AS.
    ***************************************************************************
    """
    mensagem = f"{usuario}:{desafio}".encode("utf-8")
    prova = hmac.new(
        chave_autenticacao,
        mensagem,
        hashlib.sha256,
    ).digest()
    return base64.b64encode(prova).decode("utf-8")


def verificar_senha(senha: str, salt_base64: str, verificador_salvo: str) -> bool:
    """
    ***************************************************************************
    Funcao: verificar_senha

    @brief Verifica se uma senha reproduz o verificador armazenado.

    Descricao:
    Deriva novamente a chave a partir da senha e do salt e compara o verificador
    calculado com o verificador salvo. A funcao e util para testes e scripts de
    apoio, embora o fluxo TCP de autenticacao use desafio e prova HMAC.

    Parametros:
    @param senha Senha a ser verificada.
    @param salt_base64 Salt do usuario em Base64.
    @param verificador_salvo Verificador Base64 persistido.

    Valor retornado:
    @return True se a senha reproduz o verificador; False caso contrario.

    Assertiva de entrada:
    @pre Salt e verificador devem estar em Base64 valido.

    Assertiva de saida:
    @post Nao altera estado; apenas retorna o resultado da verificacao.

    Excecoes:
    @throws Exception Pode propagar erros da KDF ou de Base64.

    Observacoes:
    Nao deve ser confundida com a troca de mensagens AS-REQ/AS-REP usada pelo
    cliente TCP.
    ***************************************************************************
    """
    chave = derivar_chave_senha(senha, salt_base64)
    verificador_calculado = gerar_verificador_chave(chave)

    return verificador_calculado == verificador_salvo
