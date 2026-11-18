# Better Item 1.8 — escopo aprovado

Aprovado em **18/11/2026**. Base: **1.7.10**, commit `f7337d0`. **Fase 1: preparação sem alteração de comportamento.** A aprovação do escopo não antecipa a aprovação da fase 2; protótipo, tabelas e lista B1 serão apresentados antes de implementar.

## Tema

**Quando o Better Item recusa ou não consegue medir, diz o motivo e deixa o usuário resolver.**

Release de diagnóstico e recuperação. Sem mudança estrutural de layout além do necessário para exibir ou acionar a solução. Layout é da 1.9.

## Problema do usuário

- Dois ou mais objetos disputam a mesma posição, o Distribute recusa com BI-D002 e o usuário precisa mover objetos à mão, só para desempatar.
- O mesmo conceito, o mínimo do solver, aparece com quatro nomes diferentes entre propriedade, rótulo, operador e mensagens.
- Hipótese inicial de U1: BI-D002 e BI-D003 teriam a mesma causa numérica. A preparação demonstrou causas distintas; ver a tabela U1 antes de decidir sua entrada.
- Se o modificador de Dimensions está fora do fim da pilha ou desligado, o usuário recebe a instrução, mas precisa corrigir sozinho.

## Entra

### U2 — Ordem manual em empates (núcleo)

Estado atual verificado no fonte 1.7.10: `better_item.distribute.invoke` termina em `execute`; **não abre diálogo próprio**. O método `draw` fornece os campos de redo/F9. O parâmetro `order_override` existe **só** em `endpoint_plan` (usado pela sessão Live). `offset_plan` não o aceita. Portanto U2 exige um parâmetro de ordem no planejamento do Offset, sem alterar a matemática do solver.

Comportamentos verificáveis:

1. **Dado** um Offset (qualquer Placement) que hoje recusa com BI-D002, **quando** o usuário executa Distribute pela interface, **então** abre um diálogo que lista **somente** os objetos empatados (cada grupo separado), em ordem natural por nome.
2. Cada linha tem subir e descer; o primeiro não sobe e o último não desce. Toda ordem possível é válida (teste exaustivo das permutações para N=3 e N=4: posições finais distintas e iguais ao oráculo independente).
3. **OK** distribui usando a ordem escolhida só para o grupo empatado; os demais mantêm a regra atual. Um único passo de Undo desfaz tudo.
4. **Cancelar/Esc** não move nada nem altera o estado salvo.
5. **Por script:** com a ordem como argumento, não há diálogo e a ordem é usada; **sem** ela, a recusa BI-D002 permanece exatamente como hoje (os testes existentes continuam passando sem alteração).
6. Uma ordem que não seja permutação do grupo empatado é recusada sem mover objetos.
7. F9 (redo) reabre o diálogo com a ordem escolhida e produz o mesmo resultado.

U2 é o maior risco técnico da release. O risco não está na matemática, e sim na integração com o Blender:
- diálogo com conteúdo dinâmico (número variável de linhas e grupos);
- persistência da ordem no redo/F9;
- cancelamento sem nenhuma alteração;
- identificação estável dos objetos empatados entre o invoke, o execute e o redo.

**Protótipo de viabilidade antes de implementar**, em 4.2, 4.5 e 5.3, cobrindo os quatro pontos acima. O requisito é preservar uma ordem **válida e reproduzível**; a forma de guardá-la na RNA do operador é consequência do protótipo, não está decidida. Preservar a ordem de declaração das propriedades que a 1.7.7 protegeu. Se o protótipo mostrar que algum dos quatro pontos não é confiável numa das builds, U2 volta para decisão antes de entrar.

Decisões aprovadas:
- **Live:** sessão com empate continua recusando BI-D002, sem diálogo dentro do timer.
- **Endpoint:** empates de distância ao Start ficam fora da 1.8.

### U1 — "Nada a fazer" e recusa por precisão (condicional)

Condicionado à tabela de casos abaixo. Se a tabela mostrar que esses códigos **não** representam o mesmo problema, U1 precisa de outro desenho e sai da 1.8.

Hipótese a verificar: BI-D002 (ordem ambígua nas coordenadas iniciais), BI-D003 (verificação depois de aplicar) e BI-G002 (gap que o Blender não distingue) representariam um mesmo limite numérico. Essa equivalência **não é um fato assumido**; a tabela de casos decide se U1 entra. O desenho: o que já está distribuído é informado como "nada a distribuir"; o que ficaria abaixo do mínimo é recusado como precisão.

