# Roteiro reformulado para apresentacao em 4 pessoas

Tempo sugerido: 16 a 22 minutos.

Objetivo desta versao: deixar a apresentacao mais forte tecnicamente, com foco
claro no Kerberos. A divisao abaixo coloca duas pessoas explicando a parte mais
importante para a nota, que e o protocolo, e duas pessoas explicando a aplicacao,
a demonstracao, os testes, a documentacao e as limitacoes.

Resumo da estrategia:

- Apresentador 1: parte tecnica forte - arquitetura, criptografia, senha, KDF,
  AS e TGT.
- Apresentador 2: parte tecnica forte - TGS, Service Ticket, autenticadores,
  autenticacao mutua, replay e operacoes protegidas.
- Apresentador 3: parte mais simples - Portal de Notas, perfis, interface,
  fluxo professor/aluno e logs visiveis.
- Apresentador 4: parte mais simples - execucao, testes, Doxygen, limitacoes e
  conclusao.

O foco principal do video deve ser: o Kerberos nao esta apenas no login. Ele
protege o caminho completo ate o servico de notas e tambem as operacoes feitas
depois do login.

---

## Preparacao antes de gravar

Abra a raiz do projeto:

```powershell
cd <pasta-do-projeto>
```

Instale o projeto, se ainda nao estiver instalado:

```powershell
python -m pip install -e .
```

Inicie os servidores Kerberos em um terminal:

```powershell
python scripts/iniciar_servidores.py
```

Inicie o cliente Flask em outro terminal:

```powershell
python run.py
```

Acesse:

```text
http://127.0.0.1:5000
```

Contas cadastradas no projeto:

- `SilvioSants`: professor;
- `AkinGOD777`: aluno;
- `kassio`: professor;
- `kassio12`: aluno;
- `malululu10`: aluno.

Importante: nao mostrar senhas na gravacao. O arquivo `data/usuarios.json` deve
ser usado apenas para mostrar que existem `salt`, `verificador` e `perfil`, e
que nao existe senha em texto claro.

---

## Divisao geral

| Parte | Apresentador | Foco | Nivel | Tempo |
|---|---|---|---|---|
| 1 | Apresentador 1 | Arquitetura Kerberos, KDF, AS e TGT | Tecnico forte | 5 a 6 min |
| 2 | Apresentador 2 | TGS, Service Ticket, autenticadores, replay e autenticacao mutua | Tecnico forte | 5 a 6 min |
| 3 | Apresentador 3 | Portal de Notas, perfis, interface e demonstracao funcional | Mais simples | 4 a 5 min |
| 4 | Apresentador 4 | Execucao, testes, Doxygen, limitacoes e conclusao | Mais simples | 3 a 5 min |

---

## Mensagem central para todos repetirem

> Nosso projeto implementa uma simulacao academica do Kerberos para proteger
> um Portal de Notas. O usuario usa senha apenas no inicio, a senha nao atravessa
> a rede, o AS emite o TGT, o TGS emite o Service Ticket, o Portal valida o
> ticket e o autenticador, e cada operacao de notas continua protegida por
> requisicao cifrada, nonce, timestamp e autenticador.

---

# Apresentador 1 - Kerberos, criptografia, senha, KDF, AS e TGT

## Objetivo da parte

Essa pessoa precisa deixar claro que o projeto atende aos requisitos mais
importantes do trabalho:

- Kerberos implementado manualmente;
- uso de criptografia simetrica;
- senha processada com KDF;
- AS implementado;
- TGT emitido corretamente;
- senha nao enviada pela rede.

## O que mostrar na tela

Mostrar nesta ordem:

1. `README.md`, secao de arquitetura.
2. `run.py`, destacando `create_app(usar_rede=True)`.
3. `scripts/iniciar_servidores.py`, destacando os tres processos.
4. `src/kerberos_notas/rede/cliente_tcp.py`.
5. `src/kerberos_notas/crypto/kdf.py`.
6. `src/kerberos_notas/crypto/crypto_utils.py`.
7. `src/kerberos_notas/kerberos/as_server.py`.
8. `src/kerberos_notas/kerberos/tickets.py`.

## Fala pronta

> Nesta primeira parte, vamos explicar a base tecnica do projeto. O sistema e
> um Portal de Notas protegido por uma simulacao academica do protocolo
> Kerberos. A ideia principal e que o usuario nao acessa o servico diretamente
> apenas com usuario e senha. Ele passa por um fluxo de autenticacao em etapas:
> primeiro o Cliente conversa com o AS, depois com o TGS, e por fim com o
> Servico de Notas.

