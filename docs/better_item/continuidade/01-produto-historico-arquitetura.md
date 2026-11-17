# Produto, histórico, arquitetura e persistência

[Índice](README.md) · [Manual integral](../CONTINUIDADE-IA.md)

> Leia primeiro [Contexto atual](../CONTEXTO-ATUAL.md). Este capítulo é histórico; não representa sozinho o estado vigente.

Base: Better Item 1.7.3, commit `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.

Gerado de CONTINUIDADE-IA.md, SHA-256 `3aa559e3c3679f3a3488d2f82041f1a0c7e7638313a53f9794d93abea316b928`. Não editar este capítulo isoladamente; altere o manual integral e execute `gerar.py`.

<a id="s01"></a>
## 1. Como assumir o projeto

### 1.1. A sequência correta

Antes de editar código:

1. Leia a solicitação atual do usuário e identifique o resultado esperado, não apenas o nome de uma função.
2. Confirme a versão em `src/better_item/blender_manifest.toml` e o commit em que está trabalhando.
3. Leia as seções de escopo, referenciais, persistência, Live e testes deste documento.
4. Abra o módulo que resolve o comportamento e seus chamadores. Não deduza o comportamento apenas pela UI.
5. Reproduza o caso em uma cena sintética mínima. Registre unidade, pais, deltas, seleção, referências, modificadores e modo do Blender.
6. Separe defeito, limitação deliberada, informação incompleta e nova solicitação de produto.
7. Faça a menor mudança verificável que respeite o contrato vigente.
8. Teste resultado e efeitos colaterais; em seguida teste o ZIP real, se a entrega alterar o runtime.

Não comece reorganizando os módulos para deixá-los parecidos com uma arquitetura de sua preferência. Existem nomes e campos legados que continuam presentes para preservar arquivos `.blend`. Uma aparente redundância pode ser compatibilidade de dados.

### 1.2. Classifique a evidência

Use estas categorias nos relatórios:

| Categoria | Significado |
|---|---|
| Observado no código | A implementação possui determinada condição, caminho ou estrutura. Não prova que todas as situações de execução funcionem. |
| Reproduzido | Um caso executado demonstrou o problema ou o resultado. Informe ambiente e condições. |
| Validado por teste | Uma propriedade foi verificada por um teste identificado, com saída atual e escopo finito. |
| Registro histórico | Uma entrega anterior relata uma verificação. Não significa que você a repetiu agora. |
| Hipótese / risco | Há motivo técnico para investigar, mas não há reprodução suficiente para declarar um bug. |
| Decisão de produto | Comportamento escolhido pelo usuário; não é uma deficiência por não cobrir outro fluxo. |

Não converta feedback de outra IA em verdade automaticamente. Algumas críticas anteriores acertaram defeitos numéricos importantes; outras propunham funcionalidades fora do escopo ou usavam expectativas que já haviam sido alteradas.

### 1.3. O que este manual não promete

Ele não afirma que todos os casos matemáticos do Blender foram resolvidos. Não certifica compatibilidade com todas as versões declaradas no manifesto. Não transforma testes automatizados de UI em uma auditoria manual completa de mouse, teclado e experiência comercial. Não contém transcrição literal de toda a conversa nem de todos os arquivos temporários enviados pelo usuário.

Ele consolida decisões da conversa, implementação auditada, relatórios persistidos e estratégias efetivamente utilizadas. Quando não há registro suficiente, a lacuna é indicada.

<a id="s02"></a>
## 2. Identidade, escopo e decisões do usuário

### 2.1. Definição operacional

**Better Item amplia a leitura, a edição numérica e a reutilização de referenciais espaciais no Blender.** O produto combina um painel Transform, Reference Frames e ferramentas de alinhamento/distribuição. Sua proposta não é substituir todas as ferramentas nativas.

O usuário trabalha com precisão espacial, peças, dimensões e organização técnica. A prioridade é previsibilidade, clareza de referência, preservação de dados e diagnóstico útil. A aproximação visual com o painel Item nativo é intencional.

### 2.2. Regras de produto consolidadas

- Interface do add-on em inglês, usando nomes familiares do Blender.
- Ordem dos painéis: **Reference Frames → Transform → Align and Distribute**.
- Dentro de Reference: **Location antes de Orientation**.
- Ícone de posição junto à categoria Location; ícone de Gimbal junto a Orientation.
- Campos dependentes de Object/Frame/Name ficam indentados, com ramificação visual. Não duplicar ícones de categoria nos rótulos filhos.
- Reference pode usar **Individual** — origem e orientação independentes — ou **Frame**, reunindo os dois componentes.
- Frame é um pacote de dois referenciais independentes, não uma relação de parentesco.
- Transform edita o objeto ativo; operações de seleção ficam em Align/Distribute ou nas ferramentas nativas.
- Trocar a referência muda a leitura, não o objeto.
- Escala nativa não deve ser apresentada como uma escala universal em qualquer base arbitrária.
- Nenhum seletor extra de direção na distribuição: o sinal de Spacing define o sentido.
- Geometry Bounds está disponível em Offset; Endpoint atual distribui pontos.
- O instalador continua sendo **`addons/better_item.zip`**. Atualizações substituem esse arquivo.

### 2.3. Animação está fora do produto atual

Houve um protótipo de animação relativa. O usuário rejeitou sua manutenção no escopo porque a dependência de um add-on para preservar animações aumentava o risco e a complexidade sem benefício suficiente para a proposta principal.

Não reintroduza inserção de keyframes, criação de drivers, bake de trajetórias ou um runtime de animação relativa como uma melhoria implícita. O protótipo foi preservado em `archive/better_item-animation-1.5.1/`, não no instalador atual.

Existem leituras de dados avaliados que podem estar afetados por animação nativa, proteções contra drivers e invalidação de cache em mudanças de frame. Isso não significa autoria ou gerenciamento de animação. O Live de distribuição é uma sessão temporária de edição: termina em mudanças de frame/render e não grava um vínculo de distribuição no arquivo.

### 2.4. Decisões que não devem ser revertidas sem discussão

- Não criar outro sistema completo de pivôs/manipuladores para competir com o viewport.
- Não adicionar uma opção genérica de “pegar o pivô/orientação atualmente selecionado na viewport” como atalho redundante de Reference. Isso foi explicitamente rejeitado.
- **View** como orientação nativa e **exportar um Frame para uma orientação nativa** são capacidades diferentes daquele atalho rejeitado. Não as remova por confusão de nomes.
- Não recolocar um Local autocentrado que lê sempre zero como solução para a leitura nativa. **Default / Local** significa canais nativos do objeto, não usar o próprio objeto como base móvel.
- Não recriar Parent como opção visível apenas para selecionar indiretamente um objeto que já pode ser escolhido por Object. A leitura nativa foi atendida por Default / Local; campos Parent legados podem continuar necessários para migração.
- Não acrescentar recursos comerciais, Lite/Pro, novos atalhos ou novas operações apenas para uma demonstração.
- Não flexibilizar constraints indiscriminadamente para fazer uma operação “passar”.

### 2.5. Forma de colaborar com Gabriel

Explique o resultado e o motivo técnico com franqueza. Ele prefere correção a concordância. Quando uma premissa estiver errada, mantenha a distinção relevante: um centroide é um termo matemático válido, por exemplo, mas o rótulo familiar do Blender é melhor na UI.

Não implemente todas as possibilidades citadas em uma discussão exploratória. Identifique o pacote acordado. Também não peça autorização para cada detalhe reversível já contido no pedido. Antes de alterar armazenamento, semântica ou escopo, entenda qual problema está sendo resolvido.

<a id="s03"></a>
## 3. Histórico de produção e mudanças de direção

### 3.1. Origem da conversa e separação dos projetos

A conversa começou com modificações em **Export Paper Model**: PDF, cotas em milímetros, escala, orientação de peças, tolerâncias e extração de chapas. Esse projeto continua no mesmo repositório, mas é outro add-on. Better Item nasceu depois como uma ferramenta nova de transformação e referenciais.

Não atribua ao Better Item a arquitetura, os operadores ou a licença de um fork de Paper Model por associação. Também não altere o exportador de papel ao preparar uma entrega do Better Item.

### 3.2. Linha de evolução consolidada

As etapas iniciais são reconstruídas da conversa e dos registros, sem inventar datas ou versões exatas onde o histórico não foi auditado.

| Etapa | Problema e direção tomada |
|---|---|
| Transform proporcional inicial | Criar painel parecido com Item, com vínculos XYZ para Location, Rotation, Scale e Dimensions; alinhar/distribuir origens. |
| Referenciais arbitrários | Separar orientação dos eixos da posição do pivô; permitir referências globais, objetos e Frames. Evitar tratar orientação como pivot point. |
| Painel único de leitura/edição | Uma versão intermediária apresentou campos incrementais e botões Apply separados dos canais nativos. O usuário rejeitou a UI. A solução foi uma única visão que lê e edita segundo a referência escolhida. |
| Frames independentes | Posição e orientação passaram a ter fontes próprias. Criar um Frame não exige escolher um único objeto fonte para ambos. Aplicar um componente transforma seu resultado em dado manual independente. |
| Integração nativa | Exportar eixos de Frame como custom transform orientation para G/R; acompanhar alteração, renomeação e remoção pelo menu nativo. |
| 1.4.x | Correções de rotação com zeros, escala negativa, deltas, travas e pais, tipos sem geometria, enumerações de Frames removidos e falsos erros de precisão. Ver registro histórico e revisão 1.4.2 nos testes. |
| 1.5.1 arquivada | Protótipo de animação relativa e suas proteções. Não é a base funcional a retomar. |
| 1.5.2 | Retirada do runtime de animação; Default / Local, hierarquias/Parent Inverse e correções de precisão em faixas de coordenadas. |
| 1.5.3 | Grupos indisponíveis, validação de canais/tipos e refinamento de leitura/UI. |
| 1.5.4 | Dimensions como extensão física projetada em direções unitárias; caches de geometria e testes de dependências indiretas. |
| 1.5.5 | Limpeza de legado e robustez do estágio afim: identificar modificador próprio em toda a pilha, não duplicar/reordenar silenciosamente, preservar dados antigos de autoria sem administrá-los. |
| 1.5.6 / 1.5.7 | Zeros relativos, proporções explosivas, condicionamento, validação de matrizes, integridade de Geometry Nodes, regressões amplas e revisão crítica de feedbacks. Consulte os relatórios, não apenas a numeração. |
| 1.6.0 | Geometry Bounds em distribuição Offset, alinhamento de orientação Match Reference/Set Rotation, Solver Settings recolhido e diagnósticos por gravidade. |
| 1.6.1 | Revisão de manutenção, arranjo e distinção entre defeitos e limites deliberados. |
| 1.6.2 / 1.6.3 | Hierarquia visual das referências, Location antes de Orientation e ícone de Gimbal. O relatório de UI 1.6.2 e o histórico Git complementam essa etapa. |
| 1.7.0 | Offset/Endpoint, dois caminhos para Endpoint, novas bases de ponto, inspeção de espaçamento e sessão Live inicialmente transacional. Naquela versão havia Endpoint por intervalos geométricos. |
| 1.7.1 | Zero conserva último sentido; Offset deixa de alinhar eixos desmarcados; Live vira checkbox sem Confirm/Cancel na UI. |
| 1.7.2 | Verificação geométrica passa a incluir arredondamento das coordenadas mundiais; cache da inspeção elimina recomputação a cada redraw. |
| **1.7.3** | **Endpoint passa a distribuir apenas pontos. Placement é guardado por método. Nomes Center of Mass. Live acompanha referências externas e mantém alvos/Active capturados após trocar seleção.** |

### 3.3. Exemplos de ideias abandonadas que explicam o código

O runtime ainda contém identificadores como `VIEWPORT`, `LOCAL`, `PARENT`, `MATCH` e `arrange_on_axis` em caminhos de compatibilidade. Isso não autoriza recolocá-los na interface. Da mesma forma, BEGIN/CONFIRM/CANCEL existe como API legada, embora o fluxo atual seja um checkbox.

Há relatórios históricos de 320 lotes de Endpoint porque a matriz incluía Geometry Bounds. A matriz atual tem 256 lotes de Endpoint por pontos. A redução corresponde à retirada de uma combinação de produto, não a uma regressão escondida na contagem.

O usuário propôs benchmark de outros add-ons CAD/espaciais. Não há, no material auditado, um estudo comparativo concluído que permita atribuir a implementação a um concorrente específico. Não invente esse benchmark. O aproveitamento verificável de soluções existentes foi principalmente o das ferramentas e APIs nativas do Blender, além de NumPy e mathutils.

<a id="s04"></a>
## 4. Repositório, instalador e fontes de verdade

### 4.1. Estrutura relevante

```text
Blender-Plugins/
  addons/better_item.zip             # instalador estável
  src/better_item/                   # runtime e manual do usuário
  tests/better_item/                 # scripts de teste, fora do instalador
    results/1.7.3/                   # evidências da entrega
  docs/better_item/                  # revisões e relatórios históricos
  dist/SHA256SUMS                    # checksum do instalador
  archive/better_item-animation-1.5.1/# protótipo retirado
