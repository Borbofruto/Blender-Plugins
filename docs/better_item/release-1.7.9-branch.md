> Registro anterior da contribuição `release/1.7.9`, commit `de73eaa`. Seu ZIP não é o consolidado atual. Consulte [a entrega consolidada](release-1.7.9.md).

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

Correção: enquanto os canais estão exatamente como a edição linkada anterior os deixou, na mesma referência resolvida, o vetor de antes do gesto continua sendo a fonte da razão. Qualquer mudança externa, troca de links, troca de referência, outro objeto ou limpeza de caches descarta essa memória (máximo de 16 entradas). Quando não há continuidade, BI-T008 continua valendo como antes.

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

## Validação

### Executada no PC Windows x64 da Gabriel, 16/11/2026

Instalador: `addons/better_item.zip`, 99.588 bytes, SHA256 `c053f3663cff7b9a954656c15b3d2de8d66885fb3b7657dba04dae9410de288f`, gerado com `blender --command extension build` (5.3.0) a partir de `git archive` da branch (finais de linha LF, como o ZIP 1.7.8; os 10 módulos inalterados têm o mesmo hash da 1.7.8). `extension validate`: sucesso. `python_source_sha256`: `d1644391d679e3aa8e2315c654879edbfc2413f7b4ad0fa12292661f0d53c88b`.

**Matriz padrão, 23 entradas** (API probe, 21 anteriores e `test_better_item_gestures179.py` em `background`), portáteis oficiais conferidos com o SHA256 oficial, perfis isolados, uma extração por vez:

| Build | Resultado |
| --- | --- |
| 4.2.0, 4.2.23, 4.3.2, 4.4.3, 4.5.16 | 23/23 em cada |
| 5.0.1, 5.1.2, 5.2.4, 5.3.0 | 23/23 em cada |
| 5.3.0 instalado (perfil isolado, `--factory-startup`) | 23/23 |

Total: 230 execuções, 0 falhas, com o ZIP final (após a correção da chave linkada descrita abaixo). Os sete casos do teste novo rodaram em todas as builds (nenhum `skipped`). O teste novo, rodado contra o ZIP 1.7.8 no 5.3.0, **falha** no caso de deriva: `(5, 10, 14,99998951)`. A matriz também havia passado 230/230 no ZIP anterior à correção (`beb561ad…`, commit `dd012cf`).

**Benchmark** (`benchmark_cache_invalidation.py`, mesmo script nos dois ZIPs, processos novos e em sequência, sem outros testes). O lado 1.7.9 foi medido no ZIP anterior à correção da chave linkada; ela altera só `transform_view.edit_component`, que os benchmarks não executam. Foi acrescentado o cenário `cold_first_read`, que limpa todos os caches de runtime antes de cada amostra (mediana de 3); o `cold_seconds` antigo só limpava a inspeção da distribuição.

| Primeira leitura (mediana) | 4.2.23: 1.7.8 | 4.2.23: 1.7.9 | 5.3.0: 1.7.8 | 5.3.0: 1.7.9 |
| --- | ---: | ---: | ---: | ---: |
| Geometry Bounds, 600 | 0,290 s | 0,098 s | 0,379 s | 0,101 s |
| Volume, 600 | 0,419 s | 0,227 s | 0,543 s | 0,258 s |
| Geometry Bounds, 1.500 | 0,733 s | 0,247 s | 1,014 s | 0,254 s |
| Volume, 1.500 | 1,059 s | 0,551 s | 1,443 s | 0,654 s |

Edição de shader usado (invalida a inspeção) segue o mesmo ganho: Geometry/1.500 0,96 → 0,26 s no 5.3.0. Transformação alheia, Origins e sync em Object Mode ficaram iguais (diferenças abaixo de 1 ms). Contagens de inspeção idênticas entre as versões.

**Edit Mode, Normal** (`benchmark_editmode_normal179.py`, estudo `gui_sync` novo, janela real, UV sphere com 130.562 vértices, orientação Normal, `native_refs.sync()` chamado como o timer de 0,2 s):

| | 4.2.23: 1.7.8 | 4.2.23: 1.7.9 | 5.3.0: 1.7.8 | 5.3.0: 1.7.9 |
| --- | ---: | ---: | ---: | ---: |
| Tick ocioso (mediana de 30) | 35,9 ms | 0,041 ms | 46,6 ms | 0,060 ms |
| Varreduras de elementos em 30 ticks | 30 | 0 | 30 | 0 |
| Troca por outro vértice, mesma contagem | 72,5 ms | 70,6 ms | 93,5 ms | 108,1 ms |
| Tick após o intervalo de 2 s | 35,9 ms | 35,8 ms | 44,0 ms | 48,4 ms |

A troca de vértice com a mesma contagem foi detectada nas duas versões (amostra de Normal diferente). Uma varredura completa a cada 2 s continua existindo como rede de proteção. São medições sintéticas, sem limite de aprovação; não são promessa de FPS.

### Problema encontrado na validação e corrigido

**A âncora das edições linkadas não levava em conta a referência.** No patch original, a chave era (objeto, grupo, links). Reprodução (`tests/better_item/results/1.7.9/extra/`): Location linkada em X/Y, Reference/Global, arrastar X até 0, o que dá `(0, 0, 3)`. Trocar a Orientation do objeto para um Frame girado 90° em Z com a mesma origem; a leitura continua `(0, 0, 3)`, então a âncora casava. Digitar X = 1:

- 1.7.8: recusa com BI-T008.
- 1.7.9 antes da correção: aceitava com a razão medida em Global; o objeto ia para world `(-2, 1, 3)`.

Correção (`transform_view._link_reference`): a chave passa a incluir os números da referência resolvida antes da edição: eixos (todos os grupos), origem (Location) e ordem Euler (Rotation). Trocar Frame, orientação ou pivô, ou usar uma referência que se move junto com o alvo, muda a chave; a edição volta a partir dos valores atuais, como na 1.7.8. Com referência fixa, a continuidade do gesto continua valendo. O modo Default não muda (seus valores são os canais nativos). Novo caso `reference_switch` em `test_better_item_gestures179.py`: falha no pacote anterior à correção, na asserção de BI-T008, e passa depois dela.

### Executada antes, em Linux com `bpy` do pip (relatório da sessão que gerou o patch, não repetido aqui)

- `test_better_item_gestures179.py` passa em 4.2.23 e 5.3.0; o caso de deriva falha na 1.7.8.
- Suítes legadas (reg, g1, o1, e2, ui2, x2, l2, q2, q5, p6, b1, new152, m2, n2, p10, q8, q9, q10): saída idêntica entre 1.7.8 e 1.7.9, exceto o caminho impresso. m2 e p10 terminam com traceback, idêntico na 1.7.8; causa não investigada.
- Frescor de cache: 0 resultados velhos em 12 cenários × 3 bases.
- Tempos de Linux citados nas seções acima.

## Não executado

- Passada manual com mouse (checklist abaixo), F9, GPU/backends, macOS/Linux GUI.
- Arrasto físico no painel: os testes chamam o setter da propriedade, como o painel faz a cada passo.

### Checklist manual (mouse)

1. Arrastar com o mouse um campo X linkado de Location, Rotation e Scale atravessando 0, com e sem Ctrl; depois Ctrl+Z e Ctrl+Shift+Z.
2. Digitar valores durante o gesto e cancelar com Esc.
3. Normal em Edit Mode com malha densa: selecionar por clique, por caixa de seleção e trocar de vértice; o eixo deve acompanhar sem atraso perceptível.
4. Dimensions com Geometry Nodes e malha densa: arrasto contínuo do campo.