> O projeto foi implementado sem biblioteca pronta de Kerberos. Isso e
> importante para o requisito do trabalho. O que usamos sao primitivas
> criptograficas basicas: PBKDF2-HMAC-SHA256 para derivar chave a partir da
> senha, HMAC-SHA256 para provar conhecimento da senha, AES-GCM para cifrar e
> autenticar mensagens, alem de timestamps, nonces e geracao segura de bytes
> aleatorios.

> A arquitetura roda em quatro partes principais. O Flask roda como Cliente Web
> na porta 5000. O AS roda na porta 9001. O TGS roda na porta 9002. O Portal de
> Notas roda na porta 9003. O arquivo `scripts/iniciar_servidores.py` inicia AS,
> TGS e Portal como processos separados. O `run.py` inicia o Flask com
> `usar_rede=True`, entao a aplicacao web usa sockets TCP reais para falar com
> AS, TGS e Portal.

> A comunicacao TCP esta encapsulada em `ClienteKerberosTCP`. Ele possui metodos
> para pedir parametros ao AS, enviar a prova ao AS, solicitar o ticket de
> servico ao TGS, autenticar no Portal e executar operacoes protegidas. Isso
> mostra que a separacao entre os componentes nao e apenas organizacao de
> codigo; existe comunicacao por rede local entre processos.

## Fala sobre senha e KDF

> Agora vem um ponto essencial: a senha. O usuario informa a senha na tela de
> login, mas a senha nao deve ser enviada ao AS, ao TGS ou ao Portal. No nosso
> projeto, a senha e usada localmente pelo Cliente Web para derivar uma chave.

> No arquivo `crypto/kdf.py`, a funcao `derivar_chave_senha` usa
> PBKDF2-HMAC-SHA256. Os parametros principais sao salt de 16 bytes, chave de
> 32 bytes e 200.000 iteracoes. O salt fica salvo em `data/usuarios.json`, junto
> com o verificador e o perfil do usuario. O arquivo nao armazena senha em texto
> claro.

> Quando o login comeca, o Cliente pede ao AS os parametros de autenticacao. O
> AS devolve o salt, a quantidade de iteracoes da KDF e um desafio aleatorio.
> Com isso, o Cliente deriva a chave da senha e gera uma prova HMAC do desafio.
> Essa prova e enviada ao AS. Assim, o Cliente prova que conhece a senha sem
> transmitir a senha.

## Fala sobre AS e TGT

> O Authentication Server esta implementado em `kerberos/as_server.py` e exposto
> por TCP em `servidores/servidor_as.py`. Ele possui duas etapas principais.
> Primeiro, `criar_desafio_as` cria o desafio e devolve os parametros da KDF.
> Depois, `autenticar_no_as_com_prova` valida a prova HMAC enviada pelo Cliente.

> O desafio tambem tem protecao propria: ele fica guardado em memoria por pouco
> tempo e e consumido quando usado. Se alguem tentar reutilizar o mesmo desafio,
> a autenticacao falha.

> Se a prova HMAC estiver correta, o AS gera uma chave de sessao Cliente-TGS e
> emite o TGT, que significa Ticket Granting Ticket. Esse TGT contem a identidade
> do cliente, a chave Cliente-TGS, timestamps de validade e um nonce. Mas o
> cliente nao consegue abrir o TGT, porque ele e cifrado com a chave secreta do
> TGS.

> Essa parte e fundamental no Kerberos: o cliente transporta o ticket, mas nao
> consegue ler nem alterar seu conteudo. Quem consegue abrir o TGT e o TGS.

## Pontos que o professor precisa perceber

- A senha nao trafega pela rede.
- Existe KDF real: PBKDF2-HMAC-SHA256.
- Existe desafio criptografico.
- Existe AS real no projeto.
- Existe TGT cifrado com chave do TGS.
- A implementacao usa criptografia simetrica e primitivas basicas.

## Frase de transicao

> Com o TGT emitido pelo AS, o Cliente ainda nao acessa o Portal de Notas. Ele
> primeiro precisa pedir ao TGS um ticket especifico para o servico de notas.

---

# Apresentador 2 - TGS, Service Ticket, autenticadores, replay e autenticacao mutua

## Objetivo da parte

Essa pessoa deve explicar a parte mais forte do Kerberos depois do AS:

