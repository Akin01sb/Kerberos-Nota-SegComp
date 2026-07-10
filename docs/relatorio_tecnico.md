# Relatório técnico - Portal de Notas com Kerberos

Este documento descreve a versão final do projeto acadêmico de Segurança
Computacional. O foco é evidenciar a implementação manual do fluxo Kerberos,
sem bibliotecas prontas do protocolo, usando somente primitivas criptográficas
básicas.

## 1. Introdução

O projeto implementa uma versão acadêmica e simplificada do protocolo Kerberos
usando criptografia de chave simétrica. O serviço protegido escolhido é um
Portal de Notas Escolares. Professores podem administrar notas e alunos podem
consultar somente seus próprios resultados.

## 2. Arquitetura

```text
Cliente Web -> Authentication Server -> Ticket Granting Server -> Portal de Notas
```

Os componentes executam como processos separados e se comunicam por TCP:

- `crypto`: KDF e AES-GCM;
- `kerberos`: AS, TGS, tickets e autenticadores;
- `client`: interface Flask e cliente Kerberos;
- `notes`: Portal, autorização e persistência;
- `rede`: enquadramento JSON e cliente TCP;
- `servidores`: processos AS, TGS e Notas;
- `data`: arquivos JSON;
- `tests`: validações automatizadas.

## 3. Authentication Server

O AS está em `src/kerberos_notas/kerberos/as_server.py` e escuta na porta 9001.
Primeiro ele envia salt, parâmetros da KDF e um desafio aleatório. O cliente
deriva a chave da senha localmente e responde com uma prova HMAC-SHA256. Assim,
a senha não é salva, registrada em logs ou transmitida pela rede.

Após validar as credenciais, o AS:

1. gera uma chave de sessão Cliente-TGS;
2. cria o TGT com usuário, chave, validade e nonce;
3. cifra o TGT com a chave secreta do TGS;
4. cifra a resposta com a chave de longo prazo reproduzida pelo cliente.

O cliente transporta o TGT, mas não consegue ler ou alterá-lo.

## 4. Ticket Granting Server

O TGS está em `src/kerberos_notas/kerberos/tgs_server.py`. Ele recebe o TGT e um
autenticador Cliente-TGS. O TGS abre o TGT com sua chave, verifica identidade e
validade e abre o autenticador com a chave Cliente-TGS. Um cache de nonces em
memória rejeita a reutilização do mesmo autenticador no TGS.

Quando as validações passam, ele gera uma chave Cliente-Serviço e um Service
Ticket para `notas`. O ticket é cifrado com a chave secreta do Portal. A chave
Cliente-Serviço é entregue ao cliente em uma resposta cifrada com a chave
Cliente-TGS.

## 5. KDF e senha

`src/kerberos_notas/crypto/kdf.py` utiliza PBKDF2-HMAC-SHA256 com:

- salt aleatório de 16 bytes;
- 200.000 iterações;
- chave derivada de 32 bytes.

No cadastro são salvos o salt, um verificador SHA-256 da chave derivada e o
perfil. No login, o cliente repete a derivação, cria a prova HMAC do desafio e
usa o verificador como chave de longo prazo para abrir a resposta do AS.

## 6. Tickets e autenticadores

O TGT permite solicitar tickets sem reenviar a senha. O Service Ticket permite
acessar somente o serviço indicado. Ambos possuem validade limitada.

O autenticador contém usuário, timestamp e nonce. O autenticador Cliente-TGS é
cifrado com a chave Cliente-TGS. O autenticador Cliente-Serviço é cifrado com a
chave Cliente-Serviço. Assim, carregar um ticket sem conhecer sua chave de
sessão não é suficiente.

## 7. Portal de Notas e autenticação mútua

A implementação está em `src/kerberos_notas/notes/portal_notas.py`.

