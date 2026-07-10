# Roteiro de Apresentação do Portal de Notas com Kerberos

Tempo total sugerido: 14 a 17 minutos.

## 1. Estrutura real encontrada

O projeto é uma aplicação Flask com uma implementação acadêmica do fluxo
Kerberos. AS, TGS e Portal de Notas executam como processos TCP separados.

```text
kerberos-notas-base/
|-- run.py
|-- requirements.txt
|-- pyproject.toml
|-- data/
|   |-- usuarios.json
|   `-- notas.json
|-- scripts/
|   |-- criar_usuario.py
|   |-- iniciar_servidores.py
|   `-- reset_dados.py
|-- src/kerberos_notas/
|   |-- rede/
|   |-- servidores/
|   |-- config.py
|   |-- client/routes.py
|   |-- crypto/
|   |   |-- crypto_utils.py
|   |   `-- kdf.py
|   |-- kerberos/
|   |   |-- as_server.py
|   |   |-- authenticator.py
|   |   |-- tgs_server.py
|   |   `-- tickets.py
|   |-- notes/
|   |   |-- portal_notas.py
|   |   |-- repository.py
|   |   `-- service.py
|   `-- storage/json_store.py
|-- templates/
|   |-- login.html
|   |-- notas.html
|   `-- erro.html
|-- static/css/style.css
|-- tests/
|   |-- test_crypto.py
|   |-- test_as_server.py
|   |-- test_tgs.py
|   |-- test_notas.py
|   `-- test_fluxo.py
`-- docs/
    |-- fluxo_kerberos.md
    |-- relatorio_tecnico.md
    `-- README_TESTES_E_DEMO.md
```

### Componentes confirmados

- Entrada da aplicação: `run.py`, função importada `create_app`.
- Cliente e integração Kerberos: `src/kerberos_notas/client/routes.py`.
- AS: `src/kerberos_notas/kerberos/as_server.py`.
- TGS: `src/kerberos_notas/kerberos/tgs_server.py`.
- TGT e Service Ticket: `src/kerberos_notas/kerberos/tickets.py`.
- Autenticadores: `src/kerberos_notas/kerberos/authenticator.py`.
- KDF: `src/kerberos_notas/crypto/kdf.py`.
- AES-GCM: `src/kerberos_notas/crypto/crypto_utils.py`.
- Serviço protegido: `src/kerberos_notas/notes/portal_notas.py`.
- Regras de professor e aluno: `src/kerberos_notas/notes/service.py`.
- Persistência: `src/kerberos_notas/notes/repository.py` e
  `src/kerberos_notas/storage/json_store.py`.
- Interface: rotas em `client/routes.py` e templates em `templates/`.
- Testes confirmados: 34.

### Rotas Flask confirmadas

| Rota | Método | Função | Finalidade |
|---|---|---|---|
| `/` | GET | `index` | Redireciona para login ou notas |
| `/login` | GET/POST | `login` | Executa o fluxo Kerberos |
| `/notas` | GET/POST | `notas` | Lista ou lança notas |
| `/notas/<nota_id>/editar` | POST | `editar` | Edita uma nota |
| `/notas/<nota_id>/excluir` | POST | `excluir` | Exclui uma nota |
| `/logout` | GET | `logout` | Remove a sessão Kerberos |

### Usuários e perfis existentes

O arquivo `data/usuarios.json` possui atualmente:

- professores: `kassio` e `SilvioSants`;
- alunos: `kassio12`, `AkinGOD777` e `malululu10`.

As senhas não estão no arquivo. Use somente credenciais conhecidas. Se
necessário, crie usuários de demonstração com `scripts/criar_usuario.py`.

### Pontos encontrados na auditoria

- Não existe módulo de chat.
- `scripts/reset_dados.py` apaga somente notas após confirmação.
- `docs/fontes_algoritmos.md` reúne as fontes oficiais utilizadas.
- O arquivo vazio `kerberos/time_utils.py` foi removido.
- Não há `pytest-cov` nem configuração de cobertura.
- `data/notas.json` contém registros de demonstrações anteriores.
- O bloqueio de aluno é testado com HTTP 403, mas a interface simplesmente
  oculta os controles de professor.