- TGS;
- Service Ticket;
- chave Cliente-Servico;
- autenticadores;
- timestamp;
- nonce;
- replay;
- autenticacao mutua;
- protecao das operacoes do Portal.

## O que mostrar na tela

Mostrar nesta ordem:

1. `src/kerberos_notas/kerberos/tgs_server.py`.
2. `src/kerberos_notas/kerberos/authenticator.py`.
3. `src/kerberos_notas/kerberos/tickets.py`.
4. `src/kerberos_notas/notes/portal_notas.py`.
5. `src/kerberos_notas/client/routes.py`, funcao `executar_operacao_kerberos`.
6. `src/kerberos_notas/servidores/servidor_tgs.py`.
7. `src/kerberos_notas/servidores/servidor_notas.py`.

## Fala pronta

> Depois que o Cliente recebe o TGT, ele passa para a segunda fase do Kerberos:
> solicitar ao TGS um ticket para um servico especifico. No nosso projeto, o
> servico protegido se chama `notas`.

> O TGS esta implementado em `kerberos/tgs_server.py` e roda por TCP em
> `servidores/servidor_tgs.py`. O Cliente envia ao TGS tres informacoes: o nome
> do usuario, o TGT recebido do AS e um autenticador Cliente-TGS.

## Fala sobre autenticador Cliente-TGS

> O autenticador esta em `kerberos/authenticator.py`. Ele e uma mensagem cifrada
> com uma chave de sessao. No caso do TGS, o autenticador e cifrado com a chave
> Cliente-TGS. Dentro dele ficam usuario, timestamp e nonce.

> Isso e importante porque possuir apenas um ticket capturado nao deve ser
> suficiente. O cliente tambem precisa provar que conhece a chave de sessao.
> Para isso, ele cria um autenticador recente, com timestamp e nonce.

> No TGS, a funcao `validar_tgt` abre o TGT usando a chave secreta do TGS. Depois
> confere se o ticket pertence ao usuario correto, se contem a chave Cliente-TGS
> e se ainda esta dentro da validade. Em seguida, `validar_autenticador` abre o
> autenticador com a chave Cliente-TGS e confere usuario, timestamp e nonce.

## Fala sobre replay no TGS

> O projeto tambem implementa protecao contra replay no TGS. O arquivo
> `tgs_server.py` possui um cache chamado `NONCES_TGS_UTILIZADOS`. Quando um
> autenticador e aceito, o par usuario e nonce fica registrado temporariamente.
> Se o mesmo nonce aparecer de novo, o TGS rejeita a requisicao como possivel
> replay.

## Fala sobre Service Ticket

> Se o TGT e o autenticador estiverem validos, o TGS gera uma nova chave de
> sessao: a chave Cliente-Servico. Depois cria o Service Ticket para o servico
> `notas`. Esse ticket e cifrado com a chave secreta do Portal de Notas.

> Entao a ideia e parecida com o TGT: o cliente carrega o Service Ticket, mas
> nao precisa abrir o conteudo dele. Quem abre esse ticket e o Portal de Notas,
> porque somente o Portal conhece a chave secreta do servico.

> O TGS tambem envia ao Cliente a chave Cliente-Servico, mas essa resposta e
> cifrada com a chave Cliente-TGS. Assim, so o Cliente autenticado consegue ler
> a chave que sera usada com o Portal.

## Fala sobre Portal e autenticacao mutua

> Agora chegamos no servico protegido. O Portal de Notas esta em
> `notes/portal_notas.py` e roda por TCP em `servidores/servidor_notas.py`.
> Antes de executar qualquer operacao, o Portal recebe o Service Ticket e um
> autenticador Cliente-Servico.

> O Portal abre o Service Ticket com sua chave secreta, extrai a chave
> Cliente-Servico e usa essa chave para abrir o autenticador. Depois valida
> usuario, timestamp e nonce.

> Para autenticar o servico para o cliente, o Portal devolve uma confirmacao
> cifrada com a chave Cliente-Servico. Essa confirmacao contem o timestamp do
> autenticador incrementado em 1 e o mesmo nonce recebido. O Cliente valida essa
> resposta em `validar_confirmacao_portal`.

> Isso e a autenticacao mutua: o Portal valida o Cliente, e o Cliente tambem
> valida que esta falando com o Portal correto, porque somente o Portal teria
> conseguido abrir o Service Ticket e responder com a chave Cliente-Servico.