**Antes de implementar**, produzir uma tabela de casos reproduzidos: combinação de método, Placement, espaçamento e coordenadas → código e texto atuais → texto desejado. O texto das mensagens ainda não foi definido; sem essa tabela, o item não entra.

Comportamentos mínimos a verificar quando a tabela existir:
1. Seleção já distribuída conforme o espaçamento pedido → mensagem informativa, nenhum objeto movido, nenhum erro.
2. Resultado abaixo do mínimo → recusa que diz que é limite de precisão e o que ajustar, sem movimento parcial.

### P2 — Um nome só para o mínimo (núcleo)

Hoje: "Minimum Separation (mm)" (propriedade da Scene), "Minimum (mm)" (rótulo do painel Solver), "Minimum Distance (mm)" (propriedade do operador) e, nas mensagens BI-D001, "Minimum Distance" ou "Solver minimum separation". Inventário em `minimum-naming-1.7.9.md`.

1. Todo texto visível (rótulo, dica, mensagem) usa o termo escolhido. Prova: busca nos textos visíveis, sem sobrar variante.
2. Os identificadores `minimum_distance_mm` e `minimum_mm`, o armazenamento e a migração **não mudam**. Cenas salvas na 1.7.10 abrem sem alteração.
3. A dica diz que é parâmetro do solver, **não** tolerância de erro físico.

Decisão aprovada: termo único **Minimum Separation**, sem mudança de identificadores.

### F4 — Corrigir o modificador de Dimensions por botão (núcleo)

Hoje BI-M002 (modificador não está no fim da pilha) e BI-M004 (modificador desligado) só instruem. Em M002 a mensagem promete que o addon "não reordena nem duplica".

1. Nas recusas M002 e M004, e só nelas, aparece um botão de correção.
2. O clique move **apenas** o modificador do Better Item para o fim da pilha (M002) ou o liga (M004). Nenhum outro modificador muda. Um passo de Undo.
3. O clique **não** reaplica automaticamente a edição recusada; o usuário repete.
4. M003 (grupo incompatível) e as demais recusas não ganham botão.
5. O texto de M002 deixa de prometer "não reordena" e passa a dizer que só reordena por ação explícita.
6. **Revalidação antes de agir.** O botão guarda a identidade do objeto e do modificador do diagnóstico, não "o objeto ativo". No clique, se o objeto ou o modificador não existir mais, se o modificador não for mais o do Better Item, ou se o estado já não for o que gerou o diagnóstico, o botão não altera nada e informa que o diagnóstico ficou desatualizado. Teste: trocar a seleção, apagar o objeto, apagar o modificador e corrigir manualmente antes do clique; em todos os casos nenhum outro objeto ou modificador muda.

Decisão aprovada: o addon só reordena ou liga o modificador quando a pessoa clica no botão, após revalidação.

### P3 — Resolução efetiva do gap (condicional)

Entra **só** se a regra puder ser definida e testada sem falso positivo: avisar antes de aplicar quando o gap pedido é poucas vezes a resolução de coordenada na distância de trabalho (referência: erro de até 0,051 mm num gap de 1 mm a 1 km da origem, em `units-1.7.9.md`). Precisa fixar o limiar, o oráculo e onde o aviso aparece. Sem isso, fica para depois.

### B1 — Diagnósticos corretos (só como auditoria)

B1 não entra como item aberto. Entra como **auditoria com saída verificável**:

1. Tabela de todos os códigos BI-* da 1.7.10: onde é lançado, gatilho, classe (configuração incompleta, geometria incompatível, recusa matemática, falha inesperada) e se o texto diz o que fazer.
2. Só entram na 1.8 os desvios **reproduzidos**, como foi o do Volume em malha aberta na 1.7.10. Cada um com teste que falha na 1.7.10 e passa na 1.8.
3. Um desvio sem reprodução vai para o backlog, não para esta release.

**Limite operacional:**
- A auditoria é entregue como tabela **antes** de qualquer correção dela, e Gabriel aprova a lista do que entra.
- Só entram desvios reproduzidos cuja correção é texto ou ação de diagnóstico. Desvio que exija mudar regra do produto, solver ou contrato vai para o backlog, mesmo reproduzido.
- A auditoria não bloqueia U2, P2 e F4. Se não terminar a tempo, a 1.8 sai sem correções de B1, e a tabela segue para a release seguinte.

