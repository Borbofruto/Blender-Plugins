# Better Item 1.7.9 — gestos lineares, leitura fria e fingerprint de Normal

Manutenção sobre `97a676d` (1.7.8), em 16/11/2026. Mínimo preservado: Blender **4.2.0**. Sem funcionalidade nova, alteração de schema, de contrato matemático ou de layout de UI. Esta branch (`release/1.7.9`) não substitui a `main`.

## Triagem dos dois relatórios externos contra o código 1.7.8

Cada ponto foi tratado como hipótese e medido em Blender 4.2.23 e 5.3.0 (pip `bpy`, Linux). Notas e comparações com concorrentes não foram avaliadas como prova.

| Ponto | Resultado |
| --- | --- |
| `native_refs.sync` varrendo objetos; `NodeTree` de shader; inspeção perdida após mover objeto alheio | Já corrigido na 1.7.8 e confirmado: 0 resultados velhos em 12 cenários × 3 bases |
| Getters repetidos do painel Transform (4× por grupo) | **Não procede como problema**: `values()` custa 0,002–0,056 ms; um redesenho completo estimado em 0,4 ms (cadeia de 2 pais com escala não uniforme). Cache por depsgraph seria arriscado (cursor, Frames manuais) |
| `set_dimensions` oblíquo com 2× `to_mesh` por tick | **Não procede**: 1 leitura de geometria e 1 `to_mesh` por tick (4,2 ms com 41 mil vértices) |
| Deriva e falha em eixos linkados durante o arrasto | **Reproduzido e corrigido** (abaixo) |
| Leitura fria cara | **Reproduzido, causa encontrada e corrigida** (abaixo) |
| Assinatura de Normal em seleção densa | **Reproduzido e corrigido** (abaixo) |
| `context` vs `bpy.context` | Não reproduzido como defeito: dentro de `temp_override` os dois coincidem. Sem alteração |
| `as_pointer()` vs `session_uid` | Não reproduzido e não testado especificamente (reutilização de endereço após exclusão). Os caches continuam sendo limpos em atualizações não classificadas. Sem alteração |
| Docstring de `position_roundoff` | Corrigido (somente texto) |
| `placement` usando `_coordinates`/`_geometry_key` privados | Verdadeiro (1 uso), sem efeito em runtime. Fica para uma refatoração futura, fora do escopo |
| `ruff format`, Session, migration.py, camadas | Fora de uma versão de correção: reescreve todas as linhas e invalida as verificações por hash |
| Pie menu, Frame selecionável por gizmo, New Frame com origem, largura dinâmica do texto, modo simples | Funcionalidade/UX: 1.8.x |

## Corrigido

### Edições linkadas contínuas (Location, Rotation, Scale, Dimensions)

Reproduzido na 1.7.8 com Location linkado, Reference e Default:

- Arrasto de X de 1 a 5 em 400 passos, com Y/X = 2 e Z/X = 3: Z terminava em **14,999916** (razão 2,999983). Cada passo relê o valor do armazenamento float32 e multiplica de novo.
- Valor passando por 0: todos os eixos linkados viravam 0 e **todos os passos seguintes falhavam com BI-T008**. Em Rotation linkada, os outros eixos ficavam em 0 para sempre.

Correção: enquanto os canais estão exatamente como a edição linkada anterior os deixou, o vetor de antes do gesto continua sendo a fonte da razão. Qualquer mudança externa, troca de links, outro objeto ou limpeza de caches descarta essa memória (máximo de 16 entradas). Quando não há continuidade, BI-T008 continua valendo como antes.

Resultado nas duas builds: 400 passos terminam em (5, 10, 15) exatos; 0,5 → 0 → −0,05 → −1 produz (−1, −2, −3).

### Leitura fria da inspeção: custo quadrático

O perfil mostrou que 65% da leitura fria de 1.500 objetos estava na verificação BI-M005, que percorria **todas** as instâncias do depsgraph para cada objeto medido (2,25 milhões de iterações). Agora os pais de instância são levantados uma vez por estado avaliado.

| Linux, 5.3.0, 1.500 objetos | 1.7.8 | 1.7.9 |
| --- | ---: | ---: |
| Geometry Bounds, primeira inspeção | 1,59 s | 0,12 s |
| Volume, primeira inspeção | 1,98 s | 0,42 s |
| Geometry Bounds, 600 objetos | 0,15 s | 0,045 s |
| Volume, 600 objetos | 0,26 s | 0,14 s |

O custo também dependia dos objetos não selecionados da cena: 300 selecionados com 5.000 outros custavam 0,62 s; agora 0,023 s. O cache de geometria permanece com 8 entradas, porque ampliá-lo não trouxe ganho consistente.

### Assinatura de Normal em Edit Mode

Com a orientação Normal em uso, o timer de 0,2 s percorria todos os vértices, arestas e faces em Python a cada tick: 5,8 ms com 10 mil vértices, 29 ms com 41 mil, **103 ms com 164 mil** (52% de um núcleo). Agora o fingerprint de elementos é reutilizado até haver evento do depsgraph (seleção por operador emite evento de shading, sem flag de geometria), mudança do conjunto de objetos ou 2 s de intervalo de segurança. Tick ocioso com 164 mil vértices: 0,008 ms; uma passada completa a cada 2 s permanece como rede de proteção para scripts que alterem seleção sem evento.

Verificado: troca de um vértice por outro com a mesma contagem continua detectada.

## Validação executada

- `test_better_item_gestures179.py` (novo): deriva, zero, mudança externa, limite de âncoras, instanciadores adicionados/removidos e fingerprint de Normal. Passa em 4.2.23 e 5.3.0; o caso de deriva **falha na 1.7.8**.
- Suítes legadas (reg, g1, o1, e2, ui2, x2, l2, q2, q5, p6, b1, new152, m2, n2, p10, q8, q9, q10): saída idêntica entre 1.7.8 e 1.7.9 nas duas builds, exceto o caminho impresso. m2 e p10 terminam com traceback, idêntico na 1.7.8; a causa não foi investigada nesta rodada.
- Frescor de cache: 0 resultados velhos em 12 cenários × 3 bases.

## Não executado

- Matriz Windows x64 de 22 testes e as demais builds portáteis (4.2.0, 4.3, 4.4, 4.5, 5.0, 5.1, 5.2): exigem o runner da suíte no PC.
- Passada manual de mouse/F9, Undo/Redo, GPU e a matriz do instalador. `tests/better_item/compatibility/suite.json` ainda fixa o SHA do instalador 1.7.8; o ZIP 1.7.9 não foi gerado nesta branch.
- Arrasto físico no painel (o teste chama o setter da propriedade, como o painel faz a cada passo).