1. O Portal abre o Service Ticket com sua chave secreta.
2. Verifica o serviço, a validade e o usuário.
3. Obtém do ticket a chave Cliente-Serviço.
4. Abre e valida o autenticador Cliente-Serviço.
5. Devolve uma confirmação cifrada contendo timestamp incrementado e nonce.
6. O cliente abre a confirmação e compara os dois valores.
7. Somente depois disso a sessão do Portal é criada.

Para cada operação posterior, o cliente cria uma requisição cifrada com ação,
dados e nonce. Um novo autenticador inclui a ação e o hash da requisição. A
função `processar_operacao_portal` valida novamente o Service Ticket, rejeita
nonces reutilizados, confere ação e hash e somente então executa o CRUD. A
resposta de cada operação também é cifrada e validada pelo cliente.

O cookie Flask guarda apenas um identificador aleatório. Ticket e chave de
sessão permanecem em memória no lado servidor.

## 8. Autorização e dados escolares

`src/kerberos_notas/notes/service.py` aplica as regras:

- professor lista todas as notas e pode criar, editar e excluir;
- aluno lista somente os registros associados ao próprio usuário;
- ações de alteração feitas por alunos geram acesso negado.

Cada nota possui aluno, disciplina, valor de 0 a 10, observação, professor e
datas de criação e atualização. A persistência continua em JSON para manter a
implementação adequada ao escopo acadêmico.

## 9. Algoritmos

- **PBKDF2-HMAC-SHA256:** transforma senha em chave e dificulta tentativas em
  massa pelo uso de salt e muitas iterações.
- **AES-256-GCM:** protege respostas, tickets, autenticadores e confirmações,
  oferecendo confidencialidade e detecção de adulteração.

Não foi utilizada biblioteca pronta de Kerberos.

## 10. Testes

```powershell
python -m pytest -q
```

Resultado atual: `48 passed`.

A suíte verifica criptografia, KDF, AS, TGS, adulteração, tickets expirados,
autenticadores inválidos, replay no TGS e no Portal, autenticação mútua por
operação, CRUD, isolamento entre alunos, fluxo web e comunicação TCP real.

## 11. Limitações

As chaves didáticas possuem valores padrão, os dados ficam em JSON e sessões e
nonces utilizados são mantidos somente em memória. As chaves podem ser
substituídas por variáveis de ambiente, e o script `scripts/gerar_chaves.py`
gera valores Base64 adequados para essa configuração. Em uma implantação real
seriam usados um banco de dados, HTTPS entre navegador e Flask e TLS entre
máquinas.

Também existe um modo local usado pelos testes automatizados para chamar as
funções do AS, TGS e Portal no mesmo processo. Esse modo não envia senha ao AS:
ele usa o mesmo mecanismo de desafio e prova HMAC do fluxo TCP. A execução real
do projeto via `run.py` usa `create_app(usar_rede=True)` e passa pelos sockets
AS, TGS e Portal.

## 12. Dificuldades e aprendizados

As principais dificuldades foram separar o fluxo Kerberos em etapas claras,
evitar que a senha atravessasse a rede, proteger tickets e autenticadores contra
adulteração e replay, e manter o serviço de notas simples sem enfraquecer a
autenticação.

Os principais aprendizados foram:

- a senha não deve ser usada diretamente como segredo trafegado;
- tickets precisam ser protegidos com chaves conhecidas apenas pelos servidores
  corretos;
- autenticadores precisam de timestamp e nonce para evitar reutilização;
- autenticação mútua exige que o serviço também prove conhecer a chave de
  sessão;
- separar AS, TGS e serviço por sockets torna o fluxo mais fiel ao Kerberos
  apresentado em aula.

## 13. Conclusão

O projeto demonstra o caminho completo Cliente -> AS -> TGS -> Portal de Notas.
A senha é usada somente na autenticação inicial; depois, tickets, autenticadores
e chaves temporárias protegem o acesso. A autenticação mútua confirma cliente e
Portal, enquanto os perfis restringem corretamente as operações escolares.