- Edição e exclusão possuem testes da camada de serviço e das rotas HTTP.
- Existe cache de nonces em memória para rejeitar replay.

## 2. Preparação antes da gravação

1. Escolha uma conta de professor e uma de aluno cujas senhas sejam conhecidas.
2. Preferência para a demonstração atual:
   - professor: `SilvioSants`;
   - aluno: `AkinGOD777`.
3. Se as senhas não forem conhecidas, crie contas novas antes de gravar:

```powershell
$env:PYTHONPATH='src'
python scripts/criar_usuario.py
```

Execute duas vezes e escolha os perfis `professor` e `aluno`. Não grave a
digitação das senhas.

4. Cadastre previamente uma nota limpa ou prepare-se para cadastrá-la no vídeo.
5. Evite destacar os registros legados de `data/notas.json`.
6. Feche terminais que possam mostrar informações desnecessárias.

## 3. Comandos reais do projeto

### Criar e ativar o ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Executar o projeto

```powershell
$env:PYTHONPATH='src'
python run.py
```

Acesso: `http://127.0.0.1:5000`.

### Executar os testes

```powershell
python -m pytest -q
```

Resultado confirmado na auditoria:

```text
48 passed
```

### Cobertura e dados iniciais

- Cobertura não está configurada. Não execute `pytest --cov` no vídeo.
- Não existe seed.
- O único utilitário funcional de dados é `scripts/criar_usuario.py`.

Para limpar somente as notas antes de uma nova demonstração:

```powershell
python scripts/reset_dados.py
```

# Roteiro detalhado

## Parte 1 - Abertura

Tempo estimado: 30 segundos.

### O que falar

> Este trabalho apresenta uma implementação acadêmica simplificada do
> protocolo Kerberos usando criptografia de chave simétrica. O serviço
> protegido escolhido foi um Portal de Notas Escolares, com perfis de professor
> e aluno.

### O que mostrar

- Abra `README.md`.
- Mostre o título e a seção “Fluxo principal”.

### O professor deve perceber

- O escopo está definido.
- O Portal de Notas é o único serviço protegido.
- O projeto não se apresenta como solução de produção.

### Requisitos comprovados

- 1, 4, 5 e 16.

## Parte 2 - Objetivo funcional

Tempo estimado: 40 segundos.

### O que falar

> Depois da autenticação Kerberos, professores podem visualizar alunos, lançar,
> editar, excluir e consultar notas. Alunos podem consultar somente as próprias
> notas e não recebem permissão de alteração.

### O que mostrar

- Em `README.md`, mostre a seção “Perfis”.
- Abra `data/usuarios.json` apenas para mostrar `perfil`, `salt` e
  `verificador`. Não mostre nem fale senhas.

### Destacar

- `perfil: "professor"` em `SilvioSants`.
- `perfil: "aluno"` em `AkinGOD777`.

### Requisitos comprovados

- 17, 18, 19 e 20.

## Parte 3 - Explicação rápida do Kerberos

Tempo estimado: 50 segundos.

### O que falar

> O usuário utiliza a senha somente no cliente. O AS envia um desafio e valida
> uma prova HMAC antes de emitir o TGT. O cliente usa esse TGT e um autenticador
> para solicitar ao TGS um Service Ticket. Depois, o Portal valida o Service
> Ticket e outro autenticador antes de concluir a autenticação mútua.

### O que mostrar

- Abra `docs/fluxo_kerberos.md`.
- Percorra os sete passos do diagrama.

### O professor deve perceber

- TGT e Service Ticket possuem finalidades diferentes.
- A senha não é enviada ao AS, ao TGS ou ao Portal.

### Requisitos comprovados

- 8, 9, 10, 13, 14, 15 e 16.

## Parte 4 - Arquitetura e separação dos módulos

Tempo estimado: 50 segundos.

### O que falar

> AS, TGS, cliente e Portal são separados por responsabilidade e por processo.
> Eles trocam mensagens JSON com tamanho prefixado por sockets TCP locais.

