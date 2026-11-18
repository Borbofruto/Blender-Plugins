# Better Item — backlog de ideias de UX/UI e design

Documento vivo. Registra ideias conforme surgem; o encaixe em versões segue [roteiro-de-releases.md](roteiro-de-releases.md) e, para a 1.8, [escopo-1.8.md](escopo-1.8.md). Última atualização: 18/11/2026.

> **Nota de 18/11:** a 1.7.10 publicada na `main` é a versão `release/1.7.10-vg`. P1, F6, F7 e F8 estão entregues nela. As menções à branch `claude/better-item-1.7.10-vc` neste documento são históricas.

**Status:** `ideia` · `em discussão` · `desenhada` (comportamento definido, falta implementar) · `entregue` · `decidida` · `descartada`.
**Encaixe:** preenchido só quando a ideia é escolhida para uma versão.

## 1. Base original da 1.8.x

Substituída pelo modelo de releases por tema (ver roteiro). Mantida como referência.

| ID | Item | Encaixe atual |
| --- | --- | --- |
| B1 | Diagnósticos corretos e acionáveis | 1.8, só como auditoria limitada |
| B2 | Legibilidade e clareza dos estados | 1.9 (tema em discussão) |
| B3 | Confiabilidade dos gestos de edição, só falhas reproduzidas | sem release até haver falha reproduzida |
| B4 | Resposta rápida nos caminhos de leitura | sem release até haver medição |

## 2. Decisões de UX

| ID | Ideia | Origem / gatilho | Status | Encaixe |
| --- | --- | --- | --- | --- |
| U1 | **"Nada a fazer" / recusa por precisão.** Quando as coordenadas diferem menos que o limiar: se já estão distribuídos, informar "nada a distribuir"; se o resultado ficaria abaixo do mínimo, recusar como precisão. D002, D003 e G002 parecem o mesmo limite numérico; a tabela de casos confirma ou não. | 16/11. D002, D003, G002 | desenhada (falta texto e tabela) | 1.8, condicional |
| U2 | **Ordem manual em empates.** Diálogo lista só os objetos empatados, com subir/descer, aberto em ordem natural por nome. Por script, a ordem é parâmetro; sem ela, mantém a recusa D002. Ctrl+Z desfaz. | 16/11. D002 | desenhada | 1.8, núcleo (após protótipo) |
| U3 | **Placement por contato geométrico.** Nova base de Placement só de Offset: o contato real entre geometrias define a distância, não a caixa envolvente. Pontos a decidir: (a) espaçamento ao longo do eixo ou perpendicular; (b) sem sobreposição transversal, recusar ou cair para Bounds; (c) um eixo por vez. Exige protótipo de desempenho (paralelogramo, peça em L; 1 mil, 10 mil e 100 mil triângulos). Pendente: a ideia de "aresta com comprimento e ângulo" citada por Gabriel. | 17/11 | em discussão | sem número até o protótipo |

## 2b. Apresentação e precisão

Fonte: `docs/better_item/units-1.7.9.md`, `followup-review-1.7.9.md`.

| ID | Ideia / achado | Status | Encaixe |
| --- | --- | --- | --- |
| P1 | Casas decimais por grupo no painel Transform (5 em Location, Rotation, Dimensions; 3 em Scale). | entregue | 1.7.10 |
| P2 | **Um nome só para o mínimo.** Hoje: "Minimum Separation (mm)", "Minimum (mm)", "Minimum Distance (mm)" e variantes nas mensagens D001. Inventário em `minimum-naming-1.7.9.md`. Identificadores `minimum_distance_mm` e `minimum_mm` não mudam. | desenhada | 1.8, núcleo |
| P3 | **Comunicar a resolução efetiva** (erro de até 0,051 mm num gap de 1 mm a 1 km da origem). | ideia | 1.8, condicional |
| P4 | **Contrato de erro físico admissível.** Muda o contrato; decisão de Gabriel. | em aberto | sem release |

## 2c. Edit Mode e referências a partir de seleção

Base: `docs/better_item/edit-mode-2.0-feasibility.md`.

| ID | Ideia | Status | Encaixe |
| --- | --- | --- | --- |
| E1 | Alinhar e distribuir em Edit Mode. Sequência do estudo: vértices, depois multiobjeto e ilhas, depois arestas e faces. Vértice compartilhado com destinos conflitantes: decidir regra; nunca separar a malha em silêncio. | em discussão | 2.0 (vértices); 2.1+ (resto) |
| E2 | Criar Frame a partir de elementos selecionados (dois vértices dão direção, três dão o plano). Captura antes de vínculo persistente. | ideia | 2.0 |

## 3. Atritos e defeitos

| ID | Situação | Gatilho | Status | Encaixe |
| --- | --- | --- | --- | --- |
| F1 | Empty, câmera ou luz na seleção cancela o Geometry Bounds inteiro | G001 | ideia | fora até decisão de comportamento |
| F2 | Vínculo ligado com valor zero bloqueia a edição vinculada | T008 | ideia | |
| F3 | Objeto bloqueado ou com constraint cancela o lote | T003, T004 | ideia | fora até decisão de comportamento |
| F4 | Modificador Dimensions fora do fim da pilha ou desligado: botão explícito para corrigir, com revalidação do alvo | M002, M004 | desenhada | 1.8, núcleo |
| F5 | Dependências detectadas só depois de aplicar e reverter (são verificações pós-aplicação; detectar antes é recurso novo) | T009, A005, A006, G003, G004, G005, T011 | ideia | tema próprio, depois |
| F6 | Título próprio para BI-F006 | F006 | entregue | 1.7.10 |
| F7 | Malha aberta em Volume mostrava "Complete references" | P003 | entregue | 1.7.10 |
| F8 | `window.scene` sem proteção no observador nativo | — | entregue | 1.7.10 |

## 4. Candidatas depois da 1.8

| ID | Ideia | Encaixe |
| --- | --- | --- |
| C1 | Inicializar Frame a partir de uma fonte (Object Mode) | 1.10 |
| C2 | Ações de acesso rápido | 1.10 (ou 1.9, se o tema da 1.9 mudar para comandos fora do painel) |
| C3 | Selecionar Frame pelo indicador no viewport | 1.10, condicionado ao escopo de viewport |
| C4 | **Comandos fora do painel:** menu de contexto no viewport, atalhos, menu pie, busca F3. Retorno consistente de usuários: tudo depende do painel. Proposta em aberto: virar o tema da 1.9. | decisão de Gabriel depois da 1.8 |

## 5. Fora da primeira implementação da 1.8.x

Arrastar Frames no viewport · snapping próprio · modo simples/avançado · guias de distribuição que medem durante o redesenho · migrar o estado de Transform para a Scene · refactor geral.

## 6. Adiado sem data

`ruff format` · Session · `migration.py` · camadas · gizmo selecionável · largura de texto dinâmica (candidata à 1.9).

## Como registrar uma ideia nova

Uma linha na seção que couber: o que é, de onde veio, status e decisões em aberto. O encaixe só é preenchido quando Gabriel escolhe a versão.
