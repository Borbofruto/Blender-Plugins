# Better Item 1.7.5 — matriz inicial de compatibilidade

Auditoria executada em 16/11/2026, Windows x64. O mesmo ZIP foi usado em todas as versões: SHA256 `c88daf4651a80380d3ac5495186340977da3a5c5f86240df189651e79c9a380d`. Os portáteis vieram dos diretórios oficiais e tiveram seus SHA256 conferidos antes da execução. Nenhuma instalação existente, associação de arquivos ou preferência padrão do usuário foi substituída.

## Resultado observado

| Blender | Build | Python / NumPy | Entradas de API/regressão | ZIP habilitado pelo instalador |
| --- | --- | --- | --- | --- |
| 5.3.0 | 02f0899d78e3 | 3.13.13 / 2.3.4 | 19/19 | Sim |
| 5.2.4 | cd5dc428cce1 | 3.13.13 / 2.3.4 | 19/19 | Sim |
| 5.1.2 | ec6e62d40fa9 | 3.13.9 / 2.3.4 | 19/19 | Sim |
| 5.0.1 | a3db93c5b259 | 3.11.13 / 1.26.4 | 19/19 | Sim |
| 4.5.16 | 3f6797307da5 | 3.11.15 / 1.26.4 | 19/19 | Não; mínimo declarado 5.0 |

Cada versão executou 20 entradas: 19 de API/regressão e uma de instalação. Na 4.5, a asserção de instalação verifica a ausência de ativação sob o mínimo 5.0 do manifesto; isso não equivale a instalar o produto com suporte nessa versão. O teste do código na 4.5 foi diagnóstico, por importação controlada. Não foi identificado um rompimento do núcleo matemático entre as versões testadas. A primeira fronteira de uso normal encontrada foi a elegibilidade do pacote, e não uma falha matemática comprovada. Não alteramos o mínimo do manifesto nem afirmamos suporte à 4.5. Versões anteriores a 4.5 não foram testadas nesta primeira matriz; tampouco foi executado o patch inicial 5.0.0.

## O que foi exercitado

- Registro/desregistro; campos RNA; nós/sockets usados pelo add-on; leitura de geometria avaliada; callbacks, timers e busca de referências por Frame/Objeto.
- 256 lotes Endpoint e 140 Offset; 168 lotes geométricos e 72 de orientação; sinais, unidades, âncoras, espelhos, pais e máscaras de eixo.
- Live: 96 lotes e 192 atualizações de referência, cursor e objeto, identidade capturada, ordem estável, preservação transversal e interrupção da sessão.
- Grade de estresse ajustada ao escopo atual: 8.064 combinações por versão, com 5.408 aceitações e 2.656 recusas esperadas/atômicas na grade de referências. Não se deve contar uma recusa prevista como defeito ou como operação aceita. Há também 192 comparações de rotação com operadores nativos, 54 comparações de direção Gimbal, 1.000 edições encadeadas, hierarquias profundas e escalas negativas.
- Precisão de coordenadas grandes e cadeias longas; rejeição de colapsos; locks, drivers e condições não suportadas; preservação da geometria e reversão quando necessário.
- Cache com até 1.500 objetos, dependências indiretas de Geometry Nodes, shape keys, mudança de frame e Undo/Redo. Animação nativa aparece somente como dado de teste do cache; não existe runtime de animação relativa.
- GUI real: timer, invocação nativa, F9, Undo/Redo, exportação dos Frames, G nos eixos exportados, detecção de exclusão nativa e desenho dos painéis sem exceções capturadas.
- Salvar/reabrir em processo novo, incluindo referências retiradas; instalação do ZIP real em repositório local isolado nas versões 5.x. O bootstrap reproduzível também foi testado a partir de uma árvore com a estrutura do repositório.

Os números são cobertura finita. Não significam testar todas as cenas, plataformas, GPUs ou sequências possíveis.

## Duas falhas do executor, separadas do produto

**5.1.2, encerramento após reabrir arquivo.** A primeira execução do estresse completou os onze grupos, mas o processo caiu em `wm_exit_schedule_delayed` ao chamar `wm.quit_blender` sem janela corrente. Um programa sem Better Item reproduziu o mesmo crash. Obtendo uma janela existente e passando-a por `Context.temp_override`, o controle terminou com exit code 0. Corrigimos apenas o launcher e repetimos a matriz completa na 5.1.2: 20 entradas aprovadas. O resultado inicial foi preservado; não foi convertido retrospectivamente em sucesso.