```

O ZIP do repositório inteiro não é o instalador do add-on. O pacote de extensão contém `blender_manifest.toml`, `__init__.py` e os demais arquivos de runtime na raiz apropriada do pacote. Já para import Python no teste, `src/better_item` é um pacote dentro de um diretório pai `src`.

### 4.2. Identificação da entrega auditada

- Commit: `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.
- Versão do manifesto: `1.7.3`.
- Tamanho registrado do ZIP: `95533` bytes.
- SHA-256 do ZIP: `151bf9ccf0d9f780647130301aeed7eb02bda437cb3db0fa0a348928fced2fa8`.
- Blob Git do ZIP: `6441b7e2a74c8d6728ee2b498353deda3e5c723d`.
- Última implementação verificada em Blender 5.2.3 LTS/Windows; `blender_version_min = "5.0.0"` é declaração de manifesto, não teste em todas as versões a partir dela.

O [snapshot de continuidade](../handoff-1.7.3.json) acompanha este manual com inventário e hashes. Um commit posterior apenas de documentação pode mudar `main` sem mudar essa versão do runtime ou esse ZIP.

### 4.3. O ambiente local usado durante a produção

O diretório de trabalho utilizado nas últimas entregas foi `C:/Users/gabri/Documents/Codex/better-item-170`. O nome **não** indica que seu conteúdo permaneceu na 1.7.0. Ali existem staging folders `publish173`, `zip_check173`, testes, logs e scripts temporários de patch/build.