### O que mostrar

No explorador do VS Code, expanda:

- `src/kerberos_notas/client`;
- `src/kerberos_notas/crypto`;
- `src/kerberos_notas/kerberos`;
- `src/kerberos_notas/rede`;
- `src/kerberos_notas/servidores`;
- `src/kerberos_notas/notes`;
- `tests`;
- `templates`.

Abra rapidamente `run.py` e mostre:

```python
app = create_app(usar_rede=True)
```

### Requisitos comprovados

- 2, 3, 4 e 16.

## Parte 5 - Criptografia simétrica e KDF

Tempo estimado: 1 minuto.

### O que falar

> A senha não é usada diretamente como chave. A função
> PBKDF2-HMAC-SHA256 combina senha e salt em 200 mil iterações para produzir
> uma chave de 32 bytes. Os pacotes do protocolo são protegidos com AES-GCM,
> também com chaves de 32 bytes e nonces aleatórios.

### O que mostrar

Abra `src/kerberos_notas/crypto/kdf.py`.

Destaque:

- `TAMANHO_SALT = 16`;
- `TAMANHO_CHAVE = 32`;
- `ITERACOES_PBKDF2 = 200_000`;
- `gerar_salt`;
- `derivar_chave_senha`;
- `gerar_verificador_chave`;
- `verificar_senha`.

Depois abra `src/kerberos_notas/crypto/crypto_utils.py`.

Destaque:

- `gerar_chave_simetrica`;
- `criptografar_json`;
- `descriptografar_json`;
- uso de `AESGCM`;
- nonce de 12 bytes.

### Testes relacionados

- `test_aes_gcm_criptografa_e_descriptografa_json`;
- `test_aes_gcm_rejeita_chave_errada`;
- `test_aes_gcm_detecta_ciphertext_adulterado`;
- `test_aes_gcm_usa_nonces_diferentes`;
- três testes de KDF em `tests/test_crypto.py`.

### Requisitos comprovados

- 1, 6 e 7.

## Parte 6 - Authentication Server

Tempo estimado: 1 minuto e 15 segundos.

### O que falar

> O Authentication Server realiza a autenticação inicial. Ele envia salt e um
> desafio. O cliente deriva a chave localmente e responde com uma prova HMAC.
> Se a prova estiver correta, o AS gera uma chave Cliente-TGS e um TGT.

### O que mostrar

Abra `src/kerberos_notas/kerberos/as_server.py`.

Destaque nesta ordem:

1. `carregar_usuarios`;
2. `criar_desafio_as`;
3. `autenticar_no_as_com_prova`;
4. `gerar_tgt`.

Em `autenticar_no_as_com_prova`, mostre:

- `gerar_prova_as`;
- `gerar_chave_simetrica`;
- `criptografar_json(CHAVE_SECRETA_TGS, tgt)`;
- resposta cifrada com `chave_cliente`.

Abra também `src/kerberos_notas/kerberos/tickets.py` e mostre `criar_tgt`.

### O que falar sobre segurança

> O cliente recebe o TGT, mas não possui a chave secreta do TGS para abri-lo ou
> alterá-lo. A resposta externa do AS é cifrada com a chave de longo prazo
> reproduzida pelo cliente, e a senha nunca atravessa o socket.

### Testes relacionados

Em `tests/test_as_server.py`, mostre:

- `test_as_autentica_usuario_valido`;
- `test_as_rejeita_senha_invalida`;
- `test_as_gera_tgt_valido_com_dados_necessarios`;
- `test_tgt_nao_fica_legivel_sem_chave_correta`;
- `test_tgt_do_as_e_aceito_pelo_tgs`.

### Requisitos comprovados

- 2, 6, 7, 8 e 9.

## Parte 7 - Autenticador Cliente-TGS e TGS

Tempo estimado: 1 minuto e 20 segundos.

### O que falar

> Para pedir acesso ao Portal, o cliente envia ao TGS o TGT e um autenticador
> cifrado com a chave Cliente-TGS. O TGS valida identidade, validade e
> timestamp. Depois gera a chave Cliente-Serviço e o Service Ticket específico
> para `notas`.

