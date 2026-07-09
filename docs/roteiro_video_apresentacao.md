# Roteiro de apresentação

Tempo sugerido: 8 a 12 minutos.

## 1. Abertura

> Nosso projeto implementa uma versão acadêmica do Kerberos utilizando
> primitivas criptográficas básicas. AS, TGS e Portal de Notas são processos
> separados que se comunicam por sockets TCP.

Mostre as portas `9001`, `9002` e `9003` no terminal dos servidores.

## 2. KDF e AS

Mostre `crypto/kdf.py`, `kerberos/as_server.py` e `servidores/servidor_as.py`.

- PBKDF2-HMAC-SHA256 com salt e 200 mil iterações;
- desafio aleatório e prova HMAC-SHA256;
- senha processada somente no cliente;
- resposta do AS e TGT protegidos por AES-GCM.

## 3. TGS

Mostre `servidores/servidor_tgs.py` e `kerberos/tgs_server.py`.

- validação do TGT e do autenticador Cliente-TGS;
- proteção contra replay;
- emissão do Service Ticket e da chave Cliente-Serviço.

## 4. Portal de Notas

Mostre `servidores/servidor_notas.py` e `notes/portal_notas.py`.

- autenticação mútua;
- requisição cifrada e autenticador novo em cada operação;
- validação de usuário, timestamp, nonce, ação e hash;
- CRUD protegido e autorização professor/aluno.

## 5. Demonstração

1. Execute `python scripts/iniciar_servidores.py`.
2. Em outro terminal, execute `python run.py`.
3. Entre como professor, lance e edite uma nota.
4. Mostre as solicitações nos terminais e os logs da interface.
5. Entre como aluno e mostre que ele vê apenas as próprias notas.

## 6. Testes

```powershell
python -m pytest -q
```

Resultado atual: `48 passed`.

Destaque `tests/test_rede.py`, que abre sockets reais para os três servidores e
verifica também que a senha não aparece nas mensagens enviadas ao AS.

## 7. Limitações

> O projeto usa chaves didáticas configuráveis por variáveis de ambiente,
> armazenamento JSON e caches em memória. Em produção também seriam necessários
> HTTPS entre navegador e Flask, TLS entre máquinas e um banco de dados.