Esses diretórios não são a organização canônica para um novo mantenedor. A publicação foi feita por Git Data API, não a partir de um checkout Git local convencional. Uma nova IA deve preferir um checkout limpo do repositório e confirmar `git status`, origem e commit.

Não execute cegamente `build173.py` ou scripts `patch*.py` encontrados naquele workspace: eles refletem operações já realizadas, caminhos absolutos e listas de arquivos de uma entrega específica. Rodar um patch histórico duas vezes pode duplicar ou corromper alterações.

<a id="s05"></a>
## 5. Mapa dos módulos e fluxo de dados

O runtime auditado tem **15 módulos Python**. A separação importante é entre resolver uma referência, medir um estado, planejar uma operação e efetivar uma alteração.

| Módulo | Responsabilidade e pontos de entrada |
|---|---|
| `__init__.py` | Registro, propriedades RNA, callbacks, operadores, painéis e ciclo de vida. `_component`, `_linked_rows`, `register`, `unregister`, `_clear_runtime`. |
| `math_core.py` | Regras sem bpy: erros de domínio, vetores, vínculos proporcionais e planejadores simples de origens. `linked_values`, `align_positions`, `distribute_positions`. |
| `references.py` | Opções visíveis, mapeamento entre campos legados e semântica atual, resolução e UI compartilhada. `axes`, `origin`, `location_kind`, `choice_property`, `draw_component`, `migrate`. |
| `frames.py` | Dados dos Frames, componentes independentes, recursão/ciclos, Apply, criação, escolhas e indicadores. `frame_origin`, `frame_axes`, `set_position`, `apply_reference`, `clear_missing_choices`. |
| `orientation.py` | Rotação de canais, deltas, herança e remoção de sinais de escala da interpretação rotacional. `rotation`, `local_rotation`, `inherited_rotation`. |
| `native_refs.py` | Pivôs/orientações nativas e sincronização de custom orientations. `view_context`, `checked`, `orientation`, `pivot`, `publish`, `remove_native`, `sync`. |
| `transform_view.py` | Leitura e edição do Transform; geometria avaliada; Dimensions; estágio afim e caches. `values`, `edit_component`, `set_rotation`, `set_dimensions`, `projected_bounds`. |
| `engine.py` | Guardas de edição/driver, Scale nativo e escrita transacional de posições mundiais. `_target_location`, `_world_roundoff`, `apply_world_positions`. |
| `arrange.py` | Alinhamento de posição/orientação, referências de operação e caminhos legados de distribuição. `reference_frame`, `plan`, `align_orientations`. |
| `geometry_arrange.py` | Planejar e verificar gaps físicos de Geometry Bounds em Offset. `plan`, `position_roundoff`. |
| `placement.py` | Pontos geométricos, intervalos e escolhas por método; centroides calculados sobre geometria avaliada. `offset`, `intervals`, `items`, `read/write`, migração. |
| `distribution.py` | Contratos atuais Offset/Endpoint, fontes Start/End, planejamento, aplicação e inspeção. `point`, `endpoint_plan`, `offset_plan`, `apply`, `inspect_spacing`. |
| `distribution_preview.py` | Sessão Live temporária e observador. `begin`, `reference_context`, `_signature`, `update`, `poll`, `finish`, guardas de frame/render. |
| `diagnostics.py` | Traduzir falhas e passos incompletos para informação acionável. `Diagnostic`, `draw`, `report`. |
| `trace.py` | Transform Information: inspeção sem escrita da composição local/mundial e das referências. Não é um solver alternativo. |