### O que mostrar

Abra `src/kerberos_notas/kerberos/authenticator.py`.

Destaque:

- `criar_autenticador`;
- campos `usuario`, `timestamp` e `nonce`;
- `abrir_autenticador`.

Depois abra `src/kerberos_notas/kerberos/tgs_server.py`.

Destaque:

1. `CHAVES_SERVICOS`, contendo somente `notas`;
2. `validar_tgt`;
3. `validar_autenticador`;
4. `_registrar_nonce_tgs`;
5. `emitir_ticket_servico`;
6. `abrir_ticket_servico`.

Mostre em `emitir_ticket_servico`:

- geração da chave Cliente-Serviço;
- chamada de `criar_ticket_servico`;
- ticket cifrado com a chave do Portal;
- resposta do cliente cifrada com a chave Cliente-TGS.

### Testes relacionados

Em `tests/test_tgs.py`, destaque:

- `test_tgs_emite_ticket_servico_com_tgt_valido`;
- `test_tgs_rejeita_tgt_expirado`;
- `test_tgs_rejeita_autenticador_invalido`;
- `test_tgs_rejeita_autenticador_reutilizado`;
- `test_tgs_rejeita_servico_desconhecido`;
- `test_ticket_servico_tem_dados_necessarios`;
- `test_ticket_servico_nao_fica_legivel_sem_chave_correta`;
- `test_ticket_servico_expirado_nao_e_aceito`.

### Requisitos comprovados

- 3, 8, 10, 11 e 13.

## Parte 8 - Portal e autenticação mútua

Tempo estimado: 1 minuto e 30 segundos.

### O que falar

> O Portal é o serviço protegido. Ele não recebe a senha nem o TGT. Ele recebe
> o Service Ticket e o autenticador Cliente-Serviço. O ticket é aberto com a
> chave secreta do Portal e fornece a chave Cliente-Serviço usada para validar
> o autenticador.

### O que mostrar

Abra `src/kerberos_notas/notes/portal_notas.py`.

Destaque:

1. `SERVICO_NOTAS = "notas"`;
2. `validar_ticket_portal`;
3. `autenticar_portal_notas`;
4. validação do usuário e timestamp;
5. resposta com `timestamp_resposta = timestamp + 1`;
6. resposta com `nonce_autenticador`;
7. `validar_confirmacao_portal`;
8. `calcular_hash_requisicao`;
9. `processar_operacao_portal`;
10. `_registrar_nonce`;
11. `validar_resposta_operacao`.

### O que falar sobre autenticação mútua

> O Portal demonstra conhecer a chave Cliente-Serviço ao cifrar uma confirmação
> com o timestamp incrementado e o mesmo nonce. O cliente abre essa resposta e
> confere os dois valores. Somente depois a sessão é considerada autenticada.
> Para cada operação posterior, um novo autenticador vincula ação, nonce e hash
> a uma requisição cifrada. O Portal rejeita replay e só executa o CRUD após
> validar todo esse conjunto.

Abra `src/kerberos_notas/client/routes.py` e mostre, dentro de
`autenticar_com_kerberos`:

- criação de `autenticador_portal`;
- chamada de `autenticar_portal_notas`;
- chamada de `validar_confirmacao_portal`;
- `portal_autenticado: True`.

### Testes relacionados

Em `tests/test_notas.py`, mostre:

- `test_portal_realiza_autenticacao_mutua`;
- `test_portal_rejeita_autenticador_com_chave_errada`;
- `test_portal_rejeita_ticket_adulterado`.
- `test_portal_rejeita_reutilizacao_do_autenticador`;
- `test_portal_rejeita_requisicao_adulterada`;
- `test_portal_rejeita_autenticador_de_outra_acao`.

### Requisitos comprovados

- 4, 5, 12, 14 e 15.

## Parte 9 - Fluxo integrado e logs

Tempo estimado: 50 segundos.

### O que falar