## Fala sobre operacoes protegidas

> Um ponto que merece destaque e que o Kerberos nao protege apenas o login. No
> nosso projeto, cada operacao do Portal passa por `executar_operacao_kerberos`.
> Isso inclui carregar painel, criar nota, criar varias notas, editar nota e
> excluir nota.

> Para cada operacao, o Cliente cria uma requisicao com usuario, acao, dados e
> nonce. Depois calcula um hash SHA-256 dessa requisicao. A requisicao e cifrada
> com AES-GCM usando a chave Cliente-Servico, e o autenticador tambem leva a
> acao e o hash da requisicao.

> No Portal, `processar_operacao_portal` valida novamente o Service Ticket, abre
> e valida o autenticador, confere se o usuario da requisicao e o mesmo do
> ticket, compara o nonce, compara a acao e recalcula o hash da requisicao.
> Somente depois disso a regra de negocio do sistema de notas e executada.

> A resposta da operacao tambem volta cifrada e e validada pelo Cliente. Isso
> deixa o fluxo mais completo, porque o servico continua protegido mesmo depois
> da autenticacao inicial.

## Pontos que o professor precisa perceber

- O TGS valida TGT e autenticador.
- O Service Ticket e especifico para o servico `notas`.
- Existem chaves de sessao diferentes: Cliente-TGS e Cliente-Servico.
- Autenticadores usam timestamp e nonce.
- O projeto rejeita replay no TGS e no Portal.
- Existe autenticacao mutua real entre Cliente e Portal.
- As operacoes de notas tambem sao protegidas pelo Kerberos.

## Frase de transicao

> Depois de mostrar a parte criptografica e o fluxo Kerberos, agora vamos ver
> como isso aparece para o usuario no Portal de Notas.

---

# Apresentador 3 - Portal de Notas, perfis, interface e demonstracao funcional

## Objetivo da parte

Essa parte deve ser mais simples e visual. O objetivo e mostrar que o servico
protegido existe e que as regras de professor e aluno funcionam.

## O que mostrar na tela

Mostrar nesta ordem:

1. Navegador em `http://127.0.0.1:5000`.
2. Login como professor.
3. Tela do professor.
4. Lancamento de nota.
5. Edicao de nota.
6. Logs didaticos na interface.
7. Logout.
8. Login como aluno.
9. Tela do aluno sem botoes de alteracao.
10. `src/kerberos_notas/notes/service.py`.
11. `src/kerberos_notas/notes/repository.py`.
12. `templates/notas.html`.

## Fala pronta

> Agora vamos mostrar o servico protegido que foi escolhido para o trabalho: o
> Portal de Notas. A parte visual e feita em Flask, mas o acesso ao Portal so
> acontece depois que o fluxo Kerberos foi concluido.

> No projeto existem dois perfis principais: professor e aluno. O professor pode
> listar alunos, lancar notas, editar notas, excluir notas e consultar os
> registros. O aluno pode consultar apenas as proprias notas.

> Essa regra esta implementada em `notes/service.py`. A funcao
> `_validar_professor` impede que um usuario com perfil de aluno faca operacoes
> de alteracao. A funcao `listar_notas` tambem diferencia professor e aluno:
> professor ve todas as notas, aluno ve apenas as notas associadas ao proprio
> usuario.

## Demonstracao como professor

Passo a passo:

1. Abrir `http://127.0.0.1:5000`.
2. Fazer login com uma conta professor, por exemplo `SilvioSants`.
3. Nao mostrar a senha.
4. Mostrar que aparece o painel de professor.
5. Selecionar um aluno, por exemplo `AkinGOD777`.
6. Lancar uma nota.
7. Mostrar a nota cadastrada na tabela.
8. Editar a nota.
9. Mostrar mensagem de sucesso.

Fala para ler:

> Ao entrar como professor, a tela permite escolher um aluno e cadastrar notas.
> Embora pareca uma operacao comum de formulario, por baixo o Flask esta criando
> uma operacao Kerberos protegida. A acao de criar ou editar nota passa pelo
> Portal com Service Ticket, autenticador, requisicao cifrada, nonce e hash.

## Demonstracao dos logs didaticos

Mostrar:

- terminal dos servidores;
- terminal Flask;
- bloco de etapas Kerberos na interface, se estiver visivel.

Fala para ler:

> Os logs didaticos ajudam a acompanhar o fluxo. Eles mostram o Cliente Web
> iniciando o processo, o Cliente TCP enviando requisicoes, o AS validando a
> prova, o TGS emitindo o Service Ticket e o Portal validando o acesso. Campos
> sensiveis como senha, chaves, tickets, autenticadores, nonces e ciphertexts
> sao mascarados.

## Demonstracao como aluno

Passo a passo:

1. Fazer logout.
2. Entrar com uma conta aluno, por exemplo `AkinGOD777`.
3. Mostrar o painel de aluno.
4. Mostrar que o aluno ve apenas suas proprias notas.
5. Mostrar que nao aparecem controles de lancar, editar ou excluir.

Fala para ler:

> Ao entrar como aluno, o sistema continua passando pelo mesmo fluxo Kerberos.
> A diferenca esta na autorizacao do Portal. O aluno nao recebe permissoes para
> alterar notas. A interface oculta os controles, e a camada de servico tambem
> bloqueia qualquer tentativa direta.

## Persistencia em JSON

Fala para ler:

> As notas ficam em `data/notas.json`. A camada `notes/repository.py` cuida de
> adicionar, listar, editar e excluir notas. A escrita e apoiada por
> `storage/json_store.py`, que usa arquivo temporario e substituicao atomica.
> Isso e suficiente para a proposta academica do trabalho.

## Pontos que o professor precisa perceber

- Existe um servico protegido real: Portal de Notas.
- Professor e aluno tem permissoes diferentes.
- A interface e simples, mas as operacoes passam por Kerberos.
- Logs ajudam a provar o fluxo durante a apresentacao.
- Persistencia e JSON, adequada ao escopo academico.

## Frase de transicao

> Agora que vimos o sistema funcionando, vamos fechar mostrando como executar,
> quais testes comprovam o fluxo e quais sao as limitacoes academicas.

---

# Apresentador 4 - Execucao, testes, Doxygen, limitacoes e conclusao

## Objetivo da parte

Essa parte deve fechar a apresentacao de forma organizada, mostrando que o
projeto e reproduzivel, testado e documentado.

## O que mostrar na tela

Mostrar nesta ordem:

1. Terminal com `python scripts/iniciar_servidores.py`.
2. Terminal com `python run.py`.
3. `tests/test_rede.py`.
4. `tests/test_as_server.py`.
5. `tests/test_tgs.py`.
6. `tests/test_notas.py`.
7. Execucao de `python -m pytest -q`.
8. `Doxyfile`.
9. `docs/html/index.html`.
10. `docs/relatorio_tecnico.md`.

## Fala sobre execucao

> Para executar o projeto, usamos dois terminais. No primeiro, iniciamos os
> servidores Kerberos com `python scripts/iniciar_servidores.py`. Esse comando
> sobe AS, TGS e Portal de Notas em processos separados. No segundo terminal,
> iniciamos a aplicacao Flask com `python run.py`. Depois acessamos
> `http://127.0.0.1:5000`.

> Essa forma de execucao e importante porque evidencia a separacao real entre
> os componentes. O Flask nao esta chamando tudo diretamente no mesmo processo;
> ele fala com AS, TGS e Portal usando o cliente TCP.

## Fala sobre testes

> A suite de testes automatizados comprova as partes mais importantes do projeto.
> O comando principal e:

```powershell
python -m pytest -q
```

> O resultado atual esperado e 48 testes passando. Os testes estao divididos por
> responsabilidade:

- `test_crypto.py`: AES-GCM, KDF, nonces e adulteracao;
- `test_as_server.py`: desafio, prova HMAC, autenticacao e TGT;
- `test_tgs.py`: TGT, autenticador, replay e Service Ticket;
- `test_notas.py`: Portal, autenticacao mutua, CRUD, permissoes e replay;
- `test_fluxo.py`: fluxo integrado entre login, professor e aluno;
- `test_rede.py`: AS, TGS e Portal em sockets TCP reais.

> O `test_rede.py` e especialmente importante para a apresentacao, porque ele
> sobe os tres servidores em portas TCP reais e verifica que o fluxo passa por
> AS, TGS e Portal. Tambem existe teste garantindo que a senha nao aparece nas
> mensagens enviadas ao AS.

## Fala sobre Doxygen

> O projeto tambem possui documentacao Doxygen. O arquivo `Doxyfile` configura a
> entrada dos arquivos, a pagina principal, a geracao HTML e o layout. O arquivo
> `DoxygenLayout.xml` adiciona a aba "Como executar o codigo" no menu superior.
> A documentacao gerada fica em `docs/html/index.html`.