### 5.1. Fluxos essenciais

```text
Campo Transform
  -> _component / transform_view.edit_component
  -> leitura segundo Default ou Reference
  -> linked_values + guardas
  -> Location: frames.set_position -> engine.apply_world_positions
  -> Rotation: transform_view.set_rotation
  -> Scale: engine.edit_scale_component
  -> Dimensions: transform_view.set_dimensions

Distribute
  -> copiar parâmetros no invoke / selecionar objetos
  -> distribution.plan
     -> endpoint_plan OU offset_plan
     -> Geometry Offset: geometry_arrange.plan
  -> engine.apply_world_positions(..., verify=...)

Live
  -> capturar identidades e estado inicial
  -> observar mudança de entradas
  -> restaurar baseline dos alvos móveis
  -> usar o mesmo distribution.apply transacional
  -> ler/verificar resultado e atualizar assinatura
```

Não crie um segundo algoritmo de distribuição dentro do timer ou da UI. O Live deve continuar usando o mesmo planejador e as mesmas verificações da operação única.

<a id="s06"></a>
## 6. Estado persistente, enumerações e migrações

### 6.1. Quem é a fonte de verdade

| Estado | Dono | Persistência e cuidado |
|---|---|---|
| Location/Rotation/Scale nativos | Object/RNA do Blender | O add-on lê ou escreve canais existentes. Não mantenha uma cópia independente como verdade principal. |
| Referências e vínculos XYZ do Transform | `Object.better_item` | Por objeto. Trocar o ativo pode trocar a configuração exibida. Isso continua assim na 1.7.3. |
| Align/Distribute, Start/End, eixos e preferências | `Scene.better_item` | Por cena, não por objeto e não global entre todos os arquivos. |
| Coleção de Frames | `Scene.better_item.frames` | UID e número estável; componentes podem ser Manual, Object, Frame ou fontes nativas/contextuais admitidas. |
| Escolhas Placement | ID properties da configuração da cena | `offset_placement_value` e `endpoint_placement_value` guardam escolhas independentes. |
| Placement no operador/F9 | Propriedades RNA do operador | `offset_placement` e `endpoint_placement`; não tratar Operator como um ID arbitrário. |
| Último sentido não zero | Configuração da cena | `distribution_last_sign`; usado quando Spacing geométrico chega a zero. |
| Estado Live | Módulo `distribution_preview` | Uma sessão em memória. Não é salvo/reconstituído como relacionamento. |
| Caches e erros apresentados | Módulos de runtime | Transitórios; precisam de limpeza e invalidação. |
| Matriz afim de Dimensions | Node group próprio e identificadores do objeto | É alteração constante de geometria; não uma ligação à referência. |