> A função que integra todas as etapas é `autenticar_com_kerberos`. Ela chama os
> servidores AS, TGS e Portal por sockets TCP e valida a autenticação mútua.
> Depois do login,
> `executar_operacao_kerberos` repete ticket, autenticador e confirmação mútua
> em cada ação do Portal.

### O que mostrar

Em `src/kerberos_notas/client/routes.py`, percorra
`autenticar_com_kerberos` do início ao fim.

Depois mostre `executar_operacao_kerberos` e destaque:

- requisição com `usuario`, `acao`, `dados` e `nonce`;
- `calcular_hash_requisicao`;
- `criar_autenticador`;
- `cliente_tcp.executar_operacao`;
- `validar_resposta_operacao`.

Destaque `registrar_etapa` e as mensagens:

- `[CLIENTE]`;
- `[AS]`;
- `[TGS]`;
- `[PORTAL]`.

Abra `templates/notas.html` e mostre:

- texto “Service Ticket válido e autenticação mútua concluída”;
- bloco “Etapas da autenticação Kerberos”.

### Observação

Os logs informam apenas que a senha foi processada localmente e nunca imprimem
seu valor.

### Requisitos comprovados

- 16 e 23.

## Parte 10 - Regras de acesso e persistência

Tempo estimado: 1 minuto.

### O que falar

> Depois da autenticação, a camada de serviço aplica autorização. Professor
> lista todos os registros e pode alterá-los. Aluno recebe somente a lista
> associada ao próprio nome e qualquer tentativa de alteração gera
> `PermissionError`.

### O que mostrar

Abra `src/kerberos_notas/notes/service.py`.

Destaque:

- `PERFIL_PROFESSOR` e `PERFIL_ALUNO`;
- `obter_perfil_usuario`;
- `listar_alunos`;
- `listar_notas`;
- `_validar_professor`;
- `criar_nota`;
- `editar_nota`;
- `excluir_nota`.

Abra rapidamente `src/kerberos_notas/notes/repository.py`.

Destaque:

- `listar_notas_usuario`;
- `listar_todas_notas`;
- `adicionar_nota_usuario`;
- `atualizar_nota_por_id`;
- `excluir_nota_por_id`.

### Requisitos comprovados

- 17, 18, 19 e 20.

## Parte 11 - Demonstração web como professor

Tempo estimado: 2 minutos.

### Antes de começar

Execute:

```powershell
$env:PYTHONPATH='src'
python run.py
```

Acesse `http://127.0.0.1:5000`.

### Passo a passo

1. Abra `/login`.
2. Entre com `SilvioSants` ou outra conta de perfil professor.
3. Não mostre a senha na gravação.
4. Após o redirecionamento, mostre “Painel de Professor”.
5. Mostre a confirmação verde do Service Ticket e autenticação mútua.
6. Abra “Etapas da autenticação Kerberos”.
7. Leia rapidamente as etapas de AS, TGS e Portal.
8. No formulário “Lançar nota”:
   - selecione `AkinGOD777` ou outro aluno;
   - disciplina: `Segurança Computacional`;
   - nota: `9.0`;
   - observação: `Demonstração do fluxo Kerberos`.
9. Clique em “Lançar nota”.
10. Mostre a nota na tabela.
11. Altere a nota para `9.5` e clique em “Salvar”.
12. Mostre a mensagem e os logs de autenticação da operação `editar_nota`.
13. Não exclua essa nota, pois ela será usada na visão do aluno.
14. Clique em “Sair”.

### Arquivos que sustentam a demonstração

- rota `/login`: `client/routes.py`, função `login`;
- rota `/notas`: função `notas`;
- edição: rota `/notas/<nota_id>/editar`, função `editar`;
- template: `templates/notas.html`;
- autorização: `notes/service.py`.

### Requisitos comprovados

- 6, 8, 10, 12, 14, 15, 17, 18 e 23.

## Parte 12 - Demonstração web como aluno

Tempo estimado: 1 minuto e 30 segundos.

### Passo a passo