Observação do levantamento: o código BI-D001 é lançado em 12 pontos, de quatro arquivos, para causas diferentes (escala da cena inválida, espaçamento zero ou abaixo do mínimo, mínimo não positivo, espaçamento não finito). As mensagens são corretas uma a uma; o que falha é o nome do mínimo (P2). Trocar ou dividir códigos é decisão separada e **não** está proposta.

## Fica de fora

| Item | Motivo | Onde entra |
| --- | --- | --- |
| F5 (detectar dependências antes de aplicar) | Os sete códigos (T009, A005, A006, G003, G004, G005, T011) são verificações **depois** da aplicação, seguidas de reversão; as mensagens já orientam. Detectar antes é análise nova de dependências, ou seja, recurso. | Tema próprio, depois |
| F1 (empty, câmera ou luz cancelando Geometry Bounds) | Muda a regra do produto. | Depende de decisão |
| F3 (objeto bloqueado ou com constraint cancelando o lote) | Muda a regra do produto. | Depende de decisão |
| B2 e qualquer reorganização de layout | Tema da 1.9. | 1.9 |
| C1, C2, C3 | Tema da 1.10. | 1.10 |
| Gestos (B3) e responsividade (B4) | Sem falha reproduzida nem medição. | Patch, se surgir algo objetivo |
| U3, Edit Mode, P4 | Outros temas. | Ver roteiro |

## Pronto quando

- Todos os comportamentos acima têm teste automatizado com oráculo independente, e os testes de U2 passam pela invocação real (diálogo, Esc, redo) além do planejamento.
- Cada correção de B1 tem teste que falha na 1.7.10.
- Recusa continua sem efeito parcial: nenhum objeto se move quando a operação é recusada.
- O gate de publicação existente passa, com a matriz completa nas nove builds do Windows sobre o **ZIP final** e resultados registrados por SHA.
- Do [checklist manual](../manual-publication-checklist.md): Esc, Undo/Redo e F9 no diálogo novo. Digitação com separadores por idioma segue pendente da 1.7.10 e **não** pode ser declarada testada por setter.
- Limites declarados no relatório, sem apresentar evidência de outra versão como desta.

## Texto público previsto (não publicado na fase 1)

> Quando o Better Item recusa ou não consegue medir, diz o motivo e deixa o usuário resolver.
> Resolva empates de ordem na distribuição Offset por um diálogo.
> Use Minimum Separation como nome único do parâmetro de separação.
> Corrija o estado do modificador de Dimensions por ação explícita.

## Fases e ponto de parada

### Fase 1 — preparação autorizada

- Integrar este planejamento na `release/1.8`, criada da 1.7.10.
- Atualizar contexto, continuidade e encaixes do backlog.
- Executar protótipo U2 descartável fora do addon em portáteis 4.2, 4.5 e 5.3: diálogo dinâmico, ordem no redo/F9, cancelamento e identidade estável.
- Entregar tabela U1 (método, Placement, espaçamento, coordenadas, diagnóstico atual e texto proposto), auditoria B1 de todos os códigos e tabela P3 (limiar, oráculo e local do aviso, ou justificativa de inviabilidade sem falso positivo).
- Apresentar resultados e lista proposta de correções B1. **Parar e aguardar aprovação.**

### Fase 2 — não autorizada nesta etapa

Ordem sugerida: P2 → F4 → U2. U1 e P3 só entram mediante aprovação específica após as tabelas. B1 só recebe a lista reproduzida e aprovada, dentro do limite operacional acima.

Nenhum teste usa o Blender instalado: somente portáteis e perfis isolados. ZIP, manifesto e comportamento do addon permanecem na 1.7.10 durante a preparação.

**Núcleo:** U2, P2, F4. **Condicional:** U1 (tabela), P3 (regra sem falso positivo). **Auditoria limitada:** B1. U1 e P3 só entram se terminarem com uma explicação e uma ação possível para o usuário.

## Resultado da fase 1

Preparação concluída: [protótipo, três tabelas e lista B1 proposta](fase-1-resultados.md). U2 viável nos casos ensaiados em 4.2.0/4.5.16/5.3.0; unificação U1 e aviso simples P3 não recomendados. Aguardam decisão: quatro correções B1 e eventual U1 menor. **Fase 2 não iniciada.**
