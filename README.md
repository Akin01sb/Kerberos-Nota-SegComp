# Portal de Notas Escolares com Kerberos

Projeto acadêmico de Segurança Computacional que implementa uma versão
simplificada do protocolo Kerberos sem usar implementações prontas do
protocolo. O sistema utiliza somente sockets TCP e primitivas criptográficas
básicas fornecidas pela biblioteca `cryptography` e pela biblioteca padrão.

## Documentação do código

Para conhecer detalhadamente as funções, classes, módulos e demais componentes
que fazem parte da implementação do Kerberos, consulte a documentação
estruturada gerada a partir do código-fonte com o Doxygen.

Para acessá-la, abra o seguinte arquivo no navegador:

[**Abrir documentação do projeto**](docs/html/index.html)

Caminho no projeto:

```text
Kerberos-Nota-SegComp\docs\html\index.html
```

> A documentação deve ser aberta localmente após o download ou a clonagem do
> projeto. No Windows, também é possível acessar o arquivo diretamente pelo
> Explorador de Arquivos.

## Integrantes do grupo

| Integrante                    | Matrícula |
| ----------------------------- | --------: |
| Akin Sangiàcomo Bazila        | 221002002 |
| Kassio Gandara de Souza       | 180140540 |
| Thelma Evangelista dos Santos | 231003513 |
| Hagatta Amorim Reis           | 211055479 |

## Arquitetura

O sistema é dividido em quatro processos:

```text
Navegador -> Cliente Flask :5000
                    |
                    +-> AS    :9001
                    +-> TGS   :9002
                    +-> Notas :9003
```

- **AS:** entrega os parâmetros da KDF, valida uma prova HMAC e emite o TGT.
- **TGS:** valida TGT e autenticador e emite o Service Ticket.
- **Notas:** valida Service Ticket, autenticadores e operações protegidas.
- **Flask:** apresenta a interface e executa o papel de cliente Kerberos.

AS, TGS e Notas são processos separados e se comunicam por mensagens JSON com
tamanho prefixado sobre sockets TCP. A senha é processada somente no cliente:
ela não é enviada para nenhum dos três servidores.

## Fluxo Kerberos

1. O cliente solicita ao AS o salt e um desafio aleatório.
2. A senha é transformada localmente com PBKDF2-HMAC-SHA256.
3. O cliente responde ao desafio usando HMAC-SHA256.
4. O AS valida a prova e devolve a chave Cliente-TGS e o TGT em uma resposta
   protegida por AES-GCM.
5. O cliente envia TGT e autenticador ao TGS.
6. O TGS emite o Service Ticket e a chave Cliente-Serviço.
7. Cliente e Portal de Notas realizam autenticação mútua.
8. Cada operação de notas usa um autenticador novo e uma requisição AES-GCM.
9. O Portal valida usuário, ticket, timestamp, nonce, ação e hash da requisição.
10. O cliente valida a confirmação criptografada da operação.

## Perfis

**Professor**

- visualiza os alunos;
- lança uma ou várias notas por envio;
- usa uma lista de disciplinas ou informa uma disciplina personalizada;
- lista, edita e exclui notas.

**Aluno**

- visualiza somente as próprias notas;
- não pode criar, editar ou excluir registros.

Usuários e perfis ficam em `data/usuarios.json`. As senhas não são salvas.
As notas ficam em `data/notas.json`.

| Usuário | Perfil |
|---|---|
| `kassio` | professor |
| `AkinGOD777` | aluno |
| `kassio12` | aluno |
| `SilvioSants` | professor |
| `malululu10` | aluno |

Para criar outro usuário:

```powershell
python scripts/criar_usuario.py
```

## Instalação

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Esse comando instala as dependências da aplicação e dos testes: Flask,
Cryptography e Pytest.

## Executar

Abra dois terminais na raiz do projeto.

Terminal 1, servidores Kerberos:

```powershell
python scripts/iniciar_servidores.py
```

Terminal 2, cliente web:

```powershell
python run.py
```

Acesse `http://127.0.0.1:5000`.

As portas podem ser alteradas pelas variáveis `KERBEROS_PORTA_AS`,
`KERBEROS_PORTA_TGS` e `KERBEROS_PORTA_NOTAS`.

## Configuração de chaves

As chaves acadêmicas padrão permitem executar o projeto imediatamente. Para
substituí-las, defina valores Base64 que representem 32 bytes:

```powershell
python scripts/gerar_chaves.py
```

Use os comandos gerados no terminal dos servidores e no terminal do Flask antes
de iniciar a aplicação:

```powershell
$env:KERBEROS_CHAVE_TGS='<chave-base64>'
$env:KERBEROS_CHAVE_NOTAS='<chave-base64>'
$env:FLASK_SECRET_KEY='<segredo-aleatorio>'
```

As mesmas variáveis precisam estar disponíveis nos processos correspondentes.

## Testes

```powershell
python -m pytest -q
```

Resultado atual:

```text
48 passed
```

Além dos testes unitários, `tests/test_rede.py` inicia os três servidores em
portas TCP reais e verifica login, emissão de tickets, operação de notas,
integração Flask e ausência da senha nas mensagens enviadas ao AS.

## Estrutura

```text
src/kerberos_notas/
  client/       cliente web e fluxo Kerberos
  crypto/       PBKDF2, HMAC, AES-GCM e Base64
  kerberos/     regras do AS, TGS, tickets e autenticadores
  notes/        regras do Portal e CRUD
  rede/         protocolo TCP e cliente de rede
  servidores/   processos AS, TGS e Notas
scripts/
  iniciar_servidores.py
data/           usuários e notas em JSON
tests/          testes unitários e de integração TCP
docs/
  relatorio_tecnico.md
  roteiro_video_apresentacao.md
```

## Limitações acadêmicas

- TCP protege a separação dos serviços, mas não substitui TLS fora do ambiente
  local. Os dados Kerberos sensíveis já são protegidos por AES-GCM.
- As chaves padrão são didáticas e devem ser substituídas por variáveis de
  ambiente em uma implantação real.
- As sessões do Flask e os caches contra replay ficam em memória.
- O armazenamento em JSON usa bloqueio e gravação atômica, mas um banco de
  dados seria mais apropriado para múltiplas máquinas.
- O tráfego entre o navegador e o Flask exigiria HTTPS em produção.