1. Entre com `AkinGOD777` ou a conta aluno usada no passo anterior.
2. Mostre “Painel de Aluno”.
3. Mostre novamente a confirmação Kerberos.
4. Abra os logs para confirmar que o aluno também passou por AS, TGS e Portal.
5. Mostre a nota de `Segurança Computacional`.
6. Mostre que não aparece o formulário “Lançar nota”.
7. Mostre que não aparecem os botões “Salvar” e “Excluir”.
8. Explique que a interface oculta as ações e a camada de serviço também as
   bloqueia.
9. Faça logout.

### Como demonstrar o bloqueio sem inventar tela

Não existe botão visível para o aluno provocar o erro. Em vez de manipular o
navegador, mostre no VS Code:

- `tests/test_notas.py`, teste `test_rota_impede_aluno_de_lancar_nota`;
- asserção `status_code == 403`;
- `test_aluno_nao_pode_editar_nota`;
- `tests/test_fluxo.py`, verificação de que “Lançar nota” não aparece.

### Requisitos comprovados

- 17, 19 e 20.

## Parte 13 - Acesso sem ticket

Tempo estimado: 40 segundos.

### O que falar

> O acesso ao Portal não depende apenas do cookie Flask. A sessão do navegador
> guarda um identificador opaco. Ticket e chave ficam na memória do servidor. A
> função `exigir_sessao_kerberos` exige uma sessão autenticada. O Portal de
> Notas reabre e valida o Service Ticket recebido por socket em cada ação, e
> `executar_operacao_kerberos` cria um autenticador novo.

### O que mostrar

Em `src/kerberos_notas/client/routes.py`, destaque:

- `sessoes_kerberos = {}`;
- `obter_sessao_kerberos`;
- `exigir_sessao_kerberos`;
- `validar_sessao_portal`;
- `validar_ticket_notas`.

Em `tests/test_notas.py`, mostre:

- `test_rota_recusa_acesso_sem_service_ticket`;
- `test_portal_rejeita_ticket_adulterado`.

### Requisitos comprovados

- 12 e 21.

## Parte 14 - Testes automatizados

Tempo estimado: 1 minuto e 30 segundos.

### O que falar

> A suíte possui 48 testes. Eles cobrem criptografia, KDF, AS, TGS, tickets,
> autenticadores, autenticação mútua por operação, replay, permissões e o fluxo
> web integrado, incluindo os três sockets TCP.

### O que executar

```powershell
python -m pytest -q
```

Mostre o resultado:

```text
48 passed
```

### Distribuição real

| Arquivo | Quantidade | Evidência principal |
|---|---:|---|
| `tests/test_crypto.py` | 7 | AES-GCM, adulteração, nonce e KDF |
| `tests/test_as_server.py` | 7 | Login, TGT e integração com TGS |
| `tests/test_rede.py` | 5 | AS, TGS e Notas por sockets TCP |
| `tests/test_tgs.py` | 9 | TGT, replay Cliente-TGS e Service Ticket |
| `tests/test_notas.py` | 18 | CRUD protegido, perfis, replay e autenticação mútua |
| `tests/test_fluxo.py` | 2 | Fluxo completo e interface professor/aluno |

### Testes mais fortes para abrir

1. `test_fluxo_as_tgs_portal_com_autenticacao_mutua`;
2. `test_fluxo_web_professor_lanca_e_aluno_consulta`;
3. `test_portal_rejeita_ticket_adulterado`;
4. `test_portal_rejeita_reutilizacao_do_autenticador`;
5. `test_rotas_editar_e_excluir_usam_operacao_kerberos`;
6. `test_rota_impede_aluno_de_lancar_nota`;
7. `test_aes_gcm_detecta_ciphertext_adulterado`.

### Requisito comprovado

- 22.

## Parte 15 - Limitações e conclusão

Tempo estimado: 1 minuto.

### O que mostrar

Abra:

- `README.md`, seção “Limitações acadêmicas”;
- `docs/relatorio_tecnico.md`, seção “Limitações”.

### O que falar

