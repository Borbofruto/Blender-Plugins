# Better Item 1.6.0 — pacote inicial de geometria, orientação e UX

Implementação baseada na 1.5.7. Ambiente executado: Blender 5.2.3 LTS / Windows. A mudança é uma versão de funcionalidade 1.6.0, não uma correção 1.5.x.

## O que entrou

### Distribution: Origins / Geometry Bounds

Os dois modos usam o mesmo campo **Spacing com sinal**. Valor positivo escolhe o sentido positivo dos eixos de movimento; negativo escolhe o sentido negativo. Não há seletor Direction.

Em Geometry Bounds, o módulo de Spacing é a distância física entre extremos projetados dos vértices avaliados. Zero permite limites encostados e usa o sentido positivo. Essa regra é explícita; não depende da direção anterior nem do sinal oculto de um zero IEEE.

O modo Origins conserva os intervalos de origens da versão anterior, inclusive os valores negativos salvos. Quando a referência é Bounding Box Center, Origins conserva a distribuição entre extremos fixos da seleção e deriva os intervalos; nesse caso não existe um Spacing manual usado pela operação.

Geometry Bounds usa mínimos e máximos reais relativos à origem de cada objeto, não metade de Dimensions. Assim, suporta origens deslocadas, modificadores avaliados, malhas compartilhadas, escalas negativas e objetos com rotações diferentes sem alterar a malha ou a pilha de modificadores.

Referência geométrica por Object: o objeto de referência fica parado e o primeiro limite é posicionado depois de sua borda correspondente, respeitando o intervalo. Referência de ponto/Frame manual/cursor/Empty: a primeira borda fica à distância indicada do ponto. Bounding Box Center: o empacotamento parte da borda externa original da seleção no sentido escolhido; a outra extremidade fica livre para se mover.

Com cubos de lado 2, referência no primeiro cubo de origem 0 e Spacing = 0, as origens seguintes ficam em 2 e 4. Spacing = -0.1 coloca os demais do lado negativo, deixando intervalo de 0.1 entre os limites.

A ordem usa as posições iniciais das origens projetadas. Em referência por chave/ponto, preserva a prioridade anterior: lado oposto ao sentido escolhido primeiro, do mais próximo ao mais distante; depois o lado do sentido escolhido. Eixos múltiplos são ordenados independentemente. Origens coincidentes não fornecem ordem inequívoca: a mensagem informa os nomes e eixos a separar. Zero no espaçamento não desabilita essa condição inicial.

O contrato é sobre projeções nos eixos da referência. Não promete contato entre faces arbitrárias, encaixe, eliminação de colisões, descarte de vértices soltos ou uma caixa local de cada objeto. Rotação diferente é entrada válida; não recebe advertência genérica. Instâncias GN precisam estar realizadas. Geometria/transformações que mudam em função do próprio deslocamento são diagnosticadas e a operação é revertida.

### Alignment: Position / Orientation

Position mantém o comportamento anterior. Orientation oferece:

- **Match Reference:** iguala a orientação completa à componente rotacional do referencial.
- **Set Rotation:** aplica somente os componentes Euler selecionados, com ordem Euler explícita. Os componentes desmarcados são planejados a partir da orientação inicial de cada alvo.

As origens mundiais dos objetos selecionados e suas escalas nativas são preservadas. O objeto conhecido que fornece a orientação, quando selecionado, permanece como chave. Pais selecionados são processados antes dos filhos; uma falha em qualquer alvo restaura o lote. Filhos não selecionados seguem seus pais como normalmente ocorre no Blender.

A referência é resolvida uma vez por execução. Não são alteradas as referências nem os hints do painel Transform de cada alvo. Uma Location ainda não configurada não bloqueia Orientation. Bases oblíquas/refletidas usam sua componente rotacional, com nota contextual no painel; não se promete tornar três eixos não ortogonais em uma rotação rígida.

Foi reutilizado o solver de rotação nativa já testado do Transform, com entrada explícita para eixos/ordem da operação. Não há segundo solver nem um novo modificador para fazer rotação.

Não entraram mínimo/máximo/média angular nem alinhamento de um vetor com liberdade de giro residual. Essas operações exigem contratos próprios e não são apresentadas como equivalentes a copiar uma orientação.

### Solver Settings e diagnóstico

Minimum Separation (mm) fica em **Solver Settings**, recolhido por padrão. O parâmetro distingue a ordem das origens e mantém o intervalo mínimo de Origins. Não impede Spacing = 0 em Geometry Bounds.

O painel distingue:

1. **Setup needed / INFO:** seleção de fonte ou outro passo ainda não concluído. Campos dependentes ficam indisponíveis; grupos válidos continuam funcionando.
2. **Operação recusada / WARNING:** razão específica e ação que o usuário pode executar. Sem alerta crítico vermelho por uma limitação ou entrada corrigível.
3. **Falha inesperada / ERROR:** indicação de falha, com informação técnica em Details para suporte.

Foram introduzidos estados explícitos de referência pendente e metadados de severidade/contexto. A causa não é deduzida de qualquer ValueError genérico. O último recurso na fronteira da interface diferencia exceções de domínio de falhas da API, depois que os backends restauram o estado.

Códigos e conteúdo técnico ficam em **Details**, recolhido inicialmente. Mensagens de operações ficam próximas da seção Reference, para não desaparecerem abaixo dos controles. Frame com fonte faltante não apresenta números artificiais como se fossem medidas. Ponteiro vazio não permite provar se a fonte nunca foi escolhida ou se foi removida; a mensagem solicita uma fonte válida sem inventar essa distinção.

## Validação nova

| Bateria | Execução |
|---|---|
| Matriz geométrica | 168 combinações: sete máscaras de eixos; referências giradas e oblíquas; referência de objeto/ponto; duas escalas de unidade; espaçamento zero, positivo e negativo; pais anisotrópicos, escala negativa e malhas compartilhadas |
| Matriz de orientação | 72 lotes / 288 alvos, seis ordens Euler, Match/Set, componentes parciais, referências de Object/Frame e alvos em diferentes modos de armazenamento |
| Exemplos e invariantes | Cubos com tamanhos diferentes, origens deslocadas, Array avaliado, preservação de vértices/escala/rotação na distribuição, fonte geométrica fixa e seleção Bounding Box Center |
| Falhas atômicas | Espaçamento positivo não resolvível, coordenadas grandes, eixos travados, falha em alvo posterior do lote, geometria dependente de posição e referência que acompanha um alvo |
| Hierarquia | Pai e filho selecionados na distribuição; chave filha que precisa compensar a rotação de um pai selecionado; tipos adicionais de objeto para Orientation |
| UX e dados | INFO/WARNING/ERROR; configuração incompleta sem vermelho; ausência de controle Direction; Settings recolhido; Location pendente não bloqueia orientação; componentes de Frame indisponíveis sem zeros artificiais; salvar/reabrir e Undo/Redo |
| Interface real | Sidebar N, Geometry INVOKE lendo Y e Spacing, zero para o lado positivo, valor negativo invertendo o empacotamento, Set Rotation preservando posições, duas chamadas capturando ângulos novos, Solver fechado/aberto, aviso corrigível e Details |

Scripts: `test_better_item_features160.py`, `test_better_item_edge160.py`, `test_better_item_matrix160.py`, `test_better_item_gui160.py`. Resultados em `tests/better_item/results/1.6.0/`.

Também foram executadas as regressões numéricas anteriores, incluindo a matriz de 9.216 casos (6.240 sucessos e 2.976 rejeições verificadas), 192 comparações de rotação com operadores nativos, 630 combinações de arranjo por origens, cache, malhas compartilhadas, referências, grupos indisponíveis, salvaguardas de Geometry Nodes e ausência do runtime de animação.

Os testes antigos de arranjo foram ajustados para aceitar o status **CANCELLED** de uma recusa informativa/aviso, conferindo os mesmos códigos de suporte e a ausência de alterações. Não exigem mais que uma condição corrigível se apresente como RuntimeError crítico.

## Compatibilidade e limites

- Versão declarada mínima continua Blender 5.0; execução desta entrega usou somente 5.2.3 LTS / Windows. Não foi testado em outras versões ou sistemas.
- Em scripts, verificar status CANCELLED. Para distribuição por EXEC_DEFAULT, passar explicitamente `distribution_mode='GEOMETRY'`, `axes` e `spacing`; INVOKE da UI captura os controles do painel.
- Orientações herdadas que não possam ser obtidas como rotação rígida continuam sendo recusadas com reversão. Não se acrescentou cisalhamento de geometria para contornar a hierarquia.
- Os controles de Solver não são uma garantia de precisão física ilimitada. A posição nativa continua float32; espaçamentos que não possam ser representados são rejeitados.
- Animação, novos gizmos, flexibilização de constraints, média angular e resolução automática de dependências móveis ficaram fora desta entrega.

O pacote instalável fica em `addons/better_item-1.6.0.zip`; código e testes seguem separados. Não é necessário importar scripts de teste para instalar a extensão.
