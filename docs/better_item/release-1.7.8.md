# Better Item 1.7.8 — primeira rodada de otimização de cache

Manutenção sobre `e8f5ad69f42cb8e8aad308956c34bb352e8300d6` (1.7.7), em 16/11/2026. Mínimo preservado: Blender **4.2.0**. Sem novas funcionalidades, alteração de schema ou refatoração geral.

## O que foi investigado

Gabriel trouxe dois relatórios externos sobre a 1.7.6. Eles foram tratados como análises a verificar, não como instruções de implementação. O segundo declarou ter recebido código parcial, inclusive `__init__.py` truncado, e não teve acesso aos testes completos. A afirmação de ausência de testes não descreve o repositório, que já possui runner, testes de dependências, GUI real e resultados versionados. Não foi reconstruída essa infraestrutura.

As notas/scorecards não constituem prova de correção, e as verificações numéricas finitas do produto não são uma demonstração formal de todos os estados do Blender. As comparações com concorrentes e sugestões de UI, migração de schema, classes Session, troca geral de identidade e formatação global não foram adotadas nesta etapa. Endpoint e changelog já estavam corrigidos na 1.7.7.

Foram priorizados três caminhos identificáveis no código e confirmados por instrumentação: perda da inspeção após transformar objeto alheio; busca dos tipos de referência de todos os objetos pelo timer em Object Mode; busca de dependentes de Geometry Nodes acionada por NodeTree de shader. Os relatórios originais não foram republicados integralmente; nomes e fingerprints constam no [snapshot](handoff-1.7.8.json).

## Mudanças pequenas, com contratos preservados

### Inspeção de espaçamento

Cada uma das no máximo quatro entradas guarda o resultado e um conjunto imutável de identidades numéricas dos alvos e âncoras diretas. Um lote de updates **exclusivamente de transformação de objetos, sem atualização geométrica**, descarta somente entradas que incluem esses objetos. Os pontos/eixos resolvidos de referências continuam na chave, incluindo fontes indiretas de Frame e cursor. O conjunto de dependências é criado somente numa leitura fria, reutilizando as identidades já calculadas para a chave.

Geometria, malha, shape keys, node trees, coleções, outros dados e eventos não classificados continuam invalidando conservadoramente. Não se tentou construir um segundo Dependency Graph no Python. A revisão geométrica global continua na chave; uma atualização geométrica alheia ainda pode provocar nova inspeção. Undo/Redo/load/frame/unregister continuam limpando os estados transitórios. Nenhum wrapper RNA foi adicionado ao estado duradouro do cache.

Aplicar distribuição continua planejando e verificando independentemente desse resultado de apresentação. Uma regressão substitui a inspeção por uma função que falha, aplica a distribuição e confere as posições, para garantir essa separação.

### Sincronização nativa

`native_refs.sync()` só consulta `_source_names(scene)` fora de Object Mode, porque a amostra de Normal de seleção não é consumida em Object Mode. O timer de 0,2 s, migrações, reconhecimento de exclusão nativa, publicação de Frames e contextos de janela permanecem. O teste verifica publicação e preservação da orientação nativa em Object Mode e atualização de Normal numa seleção BMesh em Edit Mode. Isso mantém uma captura já existente; não implementa alvos de edição de malha no produto.

Substituir o timer inteiro por eventos não foi necessário nem demonstrado como equivalente: remoção de orientação nativa e contexto de viewport também fazem parte de sua responsabilidade.

### Invalidação de geometria

Somente `GeometryNodeTree` provoca a busca por modificadores GN e grupos aninhados. Shader/compositor não iniciam essa busca por pertencerem à classe base NodeTree. Se os caches de vértices e projeção já estiverem vazios, não há entrada deles a remover e a busca pode ser pulada. **A revisão geométrica avança antes dessa saída**, pois Placement e Live também a utilizam, mesmo sem arrays armazenados.