> Esta é uma implementação acadêmica simplificada. Os serviços usam processos
> TCP separados, e as chaves didáticas podem ser substituídas por variáveis de
> ambiente. Os dados ficam em JSON e as sessões e caches contra replay ficam em
> memória. Em produção seriam necessários banco de dados, HTTPS e TLS.

### Conclusão pronta

> O projeto demonstra o fluxo completo Cliente, AS, TGS e Portal de Notas. A
> senha é usada apenas na autenticação inicial e transformada por uma KDF.
> Depois disso, TGT, Service Ticket, autenticadores e chaves temporárias
> controlam o acesso. O Portal valida o cliente, o cliente valida o Portal e as
> permissões distinguem corretamente professor e aluno. Assim, conseguimos
> demonstrar de forma didática os principais conceitos do Kerberos usando
> somente criptografia simétrica.

### Requisito comprovado

- 24 e encerramento dos demais.

# Mapeamento dos 24 requisitos

| Requisito | Onde é atendido | Arquivo, função ou teste | Como mostrar no vídeo |
|---|---|---|---|
| 1. Kerberos com chave simétrica | AES-GCM e chaves compartilhadas | `crypto/crypto_utils.py`: `criptografar_json`; `config.py` | Mostrar `AESGCM` e as chaves do TGS/Portal |
| 2. AS | Autenticação inicial e TGT | `kerberos/as_server.py`: `autenticar_no_as_com_prova` | Abrir a função e os testes do AS |
| 3. TGS | Valida TGT e emite Service Ticket | `kerberos/tgs_server.py`: `emitir_ticket_servico` | Mostrar validações e emissão |
| 4. Serviço protegido | Portal exige ticket e autenticador em cada ação | `notes/portal_notas.py`: `processar_operacao_portal` | Mostrar o processamento protegido |
| 5. Portal de Notas | Serviço identificado como `notas` | `portal_notas.py`: `SERVICO_NOTAS`; `tgs_server.py`: `CHAVES_SERVICOS` | Mostrar que só existe `notas` |
| 6. Senha | KDF local e prova HMAC | `templates/login.html`; `routes.py`: `login`; `kdf.py`: `gerar_prova_as` | Mostrar que ela não atravessa a rede |
| 7. KDF | PBKDF2-HMAC-SHA256 | `crypto/kdf.py`: `derivar_chave_senha` | Mostrar parâmetros e testes |
| 8. Tickets | Criação, transporte e abertura | `tickets.py`, `as_server.py`, `tgs_server.py`, `portal_notas.py` | Percorrer o fluxo |
| 9. TGT | Criação e cifra com chave do TGS | `tickets.py`: `criar_tgt`; `as_server.py`: `gerar_tgt` | Mostrar campos e cifra |
| 10. Service Ticket | Emissão específica para notas | `tgs_server.py`: `emitir_ticket_servico` | Mostrar `servico="notas"` no fluxo |
| 11. TGT validado pelo TGS | Identidade, chave e validade | `tgs_server.py`: `validar_tgt` | Mostrar teste de TGT expirado |
| 12. Service Ticket validado | Portal abre e valida ticket | `portal_notas.py`: `validar_ticket_portal`; `tgs_server.py`: `abrir_ticket_servico` | Mostrar teste adulterado |
| 13. Autenticador Cliente-TGS | Criado pelo cliente e aberto pelo TGS | `routes.py`: `autenticador_tgs`; `tgs_server.py`: `validar_autenticador` | Mostrar os dois pontos |
| 14. Autenticador Cliente-Serviço | Novo autenticador por operação | `routes.py`: `executar_operacao_kerberos`; `authenticator.py`: `criar_autenticador` | Mostrar ação, hash e nonce |
| 15. Autenticação mútua | Timestamp + 1, nonce e ação em cada resposta | `portal_notas.py`: `validar_resposta_operacao` | Mostrar logs e testes de operação |
| 16. Fluxo completo | Integração inicial e proteção do CRUD | `routes.py`: `autenticar_com_kerberos`, `executar_operacao_kerberos` | Mostrar login e lançamento |
| 17. Perfis | Perfil carregado e aplicado | `service.py`: `obter_perfil_usuario`; `data/usuarios.json` | Mostrar professor/aluno |
| 18. Professor administra notas | CRUD despachado após Kerberos | `portal_notas.py`: `_executar_acao`; rotas de notas | Demonstrar no navegador |
| 19. Aluno vê só suas notas | Consulta pelo nome do usuário | `service.py`: `listar_notas`; `repository.py`: `listar_notas_usuario` | Entrar como aluno |
| 20. Aluno não altera | Validação de perfil e HTTP 403 | `service.py`: `_validar_professor`; `test_rota_impede_aluno_de_lancar_nota` | Mostrar ausência dos botões e teste |
| 21. Sem ticket não acessa | Sessão e ticket obrigatórios | `routes.py`: `exigir_sessao_kerberos`, `validar_ticket_notas`; `test_rota_recusa_acesso_sem_service_ticket` | Abrir rota sem login e mostrar teste |
| 22. Testes | 48 testes automatizados | pasta `tests/` | Executar `python -m pytest -q` |
| 23. Logs didáticos | Etapas armazenadas e exibidas | `routes.py`: `registrar_etapa`; `templates/notas.html` | Abrir os logs no painel |
| 24. Limitações | Restrições documentadas | `README.md`; `docs/relatorio_tecnico.md` | Mostrar a seção final |

