# Next-session prompt — X-COM T025

> **Superseded on 2026-09-26 by ADR-0020. Do not execute this SESN workflow.** It is preserved as historical planning context; use [next-session-t025-direct.md](next-session-t025-direct.md) for the successor work.


Trabalhe em `/home/jefferson/xverse-platform` e use o SESN local em
`/home/jefferson/sesn`. Leia integralmente `AGENTS.md`, `.specify/memory/constitution.md`,
os comandos Spec Kit aplicáveis e os arquivos autoritativos listados abaixo antes de agir.

Ao enviar este prompt, eu aceito explicitamente somente o escopo protótipo limitado da
observação X-COM descrito em
`specs/019-feat-ae449f37735949a6/acceptance-decision.md`, para o candidato exato
`d244eeb3aa26f1b27d23d75fabc750380405269f`, com todas as exclusões e limitações ali
registradas. Registre essa aceitação sem inventar ou reconstruir retroativamente um estado SESN
histórico inexistente. Se o `HEAD` não for esse candidato ou um descendente comprovadamente
equivalente, se a evidência/revisão não corresponder ao candidato, ou se houver achado aberto,
pare antes de modificar código e reporte o bloqueio.

Depois de fechar esse gate, implemente somente a próxima tarefa X-COM:

`T025 — explicit time-authority interface, local validation-permit validation/consumption,
and bounded validation-session lifecycle`.

## Modelo e execução

- Use Codex Terra Medium como cliente/orquestrador SESN.
- Use o DeepSeek oficial para o máximo de trabalho elegível e útil, especialmente propostas de
  implementação C++ e testes, sempre por meio dos gates e do executor batch do SESN; nunca chame a
  API diretamente.
- Para esta run, declare limite de `US$ 0,10` por pedido e `US$ 0,50` agregado. O agregado inclui
  todos os pedidos, retries e itens do batch. Não ultrapasse esses limites nem use fallback pago.
- Não presuma modelo, preço, endpoint ou price card de runs anteriores. Exija price card atual,
  política admitida, rota saudável e contabilização completa.
- Trate o workspace completo como RESTRICTED até classificação. Envie ao DeepSeek somente pacotes
  mínimos diretamente PUBLIC ou validados como SANITIZED, hash-bound e secret-scanned. Nunca envie
  caminhos privados, credenciais, `.sesn`, estado local, manifests de ambiente sensíveis, payloads,
  endereços, trechos privados ou dados de implantação.
- Registre packet ID/hash, classificação, admission/policy/routing IDs, limites declarados, uso e
  custo reportados, limitações e vínculo ao candidato. Incerteza de segurança, preço ou custo deve
  falhar fechada.
- Use Sol High apenas para integração/reparo local complexo se uma proposta DeepSeek for rejeitada.
  Reserve Astra XHigh para a revisão independente final, em sessão separada e somente leitura.

## Fontes autoritativas

- `specs/007-xcom-core/spec.md`, especialmente US3, FR-015–FR-020 e FR-033.
- `specs/007-xcom-core/data-model.md`, entidades `ValidationPermit`, `ValidationSession` e
  `TimeAuthority`, seus estados e invariantes.
- `specs/007-xcom-core/contracts/validation-tool.md`.
- `specs/007-xcom-core/plan.md` e `specs/007-xcom-core/tasks.md`.
- `specs/007-xcom-core/reference-traceability.md` e os registros REF-002 por ele referenciados.
- `docs/adr/ADR-0018-platform-first-delivery-sequence.md`.
- `docs/adr/ADR-0019-xcom-validation-and-observation-boundaries.md`.
- `docs/reviews/014-xcom-observation-implementation-review.md`.
- `specs/019-feat-ae449f37735949a6/acceptance-decision.md` e evidência associada.
- Contratos C++ já aceitos sob `src/xverse/xcom/` e seus validadores em `scripts/validate_xcom_*.py`.

## Workflow obrigatório

1. Preserve todas as alterações existentes do usuário; não limpe, descarte nem sobrescreva o
   checkout sujo. Não adicione `.sesn/sesn.sqlite3` ao Git.
2. Use uma nova atividade SESN com estado privado fora do repositório e uma única especificação
   Spec Kit para a capacidade T025. Não duplique nem reescreva `specs/007-xcom-core`.
