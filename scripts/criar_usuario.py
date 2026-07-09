import json
from getpass import getpass
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from kerberos_notas.crypto.kdf import(
    gerar_salt,
    derivar_chave_senha,
    gerar_verificador_chave
)

CAMINHO_USUARIOS = Path(__file__).resolve().parents[1] / "data" / "usuarios.json"


def carregar_usuarios() -> dict:
    if not CAMINHO_USUARIOS.exists():
        return {"usuarios": {}}
    
    with open(CAMINHO_USUARIOS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)
    

def salvar_usuarios(dados: dict) -> None:
    with open(CAMINHO_USUARIOS, "w", encoding="utf-8") as arquivo:
        json.dump(dados,arquivo, indent=4, ensure_ascii=False)


def criar_usuario(nome_usuario: str, senha: str, perfil: str = "aluno") -> None:
    dados= carregar_usuarios()

    if nome_usuario in dados["usuarios"]:
        print("Usuario já existe.")
        return

    if perfil not in {"professor", "aluno"}:
        raise ValueError("Perfil deve ser professor ou aluno.")
    
    salt = gerar_salt()
    chave = derivar_chave_senha(senha, salt)
    verificador = gerar_verificador_chave(chave)

    dados["usuarios"][nome_usuario] = {
        "salt": salt,
        "verificador": verificador,
        "perfil": perfil,
    }

    salvar_usuarios(dados)

    print(f"Usuario '{nome_usuario}' criado com sucesso.")


def main():
    print("=== Cadastro de usuário Kerberos ===")

    nome_usuario = input("Usuario: ").strip()
    perfil = input("Perfil [aluno/professor]: ").strip().lower() or "aluno"
    senha = getpass("Senha: ").strip()

    if not nome_usuario or not senha:
        print("Usuario e senha são obrigatorios")
        return
    
    criar_usuario(nome_usuario, senha, perfil)




if __name__ == "__main__":
    main()