# Pontos de atenção e lacunas

1. AS, TGS e Notas são servidores TCP separados; eles não são servidores HTTP.
2. Não diga que existe banco de dados; a persistência é JSON.
3. O cache contra replay existe, mas fica apenas em memória e é perdido ao
   reiniciar o processo.
4. Não diga que existe seed ou cobertura configurada.
5. Não mostre nem fale senhas.
6. Edição, exclusão, bloqueio do aluno, replay e adulteração possuem testes.
7. Os registros legados podem deixar a tabela visualmente confusa. Use uma
   disciplina criada durante a demonstração.
8. O navegador ainda se comunica com o Flask por HTTP local. Em produção, essa
   comunicação precisaria de HTTPS.

# Script curto de narração

> Nosso projeto é uma implementação acadêmica simplificada do Kerberos. O
> serviço protegido escolhido foi um Portal de Notas Escolares.
>
> O fluxo começa no cliente web. O usuário informa a senha, que é processada
> localmente com PBKDF2-HMAC-SHA256. O Authentication Server valida uma prova
> HMAC do desafio, gera uma chave Cliente-TGS e emite um TGT cifrado com a chave
> secreta do TGS.
>
> O cliente cria um autenticador Cliente-TGS e envia os dois elementos ao TGS.
> O TGS valida identidade e validade e emite um Service Ticket para o serviço
> `notas`, além de uma chave Cliente-Serviço.
>
> Para acessar o Portal, o cliente envia o Service Ticket e um novo
> autenticador. O Portal valida o ticket, o usuário, o timestamp e o nonce.
> Depois responde com o timestamp incrementado e o mesmo nonce, cifrados com a
> chave Cliente-Serviço. O cliente valida essa resposta, concluindo a
> autenticação mútua.
>
> Após a autenticação, o perfil controla as permissões. O professor pode
> visualizar alunos, lançar, editar e excluir notas. O aluno visualiza somente
> as próprias notas e não recebe controles de alteração. Tentativas diretas são
> rejeitadas com HTTP 403.
>
> Cada ação do Portal cria um autenticador novo e uma requisição cifrada. O
> Portal valida ticket, nonce, ação e hash, rejeita replay e devolve uma
> confirmação cifrada antes de o cliente aceitar o resultado.
>
> A suíte automatizada possui 48 testes cobrindo criptografia, KDF, AS, TGS,
> tickets, autenticadores, replay, autenticação mútua por operação, permissões
> e fluxos web e TCP.
>
> Como limitações acadêmicas, existem chaves padrão, os dados ficam em JSON e
> as sessões ficam em memória. Mesmo com essas simplificações, o projeto
> demonstra o fluxo Cliente, AS, TGS e Portal de Notas em processos separados,
> usando criptografia simétrica, tickets e autenticação mútua.