**4.5.16, fixture de Grease Pencil.** O teste tentava criar um objeto com dados da coleção antiga `grease_pencils`. A falha ocorria antes de chamar o add-on. A fixture passou a escolher a coleção pública `grease_pencils_v3` quando disponível e `grease_pencils` nas versões atuais. A regressão corrigida passou na 4.5 e na 5.3. O restante da matriz da 4.5 já havia passado. A síntese acima incorpora essa repetição, explicitamente indicada no JSON.

## Estudo da API e decisões

| Transição | Mudança documentada | Relação com Better Item |
| --- | --- | --- |
| 5.0 | Separação do armazenamento RNA e propriedades customizadas; remoção de APIs legadas e módulos internos | Auditar acesso a propriedades pelo contrato correto. A persistência e os canais exercitados passaram. Não introduzir acesso à memória interna ou bypass de RNA. |
| 5.1 | Python 3.13 e mudanças de ambiente de módulos | O pacote usa bibliotecas incluídas no Blender. Testes com Python 3.11/3.13 e NumPy 1.26/2.x passaram nas versões da tabela. |
| 5.2 | Entradas/saídas de modificadores Geometry Nodes passam a ter propriedades RNA próprias | O fallback de Dimensions edita um grafo de nós e seus valores, não entradas genéricas do modificador pelo formato antigo. Os testes do grafo, propriedade e avaliação passaram nos dois lados dessa transição. |
| 5.3 | Adições de UI, GPU, interoperabilidade e alteração da ordem de `bpy.data.all_ids` | Não usar a ordem dessa coleção como identidade. As capacidades usadas foram sondadas e os fluxos executados passaram. Nenhuma camada de compatibilidade foi adicionada ao runtime para essas novidades. |

A descoberta de orientações customizadas da 1.7.4 dependia de texto de exceção e não era um contrato público estável. Ela foi **removida**, mesmo tendo funcionado no teste inicial da 5.3. Permanecem os operadores públicos de criar/excluir orientações para exportar Frames. Testar uma implementação em várias versões não transforma um comportamento não documentado em API garantida.

A política para próximas atualizações é: consultar as notas oficiais, identificar APIs realmente usadas, congelar o instalador/hash, executar os mesmos oráculos e controles nativos, separar erro de fixture/executor de erro do produto, e só então alterar código ou ampliar a declaração de suporte. Preferir detecção de capacidades públicas a condições por versão quando isso for suficiente. Não adicionar suporte genérico a todas as transformações matematicamente possíveis.

## Limites restantes

Não houve auditoria com arraste físico do mouse, todos os backends gráficos, outros sistemas operacionais, todos os pivôs em Edit Mode ou migração de arquivos entre cada par de versões do Blender. Os round-trips da matriz são feitos dentro de cada versão. As restrições documentadas de constraints, hierarquias não rígidas e precisão continuam válidas. Otimização de Normal, flexibilização de constraints e novas interações continuam fora desta entrega. Sem novas funcionalidades de animação.

Por espaço em disco, a 5.3.0 portátil permanece extraída; as extrações intermediárias foram removidas após os testes. ZIPs verificados, ferramentas e resultados permanecem no workspace e permitem reinstanciar cada ambiente.

## Evidência e reprodução

[Toolkit e instruções](../../tests/better_item/compatibility/README.md), [resultados por versão](../../tests/better_item/results/1.7.5/), [checksums oficiais usados](../../tests/better_item/results/1.7.5/official-downloads.json), [diagnóstico do executor](../../tests/better_item/results/1.7.5/harness-diagnostics.json).

Fontes primárias: [versões oficiais](https://www.blender.org/releases/), [API 5.0](https://developer.blender.org/docs/release_notes/5.0/python_api/), [API 5.1](https://developer.blender.org/docs/release_notes/5.1/python_api/), [API 5.2](https://developer.blender.org/docs/release_notes/5.2/python_api/), [API 5.3](https://developer.blender.org/docs/release_notes/5.3/python_api/). Os resultados da tabela vêm da execução local, não dessas notas.