> Isso ajuda na entrega porque permite navegar pelos arquivos, funcoes, classes
> e paginas explicativas do projeto.

## Fala sobre limitacoes

> Como o projeto e academico, algumas escolhas sao intencionalmente simples. A
> persistencia usa JSON em vez de banco de dados. As sessoes, desafios e caches
> de replay ficam em memoria. A execucao e local. O navegador fala com Flask por
> HTTP local, entao em producao seria necessario HTTPS. Tambem existem chaves
> padrao didaticas, mas elas podem ser substituidas por variaveis de ambiente
> geradas pelo script `scripts/gerar_chaves.py`.

> Essas limitacoes nao anulam o objetivo do trabalho, porque o foco e demonstrar
> o protocolo Kerberos e os mecanismos de seguranca usando primitivas basicas.

## Conclusao pronta

> Concluindo, o projeto implementa uma simulacao academica do Kerberos aplicada
> a um Portal de Notas. O usuario se autentica por senha, mas a senha nao
> atravessa a rede. O AS emite um TGT, o TGS emite um Service Ticket para o
> servico de notas, e o Portal valida ticket, autenticador, timestamp, nonce e
> hash antes de executar as operacoes. A autenticacao mutua confirma que o
> Cliente esta falando com o servico correto, e os testes comprovam o fluxo
> completo. Portanto, o sistema atende aos principais requisitos do trabalho:
> AS, TGS, servico protegido, KDF, tickets, autenticadores, replay, autenticacao
> mutua e uso exclusivo de criptografia simetrica.

---

## Checklist de requisitos para citar no video

| Requisito | Quem deve citar | Evidencia principal |
|---|---|---|
| Kerberos com criptografia simetrica | Apresentador 1 | `crypto_utils.py`, `config.py` |
| AS | Apresentador 1 | `as_server.py`, `servidor_as.py` |
| KDF por senha | Apresentador 1 | `kdf.py` |
| TGT | Apresentador 1 | `gerar_tgt`, `criar_tgt` |
| TGS | Apresentador 2 | `tgs_server.py`, `servidor_tgs.py` |
| Service Ticket | Apresentador 2 | `emitir_ticket_servico` |
| Autenticadores | Apresentador 2 | `authenticator.py` |
| Replay | Apresentador 2 | `NONCES_TGS_UTILIZADOS`, `NONCES_UTILIZADOS` |
| Autenticacao mutua | Apresentador 2 | `autenticar_portal_notas`, `validar_confirmacao_portal` |
| Operacoes protegidas | Apresentador 2 e 3 | `executar_operacao_kerberos`, `processar_operacao_portal` |
| Portal de Notas | Apresentador 3 | `notes/service.py`, `templates/notas.html` |
| Professor/aluno | Apresentador 3 | `service.py`, `usuarios.json` |
| Testes | Apresentador 4 | pasta `tests` |
| Doxygen | Apresentador 4 | `Doxyfile`, `docs/html/index.html` |
| Limitacoes | Apresentador 4 | `README.md`, `relatorio_tecnico.md` |

---

## Ordem recomendada de gravacao

1. Comecar com os terminais ja abertos.
2. Apresentador 1 explica arquitetura, senha, KDF, AS e TGT.
3. Apresentador 2 explica TGS, Service Ticket, autenticadores, replay,
   autenticacao mutua e operacoes protegidas.
4. Apresentador 3 demonstra professor e aluno no navegador.
5. Apresentador 4 roda testes, mostra Doxygen, fala das limitacoes e encerra.

---

## Pontos que nao devem ser ditos

- Nao dizer que e Kerberos real de producao.
- Nao dizer que usa banco de dados.
- Nao dizer que a senha e enviada ao AS.
- Nao dizer que o Kerberos protege apenas o login.
- Nao dizer que existe TLS/HTTPS em producao.
- Nao mostrar senhas.
- Nao mostrar tickets ou chaves como se fossem dados publicos; os logs ja
  mascaram campos sensiveis.

---

## Frase final curta para todos

> O ponto mais importante do nosso projeto e que ele demonstra o fluxo Kerberos
> completo, com AS, TGS e servico protegido separados por sockets TCP. A senha e
> usada apenas para derivar uma chave localmente, os tickets controlam o acesso,
> os autenticadores reduzem replay, a autenticacao mutua confirma o servico e
> cada operacao do Portal de Notas continua protegida.