Não se ignoram flags geométricas dos objetos resultantes de um shader. A documentação pública distingue os tipos de árvore e os tipos de update; os eventos reais foram medidos no executável, em vez de inferidos pelo nome da edição. [GeometryNodeTree 4.2](https://docs.blender.org/api/4.2/bpy.types.GeometryNodeTree.html), [índice de DepsgraphUpdate 4.2](https://docs.blender.org/api/4.2/genindex-D.html).

## Medição nova antes/depois

Mesmo benchmark, mesma máquina Windows x64, processos novos e perfis isolados, sem processos de teste concorrentes. A baseline é o ZIP imutável **1.7.7**, medido novamente nesta sessão; não são tempos históricos reaproveitados. O lado posterior usa o ZIP final **1.7.8**. A execução usa o runner existente, modo gui_sync.

O cenário tem 1.502 objetos: 1.500 cubos compartilhando uma Mesh, um objeto-modelo com GN e um Empty independente. São medidas seleções de 600 e 1.500 objetos, Origins/Geometry Bounds/Volume, sem mudança, após mover o Empty e após alterar um material realmente usado pela geometria. Cada evento tem três amostras; a tabela apresenta a mediana de **update do Blender + chamada da inspeção**. Contadores registram inspeções completas e tipos/flags de IDs avaliados.

| Blender | Selecionados | Placement | Empty alheio, 1.7.7 | Empty alheio, 1.7.8 |
| --- | ---: | --- | ---: | ---: |
| 4.2.23 | 600 | Geometry Bounds | 242,25 ms | 1,62 ms |
| 4.2.23 | 600 | Volume | 330,20 ms | 1,61 ms |
| 4.2.23 | 1.500 | Geometry Bounds | 593,41 ms | 2,15 ms |
| 4.2.23 | 1.500 | Volume | 822,59 ms | 2,18 ms |
| 5.3.0 | 600 | Geometry Bounds | 306,82 ms | 2,58 ms |
| 5.3.0 | 600 | Volume | 420,59 ms | 2,85 ms |
| 5.3.0 | 1.500 | Geometry Bounds | 733,57 ms | 3,69 ms |
| 5.3.0 | 1.500 | Volume | 1.041,32 ms | 3,06 ms |

Em todos esses casos, a baseline realizou **3 inspeções completas em 3 movimentos**; a 1.7.8 realizou **zero**, mantendo o mesmo resultado. Origins também preservou o cache. As leituras sem mudança não fizeram inspeções completas nos dois lados. Isso é redução de invalidação desnecessária, não aceleração equivalente de uma medição fria.

Em 30 chamadas explícitas de sync em contexto GUI, com 1.502 objetos e Object Mode, as buscas de fontes caíram de **30 para zero**. A mediana da chamada passou de 0,696 para 0,016 ms na 4.2.23 e de 0,804 para 0,022 ms na 5.3.0. Isso mede o corpo do callback, não a frequência efetiva de agendamento ou o FPS do viewport.

### O caso de shader que continua caro

O benchmark inicialmente usava material sem usuários, que não representava o problema. A fixture foi corrigida para usar o material na Mesh compartilhada, e a comparação final usa essa mesma fixture nos dois lados.

Com material utilizado, o Blender também emitiu updates de geometria para os objetos usuários. A busca por NodeTree de shader caiu de três chamadas de `_tree_matches` para zero, mas a inspeção continuou sendo refeita três vezes, deliberadamente. Em seleções grandes, o custo geométrico continua relevante. Ignorar o shader ou `is_updated_shading` sem considerar os demais IDs/flags seria uma otimização incorreta.

O ganho documentado não se estende a todo update ou malha densa. Medições frias, cache de centroides, extração/triangulação e as chaves O(n) ainda precisam de perfil. Não foram impostos limites arbitrários de objetos nem inserido um cache global de Transform baseado apenas em depsgraph/revisão: translação, cursor e valores manuais de Frames podem mudar sem incrementar a revisão geométrica.

## Validação do ZIP final

| Build Windows x64 | Matriz atual | Benchmark opt-in |
| --- | --- | --- |
| 4.2.23 LTS / `d0cbe84903e8` | **22/22** | Passou; comparação nova com 1.7.7 |
| 5.3.0 / `02f0899d78e3` | **22/22** | Passou; comparação nova com 1.7.7 |

A matriz acrescenta `test_cache_invalidation.py` às 21 entradas da 1.7.7. As regressões anteriores de precisão, geometria, dependências externas de GN, shape keys, Live, Endpoint direto, UI, Undo/Redo, persistência e instalação foram repetidas. O novo teste confere os cinco Placements, retenção em transformação alheia, atualização de alvos/pais/âncoras, Frames indiretos, cursor, aplicação independente da inspeção, revisão com arrays vazios, shader-only, exportação de Frame, Normal de seleção e limpeza em Undo. Seus critérios são funcionais e contadores, não um limite de tempo dependente de máquina.

Resultados separados: [matriz](../../tests/better_item/results/1.7.8/matrix/), [baseline medida agora](../../tests/better_item/results/1.7.8/benchmark/before-1.7.7/), [benchmark posterior](../../tests/better_item/results/1.7.8/benchmark/after-1.7.8/), [comparação estruturada](../../tests/better_item/results/1.7.8/comparison.json). Os resultados históricos 1.7.6/1.7.7 permanecem intactos. Os candidatos intermediários não são a aceitação do ZIP final.

SHA256 do instalador: `369fb55c5eb153f6c805d552da7bf3b3c068b8ee046aba416d3acdc75335fa61`. Apenas três módulos Python mudaram: `distribution.py`, `native_refs.py` e `transform_view.py`. Os outros 12 permanecem byte a byte iguais à 1.7.7. Integridade, AST, metadados e paridade do ZIP com as fontes e os blobs Git foram conferidos; validação e instalação nativas passaram nas duas builds.

## Continuidade e limites

1. Perfilar leituras frias por custo de geometria, `to_mesh`, triangulação, verificação de volume e reconstrução dos representantes. Separar custo da avaliação do Blender, da inspeção e do draw.
2. Medir a repetição de resolução/SVD/inversa nos getters Transform e as assinaturas de Normal em seleção densa antes de cachear esses caminhos. Uma chave incompleta pode deixar a UI rápida e errada.
3. Manter conservadora a invalidação geométrica até haver provas de dependências e resultados frescos em modificadores, shape keys, GN aninhado, fontes indiretas e mudanças de contexto.
4. Fazer a passada humana completa de publicação. Automação GUI não cobre todos os gestos físicos de mouse/F9.

Não foram repetidas a build inicial 4.2.0, as demais builds históricas, outras plataformas ou o estudo independente de Edit Mode. Mínimo 4.2.0, schema, migração, semântica de Frames, validações matemáticas e rollback foram preservados. Animação e Edit Mode 2.0 continuam fora desta entrega.
