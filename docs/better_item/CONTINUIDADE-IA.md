# Better Item — manual de continuidade para desenvolvimento assistido por IA

> **Antes de usar este manual:** leia [CONTEXTO-ATUAL.md](CONTEXTO-ATUAL.md). Este documento preserva a base histórica 1.7.3; mínimo de Blender, Custom Orientation e pendências posteriores foram atualizados no contexto 1.7.6. As instruções atuais do usuário prevalecem.

**Estado de referência:** Better Item **1.7.3**.  
**Commit de implementação auditado:** `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.  
**Data deste levantamento:** 15 de novembro de 2026.  
**Responsável pelo produto:** Gabriel Webber do Nascimento.  
**Repositório:** [Borbofruto/Blender-Plugins](https://github.com/Borbofruto/Blender-Plugins).  
**Ambiente efetivamente utilizado:** Blender 5.2.3 LTS, Windows, Python e NumPy distribuídos com o Blender.

Este é um manual de engenharia e passagem de contexto, não apenas um manual de usuário. Seu objetivo é permitir que outra pessoa ou IA entenda por que o sistema tem a forma atual, localize a implementação correta, reproduza a validação e continue o trabalho sem repetir decisões rejeitadas ou introduzir regressões conhecidas.

O estado congelado neste documento é a 1.7.3. Se `main` já estiver diferente, compare o código antes de aplicar qualquer instrução. Um relatório antigo explica sua versão; ele não redefine o contrato atual. As instruções atuais do usuário prevalecem sobre recomendações históricas deste manual.

## Índice

1. [Como assumir o projeto](#s01)
2. [Identidade, escopo e decisões do usuário](#s02)
3. [Histórico de produção e mudanças de direção](#s03)
4. [Repositório, instalador e fontes de verdade](#s04)
5. [Mapa dos módulos e fluxo de dados](#s05)
6. [Estado persistente, enumerações e migrações](#s06)
7. [Modelo matemático dos referenciais](#s07)
8. [Precisão, zeros e vínculos proporcionais](#s08)
9. [Rotação, espelhamento, parentesco e deltas](#s09)
10. [Dimensions e o estágio afim de Geometry Nodes](#s10)
11. [Frames e integração com orientações nativas](#s11)
12. [Alinhamento e distribuição](#s12)
13. [Live: sessão temporária de edição](#s13)
14. [Caches e Dependency Graph](#s14)
15. [UI, UX e diagnósticos](#s15)
16. [Problemas reais encontrados e soluções](#s16)
17. [Ambiente de desenvolvimento reproduzível](#s17)
18. [Como executar testes e interpretar resultados](#s18)
19. [Testes com interface, Undo/Redo e timers](#s19)
20. [Catálogo dos testes e evidências](#s20)
21. [Empacotamento, GitHub e publicação](#s21)
22. [Procedimento para corrigir um problema](#s22)
23. [Pendências, oportunidades e limites de conhecimento](#s23)
24. [Fontes, referências e material histórico](#s24)
25. [Roteiro inicial e mensagem de passagem para outra IA](#s25)

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

O [snapshot de continuidade](handoff-1.7.3.json) acompanha este manual com inventário e hashes. Um commit posterior apenas de documentação pode mudar `main` sem mudar essa versão do runtime ou esse ZIP.

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

<a id="s07"></a>
## 7. Modelo matemático dos referenciais

### 7.1. Três coisas diferentes chamadas informalmente de “local”

É essencial não confundir:

1. **Canais nativos:** valores gravados diretamente no objeto; o painel Item usual não mostra a composição mundial completa do pai.
2. **Orientação local de transformação:** direções dos eixos do objeto, como ao restringir uma operação nativa ao eixo local.
3. **Coordenadas relativas a um referencial:** posição e orientação do alvo medidas em relação a uma origem/base escolhidas.

Default / Local atende a primeira interpretação. Reference atende a terceira. Usar o próprio alvo como origem/base não recupera os canais nativos: tende a produzir zero e uma referência que acompanha a edição.

Exemplo: pai em X=40, filho com `location.x=0`, Parent Inverse identidade. O filho pode estar em X mundial=40 e continuar exibindo X nativo=0. Se Parent Inverse introduzir outro deslocamento, “coordenada relativa ao pai” e “canal nativo” já não coincidem automaticamente. Não resolva essa diferença apenas subtraindo a posição do pai.

### 7.2. Notação de trabalho

- `w`: origem mundial do alvo, proveniente de `matrix_world.translation`.
- `o`: origem resolvida da referência.
- `B`: matriz cujas colunas são os eixos de referência.
- `A`: parte linear de `matrix_world` do alvo.
- `v`: vértice em coordenadas locais avaliadas.
- `U`: colunas de `B` normalizadas individualmente.

Para Location em Reference:

```text
c = inverse(B) @ (w - o)
w_desejado = o + B @ c_desejado
```

É um sistema de coordenadas; a inversa é necessária. Substituir por transposta só é equivalente em bases ortonormais.

### 7.3. Não há uma única operação universal para Location, Rotation e Dimensions

As três leituras possuem contratos diferentes:

| Grupo | Operação |
|---|---|
| Location | Coordenadas na base `B`, usando sua inversa. |
| Rotation | Componente rotacional da referência e rotação do objeto, com convenção Euler de leitura/edição. |
| Dimensions | Extensão física projetada sobre cada direção unitária de `B`. |
| Scale | Canais nativos de escala, com edição limitada conforme a referência. |

Em Gimbal, as direções podem não ser ortogonais. A discrepância entre coordenada em base oblíqua e projeção escalar não prova que uma das duas operações esteja errada. Também não autoriza apresentar todos os números como se fossem a mesma decomposição afim.

`native_refs.checked` usa valores singulares para detectar base singular/mal condicionada em relação a dados float32. O teste é relativo ao maior valor singular, não um determinante absoluto com unidade escondida. `rotation_basis` extrai uma matriz rotacional usando a conversão do Blender para quaternion; não a descreva como uma decomposição polar implementada com SVD, porque não é isso que o código faz.

### 7.4. Unidade de cena não é um fator constante implícito

O código opera em unidades Blender. A conversão de distância para milímetros é:

```text
mm_por_unidade = 1000 * scene.unit_settings.scale_length
```

Com `scale_length=1`, uma unidade equivale a um metro. Com `scale_length=0.001`, equivale a um milímetro. Não multiplique tudo por 1000 sem considerar essa configuração. Ângulos são radianos internamente; a UI apresenta graus.

Teste convenções de unidade diferentes, não apenas um texto “mm” no painel. Os limites do armazenamento dependem da magnitude dos números realmente gravados, não só da unidade exibida.

<a id="s08"></a>
## 8. Precisão, zeros e vínculos proporcionais

### 8.1. A fronteira float32/float64

O cálculo intermediário em NumPy float64 reduz erros adicionais, mas não recupera informação ausente dos vértices e canais armazenados pelo Blender. Converter cedo para `mathutils.Vector/Matrix` pode voltar a arredondar antes da solução final.

A estratégia é conservar float64 em subtrações, inversas e projeções críticas, escrever somente o resultado necessário e verificar o estado avaliado. Nunca use um epsilon global em unidades de cena para todos os grupos.

### 8.2. Orçamento de erro, não “tolerância para ignorar problemas”

`engine._world_roundoff` considera termos de avaliação mundial, deltas e produtos Parent × Parent Inverse. Não basta estimar erro olhando a matriz já multiplicada: termos intermediários grandes podem se cancelar, embora o cálculo float32 já tenha perdido precisão.

`_local_roundoff` estima incerteza na transformação mundial/inversa em coordenadas locais. Ao manter um eixo local travado, a função pode aceitar o canal original dentro desse orçamento. A verificação mundial final soma a incerteza aceita, propagada pela matriz do pai. Sem isso, houve falsos BI-T003/BI-T006 em pais rotacionados/escalados.

`_native_matches` tem outro contrato: compara com a representação float32 solicitada, rejeitando um não zero que subfluxou para zero. `_dimensions_match` exige erro relativo ao tamanho pedido e não aceita um pequeno tamanho perdido sob um piso absoluto genérico.

### 8.3. Zero relativo precisa ser tratado com honestidade

O problema que motivou a correção não era apenas “mostrar muitas casas decimais”. Um resíduo como `0.0000001` era usado como denominador do vínculo proporcional e gerava valores enormes nos outros eixos.

Em `frames._position_sample`, a coordenada relativa e sua incerteza são calculadas juntas. `set_position` verifica o resultado e pode registrar uma assinatura e máscara para um **zero explicitamente pedido**. `position_values` apresenta esse eixo como zero apenas enquanto alvo, referência e demais termos relevantes continuam com a mesma assinatura e o resíduo cabe no orçamento.

Isso não é snap global, arredondamento de todos os pequenos valores nem cache que substitui leituras não zero pelo valor desejado. Mover a referência ou o alvo invalida a dica. Uma coordenada genuinamente pequena e resolvível deve continuar pequena.

### 8.4. Vínculos XYZ

Para um eixo editado com valor anterior `a` e novo valor `b`, os demais eixos vinculados recebem o fator `b/a`. O eixo editado recebe exatamente `b` como pedido, sujeito à representação nativa e verificação.

Exemplo esperado:

```text
Dimensions: (100, 200, 600) -> editar X para 300
Resultado:  (300, 600, 1800), se os três eixos estiverem vinculados.
```

As travas e drivers são verificados para os canais afetados. Não aplique primeiro para descobrir depois que um eixo travado ficou alterado sem restauração.

Para Location, denominador dentro da incerteza de leitura é recusado por BI-T008. Para zero exato em Location/Scale/Dimensions, não há razão proporcional definida; o usuário deve desvincular o eixo antes de estabelecer outro valor.

### 8.5. A regra especial da rotação

O pedido histórico foi “ler 0 como 360”. A implementação correta restringiu isso ao **denominador do eixo editado que começa em zero**. Os outros eixos zero continuam sendo zero.

```text
(0°, 0°, 40°), editar Z para 10° -> (0°, 0°, 10°)
```

Não transforme os zeros dos outros eixos em 360 e depois multiplique: isso já gerou orientações de 90°/180° e leituras absurdas de 720°. Cruzar para zero escala os demais ângulos vinculados para zero. Aritmética de componentes Euler é uma regra de produto; não equivale a interpolação de orientações no espaço de quaternions.

Também não normalize indiscriminadamente todo ângulo para `[0,360)`: o usuário pode ter fornecido voltas explícitas. As dicas de leitura Euler existem para preservar representações compatíveis quando a orientação é equivalente.

<a id="s09"></a>
## 9. Rotação, espelhamento, parentesco e deltas

### 9.1. O erro de decompor uma matriz espelhada sem contexto

Uma matriz com determinante negativo não fornece uma separação única entre rotação e sinais de escala. Converter diretamente `matrix_world.to_quaternion()` pode transferir um sinal de escala para uma rotação de 180°, ou reescrever `(-1,1,1)` como `(-1,-1,-1)` mantendo aparência semelhante.

`orientation.rotation` remove os sinais associados aos canais de escala/delta do objeto quando possível. Se há ancestral espelhado ou eixo colapsado, a rotina consulta canais e herança. `inherited_rotation` trata separadamente o pai e Parent Inverse. Matrizes refletidas/singulares sem interpretação segura são recusadas em vez de receber uma rotação inventada.

Mantenha a mesma interpretação para referências Object, fontes de Frame e Transform. Um caminho com determinante +1 e outro com -1 para a mesma fonte já foi um defeito real.

### 9.2. Solver de Rotation

`transform_view.set_rotation`:

1. Verifica edição, constraints, drivers e travas.
2. Congela a orientação de operação e resolve o Euler desejado na ordem escolhida.
3. Converte para os canais nativos respeitando modo Euler/Quaternion/Axis-Angle e delta rotation.
4. Preserva Scale e Delta Scale.
5. Calcula a transformação mundial efetiva e testa se ela seria rígida. Se a escala herdada faria a operação deformar o alvo, recusa.
6. Resolve o deslocamento necessário para conservar a origem ou girar ao redor da referência de Location, conforme a opção.
7. Verifica orientação, leitura relativa e invariantes; restaura o snapshot em caso de falha.

Não remonte `matrix_world` por decomposição genérica para “simplificar” esse fluxo. O resultado visual pode permanecer semelhante enquanto os canais assinados mudam.

### 9.3. Delta Location

Posição mundial não é sempre igual a `obj.location`. `_target_location` resolve o canal solicitado descontando deltas e a composição parental. Houve um caso em que girar um objeto com delta de posição dobrou seu deslocamento mundial; essa regressão não deve voltar.

O solver também evita a forma ingênua `location += target - current`, que pode sofrer cancelamento desnecessário. Sempre que possível resolve o canal absoluto a partir do alvo mundial.

### 9.4. Limitações deliberadas

Rotation sob pai com escala não uniforme pode introduzir deformação. A recusa é legítima quando a operação não pode preservar o contrato de rotação rígida e canais nativos. Não é obrigação do produto resolver toda transformação afim por rotação de três canais.

Constraints ativas são tratadas conservadoramente. Algumas que afetam apenas rotação poderiam permitir uma operação de posição, mas a classificação confiável por canal/hierarquia foi adiada. Não remova o bloqueio apenas porque um exemplo simples funcionou.

<a id="s10"></a>
## 10. Dimensions e o estágio afim de Geometry Nodes

### 10.1. O que Dimensions mede

`projected_bounds` usa vértices **avaliados**, incluindo modificadores, e mede extremos nas direções unitárias escolhidas:

```text
y = transpose(U) @ A @ v
Dimensions[i] = max(y[i]) - min(y[i])
```

Não é o tamanho de uma bounding box local simplesmente rotacionada; isso pode superestimar uma malha. Não é o comprimento de uma coluna da matriz nem o Scale nativo. As coordenadas locais são lidas em lote com `foreach_get`, projetadas com NumPy e a malha temporária é liberada.

Objetos sem superfície convertível não devem provocar traceback por campo/redraw. Empty, Camera, Light e outros tipos incompatíveis continuam com Location/Rotation/Scale usáveis, enquanto Dimensions aparece indisponível. Instâncias de Geometry Nodes não realizadas são explicitamente rejeitadas nesse caminho, em vez de medidas de forma incompleta.

A obtenção da malha avaliada deve seguir o contrato de `evaluated_get`/`to_mesh`/`to_mesh_clear`; use `finally` para liberar o temporário. [API de Object](https://docs.blender.org/api/5.0/bpy.types.Object.html) e [Depsgraph](https://docs.blender.org/api/5.0/bpy.types.Depsgraph.html).

### 10.2. Regra para eixos não unitários

Dimensions normaliza cada direção antes de medir. Multiplicar uma coluna da referência por 10 não deve multiplicar por 10 o comprimento físico apresentado. Inverter uma direção não muda sua extensão. Location continua utilizando a base original.

Essa decisão foi consolidada na 1.5.4. A normalização não deve modificar os dados do Frame ou a orientação compartilhada; é uma operação de medição.

### 10.3. Como a edição é construída

Com fatores de tamanho `F`, a matriz local desejada é, esquematicamente:

```text
L = inverse(A) @ inverse(transpose(U)) @ F @ transpose(U) @ A
```

Se `L` é diagonal localmente e a leitura avaliada confirma o resultado, usa-se Scale nativo. Caso contrário, a edição pode conter shear e não cabe em apenas três fatores nativos.

Para Mesh, o fallback é um modificador Geometry Nodes com transformação afim **constante**. Ele preserva a malha base, shape keys e usuários de malha compartilhada. Não guarda uma relação dinâmica com a referência. O usuário aceitou essa estratégia depois de esclarecer que não se tratava de criar um novo sistema de modificadores de produto.

O centro da edição de Dimensions continua sendo a origem do próprio objeto. A referência de Location escolhida não muda esse pivô. A opção Rotate Around Reference Location é do solver de Rotation.

### 10.4. Propriedade e integridade do modificador

O estágio é identificado por UID e marcadores próprios, não só pelo nome. `_dimensions_modifier` procura em toda a pilha e recusa:

- mais de um estágio próprio;
- estágio próprio fora do final;
- estágio desabilitado para viewport/render;
- grupo sem propriedade/estrutura válida.

Não reordena a pilha nem cria outro estágio para contornar um modificador colocado depois. Essa é a correção de um problema em que somente o último modificador era examinado e o mesmo objeto podia receber duplicações.

O grafo validado tem oito nós: entrada, saída, Position, Combine XYZ, Set Position e três Vector Math DOT_PRODUCT com nomes de linha definidos. As ligações, valores constantes e a matriz gravada devem corresponder. Uma estrutura editada pelo usuário não deve ser interpretada como se ainda fosse o operador afim original.

Se um grupo for compartilhado, faz-se copy-on-write antes de alterá-lo. Rollback deve restaurar matriz, vínculo de grupo e recursos temporários criados, sem mudar dados de outros objetos.

### 10.5. Dimensão zero

Colapsar uma largura positiva a zero por Dimensions é rejeitado: o operador fica singular e não consegue reabrir esse eixo pelo mesmo campo. Uma largura já zero também não é ampliada por um fator de escala indefinido. O usuário pode efetuar um colapso deliberado com Scale nativo, fora dessa promessa de reversibilidade por Dimensions.

<a id="s11"></a>
## 11. Frames e integração com orientações nativas

### 11.1. Frame é composição de dados, não objeto auxiliar obrigatório

`frame_origin` e `frame_axes` são independentes. Uma origem válida não deve ficar bloqueada porque a orientação do mesmo Frame está sem fonte, se a operação usa apenas Location. O caso inverso também vale.

A resolução recursiva usa identidade e componente para detectar ciclos. Aplique/valide ambos os componentes antes de gravar qualquer um quando a operação for ALL. Uma fonte ausente não deve ser “recuperada” silenciosamente para Mundo ou para um cache de animação.

`apply_reference` resolve os componentes pedidos e converte-os em dados manuais. Para bases não puramente rotacionais, `store_axes` pode preservar uma matriz manual adicional e deixar o Euler inicial em zero; `frame_axes` combina a rotação manual com essa base. Não descarte o termo adicional para tornar a UI mais simples.

Fontes dependentes da seleção são Capture nas escolhas atuais de criação/edição de Frame. Frames antigos podem conservar uma ligação contextual marcada como legada, com Apply disponível. Não declare que toda referência contextual já foi congelada automaticamente.

### 11.2. Exportar para orientação nativa

`native_refs.publish` cria/atualiza uma custom transform orientation, normalmente com nome `BI: <Frame>`. Assim, o usuário usa G/R e os gizmos nativos nos eixos do Frame. Não é uma exportação de pivô nativo independente.

O acesso por nome passa por um slot de orientação, salvando e restaurando seu estado. `view_context` procura uma janela da cena e uma região de View3D apropriada quando a operação depende de contexto. A API de `Context.temp_override` deve ser consultada para a versão real; nem todo operador consulta os mesmos membros de contexto. [Context 5.2](https://docs.blender.org/api/5.2/bpy.types.Context.html).

**Não retenha wrappers RNA de custom orientations entre callbacks.** A remoção nativa pode liberar o dado sem tornar um wrapper antigo seguro. Guarde cópias de matrizes e releia o objeto nativo quando necessário.

### 11.3. Sincronização e remoção externa

O timer `native_refs.sync` usa intervalo de aproximadamente 0,2 s. Ele atualiza fontes, exportações e estados de remoção/suspensão. Se o usuário apaga uma orientação pelo menu nativo, o add-on deve reconhecer a intenção, limpar o estado correspondente e não recriar automaticamente aquela orientação válida.

O desenho não é uma notificação síncrona garantida no mesmo instante do clique. Depende do timer/event loop e de redraw. Houve versões em que a informação só parecia se atualizar ao passar o mouse no painel; a solução incluiu pedir redraw das View3D da cena quando o estado muda.

Os gizmos de Frame atuais são indicadores, com seleção desabilitada. Isso é diferente de manipular o Frame interativamente pelo viewport. Novos manipuladores foram adiados; não anuncie essa capacidade como existente.

<a id="s12"></a>
## 12. Alinhamento e distribuição

### 12.1. Referência de operação não é um novo vínculo

Align/Distribute usa a configuração da cena. O alvo de alinhamento, os eixos e a posição de referência são resolvidos para a operação; isso não cria Child Of nem faz o alvo acompanhar a fonte permanentemente.

O módulo `arrange.py` ainda aceita caminhos históricos SELECTION/KEY/REFERENCE. A distribuição moderna passa por `distribution.py`. Não escolha o caminho legado apenas porque seu parâmetro parece mais conveniente: ele conserva comportamentos antigos, inclusive a opção de projetar numa linha que não deve reaparecer no Offset moderno.

### 12.2. Alinhamento de posição e de orientação

O alinhamento de posição atual trabalha com origens. Os eixos desmarcados são preservados. Bounding Box Center da seleção pode fornecer o contexto de faixa entre origens; um ponto Object/Frame fornece outra origem de operação.

Alinhamento de orientação tem dois modos:

- **Match Reference:** corresponder à orientação rotacional da referência.
- **Set Rotation:** definir componentes Euler selecionados em relação à referência, na ordem escolhida.

O lote congela a referência, preserva posições mundiais e Scale, planeja antes de escrever, resolve pais antes de filhos e faz rollback se alguma verificação falhar. Não transforma Orientation Alignment em uma operação de Location só porque o painel também possui eixos Move.

### 12.3. As duas classificações de distribuição

Há dois eixos de decisão, não uma lista plana de cinco algoritmos equivalentes:

1. **Method:** Offset ou Endpoint.
2. **Placement:** qual ponto ou intervalo representa cada objeto.

| Placement | Offset | Endpoint atual | Significado |
|---|---|---|---|
| Origins | Sim | Sim | Origem nativa existente. |
| Bounds Center | Sim | Sim | Centro da caixa geométrica mundial alinhada aos eixos globais, sem mudar a origem nativa. |
| Center of Mass (Surface) | Sim | Sim | Centro ponderado por área da superfície avaliada. |
| Center of Mass (Volume) | Sim | Sim | Centro de volume com densidade uniforme implícita, sob as condições suportadas de fechamento/orientação. |
| Geometry Bounds | Sim | **Não** | Intervalo geométrico ocupado projetado nas direções usadas para distribuir. |

Os centroides são obtidos da triangulação avaliada. Área usa pesos das faces; volume usa integração por tetraedros com volume assinado. A integração é recentrada antes do cálculo para reduzir cancelamento em malhas deslocadas. O volume verifica incidência de arestas e winding, mas isso **não** prova ausência de autointerseção nem validade física de cascas aninhadas. Não anuncie simulação de massa com materiais/densidades.

Reaproveitar o nome nativo não significa chamar `origin_set` para medir um centro: isso alteraria dados/origem do objeto. O ponto representativo é calculado sem reposicionar a origem nativa.

### 12.4. Bounding Box Center não é Bounds Center

Os nomes parecem próximos, mas têm funções distintas:

- **Location / Bounding Box Center**, em Object Mode, segue o pivô nativo: centro da faixa das **origens selecionadas**.
- **Placement / Bounds Center** mede a **geometria avaliada de cada objeto**.
- **Placement / Geometry Bounds** usa os extremos ocupados da geometria em uma direção.

Median Point também não é sempre igual a Bounding Box Center. Para origens em X=(0,2,10), a média é 4 e o centro da faixa é 5. Com dois objetos ou distribuições simétricas eles podem coincidir; isso não os torna redundantes.

### 12.5. Offset por pontos

Para cada eixo escolhido, o planejador ordena os pontos e coloca intervalos assinados a partir da âncora. Os demais componentes do ponto são preservados. Se a origem nativa está deslocada em relação ao centro geométrico escolhido, calcula-se a posição da origem necessária para mover aquele ponto sem alterar a origem local ou a malha.

A regra de ordem solicitada dá prioridade ao semiespaço oposto ao sentido de Spacing e, dentro de cada semiespaço, à distância em relação à referência. Em múltiplos eixos, cada eixo tem sua própria ordem. Objetos indistinguíveis segundo o critério de ordem precisam de separação inicial suficiente, com diagnóstico dos conflitos.

Spacing zero não define uma distribuição por intervalos de pontos e é recusado nesse método. Isso não impede que Endpoint distribua pontos em um segmento curto, desde que os limites sejam distintos e resolvíveis.

### 12.6. Offset por Geometry Bounds

Meça para cada objeto `[mínimo, máximo]` projetados em cada direção. Posicione o próximo intervalo depois do anterior, acrescido do gap pedido. Não suponha que a origem está no centro da geometria.

O módulo também verifica que geometria, rotação e escala não mudaram indevidamente quando Location foi alterada. GN/driver dependente da posição pode tornar o problema diferente do planejado. Recuse com rollback quando o contrato de intervalos fixos não é mantido.

**Sinal e zero:** um Spacing positivo distribui no sentido positivo; negativo, no negativo. Ao chegar a zero, preserve o último sinal não zero informado. Esse estado fica na cena. Se não existe histórico, o padrão inicial é positivo. Não adicione uma segunda UI de Direction.

**Eixos desmarcados:** Offset moderno não deve alinhar os outros eixos. A opção antiga On Reference Axis causava isso; ela saiu da UI moderna e seu valor salvo não interfere no novo caminho. Há caminhos Python legados que ainda preservam a semântica antiga, razão para testar o operador moderno também.

### 12.7. Precisão geométrica em cenas grandes

Até a 1.7.1, a verificação usava uma tolerância dependente de largura/gap, mas não do arredondamento da posição mundial. Cadeias de 200 objetos e endpoints deslocados em centenas de unidades podiam estar corretos até o limite float32 e mesmo assim ser recusados.

A 1.7.2 projetou o orçamento `_world_roundoff` na direção medida. Um gap depende dos dois extremos, portanto usa os orçamentos dos dois objetos adjacentes. A inspeção também considera a resolução dos gaps para não apresentar Mixed imediatamente após uma operação válida.

Isso não autoriza aceitar gaps positivos colapsados nem avanços de intervalos ocupados que colapsaram. Também não mistura tolerância de posição com tolerância de mudança da forma: a verificação de invariância geométrica permanece separada.

### 12.8. Endpoint entre pontos e por eixo de referência

Em **Between Points**:

```text
d = End - Start
posição_i = Start + t_i * d
```

A direção vem do próprio segmento. A Orientation compartilhada e os Move axes não devem bloquear esse caminho se não forem usados.

Em **Reference Axis**, escolha exatamente um eixo da Orientation e projete End nesse eixo através de Start. Por exemplo, Start=(0,0,0), fonte End=(10,4,0), eixo X: os alvos móveis são distribuídos na linha X até a projeção X=10. Se o objeto fonte de End estava selecionado, ele continua em (10,4,0); não é puxado para a linha.

Start herda a Location compartilhada por padrão. Override Start permite uma fonte própria. Start/End aceitam Manual mundial, Global, Object, Frame Location, cursor e Active Object. Um Frame com Location válida pode ser usado mesmo com Orientation ausente.

Endpoint distribui **pontos representativos**, não tenta encaixar volumes. Cinco cubos de tamanho dois podem ter suas origens distribuídas num segmento de 0,5: haverá sobreposição, mas nenhum redimensionamento. Os dois limites ainda precisam ser distintos; “permitir sobreposição” não é aceitar um segmento numericamente inexistente.

### 12.9. Âncoras, ordem e preservação

Fontes de endpoint conhecidas que também estão selecionadas são âncoras: o distribuidor não as move. Na base geométrica por ponto, o ponto representativo do objeto âncora define o limite efetivo. Empty pode ser uma âncora sem ter uma superfície para centro de massa.

Endpoint ordena por semiespaço e distância espacial em relação ao início. Isso permite que os objetos estejam inicialmente num plano perpendicular ao novo segmento. Empates indistinguíveis são recusados; não use nome como justificativa silenciosa para uma ordem espacial indefinida.

No Live, depois do primeiro resultado válido, a ordem é guardada por identidades para aquela configuração de método/base/caminho/eixos. Mover o início para além dos objetos não deve reorganizar continuamente os alvos pela posição que acabaram de receber. Alterar a configuração pode estabelecer sua própria ordem.

<a id="s13"></a>
## 13. Live: sessão temporária de edição

### 13.1. Por que a implementação mudou

O Live inicial respondia apenas a callbacks de campos do add-on. Um cursor ou Empty movido fora do painel não provocava atualização. A seleção também era comparada à inicial, impedindo selecionar o Empty para editá-lo. A UI mantinha um checkbox Live sem oferecer, nesse fluxo, uma entrada efetivamente acompanhada.

A solução não foi esconder Live em todo Endpoint. As fontes espaciais são as entradas; não há motivo para um slider de distância independente entre dois endpoints já definidos. A solução foi observar essas entradas durante uma sessão explicitamente habilitada.

### 13.2. Estado da sessão

`_session` guarda, entre outros:

- cena e view layer capturadas;
- objetos capturados e objeto ativo original;
- posições nativas iniciais e últimas posições válidas;
- partes lineares esperadas;
- fontes/âncoras conhecidas;
- ordens estabelecidas por configuração;
- assinatura das entradas e uma amostra geométrica reutilizável.

São referências de objetos em memória, não uma lista de nomes gravada no `.blend`. Renomear objetos não deve trocar sua identidade. Um objeto removido precisa ser reconhecido como ausente; não continue usando wrappers inválidos.

### 13.3. Contexto capturado sem alterar seleção real

`reference_context` usa `temp_override` para oferecer o Active e os objetos selecionados capturados aos resolvedores. A seleção real do Blender permanece disponível para o usuário mover os objetos de referência.

Esse é um ponto importante: manter a seleção forçada por `select_set` ou trocar continuamente `view_layer.objects.active` seria uma regressão de UX. Uma referência Active precisa ter identidade estável durante a sessão, não seguir o último objeto clicado.

### 13.4. Atualização

`poll` é registrado apenas quando Live começa. Uma assinatura detecta mudanças de fontes, controles, transformações ou geometria relevante. Se nada mudou, não aplica distribuição. Um número retornado pelo timer determina a próxima espera; `None` encerra o timer. [API de timers](https://docs.blender.org/api/5.2/bpy.app.timers.html).

Quando há atualização:

1. Verifique modo e existência dos objetos.
2. Resolva âncoras na configuração atual.
3. Detecte edição externa de alvo móvel que deve pausar, não sobrescrever.
4. Guarde as posições anteriores ao novo cálculo.
5. Restaure o baseline nativo dos alvos móveis, sem restaurar a âncora que o usuário acabou de mover.
6. Planeje/aplique com o caminho comum; reutilize a ordem estabelecida de Endpoint quando aplicável.
7. Em falha, preserve/restaure o último estado válido.
8. Atualize assinaturas e peça redraw onde necessário.

Uma trava de reentrada evita atualizar novamente enquanto a própria atualização está escrevendo dados. Não escreva posições dentro de `depsgraph_update_post` apenas porque ele detecta mudanças: isso facilita ciclos de avaliação. O observador de edição é separado da invalidação de caches.

### 13.5. Parada e recuperação

- Desmarcar Live mantém o resultado e remove o observador.
- Trocar seleção não troca alvos nem encerra por si só.
- Editar Location/Rotation/Scale de um alvo móvel por fora pausa as próximas atualizações com orientação de recaptura.
- Uma fonte incompleta/inválida mantém o último resultado e pode recuperar depois de corrigida.
- Undo/Redo/load limpam a sessão transitória.
- A guarda de frame/render encerra Live para não acompanhar playback/render como um sistema de animação.
- Desabilitar o add-on mantém as posições; não executa um Cancel implícito.
- Sair da cena/view layer capturadas ou de Object Mode suspende a observação.

O intervalo é de aproximadamente 0,1 s, mais o tempo de cálculo. Não prometa atualização a 60 FPS em malhas grandes. Um observador lento continua sujeito ao custo do planejador, da geometria e da escrita avaliada.

A descrição da API de `frame_change_pre` possui nuances: não é um evento universal “antes de qualquer mudança de frame”. O código usa esse handler para encerrar a sessão e os testes cobrem `frame_set`. Ao ampliar compatibilidade, consulte a documentação e teste playback/render reais, sem deduzir garantias de ordem apenas do nome. [Handlers](https://docs.blender.org/api/5.2/bpy.app.handlers.html).

### 13.6. Limites que não devem ser escondidos

Não há relacionamento persistente a recuperar depois de fechar/reabrir o Blender. A sessão é única, não um sistema de múltiplos arranjos paramétricos salvos. Frame/cena compartilhados e fontes que dependem dos próprios alvos exigem as mesmas verificações de dependência dos outros solvers.

A API legada BEGIN/CONFIRM/CANCEL permanece para compatibilidade e testes. A UI atual usa o checkbox; não reintroduza os botões como fluxo obrigatório.

<a id="s14"></a>
## 14. Caches e Dependency Graph

### 14.1. Inventário do estado transitório

| Cache | Limite/critério auditado | Invalidação principal |
|---|---|---|
| Coordenadas avaliadas em `transform_view` | Até 8 entradas e orçamento de 64 MiB | Dados/objetos geométricos, node trees relevantes, frame/load/undo/redo. |
| Extremos projetados | Até 32 entradas | Geometria e chave da parte linear/projeção. Translação não entra na extensão local. |
| Pontos de Placement | Até 64 entradas | Revisão geométrica, parte linear mundial, tipo de base e direções quando aplicáveis. |
| Inspeção de espaçamento | Até 4 assinaturas | Seleção/ativo/contexto, fontes resolvidas, parâmetros e atualizações avaliadas. |
| Itens de enum de Frame | Uma geração por cena | UID/nome/número; cenas removidas são descartadas. |
| Orientações/Normal nativas | Por cena/nome e assinaturas | Atualizações, remoções, migração e limpeza de runtime. |
| Amostra geométrica do Live | Uma assinatura corrente da sessão | Mudança de revisão/partes lineares/fontes; comparar resultado relevante evita reagir a geometria alheia. |

### 14.2. O problema de cache não era apenas desempenho

Um cache pode tornar a UI rápida e errada. Foram necessárias verificações com GN aninhado, fontes externas, drivers nativos, shape keys, mudanças de frame/subframe, toggles de modificador, Undo/Redo e edição no mesmo frame.

`invalidate_geometry` examina objetos/dados atualizados e node trees; `_tree_matches` percorre grupos aninhados para relacionar uma árvore modificada aos objetos. Mudanças de frame também limpam medições porque nem toda dependência indireta produz a combinação de flags esperada.

Não substitua isso por “limpar tudo em todo redraw”. O cálculo deve ser invalidado por mudanças reais; o redraw só deve ler.

### 14.3. Inspeção de espaçamento

Antes da 1.7.2, `inspect_spacing` percorria os objetos/geometrias em cada desenho, e o getter de Spacing Live podia repetir o custo. O cache atual guarda apenas um pequeno resultado escalar/status e é compartilhado pelos dois consumidores.

O planejador de uma aplicação não usa esse resultado para pular verificação. Cache de UI não é autorização matemática para efetuar uma alteração.

Em um registro da 1.7.2, 1.500 objetos em Geometry Bounds passaram de cerca de 0,66 s na primeira inspeção para cerca de 0,00075 s nas leituras sem mudanças. São números daquele ambiente e workload. A primeira medição após invalidação continua cara, e a invalidação da cena é conservadora.

### 14.4. Getter e draw não devem escrever estado persistente

Já houve erro em uma execução real porque o planejador, chamado pela inspeção durante draw, tentava gravar `distribution_schema`. O Blender bloqueia determinadas escritas nesse contexto.

Separe:

- resolver/medir/planejar, que pode ser chamado na leitura;
- aplicar/migrar, que pode alterar dados no momento apropriado.

Não marque flags de migração, crie modificadores ou altere canais só para mostrar um número no painel. Valide esse ponto com desenho real, não apenas chamando a função num script em background.

<a id="s15"></a>
## 15. UI, UX e diagnósticos

### 15.1. Hierarquia de referência

A UI compartilhada concentra nomes, ícones e relações de dependência. Alterar um resolvedor sem revisar Transform, Align/Distribute e editor de Frame pode produzir interfaces que parecem iguais e significam coisas diferentes.

O rótulo pai descreve o tipo de dado: Location ou Orientation. A escolha de tipo vem no dropdown. Uma segunda escolha de Object/Frame/Name é filha daquele tipo, com `└`/indentação. Evite quatro dropdowns visualmente equivalentes sem explicar a relação entre eles.

As categorias dos menus são Better Item e Default. As opções nativas têm iconografia familiar. Não esconda um novo universo de opções atrás de um dropdown genérico chamado Pivot sem indicar a camada adicional.

### 15.2. Três gravidades, não um bloco vermelho para tudo

| Situação | Tratamento |
|---|---|
| Falta escolher objeto/frame, falta eixo, configuração ainda incompleta | `ReferencePending`, INFO, instrução do próximo passo; grupo/operação pode ficar inativo. |
| Operação solicitada viola um limite de domínio | `BetterItemError`, normalmente WARNING, explicar por que não foi aplicada e como corrigir. |
| Falha inesperada/API/programação | ERROR; mensagem de suporte e Details com diagnóstico técnico. |

Selecionar Object e ainda não preencher qual objeto é um passo esperado do fluxo. Não é uma falha crítica. Da mesma forma, seleção com espaçamentos diferentes é Mixed, não um zero calculado nem uma média escondida.

WARNING não significa automaticamente que todo tema do Blender desenhará amarelo. A implementação atual usa rótulos/ícones e vermelho para ERROR. Avalie a aparência real antes de anunciar cores ou gravidade visual.

### 15.3. Código técnico não substitui explicação

O usuário precisa saber qual objeto/campo corrigir. O código BI- é útil para suporte e testes, mas a UI não deve expor apenas um identificador de programação.

`Diagnostic` separa resumo/ação de detalhes. `_GUIDANCE` pode substituir o texto do `raise`; portanto, mudar uma exceção sem revisar esse mapa pode não mudar a mensagem que o usuário realmente vê. Também há strings antigas que ainda usam “Volume Centroid/Surface Centroid” em uma recusa de geometria, apesar dos novos rótulos principais. Isso é uma pendência concreta de revisão textual, não motivo para reescrever o solver.

### 15.4. Grupos indisponíveis

Um getter RNA de campo numérico não pode simplesmente devolver uma string Unavailable. Internamente alguns getters retornam 0 em caso de erro de domínio; a UI deve detectar a indisponibilidade do grupo, desabilitar seus campos e exibir a instrução correspondente.

Não confunda esse valor técnico de fallback com um zero espacial válido. Não desabilite todos os quatro grupos porque Dimensions não está disponível em um Empty.

### 15.5. Famílias de diagnóstico para localizar o caminho

| Família/código | Investigue primeiro |
|---|---|
| BI-A... | Seleção, eixos, referência de arranjo e verificação do lote. |
| BI-D... | Intervalo pedido, separação mínima, ambiguidade de ordem e precisão da distribuição. |
| BI-E001 | Fontes/limites/caminho de Endpoint, coincidência ou inversão. |
| BI-E002 | Pedido legado de Geometry Bounds em Endpoint; agora escolher uma base de ponto. |
| BI-E003 | Precisão/colapso dos pontos de Endpoint. Ver também `_GUIDANCE`. |
| BI-F... | Fonte de Frame, ciclos, cena/contexto nativo e condicionamento dos eixos. |
| BI-G... | Intervalos geométricos Offset, dependências de forma/referência e mudança de rotação/escala. |
| BI-L001 | Sessão Live precisa de captura/recaptura, alvo removido/alterado ou sessão encerrada. Trocar seleção sozinho não deve causar isso na 1.7.3. |
| BI-M... | Propriedade, posição, habilitação e integridade do estágio Dimensions/GN, ou instâncias não realizadas. |
| BI-T... | Escrita de transformações, travas, drivers, constraints, singularidade, proporção e verificação. |
| BI-V... | Validação genérica ou erro inesperado. Não mascarar todos os casos com o mesmo código. |

O catálogo completo de códigos está no README do runtime. Antes de adicionar um novo, verifique se já existe um conceito correspondente e se a orientação ao usuário continuará específica.

<a id="s16"></a>
## 16. Problemas reais encontrados e soluções

Esta tabela é um mapa de investigação, não uma lista de falhas ainda abertas.

| Sintoma histórico | Causa / aprendizado | Solução adotada ou condição atual |
|---|---|---|
| Alterar Z de 40° para 10° criava X/Y de 90° | Todos os zeros vinculados foram reinterpretados como 360°. | Fallback de 360° somente no denominador do eixo editado. |
| Objeto espelhado mudava sinais de Scale e ganhava rotação de 180° | Quaternion extraído de matriz refletida sem os sinais/canais de origem. | Interpretação comum de orientação, tratamento de sinais e preservação explícita de Scale. |
| Girar objeto duplicava Delta Location | Mistura de posição mundial e canal nativo. | Resolver posição mundial em canais descontando deltas/parental. |
| BI-T003/BI-T006 apenas numa faixa de X, com filho de pai rotacionado | Comparação exata ou orçamento final menor que o arredondamento local aceito. | Propagar a incerteza dos eixos locais travados para o mundo e verificar o orçamento completo. |
| Não era possível obter zero num eixo relativo; chain link explodia outros eixos | Resíduo float32 virava denominador aparentemente não zero. | Zero explicitamente verificado com assinatura; proteção de denominador dentro da incerteza. |
| Traceback repetido em Dimensions de Empty/Camera | Tentativa de converter qualquer tipo para malha. | Classificação prévia e indisponibilidade por grupo. |
| Frame removido deixava avisos de enum em todo redraw | Número serializado continuava sem item correspondente. | Limpar escolhas numéricas inválidas em todos os consumidores. |
| Frames renomeados faziam cache crescer por assinatura histórica | Cada assinatura virava uma entrada permanente. | Uma geração por cena, mantendo strings do callback vivas. |
| Dimensions mostrava número antigo após GN externo, shape key ou seek | Invalidação incompleta da geometria avaliada. | Atualizações de objetos/dados/node trees, grupos aninhados e invalidação por frame/subframe. |
| Geometry Nodes de Dimensions era duplicado depois de inserir outro modificador | Só o último modificador era examinado. | Procurar estágios próprios em toda a pilha e recusar posição inválida/duplicação. |
| Dimensions afetava usuários de dados compartilhados | Alteração de malha/grupo sem isolamento. | Preservar base mesh e usar grupo afim com copy-on-write quando compartilhado. |
| Exportação nativa só parecia atualizar ao passar o mouse | Atualização de estado sem solicitação adequada de redraw. | Timer e redraw das View3D da cena quando o estado da exportação muda. |
| Remover orientação nativa fazia o add-on recriá-la | Ausência foi tratada como pedido de restauração. | Distinguir exclusão externa deliberada de suspensão por fonte inválida. |
| Escrever schema durante a inspeção causava erro no draw | Planejamento de leitura modificava ID data. | Marcar schema na aplicação/migração apropriada, não na leitura do painel. |
| Distribuir só X alinhava Y/Z | Opção On Reference Axis aplicava projeção transversal. | Remover essa influência do Offset moderno, inclusive para flag salva. |
| Geometry Bounds em zero mudava para o lado positivo | Zero não tem sinal e havia fallback invariável. | Guardar último sinal não zero na cena. |
| Selecionar Live parecia uma transação Apply/Confirm/Cancel | Mesmo botão misturava captura, valor solicitado e edição ao vivo. | Checkbox; leitura Current independente; desabilitar mantém resultado. |
| Live com cursor/Empty não reagia | Só callbacks dos campos do painel atualizavam. | Observador temporário de fontes e contexto de alvos capturado. |
| Selecionar um Empty encerrava/invalidava a edição | Seleção atual era exigida como se fosse o conjunto de alvos. | Capturar identidades; usar contexto temporário sem forçar seleção real. |
| Um Operator rejeitava escrita em `self['...']` | Nem todo bpy_struct suporta ID properties. | Propriedades RNA próprias para estado do operador/F9. |
| Geometry Bounds recusava cadeias em coordenadas grandes com erro de poucos ulps | Orçamento geométrico ignorava a posição mundial armazenada. | Projetar o orçamento nativo de posições e somar extremos adjacentes. |
| Sidebar custava centenas de ms ou mais em cada redraw | Inspeção completa sem cache; getter repetia o trabalho. | Cache escalar compartilhado, limitado e invalidado por estado. |
| Endpoint recusava cubos num segmento curto | Era um solver de encaixe de intervalos, contrário ao contrato final solicitado. | Retirar Geometry Bounds de Endpoint; pontos podem sobrepor geometrias. |
| README continha `â†’` e sequências quebradas | Texto passou por codificação dupla. | Ler/escrever UTF-8 conscientemente e revisar o artefato, não apenas a fonte no editor. |

Algumas soluções parecem pequenas depois de prontas. Não as remova como “complexidade desnecessária” sem reproduzir a regressão que motivou sua existência.

<a id="s17"></a>
## 17. Ambiente de desenvolvimento reproduzível

### 17.1. Ferramentas efetivamente usadas

- Blender executável completo, tanto em background quanto em janela real.
- Python distribuído com o Blender para utilitários, AST, JSON, ZIP e hashes.
- NumPy do Blender e mathutils do runtime; não depender de um bpy de sistema com versão diferente.
- PowerShell para iniciar processos e guardar logs no Windows.
- `rg` para localizar símbolos/strings e inventariar arquivos.
- GitHub conectado/Git Data API para publicar quando o workspace não tinha checkout Git.
- Captura de tela do próprio Blender para verificar desenho, recortes e aparência.

Blender/Python usados na máquina original:

```text
C:/Program Files/Blender Foundation/Blender 5.2/blender.exe
C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe
```

Use os executáveis da máquina atual. Não suponha que o diretório, versão ou permissões sejam os mesmos. A pasta do projeto inicialmente mostrada pelo aplicativo não era necessariamente o workspace onde Better Item foi produzido.

O diretório de trabalho precisa existir antes de iniciar o processo; tentar criá-lo dentro de um comando cujo `cwd` ainda não existe falha antes da execução. No Windows, especifique `encoding='utf-8'` ao ler os documentos com Python: o default pode ser uma code page diferente e provocar UnicodeDecodeError. Para busca, prefira `rg PADRAO DIRETORIO -g '*.py'` a depender da expansão de `pasta/*.py` pelo shell.

### 17.2. Checkout e baseline

Num checkout convencional, registre:

```powershell
git status --short
git remote -v
git rev-parse HEAD
git log -5 --oneline
```

Não descarte alterações do usuário para “limpar” o repositório. Se precisar de uma reprodução isolada, use cópia/worktree apropriada e fixtures sintéticos.

Para localizar o runtime, prefira a estrutura `src/better_item`. O pacote importado em testes deve vir do checkout esperado. Registre `better_item.__file__` e `bpy.app.version_string` quando houver suspeita de estar testando outra instalação.

### 17.3. Não testar em arquivos reais do cliente

Vários testes apagam objetos, criam modificadores, salvam e reabrem `.blend`. Eles devem rodar num **novo processo com cena sintética**. Não execute no Blender de trabalho do usuário com o projeto aberto.

Não publique arquivos `.blend` de clientes, screenshots com dados desnecessários, logs com tokens ou caminhos privados. Os fixtures atuais são construídos pelos scripts, normalmente com cubos, empties, malhas pequenas e node groups sintéticos.

### 17.4. Bootstrap Python

Um teste na pasta canônica `tests/better_item` normalmente insere o diretório `src` em `sys.path`, depois usa `addon_utils.enable('better_item')`. O pai do pacote deve estar no path, não a pasta `better_item` em si.

```python
import sys
from pathlib import Path
sys.dont_write_bytecode = True
repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'src'))
import bpy, addon_utils
addon_utils.enable('better_item')
import better_item
print(bpy.app.version_string, better_item.__file__)
```

Nem todo teste histórico usa o mesmo bootstrap. Alguns aceitam `--source`; outros foram criados para uma organização anterior. Inspecione os primeiros blocos do script antes de rodar em massa.

`--factory-startup` reduz dependência do startup do usuário, mas não substitui verificar que os módulos e o ambiente realmente são os esperados. Se houver interferência de outro add-on/perfil, isole o ambiente conforme a versão do Blender em vez de desregistrar arbitrariamente classes de terceiros.

<a id="s18"></a>
## 18. Como executar testes e interpretar resultados

### 18.1. Não confiar apenas no exit code padrão

Um erro Python lançado por script de linha de comando pode aparecer no console e ainda deixar exit code zero se a opção correspondente não for configurada. Isso foi observado durante a produção.

Use `--python-exit-code 1` para scripts de linha de comando. A ajuda do Blender instalado foi consultada e um controle negativo foi executado na preparação deste manual: um RuntimeError proposital encerrou com código 1. Isso valida o runner; não é uma falha do add-on. [Argumentos de linha de comando](https://docs.blender.org/manual/en/dev/advanced/command_line/arguments.html).

Essa opção não torna automaticamente exceções de timers/redraws posteriores em falhas do processo. Para UI, valide o JSON de término, o log e as exceções capturadas do draw.

### 18.2. Execução mínima confirmada

Exemplo PowerShell para um checkout real; ajuste `$repoPath` e o Blender:

```powershell
$blenderExe = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$repoPath = 'C:/caminho/Blender-Plugins'
$testPath = Join-Path $repoPath 'tests/better_item/test_better_item_173.py'
& $blenderExe --background --factory-startup --python-exit-code 1 --python $testPath
if ($LASTEXITCODE -ne 0) { throw 'Teste headless falhou.' }
```

Repita para `test_better_item_live173.py` e para os scripts relacionados ao módulo modificado. O mesmo formato foi reexecutado na preparação desta documentação, com a estrutura de repositório reconstruída a partir da entrega auditada.

Critérios de aprovação:

1. Processo terminou com código esperado.
2. Script concluiu suas asserções e escreveu seu marcador/resultado atual.
3. JSON corresponde à execução atual, não a um arquivo antigo que ficou no diretório.
4. Não há traceback inesperado nem erro de script do Blender no log.
5. A quantidade de casos, recusas e invariantes corresponde ao que o teste realmente cobre.

Não use um JSON “passed” remanescente depois que o script morreu antes de sobrescrevê-lo. Registre horário/mtime, use um diretório limpo de execução ou um mecanismo explícito de identificação de run.

### 18.3. O que testar de uma operação numérica

O teste precisa verificar, conforme o caso:

- leitura no referencial correto;
- valor aplicado e leitura após avaliação;
- posição mundial e canais nativos;
- sinais de Scale, Delta Scale e modos de rotação;
- campos/eixos não selecionados;
- preservação de malha base, usuários compartilhados e shape keys;
- pilha de modificadores, vínculos de grupos e matrizes armazenadas;
- referências e seleção real que não deveriam ser alteradas;
- comportamento diante de fonte ausente, singularidade, trava, driver e constraint;
- rollback completo quando um participante falha.

Um teste que apenas chama o planejador e compara sua própria saída com o mesmo planejador não é um oráculo independente.

### 18.4. Oráculos usados no projeto

- Pontos de cubos simétricos/deslocados: transformar o centro conhecido pela matriz mundial.
- Bounds: transformar vértices por NumPy float64 e projetar diretamente, medindo min/max sem chamar o helper em teste.
- Centro de superfície: triangulação e pesos de área independentes.
- Centro de volume: tetraedro fechado de centro conhecido, com transformações e espelhamento.
- Rotação: comparação com operadores nativos ou diferença angular de quaternions; não exigir uma representação Euler única para toda orientação equivalente.
- Estado nativo: comparar tuplas de Scale, deltas, ponteiros de dados e pilha antes/depois.
- Efeito colateral: injetar falha ou dependência que invalide o resultado e verificar que nada ficou parcialmente aplicado.

Evite introduzir outra etapa mathutils float32 no próprio oráculo quando o objetivo é medir o erro de armazenamento da transformação. Houve testes que usaram vértices e matrizes convertidos a NumPy para não acrescentar arredondamento do produto vetor/matriz.

### 18.5. Fixtures e processos independentes

Persistência real exige salvar e abrir em outro processo quando o objetivo é garantir reconstrução por registro/migração. Salvar/reabrir no mesmo processo é útil, mas pode ocultar cache ou módulo ainda carregado.

Para a migração 1.7.2 → 1.7.3:

```powershell
$migration = Join-Path $repoPath 'tests/better_item/test_better_item_migration173.py'
$oldSourceParent = 'C:/outro-checkout/src'
& $blenderExe --background --factory-startup --python-exit-code 1 --python $migration -- --prepare --source $oldSourceParent
if ($LASTEXITCODE -ne 0) { throw 'Falhou ao criar o fixture antigo.' }
& $blenderExe --background --factory-startup --python-exit-code 1 --python $migration
if ($LASTEXITCODE -ne 0) { throw 'Falhou a migração em processo novo.' }
```

O diretório antigo precisa realmente conter a implementação antiga. Para 1.7.2, o commit de runtime é `4db16357101b08c540f4313e31434ab9ce99db2c`. Não gere o fixture com a classe nova e depois anuncie teste de migração de versão antiga.

`test_better_item_persistence170.py` possui outras fases: preparar o caso corrente, preparar o legado com `--legacy [--source ...]` e conferir com `--check`. Leia o script e execute as fases na ordem; fixtures ausentes não são um defeito de persistência do add-on.

### 18.6. Paralelismo e arquivos de saída

Processos independentes de testes diferentes podem rodar em paralelo quando seus fixtures e arquivos não colidem. Não execute duas cópias do mesmo script ao mesmo tempo se ambas escrevem o mesmo `.results.json` ou `.blend`.

Não tire conclusões de desempenho a partir de uma execução simultânea com outras cargas sem registrar isso. Os números de cold/warm inspection variam conforme hardware e concorrência.

<a id="s19"></a>
## 19. Testes com interface, Undo/Redo e timers

### 19.1. Background não prova UI

Os seguintes pontos precisam de uma janela real do Blender para validação adequada:

- desenho/recorte de painéis e dropdowns;
- publicação/remoção de orientação nativa;
- região de View3D e contexto de operadores;
- observer/timers sendo realmente agendados;
- interação com seleção e operações nativas;
- fluxo do checkbox Live;
- Undo/Redo associado ao uso normal da interface.

Chamar `live.poll()` em um teste headless prova a lógica do callback, mas não que o Blender realmente o agendou corretamente. O teste GUI173 espera intervalos e verifica as mudanças feitas pelo timer real.

### 19.2. Inicialização de um teste GUI

Exemplo PowerShell que espera o processo e captura logs; as aspas internas preservam o caminho do script se ele tiver espaços:

```powershell
$scriptPath = Join-Path $repoPath 'tests/better_item/test_better_item_gui173.py'
$logDir = 'C:/caminho/resultados-ui'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$argumentLine = '--factory-startup --python-exit-code 1 --python "{0}"' -f $scriptPath
$process = Start-Process -FilePath $blenderExe -ArgumentList $argumentLine `
    -WindowStyle Hidden -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $logDir 'stdout.log') `
    -RedirectStandardError (Join-Path $logDir 'stderr.log')
if ($process.ExitCode -ne 0) { throw 'Blender GUI terminou com erro.' }
```

O script gera `test_better_item_gui173.results.json` ao lado dele. Verifique `passed`, ausência de `draw_errors` e ausência de traceback inesperado nos dois logs. `-Wait` é importante: um helper iniciado e abandonado pode ser encerrado pelo ambiente quando o processo pai termina.

### 19.3. Estrutura útil do script GUI

1. Registrar o pacote e preparar cena sintética.
2. Encontrar View3D, habilitar sidebar e selecionar a categoria Better Item.
3. Envolver o draw relevante para registrar exceções.
4. Agendar fases com `bpy.app.timers.register`.
5. Em uma fase, mudar entrada; na seguinte, conferir que o observer fez o trabalho, sem chamá-lo manualmente.
6. Fazer screenshots depois que houve tempo para redesenhar.
7. Escrever JSON final mesmo quando a própria rotina captura uma falha.
8. Encerrar o Blender.

Não faça `sleep` bloqueante longo no thread principal do Blender esperando que um timer execute: você pode estar bloqueando o próprio event loop necessário ao teste.

### 19.4. O que GUI173 efetivamente fez

Ele habilitou Live sem mover os objetos; alterou cursor; trocou a seleção para um Empty; moveu esse Empty com um operador nativo de transformação; esperou o timer; verificou os alvos desmarcados e o Active capturado; testou zero após Spacing negativo; alternou método/Placement; desabilitou Live; executou uma distribuição nativa via invoke e verificou F9 e Undo/Redo.

Isso é um smoke test automatizado de interface com leitura visual de screenshots. Não é uma auditoria de todos os gestos físicos de arrastar com mouse, modalidades de G/R, cancelamento com Esc ou todas as posições do painel.

### 19.5. Undo/Redo: detalhes que já causaram confusão

Não declare simplesmente que “background não tem Undo” nem que todo script prova Undo normal. Dependem da configuração e de como o operador é chamado.

Os testes usam, quando necessário:

```python
bpy.context.preferences.edit.use_global_undo = True
bpy.ops.ed.undo_push(message='Before test operation')
bpy.ops.better_item.distribute('INVOKE_DEFAULT', True)
```

O argumento de undo na chamada Python é relevante. Uma sequência de escritas RNA feita pelo script não equivale automaticamente à mesma interação física na UI.

Depois de Undo/Redo ou abrir arquivo, não continue usando cegamente os wrappers de Object/Scene anteriores. Recupere os dados pelo contexto atual ou pela identidade de teste apropriada. O runtime também limpa sessões e caches nesses eventos.

### 19.6. Mensagens de infraestrutura

Foram observados avisos de escrita de thumbnails em perfil sem permissão e, no encerramento de testes GUI, mensagens relacionadas a arquivo salvo com `@`. Esses avisos não impediram determinados testes de concluir suas asserções, mas não constituem uma regra para ignorar qualquer linha ERROR.

Classifique pelo contexto: resultado atual, traceback, integridade do arquivo e etapa em que ocorreu. Não recomende executar como administrador para ocultar um problema de lógica ou apenas para gerar thumbnails de teste.

<a id="s20"></a>
## 20. Catálogo dos testes e evidências

### 20.1. Entrada recomendada para o estado atual

| Script em `tests/better_item` | Objetivo principal / condição |
|---|---|
| `test_better_item_173.py` | Contrato atual: Placement por método, Endpoint curto com sobreposição, captura Live, fontes, recuperação, persistência e unregister. |
| `test_better_item_live173.py` | 96 lotes / 192 mudanças de referência; quatro bases de ponto, dois caminhos, âncoras, pais, espelho e ordem estável. |
| `test_better_item_gui173.py` | Timer real, cursor/Empty, seleção, contexto, F9, Undo/Redo e desenho. Precisa de janela. |
| `test_better_item_migration173.py` | Fixture criado com 1.7.2 e aberto em processo novo; exige fase de preparação. |
| `test_better_item_matrix170.py` | Matriz atualizada: 256 Endpoint por pontos + 140 Offset. O sufixo do nome não congela sua versão de contrato. |
| `test_better_item_170.py` | Contratos, fontes, oracle de centros, dependências, Frame e persistência; expectativas retiradas foram atualizadas. |
| `test_better_item_preview170.py` | API legada de sessão, undo, cancelamento, captura e mudanças de seleção no contrato atual. |
| `test_better_item_edge170.py` | Dependências GN, cache, fontes removidas e lote geométrico; o caso de 200 peças atual é Offset. |
| `test_better_item_171.py` | Eixos transversais preservados, último sinal, checkbox e persistência. |
| `test_better_item_precision172.py` | 21 cenários de cena grande/cadeia longa, agora com Geometry em Offset e pontos em Endpoint. |
| `test_better_item_collapse172.py` | Recusas atômicas de colapsos reais e mudança geométrica dependente em Offset. |
| `test_better_item_inspection172.py` | Cold/warm inspection, reutilização, invalidação, fontes indiretas e ciclo de registro. |
| `test_better_item_gui_inspection172.py` | Reutilização da inspeção ao longo de redraws/timer reais com 600 objetos. |

### 20.2. Regressões anteriores úteis por área

| Área | Scripts de referência |
|---|---|
| Matemática/transformações | `test_better_item.py`, `test_better_item_regressions.py`, `test_better_item_scope152.py`, `test_better_item_stress157.py` |
| Zero e proporção | `test_better_item_zero_location156.py`, `test_better_item_feedback157.py` |
| Referências/Frames | `test_better_item_references.py`, `test_better_item_frames.py`, `test_better_item_frame_creation.py`, `test_better_item_reference_parity.py`, migrações e testes UI de referência |
| Eixos/pivôs nativos | `test_better_item_native_axes.py`, `test_better_item_directions154.py`, `test_better_item_sync_gui.py` |
| Arredondamento com travas | `test_better_item_locked_roundoff.py` |
| Cache | `test_better_item_cache.py`, `test_better_item_cache154.py`, `benchmark_dimensions.py` |
| Limpeza/legado | `test_better_item_cleanup155.py`, `test_better_item_legacy155.py` |
| Dependências e limites | `test_better_item_dependencies157.py`, `test_better_item_guards153.py` |
| Arranjo/1.6 | `test_better_item_arrange.py`, `test_better_item_arrangement161.py`, `test_better_item_features160.py`, `test_better_item_matrix160.py`, `test_better_item_edge160.py`, `test_better_item_review161.py` |
| UI histórica | Scripts `gui153` a `gui171`, `reference_gui*`, `reference_ui*`, `test_better_item_ui_undo.py` |

O inventário completo está no JSON de snapshot. Leia o bootstrap e as pré-condições dos scripts antigos antes de compor uma suíte automática. Não foi auditado que todos os scripts históricos podem ser tratados como testes pytest independentes, sem fase de preparação ou ajuste de ambiente.

### 20.3. Como interpretar as pastas de resultados

`results/1.7.3/` registra os resultados efetivamente reunidos para essa entrega. As pastas anteriores são preservadas como evidência histórica. Não as sobrescreva com resultados atuais só para fazer os números parecerem consistentes.

Por exemplo:

- 320 lotes Endpoint em resultado antigo incluíam a operação geométrica agora retirada.
- 256 lotes no resultado atual cobrem as quatro bases suportadas.
- A suíte de 9.216 combinações e as comparações nativas amplas foram executadas em etapas anteriores; não foram todas repetidas na 1.7.3.
- Um arquivo `baseline` de precisão pode conter `passed: false` intencionalmente, pois descreve a versão antiga que recusava casos válidos. Não o trate como o resultado do pacote corrigido.

Relate sempre nome, versão/commit, ambiente, número de casos e limites. “Todos os testes passaram” sem definir a suíte não é um relatório útil.

<a id="s21"></a>
## 21. Empacotamento, GitHub e publicação

### 21.1. Checklist do instalador

Para uma alteração de runtime:

1. Atualizar a versão em `blender_manifest.toml`, que é a fonte de versão da extensão. Não reintroduzir `bl_info` duplicado.
2. Revisar README, CHANGELOG e códigos de diagnóstico afetados.
3. Empacotar apenas runtime, manifesto, licença e documentação do pacote.
4. Manter nome `addons/better_item.zip`; não criar uma coleção de ZIPs numerados em `addons` ou na raiz.
5. Verificar integridade do ZIP, conteúdo e ausência de testes, fixtures, `.blend`, logs, `__pycache__`, protótipo de animação ou dependências locais não planejadas.
6. Rodar validação de extensão.
7. Extrair o ZIP para outro diretório e executar testes contra o **conteúdo extraído**, confirmando o módulo importado.
8. Calcular SHA-256 e atualizar somente a linha pertinente de `dist/SHA256SUMS`, preservando outros add-ons.
9. Publicar fontes, testes, evidências e instalador coerentes.
10. Ler de volta o commit/manifesto e verificar o blob do ZIP remoto.

Para uma alteração apenas documental como este manual, não há razão para recompilar o instalador ou aumentar a versão do add-on. O commit de documentação pode ser posterior ao commit de runtime.

### 21.2. Esboço de build portátil

Os scripts de staging usados nas últimas entregas ainda eram utilitários locais com caminhos/listas específicos. Um build portátil consolidado é uma oportunidade de manutenção, não algo que se deva afirmar já existir.

Este exemplo demonstra o formato do pacote atual; adapte a política de assets se o pacote ganhar subdiretórios:

```python
from pathlib import Path
import hashlib, os, sys, tomllib, zipfile

repo = Path(sys.argv[1]).resolve()
source = repo / 'src' / 'better_item'
manifest = tomllib.loads((source / 'blender_manifest.toml').read_text(encoding='utf-8'))
assert manifest['id'] == 'better_item'
assert manifest['version']
names = {p.name for p in source.glob('*.py')}
names |= {'blender_manifest.toml', 'README.md', 'CHANGELOG.md', 'LICENSE'}
assert '__init__.py' in names
out = repo / 'addons' / 'better_item.zip'
out.parent.mkdir(parents=True, exist_ok=True)
temporary = out.with_name('better_item.zip.tmp')
with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(names):
        path = source / name
        assert path.is_file()
        archive.write(path, name)
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    assert 'blender_manifest.toml' in archive.namelist()
os.replace(temporary, out)
print(hashlib.sha256(out.read_bytes()).hexdigest())
```

Esse é um exemplo de instrução, não uma ferramenta de release adicionada por esta documentação. O código deve ser revisado e testado antes de substituir a cadeia de entrega. Metadados/timestamps do ZIP podem alterar o hash de uma reconstrução mesmo com conteúdo equivalente; o SHA publicado identifica o arquivo exato da entrega, não toda reconstrução futura possível.

### 21.3. Validação pelo Blender

```powershell
$zipPath = Join-Path $repoPath 'addons/better_item.zip'
& $blenderExe --background --factory-startup --command extension validate $zipPath
if ($LASTEXITCODE -ne 0) { throw 'Pacote de extensão inválido.' }
Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath
```

`validate` verifica o pacote/metadados conforme o comando da versão; não prova funcionamento matemático ou desenho da UI. A documentação oficial aceita um diretório de pacote ou arquivo como SOURCE_PATH. [CLI de extensões 5.2](https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html).

### 21.4. Git convencional e o método utilizado nesta produção

Com checkout autenticado e ferramentas adequadas, um fluxo normal de diff/commit/push é preferível a reconstruir um sistema paralelo de versionamento. As últimas entregas usaram o conector GitHub/Git Data porque a fonte trabalhada estava em staging local sem `.git`.

O procedimento efetivamente utilizado foi:

1. Ler `refs/heads/main` e o commit corrente.
2. Obter a árvore real do commit e seu inventário recursivo.
3. Preparar uma lista `{path, local, encoding, sha}` dos arquivos desejados.
4. Comparar com os blobs remotos e enviar somente alterações. Um blob já presente no repositório pode ser reutilizado em outro caminho.
5. Criar blobs UTF-8 para texto ou Base64 para o ZIP. Conferir o SHA retornado.
6. Criar nova árvore usando **base_tree_sha**, preservando os arquivos não relacionados, inclusive Export Paper Model.
7. Criar commit com o HEAD lido como pai.
8. Atualizar a referência com o HEAD esperado como lease e `force=false`.
9. Conferir HEAD final, manifesto e hash/tamanho do ZIP na árvore publicada.

Não confunda SHA de commit, SHA de árvore e SHA de blob. Para este repositório, o SHA de blob Git usa o cabeçalho e os bytes do arquivo, diferente de um SHA-1 simples do arquivo:

```python
blob_sha = sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
```

O arquivo de checksums de distribuição usa SHA-256, outra finalidade. O conector utilizado não era adequado para buscar o ZIP como texto; a conferência binária remota foi feita por metadados de árvore/blob e pelo payload enviado, além do teste local do ZIP.

### 21.5. Conflitos, limites de ferramentas e segurança operacional

Se o HEAD mudar antes do update da referência, releia o commit e avalie as alterações concorrentes. Não use force para contornar a lease nem reconstrua uma árvore vazia apagando arquivos alheios.

Ferramentas/conectores podem mudar de nome ou formato. Descubra as capacidades disponíveis em vez de presumir que os nomes internos da sessão anterior continuarão iguais. Se houver recusa de autorização, limitação ou falha de publicação, não anuncie push concluído: diga o que ficou preparado e o que permanece bloqueado.

Leia conteúdo multiline a partir de arquivos ou argumentos estruturados. Não trate `JSON.stringify` como escape de shell nem monte comandos que possam executar `$()`/backticks contidos num texto. Não exponha tokens nem despeje Base64 do instalador no relatório.

Não faça limpeza recursiva ampla para preparar um build. Confirme o diretório absoluto e use operações nativas com `LiteralPath` no Windows. O staging não deve depender de remover pastas do perfil do Blender ou projetos reais.

<a id="s22"></a>
## 22. Procedimento para corrigir um problema

### 22.1. Ficha mínima de reprodução

Peça ou registre somente o que falta:

```text
Versão do Blender / Better Item e caminho do módulo carregado:
Sistema operacional:
Scene Unit Scale e unidade exibida:
Objeto ativo e seleção:
Pais, Parent Inverse, deltas e sinais de Scale:
Constraints/drivers relevantes:
Modo Default / Local ou Reference:
Location e Orientation resolvidas (ou Frame + componentes):
Operação, eixos, Spacing, Placement, Start/End e caminho:
Live habilitado? Alvos/Active capturados diferentes da seleção atual?
Resultado esperado, resultado obtido e mensagem completa:
Arquivo sintético/script de reprodução:
```

Não peça um arquivo de cliente se consegue reproduzir com cinco cubos. Não atribua automaticamente a falha a “malha do usuário” sem medir qual precondição realmente falta.

### 22.2. Ordem de diagnóstico

1. **Identidade do código:** a versão instalada é a que você acha? O source importado é o correto? Há dois pacotes registrando os mesmos IDs?
2. **Configuração incompleta:** falta fonte/eixo/seleção ou é uma operação efetivamente inválida?
3. **Contrato:** Endpoint por pontos, Geometry Offset, Reference Axis ou Between Points? A expectativa é do modo atual?
4. **Referência:** congelada, vinculada, contextual ou seguindo o próprio alvo?
5. **Planejamento:** registre alvos float64 antes de escrever.
6. **Canal nativo:** qual Location/rotação/Scale foi pedido depois de resolver pai/delta?
7. **Estado avaliado:** o Blender reteve esse canal e a posição/orientação mundial?
8. **Precisão:** compare resíduos com termos de armazenamento e condicionamento, não com um epsilon improvisado.
9. **Dependências:** mover o objeto mudou sua geometria, a fonte ou o pai?
10. **Rollback:** tudo voltou ao estado anterior, inclusive grupos e pilha?

Se o resultado só parece errado visualmente, confira o ponto/intervalo representativo: geometria assimétrica, origem deslocada e projeções em eixos girados podem produzir resultados corretos que não parecem “encostar pelas faces” em 3D.

### 22.3. Pequenos casos que valem ouro

| Caso | O que revelar |
|---|---|
| Pai deslocado e filho com Location zero | Distinguir canal nativo de coordenada mundial. |
| Parent Inverse com termos grandes que se cancelam | Verificação final não pode esquecer erro intermediário. |
| Scale `(-1,1,1)` com pai e referência externa | Não transferir espelho para Euler/Scale errado. |
| Delta Location não zero e edição de Rotation | Não duplicar deslocamento. |
| Location relativa explicitamente zero num eixo, outros não zero | Dica de zero e proteção de proporção. |
| Grupo com três origens em X=3,8,19 e Offset global | Mixed antes; intervalos escolhidos depois; não usar média como estado real. |
| Cubos com Y/Z diferentes, distribuir só X | Preservar os componentes desmarcados. |
| Geometry Offset negativo e depois zero | Manter o sentido negativo. |
| Cinco cubos em Endpoint de comprimento 0,5 | Sobrepor sem redimensionar, se os pontos continuam resolvíveis. |
| Dois Empties externos e alvos desmarcados no Live | Captura e acompanhamento reais, sem mudar seleção. |
| Empty selecionado depois de capturar Active Object | Não retargetar a referência Active inadvertidamente. |
| Mover manualmente um alvo móvel no Live | Pausar, não sobrescrever a alteração do usuário. |
| Criar geometria alheia após habilitar Live | Não normalizar um grupo ainda intocado. |
| Renomear, remover ou recriar um Frame | Identidade, enum estável, strings vivas e limpeza. |
| Inserir modificador depois do estágio Dimensions | Recusar com orientação de reposicionar, sem duplicar. |
| 200 peças e referência em centenas de unidades | Precisão do armazenamento não pode ser tratada como falha indevida. |

### 22.4. Não resolver o problema errado

Uma exceção por instâncias não realizadas não exige implementar um avaliador completo de instâncias. Uma rotação impossível sob escala parental não uniforme não exige introduzir parenting artificial. Uma superfície aberta em Center of Mass (Volume) não exige estimar densidade física por heurística.

Primeiro identifique a promessa do produto. Uma recusa correta, explicada e atômica pode ser a solução certa. O trabalho é resolver o conjunto de casos contratado e diagnosticar seus limites, não cobrir toda geometria possível do Blender.

<a id="s23"></a>
## 23. Pendências, oportunidades e limites de conhecimento

Esta seção é uma agenda de investigação. Nenhum item passa a ser escopo autorizado só porque aparece aqui.

### 23.1. Decisões de produto pendentes

**Referências do Transform compartilhadas.** O usuário sugeriu que a configuração acompanhasse o painel, em vez de variar por objeto, mas a 1.7.3 manteve o armazenamento atual. Se isso voltar à pauta, definir primeiro se o dono será cena, view layer, workspace, janela ou outro contexto. Não mover todos os vínculos/travas junto por acidente. Precisará de migração e política para objetos de cenas diferentes.

**Interações adicionais.** Manipular Frame por gizmo, outro pivô nativo ou operações em massa no Transform não faz parte da entrega corrente. Verificar primeiro se ferramentas nativas ou o cursor já resolvem o caso.

**Congelamento para lançamento.** Houve concordância em priorizar correções e validação antes da primeira publicação comercial. Não usar uma revisão técnica para começar uma nova linha de recursos.

### 23.2. Trabalhos explicitamente separados

**Otimização de Normal.** O timer pode reconstruir uma assinatura grande de elementos selecionados e histórico para descobrir que nada mudou. Uma revisão incremental pode reduzir custo, mas precisa preservar atualização de seleção, modo, undo, múltiplos objetos/cenas e dependências. Não é sinônimo de remover a verificação.

**Flexibilização de constraints.** Há operações válidas que o bloqueio conservador pode recusar. Uma classificação melhor exige saber quais canais e dependências afetam o resultado, não apenas comparar o tipo de constraint. Preservar validação e rollback continua obrigatório.

**Novas interações de viewport.** É uma etapa de produto diferente de melhorar solver/cache. Os indicadores de Frame não são manipuladores, e a exportação nativa já cobre uma parte importante do fluxo.

### 23.3. Melhorias de manutenção justificadas

| Prioridade | Item | Evidência / próximo passo |
|---|---|---|
| Alta para compatibilidade | Matriz de versões/OS | 5.0 é mínimo declarado, mas só 5.2.3/Windows foi executado. Testar explicitamente antes de prometer suporte amplo ou revisar o mínimo. |
| Alta para confiabilidade | Runner unificado com códigos de saída, logs e fixtures | Muitos scripts independentes e algumas fases manuais. Consolidar execução sem apagar evidência histórica nem transformar scripts dependentes em pytest por suposição. |
| Média | Build portátil e verificável | Os builds anteriores têm listas e caminhos locais. Padronizar a partir de `src`, com validação e teste do ZIP. |
| Média | Mensagens com nomes atuais | Há texto de recusa em `placement.py` ainda falando em Volume/Surface Centroid. Revisar também `_GUIDANCE`, que pode esconder a mensagem específica do solver. |
| Média | Política de timers sob erro inesperado | `distribution_preview.poll` possui suspensão/diagnóstico, mas `native_refs.sync` tem caminhos cujo erro inesperado pode escapar. Fazer fault injection e verificar registro/recuperação; não afirmar que uma falha espontânea já foi reproduzida. |
| Média | Testes de interação manual contínua | Há timer real e operadores nativos, mas não uma auditoria completa de drag modal, Esc, seleção durante G, histórico e troca de editor. |
| Média | Fonte/contexto em múltiplas cenas/view layers | Há evidência histórica de exportações em múltiplas janelas. Ainda convém testar objetos compartilhados entre cenas com referências por objeto, view layer removida durante Live e trocas rápidas de contexto. |
| Média | Herança externa durante Live | A captura usa baselines nativos e partes lineares. Exercitar translação/rotação/escala de pais e fontes que sobrepõem alvos, definindo o comportamento esperado antes de ampliar a guarda. |
| Baixa / condicionada a medição | Otimizar observação Live de seleções grandes | Há custo O(n) de assinaturas e possíveis medições frias. Medir workloads reais; não sacrificar frescor para uma taxa de atualização aparente. |
| Baixa | Formatação/clareza de módulos | Existem funções compactas e imports locais para evitar ciclos. Melhorar quando reduzir risco real, não como refactor indiscriminado. |

### 23.4. O que não está demonstrado

- Que todos os scripts históricos passam sem configuração no snapshot atual.
- Que a declaração Blender 5.0+ foi executada em todas as versões ou sistemas.
- Que handlers garantem uma determinada ordem universal em todos os contextos de render/playback.
- Que validação de winding/arestas certifica um volume físico sem autointerseções.
- Que um painel desenhado sem exceção é agradável em toda largura, escala de UI e tema.
- Que contagens altas de testes provam ausência de bugs.
- Que os estudos comerciais/benchmark propostos foram todos concluídos.

### 23.5. Ordem recomendada de continuidade

1. Preservar o contrato atual e reproduzir qualquer novo relato com cena mínima.
2. Corrigir defeitos demonstrados com testes de regressão e efeito colateral.
3. Consolidar a validação reproduzível e o build, sem ampliar funcionalidades.
4. Fazer beta de fluxos humanos reais, incluindo arquivos de projeto tratados com cuidado.
5. Só então discutir decisões novas de armazenamento/UX e trabalhos separados, com casos de uso claros.

<a id="s24"></a>
## 24. Fontes, referências e material histórico

### 24.1. Fontes primárias do próprio projeto

Base congelada de código: [src/better_item no commit 1.7.3](https://github.com/Borbofruto/Blender-Plugins/tree/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/src/better_item).

Testes congelados: [tests/better_item no mesmo commit](https://github.com/Borbofruto/Blender-Plugins/tree/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/tests/better_item).

Instalador exato da base: [better_item.zip pelo commit](https://github.com/Borbofruto/Blender-Plugins/raw/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/addons/better_item.zip). O link por `main` entrega a versão que estiver publicada no momento, não necessariamente a base deste manual.

| Registro | Conteúdo |
|---|---|
| [README do runtime](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/src/better_item/README.md) | Manual de usuário, contratos, limites e códigos atuais. |
| [CHANGELOG](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/src/better_item/CHANGELOG.md) | Mudanças por entrega. |
| [Histórico até 1.6.0](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/delivery-history-through-1.6.0.md) | Registros antigos preservados com ressalva de evidência histórica. |
| [Manutenção 1.5.5](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/maintenance-1.5.5.md) | Limpeza, propriedade do estágio afim e escopo adiado. |
| [Feedback 1.5.6](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/feedback-1.5.6.md) e [1.5.7](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/feedback-1.5.7.md) | Triagem de feedback, precisão, zeros e integridade. |
| [Release 1.6.0](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.6.0.md) | Geometry Offset, orientação e diagnósticos. |
| [Revisão 1.6.1](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/review-1.6.1.md) e [UI 1.6.2](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/ui-1.6.2.md) | Revisão técnica e hierarquia visual. |
| [Release 1.7.0](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.0.md) | Introdução dos métodos/bases/preview; contém comportamento histórico retirado. |
| [Release 1.7.1](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.1.md) | Eixos, direção em zero e checkbox. |
| [Release 1.7.2](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.2.md) | Precisão em cena grande e cache. |
| [Release 1.7.3](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.3.md) | Contrato atual de Endpoint, Placement e Live. |
| [Arquivo de animação](https://github.com/Borbofruto/Blender-Plugins/tree/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/archive/better_item-animation-1.5.1) | Preservação de um protótipo retirado; não instalar como atualização. |

Hashes de todos os arquivos de runtime e dos relatórios inventariados estão em `handoff-1.7.3.json`. Ele também lista todos os scripts de teste encontrados, inclusive os não detalhados neste texto.

### 24.2. Documentação técnica externa consultada nesta consolidação

Use a documentação da versão efetiva do Blender. Links `current`, `latest` ou `dev` podem apontar para uma versão posterior; a fonte de execução auditada continua sendo o binário e o código do snapshot.

- [Context 5.2](https://docs.blender.org/api/5.2/bpy.types.Context.html): contexto temporário e dependency graph.
- [Application Timers 5.2](https://docs.blender.org/api/5.2/bpy.app.timers.html): registro, retorno de intervalo/None e lifecycle.
- [Application Handlers 5.2](https://docs.blender.org/api/5.2/bpy.app.handlers.html): eventos, contexto de avaliação e cuidados com mudanças de dados.
- [CLI de extensões 5.2](https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html): validar/build de pacote; verificar também `--help` no executável instalado.
- [Argumentos CLI](https://docs.blender.org/manual/en/dev/advanced/command_line/arguments.html): comportamento de `--python-exit-code` e ordem dos argumentos, confirmado localmente na 5.2.3.
- [Object API 5.0](https://docs.blender.org/api/5.0/bpy.types.Object.html) e [Depsgraph API 5.0](https://docs.blender.org/api/5.0/bpy.types.Depsgraph.html): malha temporária avaliada e liberação. São referências da API, não evidência de teste deste add-on na 5.0.
- [Operadores de Object](https://docs.blender.org/api/current/bpy.ops.object.html): nomenclatura nativa de Center of Mass; a consulta do código nativo/operador também confirmou os nomes durante a produção.
- [Modifier.persistent_uid](https://docs.blender.org/api/5.0/bpy.types.Modifier.html): referência citada na revisão 1.5.7 para a identidade do estágio afim; conferir disponibilidade na versão-alvo.
- [Formato e criação de extensões](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html): referência histórica para manifesto e metadados do pacote.

Alguns acessos diretos à documentação retornaram erro no navegador de pesquisa durante esta consolidação; os trechos recuperados por busca oficial e a ajuda do Blender local foram utilizados quando apropriado. Não afirmar que uma página completa foi auditada se ela não carregou. Não foram adotadas receitas de fóruns como fundamento para o solver.

### 24.3. Licença e materiais que não compõem o runtime

O manifesto declara GPL-3.0-or-later e o arquivo LICENSE acompanha o pacote. Preserve licença e autoria na entrega. Este manual não substitui análise jurídica de uma eventual distribuição comercial.

Documentos de roadmap comercial, screenshots e feedbacks colados pelo usuário ajudaram a definir o produto, mas nem todos esses arquivos temporários são parte do repositório. Os relatórios consolidados são a referência durável disponível. Não alegue ter lido novamente anexos antigos que não estão acessíveis.

<a id="s25"></a>
## 25. Roteiro inicial e mensagem de passagem para outra IA

### 25.1. Primeira sessão de trabalho

Antes de produzir uma alteração, a nova IA deve conseguir responder:

1. Qual versão/commit está realmente instalada e qual está sendo editada?
2. A solicitação é uma correção, uma mudança de contrato ou uma hipótese exploratória?
3. A operação usa canais nativos, coordenadas, componente rotacional ou extensões projetadas?
4. Quem é dono dos dados: Object, Scene, Frame, operador ou sessão transitória?
5. Que invariantes precisam permanecer iguais, além do número editado?
6. Qual referência pode mudar com o próprio alvo?
7. Onde há conversão para float32 e qual orçamento foi aceito?
8. Qual teste reproduz o caso e qual oráculo independente verifica o resultado?
9. O teste precisa de janela, timer, fixture antigo ou processo novo?
10. O pacote instalado é exatamente o artefato testado/publicado?

Se não souber, inspecione antes de implementar.

### 25.2. Mensagem pronta para iniciar outra conversa

```text
Você vai continuar o Better Item de Gabriel Webber do Nascimento.

Leia o manual CONTINUIDADE-IA.md e o snapshot handoff-1.7.3.json antes
de alterar código. A base documentada é 1.7.3, commit
0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9, no repositório
Borbofruto/Blender-Plugins. Compare com o HEAD real, porque o projeto
pode ter evoluído.

Não reintroduza animação relativa, vínculo permanente de distribuição,
opção redundante de capturar o pivô/orientação ativo da viewport,
nem Geometry Bounds em Endpoint. Endpoint distribui pontos e permite
sobreposição sem redimensionar. Offset preserva eixos desmarcados,
usa o sinal de Spacing e conserva o último sentido ao chegar a zero.

Live captura alvos e Active Object, acompanha referências enquanto
habilitado e termina ao desligar/frame/render/load/undo. Transform
continua com referências por objeto; mudar isso exige uma decisão
separada. Frames guardam Location e Orientation independentes.

Entenda os módulos, reproduza a solicitação atual, classifique defeito
versus escopo, faça alteração pequena e teste invariantes/rollback.
Use Blender real quando necessário, --python-exit-code 1 em testes
CLI, JSON atual e logs. Não anuncie testes históricos como executados
agora. O instalador é sempre addons/better_item.zip; a versão fica
no manifesto. Não modifique o outro add-on do repositório.

Depois de ler, apresente o entendimento do problema atual e prossiga
dentro da autorização do usuário, explicitando incertezas relevantes.
```

### 25.3. Critério de entrega de uma continuação

Uma entrega está pronta quando o comportamento pedido está concreto, o usuário consegue entender a mudança, os testes pertinentes e seus limites foram registrados e o artefato correspondente foi conferido. Uma resposta dizendo apenas que “a arquitetura está boa” ou que “provavelmente funciona” não substitui isso.

Este manual deve ser atualizado quando uma decisão estrutural ou de escopo mudar. Preserve os motivos e as regressões que explicam a solução; remova instruções obsoletas do caminho principal, deixando o histórico claramente identificado.