3. Forneça ao SESN baseline exata, requisitos stakeholder/system/software, restrições, arquitetura,
   design detalhado, unidades, ownership, verificações, perfis de modelo e limites de autorização.
4. Exija rastreabilidade bidirecional entre requisitos, arquitetura, unidades, código, testes,
   evidência e candidato, incluindo disposições explícitas dos IDs REF-002 aplicáveis como
   implemented/partial/allocated/deferred/needs-clarification. O SADS é input alvo, não prova.
5. Mantenha tarefas com ownership de arquivos não sobreposto. Revise cada proposta DeepSeek antes de
   aplicá-la pelo guard do host; workers e provedor não podem alterar requisitos, estado, decisões ou
   entradas protegidas.
6. Execute verificação host offline sobre o candidato exato. Registre achados numa passagem de revisão
   separada antes de qualquer reparo; reparos exigem nova verificação e revisão do candidato sucessor.

## Escopo de implementação T025

Implemente uma fundação C++20 domain-neutral, fixa e limitada, sem alocação ou crescimento não
controlado no caminho operacional:

- interface explícita `TimeAuthority` com identidade de clock, leitura de tempo limitada e mapeamento
  entre domínios apenas quando houver regra e tolerância declaradas;
- resultados determinísticos para clock desconhecido, mapeamento ausente, fora de tolerância,
  regressão temporal e overflow;
- `ValidationPermit` local host-controlled, imutável e ligado a um único session ID, digest exato do
  plano/XDL, cenário, deployment/environment, tool ID, interfaces, ações, intervalo de validade,
  quotas/capacidades finitas e nonce;
- validação completa e consumo exatamente uma vez, sem transformar acesso ao transporte em
  autorização;
- `ValidationSession` com ownership e handle de geração exatos, transições bounded
  `declared -> armed -> active -> closing -> closed` e terminais `expired`, `revoked` e
  `evidence-incomplete`;
- operações idempotentes quando seguro e rejeição determinística de repetição insegura, handle stale,
  foreign session, digest/action/target/environment mismatch, expiração, revogação e quota excedida;
- diagnósticos estáveis, ordenados e públicos, sem payload irrestrito ou valores sensíveis;
- documentação Doxygen completa de ownership, lifetime, thread-safety, failure semantics e bounds.

Arquivos novos podem ser criados sob nomes claros como
`src/xverse/xcom/include/xverse/xcom/time_authority.hpp`,
`src/xverse/xcom/include/xverse/xcom/validation_session.hpp` e fontes correspondentes. Modifique o
CMake somente para registrar esses targets/testes. Adicione testes sob uma nova pasta limitada em
`tests/xcom/` e um validador novo, sem enfraquecer ou monkeypatchar validadores anteriores.

## Fora do escopo

Não implemente T026–T034: nenhum journal durável, emissão/injeção, service invocation/emulation,
lease, alteração de `ProviderComposition`, gateway, Protobuf/gRPC, IPC/TCP, ferramenta externa,
replay, Argus, dashboard, persistência, XDL compiler, adaptador, protocolo, rede ou integração legacy.
Não execute binários legacy ou workloads de produção. Não faça push, deploy, release, PR ou claim de
compatibilidade, certificação, performance produtiva ou maturidade além de protótipo.

## Verificação e aceitação

Crie medidas host-owned para, no mínimo:

- unit/negative tests de clock, mapping e tolerance;
- matriz de permit válido e todos os mismatches, consumo único, nonce e limites;
- matriz completa de transições, expiry/revoke/close, handles stale/foreign e no-mutation após rejeição;
- concorrência determinística para consumo do mesmo permit e operações de sessão;
- lint/static/sanitizer conforme o ambiente offline aceito;
- strict Doxygen e reciprocidade da traceability;
- regressão de todos os validadores X-COM anteriores em seus modos substantivos, sem gate reduzido;
- confirmação de zero itens normais emitidos, pois T025 ainda não possui caminho de estimulação.

Ao terminar, entregue o candidato exato, diff/arquivos, evidências, traceabilidade, uso/custo DeepSeek,
limitações, manutenção e um prompt curto para a próxima sessão. Não aceite nem integre automaticamente:
execute revisão independente Astra XHigh e apresente o bundle ao usuário para decisão explícita.