O usuário cogitou tornar as referências do Transform compartilhadas pelo painel/cena. Isso **não foi implementado** na entrega 1.7.3. Seria uma mudança de armazenamento e migração a decidir separadamente.

### 6.2. IDs de enum não são índices descartáveis

Um `.blend` pode guardar o valor numérico de uma enumeração. Remover ou reordenar entradas sem controlar o número pode fazer um valor antigo apontar para outra opção.

Placement usa números explícitos:

```text
ORIGINS=0; GEOMETRY=1; BOUNDS_CENTER=2; SURFACE=3; VOLUME=4
```

Endpoint omite `GEOMETRY`, mas os demais números continuam iguais. Não renumere BOUNDS_CENTER para 1 só porque passou a ser o segundo item visível.

Em `references.py`, campos de armazenamento antigos e opções visíveis são camadas distintas. `_FIELDS` permite aos mesmos resolvedores atender Object e Scene sem perder compatibilidade. Antes de renomear uma propriedade, procure quem a lê, como é serializada e quais arquivos antigos a usam.

### 6.3. Migração de Placement na 1.7.3

`placement.migrate` lê o valor legado de `distribution_mode`, cria os dois valores por método e marca `placement_schema`. Um antigo Endpoint com Geometry Bounds passa a Origins para Endpoint, conserva Geometry Bounds em Offset e recebe um aviso. Uma escolha explícita de Placement limpa o aviso.

`placement.read/write` atende a configuração da cena. `placement.operator_read/operator_write` atende os campos RNA do operador. Durante desenvolvimento, escrever `self['offset_placement_value']` em um Operator provocou `TypeError: id properties not supported for this type`. O caminho corrigido usa propriedades declaradas no operador.

Não infira suporte de downgrade: preservar leitura de arquivos antigos não significa que uma versão anterior entenderá os novos campos se o usuário voltar a instalá-la.

### 6.4. Frames removidos

Frames têm UID lógico e `number` estável para os números das enums. `clear_missing_choices` limpa referências numéricas inválidas nos objetos, cena, outros Frames e endpoints, sem primeiro tentar ler um identificador inválido da enum.

Esse detalhe evita o console repetir `current value ... matches no enum` a cada getter/redraw. Não basta mostrar “Choose a Frame” na UI enquanto o dado armazenado continua inválido.

`frames._enum_cache` mantém uma geração de strings por cena e remove cenas desaparecidas. A retenção das strings também atende o tempo de vida dos itens de callbacks RNA; não substitua por objetos temporários sem verificar esse contrato.
