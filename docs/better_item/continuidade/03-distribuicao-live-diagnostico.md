# Distribuição, Live, caches, UI e diagnóstico

[Índice](README.md) · [Manual integral](../CONTINUIDADE-IA.md)

> Leia primeiro [Contexto atual](../CONTEXTO-ATUAL.md). Este capítulo é histórico; não representa sozinho o estado vigente.

Base: Better Item 1.7.3, commit `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.

Gerado de CONTINUIDADE-IA.md, SHA-256 `e2f4f2a643dfa3fb1edb364d29cbfda1b70e157af8f732cb94c781a9439573e9`. Não editar este capítulo isoladamente; altere o manual integral e execute `gerar.py`.

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
