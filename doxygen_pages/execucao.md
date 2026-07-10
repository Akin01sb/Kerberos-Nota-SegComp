# Como executar o código {#como_executar}

## Pre-requisitos

- Python 3.10 ou superior.
- Pip.
- Doxygen instalado para gerar a documentacao HTML.

## Criar a venv

```bash
python -m venv .venv
```

## Ativar a venv no Linux/WSL

```bash
source .venv/bin/activate
```

## Ativar a venv no Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

## Instalar dependencias

```bash
python -m pip install -e .
```

## Executar servidores

Em um terminal na raiz do projeto:

```bash
python scripts/iniciar_servidores.py
```

Esse comando inicia AS, TGS e Portal de Notas em processos separados.

## Executar aplicacao Flask

Em outro terminal na raiz do projeto:

```bash
python run.py
```

## Endereco no navegador

```text
http://127.0.0.1:5000
```

## Usuarios cadastrados

O arquivo `data/usuarios.json` contem usuarios cadastrados com `salt`,
`verificador` e `perfil`. As senhas nao ficam disponiveis em texto claro.
Use credenciais conhecidas pelo grupo ou crie um novo usuario com:

```bash
python scripts/criar_usuario.py
```

Perfis existentes no arquivo de usuarios:

- `kassio`: professor
- `AkinGOD777`: aluno
- `kassio12`: aluno
- `SilvioSants`: professor
- `malululu10`: aluno

## Gerar chaves de ambiente

Para substituir as chaves didaticas padrao:

```bash
python scripts/gerar_chaves.py
```

Use as variaveis geradas no terminal dos servidores e no terminal do Flask antes
de iniciar a aplicacao.

## Executar testes com Pytest

```bash
python -m pytest -q
```

## Gerar documentacao Doxygen

```bash
doxygen Doxyfile
```

A documentacao HTML deve ser criada em:

```text
docs/html/index.html
```
