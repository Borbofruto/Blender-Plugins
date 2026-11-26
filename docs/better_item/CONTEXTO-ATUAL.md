# Better Item — contexto atual

Atualizado em **26/11/2026**. Versão oficial: **1.7.10**, na **main**. A **1.7.11 é candidata** na branch `release/1.7.11`, aguardando revisão e qualificação independentes; não foi mesclada nem publicada como oficial. Mínimo **Blender 4.2.0**.

## 1. Estado atual e leitura

- Fonte: `src/better_item/`; instalador: `addons/better_item.zip`.
- SHA256 oficial: `d0d06869fcb4e6143116f4acad38912a7530e69303452b109200c9a170a02175`. [Snapshot](handoff-1.7.10.json) e [relatório](release-1.7.10.md).
- O runtime passou 28 entradas em nove builds. A embalagem oficial só atualiza o changelog em relação ao artefato dessas execuções; a validação de instalação final está registrada separadamente. Não atribuir resultados a outro SHA.
- As quatro correções da 1.7.10 estão concluídas: observador por janela, causa da inspeção indisponível, precisão visual e título BI-F006. Endpoint direto/changelog foram corrigidos na 1.7.7; cache/polling e gestos receberam correções na 1.7.8/1.7.9.
- Leia este contexto, [manual técnico histórico](CONTINUIDADE-IA.md), [validação de unidades](units-1.7.9.md), [runner](../../tests/better_item/compatibility/README.md) e [estudo Edit Mode](edit-mode-2.0-feasibility.md). O manual tem base 1.7.3; contratos e resultados atuais prevalecem.
- Documentação deve tratar do produto, arquitetura, decisões e evidências. **Não versionar comparações entre IAs, variantes por autoria, conversas ou briefings de sessões.** Revisões desse tipo ficam na conversa. Comparações técnicas com o Blender nativo e benchmarks continuam válidas.

## 2. Produto, escopo e colaboração

Better Item amplia **leitura, interpretação, edição numérica e reutilização de referenciais espaciais**, junto com alinhamento e distribuição. Não pretende substituir todas as ferramentas de transformação do Blender nem resolver toda combinação matemática que o Blender consegue representar.

Gabriel prefere entender responsabilidades, fluxo de dados, trade-offs e limites. Não aceite feedback externo como prova. Diferencie reprodução, inspeção estática, hipótese, registro histórico e decisão de escopo. Antes de alterar o sistema, entenda o caminho existente. Não comece com refatoração geral ou implementação de todas as sugestões de um relatório.

### Decisões que devem ser preservadas

- **Sem animação relativa, keyframes próprios, bake de animação ou runtime de playback.** O experimento antigo permanece apenas em `archive/better_item-animation-1.5.1/`; não o reintegre. Testes que animam dados nativos para validar invalidação de cache NÃO são uma funcionalidade de animação do produto.
- **Sem descoberta/listagem de Custom Orientations da cena como fonte direta.** Essa capacidade foi removida na 1.7.5 por fragilidade de acesso à lista na API. Não restaurar parsing de texto de exceções, sondagens que dependam de mensagens ou outro contorno equivalente.
- **Exportar a orientação de um Frame para uma Transform Orientation nativa continua suportado.** É uma operação diferente da descoberta acima. Permite usar G/R e ferramentas nativas com os eixos do Frame. A exclusão externa da orientação deve ser reconhecida pelo addon.
- Não reintroduzir a escolha redundante de usar o pivô atualmente selecionado na viewport como mais uma fonte genérica de Location. Distinguir isso de uma orientação nativa View e da exportação de Frame.
- **Geometry Nodes afim de Dimensions é aceito.** Não é um novo produto genérico de modificadores. Ele cobre transformações geométricas que não cabem nos três canais de Scale; deve preservar malha, dados compartilhados e integridade da pilha.
- Transform edita o **objeto ativo**. Não transformar esse painel num editor em massa. Operações de seleção pertencem às ferramentas nativas e Align/Distribute.
- Referenciar não cria parenting, Child Of ou constraint permanente nos alvos. Mudar a fonte depois de uma edição comum não move o alvo. **Live** é a exceção explícita e temporária de edição, não animação.
- Restrições matemáticas legítimas devem ser diagnosticadas e recusadas sem efeitos parciais. Não eliminar proteções apenas para aumentar a taxa de sucesso.
- Preparar publicação com estabilização e revisão de UI, sem usar essa fase para ampliar silenciosamente funcionalidades. Novas otimizações de Normal exigem medição; flexibilização de constraints e novas interações de viewport exigem definição de escopo.

## 3. Contratos conceituais e de interface atuais

### Reference e Frames

- Ordem dos painéis: **Reference Frames → Transform → Align and Distribute**.
- No seletor de referências: **Location primeiro, Orientation depois**. Location tem ícone próprio; Orientation usa o ícone Gimbal. Seletores dependentes de Object/Frame ficam indentados com ramificação visual, sem competir como categorias principais.
- `Individual` permite escolher Location e Orientation separadamente. `Frame` seleciona um pacote dos dois componentes de uma só vez. Pelo Individual também é possível usar só um componente de um Frame.
- Frame não é um objeto auxiliar obrigatório. É um conjunto nomeado de origem e orientação. Ambos podem ser manuais ou vinculados independentemente, inclusive a **objetos distintos** ou outros Frames. Criar exige nome; as fontes são editadas depois. Aplicar uma fonte significa capturar seus dados e torná-los manuais, não aplicar TRS no alvo.
- Frames são persistidos na Scene e salvos no `.blend`. Detectar dependências circulares e referências inválidas. Não usar handles RNA como identidade duradoura.
- Transform e Align/Distribute compartilham a lógica de resolução de referências. Não criar outra classificação concorrente de origem/orientação porque um operador ainda tem campos legados.
- Configurações de Transform e vínculos XYZ permanecem em **Object.better_item**. Referências de arranjo e Frames ficam na **Scene**. Tornar Transform global ao painel foi sugerido, mas não foi implementado nem fechado como migração. Não afirmar que já é compartilhado.

### Transform e matemática

- `Default / Local` expõe a contribuição dos canais nativos, como Item do Blender; `Reference` interpreta os valores segundo origem e eixos escolhidos. Isso preserva a informação local que se perderia num painel exclusivamente mundial.
- Não confundir canais locais nativos com um referencial que gira/anda junto do próprio alvo: esse último pode produzir leitura constantemente zero. A antiga proposta desse “Local” autorreferente foi rejeitada.
- Location, Rotation e Dimensions não são três versões da mesma operação matricial. Location resolve coordenadas na base; Dimensions mede extensões **projetadas em direções unitárias**, não unidades alongadas pela escala do referencial; Rotation exige uma base rotacional adequada e tem recusas explícitas para casos não representáveis.
- Scale em Reference continua sendo **Scale (Default)**, os canais nativos, sem fingir que são fatores universais nos eixos externos. Preservar estado editável/bloqueado conforme contrato atual.
- `Rotate Around Reference Location` significa usar a Location selecionada como centro de rotação. Sem isso, a orientação escolhida define os eixos, enquanto a origem do objeto é o centro da edição. Não chamar isso genericamente de “usar referência”, pois ela já está em uso.
- Dimensions edita em torno da origem do próprio objeto. Um referencial de Location externo não desloca automaticamente esse centro.
- Precisão: cálculos em float64 não mudam a representação nativa float32. Verificar erros com orçamento da cadeia de matrizes, sem aceitar colapsos reais por uma tolerância arbitrariamente grande.
- Zeros relativos: resíduos dentro da incerteza precisam ser tratados coerentemente na leitura e no cálculo de proporção. Não apenas arredondar texto. `BI-T008` evita multiplicar um resíduo quase zero por uma razão gigantesca.
- Rotação linkada: zero é fallback de denominador de uma volta apenas **no eixo editado**, quando necessário. Não substituir todos os outros zeros por 360°. O erro antigo fazia (0°,0°,40°) virar (90°,90°,10°).
- Preservar sinais de escala, ordem Euler, Quaternion/Axis-Angle, deltas e parent inverse. Decompor uma matriz espelhada casualmente com `to_quaternion()` já causou mudanças espúrias de canais.

### Alignment e Distribution

- Min/Max/Center e Selection Bounds seguem o fluxo atual. Não restaurar seletores redundantes sem definir sua semântica e observar os caminhos legados do operador.
- Alignment tem posição e orientação. O histórico de Min/Center/Max não significa que Center seja média aritmética: o solver legado usa `(min+max)/2`. Não renomear esses conceitos como equivalentes.
- Distribution tem duas dimensões de escolha independentes: **método** (Offset/Endpoint) e **Placement** (o representante ou intervalo geométrico).
- **Offset:** Origins, Bounds Center, Center of Mass (Surface), Center of Mass (Volume), Geometry Bounds. O sinal de Spacing define o sentido. Não adicionar um seletor separado de direção.
- Offset/Geometry Bounds: o valor é o intervalo entre limites projetados. Zero permite contato e mantém o último sentido não zero. Offset deve preservar coordenadas não selecionadas no referencial. Não alinhar os demais eixos por efeito colateral.
- **Endpoint:** somente os quatro Placement de pontos. Geometry Bounds foi removido desse método na 1.7.3. Distribuir pontos dentro de um intervalo NÃO exige que as geometrias caibam, não redimensiona objetos e permite sobreposição.
- Endpoint/Between Points: Start→End define a linha; a Orientation compartilhada não define essa direção. Endpoint/Reference Axis: usa um eixo da Orientation, projetando End como limite axial; End pode estar fora da linha.
- Start normalmente vem da Location compartilhada; pode ser sobrescrito. End possui fonte própria: Manual, Global, Object, Frame, Cursor ou Active Object. Âncoras de objeto ficam fixas quando também estão selecionadas.
- Ordenação por posição/distância inicial precisa ser preservada conforme regra do método. No Offset, priorizar a meia-região contrária ao vetor de espaçamento e depois proximidade. Empates abaixo do mínimo devem informar os nomes, em vez de escolher uma ordem geometricamente ambígua.
- Não confundir **Bounding Box Center**, pivô nativo da seleção (em Object Mode, baseado nas origens selecionadas), com **Bounds Center**, representante da geometria avaliada de cada objeto.
- Não trocar Center of Mass por nomes inventados na UI; manter nomenclatura Blender Surface/Volume. Pontos soltos e geometria extrema influenciam bounds corretamente; não “consertar” intenção visual presumida do usuário.

### Live e diagnóstico

- Live é checkbox de sessão temporária, não diálogo modal Confirm/Cancel. Habilitar não move objetos; editar dados válidos passa a replanejar. Sem Live existe Distribute.
- Captura identidades dos alvos e do Active; permite trocar a seleção para manipular fontes. Observa cursor, objetos e Frames, incluindo fontes indiretas. Não retargetar automaticamente para a nova seleção.
- Sessão retém baseline e ordem pertinente, sem acumular deslocamentos a cada edição. Editar diretamente um alvo pausa a sessão em vez de sobrescrever a edição humana.
- Timer de observação ativo só na sessão; parada em Undo/Redo, load, troca de frame, render e unregister. A sessão não persiste no arquivo. Não transformar esse mecanismo em runtime de animação.
- Falta de objeto escolhido após selecionar o tipo Object é **ReferencePending/INFO**, etapa normal de configuração. Campos indisponíveis não devem se apresentar como zeros válidos/editáveis.
- A memória transitória das razões linkadas é limitada a 16 entradas e limpa em Undo/load/unregister. Mudança dos links invalida as entradas do objeto no callback existente, mesmo se os links forem imediatamente religados. Default Rotation inclui a ordem Euler nativa na chave. Referências resolvidas continuam incluídas na chave de Reference.
- Mensagens devem explicar condição e ação do usuário. Código BI ajuda diagnóstico, mas não substitui orientação. Não agrupar causas diferentes num except amplo com mensagem enganosa.

## 4. Mapa técnico e cuidados já aprendidos

| Módulo | Responsabilidade / ponto de atenção |
|---|---|
| `__init__.py` | Classes RNA, operadores, UI e registro/remoção de handlers. Na 1.7.7, Method precede Placement na declaração RNA para preservar kwargs diretos. |
| `references.py` | Resolver referências e desenhar seletor compartilhado; separar estado persistente de contexto avaliado. |
| `frames.py` | Frames, fontes independentes, ciclos, persistência, aplicação e indicadores visuais. Setas não são manipuladores interativos. |
| `native_refs.py` | Pivôs/orientações, cache de fingerprint Normal e publicação nativa. Falha inesperada mantém timer, isola Frame/cena, expõe BI-F006 e tenta novamente em 1/2/4/8 s. Exclusão externa é respeitada; suspensão por fonte inválida mantém a política anterior. |
| `transform_view.py` | Get/set de transformações interpretadas, leitura avaliada, Dimensions e estágio GN afim. |
| `math_core.py` | Matemática pura, vínculos e erros; testes puros não validam estado avaliado do Blender. |
| `engine.py` | Aplicação em canais/matrizes, hierarquias, travas/drivers, precisão, verificação e rollback. |
| `arrange.py` | Alinhamento e caminhos de distribuição/compatibilidade legados. |
| `distribution.py` | Planejamento atual, fontes Start/End, aplicação e inspeção. Cache escalar com dependências numéricas para updates só de transformação; geometria e eventos desconhecidos continuam conservadores. |
| `placement.py` | Representantes avaliados/limites; enums e armazenamento por método. Cuidado com proxy RNA do operador. |
| `geometry_arrange.py` | Planejar/verificar intervalos projetados. Considerar orçamento de posição de ambos os objetos adjacentes. |
| `distribution_preview.py` | Sessão Live, captura de contexto/alvos e observação transitória. |
| `orientation.py` | Operações orientadas auxiliares. Não presumir que todos os ramos históricos continuam chamáveis. |
| `diagnostics.py` / `trace.py` | Severidade, instrução ao usuário e inspeção das contribuições de transformação. |

Planejar primeiro, validar plano, aplicar e conferir resultado avaliado. Em falha, restaurar os objetos envolvidos sem modificar não envolvidos. Não compartilhar cegamente a validação de canais TRS com um futuro solver BMesh.

### Geometry Nodes e caches

- Ler malha avaliada com `evaluated_get`, `to_mesh` e liberação em `finally`; extração bulk por `foreach_get` e projeção NumPy. Não executar loops Python de vértices densos a cada redraw.
- Instâncias não realizadas não equivalem automaticamente à malha final; existe recusa explícita. Não inventar avaliador de GeometrySet para contornar escopo sem necessidade.
- O estágio GN próprio de Dimensions usa identificação/integridade e copy-on-write. Se o modificador deixar de ser final, não duplicar nem reordenar a pilha silenciosamente. O manual descreve o caso e a proteção introduzida.
- O cache de **geometria/Dimensions** e o cache de **inspeção de espaçamento** são coisas diferentes. O primeiro possui invalidação de dependências de geometria; o segundo é escalar e compartilhado por draw/getter. Na 1.7.8 ele preserva entradas após transformações alheias, mas continua amplo para geometria e eventos não classificados. Não anunciar um como otimização do outro.
- Getters e draw devem evitar escrita persistente e operações de cena. Migração precisa ocorrer em contexto permitido, não disfarçada como leitura.
- Não reter wrappers de Custom Orientation, Object removido, BMesh ou outros dados RNA ao atravessar Undo, reload ou callbacks. Reobter com identidade validada; armazenar cópias numéricas quando apropriado.


## 5. Limites e pendências técnicas

- Checklist real de teclado/mouse não executado; manter esse limite explícito. Não marcar digitação, Esc/arrasto, F9 ou seleção física como testados por setters.
- Crashes em sondagens artificiais de janela não tiveram causa conclusivamente isolada. O cenário final válido passou; uma nova reprodução de uso normal deve ser investigada sem presumir a mesma causa.
- Minimum Separation não é erro máximo. Geometry Bounds já aceitou 1 mm de gap a 1 km da origem com cerca de 0,051 mm de erro dentro do orçamento atual. Exatidão absoluta exige definir tolerância e faixa de operação antes de alterar contrato.
- Invalidação geométrica permanece conservadora. Trabalho de desempenho exige medição de custo e frescor; não confundir cache de geometria/Dimensions com inspeção escalar de espaçamento.

## 6. Validação

Use clone/checkout e workspace isolados. Neste computador, novos ambientes e portáteis devem ficar no **D:** conforme pedido de Gabriel. A pasta exibida como cwd pode ser o antigo projeto Mixer e não contém necessariamente o fonte atual. Não modificar instalação nem arquivos `.blend` de clientes.

```powershell
python tests/better_item/compatibility/prepare_matrix.py --repository C:/work/Blender-Plugins --workspace C:/work/better-item-matrix
python C:/work/better-item-matrix/download_portables.py 5.3.0
python C:/work/better-item-matrix/extract_portable.py 5.3.0
python C:/work/better-item-matrix/run_matrix.py --exe C:/work/better-item-matrix/portable/blender-5.3.0-windows-x64/blender.exe --version 5.3.0
```

Python 3.11+; se o Python de sistema for 3.8, use o distribuído com Blender para os utilitários que exigem recursos novos de pathlib/tomllib. O runner verifica o SHA256, a versão, o fingerprint Python e os bytes/inventário importados antes de cada processo, além do manifesto de inputs de teste. Preparação incompatível é recusada sem apagar resultados/perfis; use um ambiente novo. Qualquer falha de integridade marca o summary como reprovado, mesmo depois de testes aprovados. O bootstrap desativa bytecode explicitamente. O runner fixa o SHA256 do instalador em `suite.json`: uma correção nova precisa de workspace/suite preparados para o **novo artefato**, sem substituir relatórios históricos. `--only` e o estudo opcional estão documentados no README do runner.

Chamada mínima de script:

```powershell
& 'C:/path/blender.exe' --background --factory-startup --python-exit-code 1 --python 'C:/work/test.py'
```

- **Sempre `--python-exit-code 1`.** Sem isso, exceção Python pode deixar exit code 0. Conferir JSON, logs, timeout e término de fases assíncronas, não só o processo.
- Use perfis separados via BLENDER_USER_CONFIG/SCRIPTS/DATAFILES/EXTENSIONS. O runner prepara isso e testa instalação pelo operador real de extensões.
- Scripts antigos podem exigir módulo/fixture ao lado ou `addon_utils.enable`; prepare_matrix resolve o ambiente das entradas listadas. Não rodar indiscriminadamente todos os testes históricos: os de Custom 1.7.4 foram retirados da matriz corrente.
- Background valida matemática e dados, mas não prova mouse/GUI. Um `bpy` PyPI não equivale necessariamente ao executável completo em contexto de janela. Para F9/Undo usar o runner GUI real com estado fresco.
- Após Undo/load, reobtenha contexto e wrappers. Um encerramento GUI 5.1 falhou também sem addon: o timer não tinha window depois de reload. O launcher obtém uma window atual e usa `bpy.context.temp_override(window=window)` ao sair. É correção do **executor**, não workaround do produto.
- Ao lançar GUI auxiliar no Windows, `Start-Process -WindowStyle Hidden`, salvo quando usuário precisa interagir. Não abrir várias janelas visíveis sem necessidade.
- Validar resultado **e efeitos colaterais**: matriz avaliada, canais que devem ser preservados, dados compartilhados, seleção/Active, origens, pilha de modificadores, undo e rollback em recusa.
- Usar oráculo independente, float64 quando necessário, geometrias assimétricas e âncoras; não comparar somente duas funções que compartilham o mesmo bug.
- Refusos legítimos (ordem empatada, volume inválido, Gimbal singular, canais bloqueados, precisão insuficiente etc.) não são falhas da suíte. Verificar diagnóstico e ausência de efeito parcial.
- Não atribuir mensagens de shutdown como “not freed memory blocks” automaticamente ao addon. Reproduzir com controle sem addon antes de concluir.


## 7. Correção crítica 1.7.11 e continuidade da 1.8

A main continua em **f7337d0 / 1.7.10**. A candidata **release/1.7.11** nasce dessa base mais o teste independente de identidade (`a2b1bc0`). O erro reproduzido alinha X, altera Y/Z e informa sucesso quando um objeto local e outro vinculado têm o mesmo nome. É patch crítico separado, anterior à 1.8. [Relatório e pendências](release-1.7.11.md), [snapshot do candidato](handoff-1.7.11.json).

Planejamento, aplicação, verificação e Live usam chaves de objeto; nomes servem para apresentação. Entradas antigas por nome nos helpers são aceitas só quando não ambíguas e normalizadas antes do cálculo. New Frame captura session_uid no operador para não atribuir um Frame ao homônimo depois de rename/troca de ativo. Essas identidades são transitórias; PointerProperty, IDs de Frame, enums e schema salvos não mudam. Não criar migração sem necessidade demonstrada.

O teste independente `test_better_item_identity1711.py` não deve ser alterado para acomodar a correção. `test_identity_frame1711.py` cobre New Frame, mapa legado ambíguo, presença na cena, alvo renomeado/removido e preservação da recusa BI-D002. Distribute moderno/legado não foi unificado, leitura zero e limpeza de cache não entram neste patch.

A branch **release/1.8**, em `3d951c4`, contém somente preparação. A fase 2 continua aguardando aprovação. Tema aprovado: **Quando o Better Item recusa ou não consegue medir, diz o motivo e deixa o usuário resolver.** Núcleo P2 → F4 → U2; quatro correções B1 propostas aguardam decisão. A unificação U1 foi refutada e o aviso P3 por distância/ULP não foi recomendado. Não retomar o antigo escopo de quatro frentes simultâneas.

O [roteiro v2](https://github.com/Borbofruto/Blender-Plugins/blob/release/1.8/docs/better_item/planejamento/roteiro-de-releases.md), o [escopo aprovado](https://github.com/Borbofruto/Blender-Plugins/blob/release/1.8/docs/better_item/planejamento/escopo-1.8.md) e o backlog permanecem na branch da 1.8. Após qualificar/publicar a 1.7.11, incorporar o patch à 1.8 e preservar o SHA original das evidências históricas. A 1.9 mantém legibilidade; mudar seu tema para comandos fora do painel continua proposta aberta. Animação segue fora; Edit Mode é 2.0.

Neste computador: portáteis em **D:/BetterItem/portables/**; novos ambientes em **D:/BetterItem/workspaces/**; candidata em **D:/BetterItem/release-1.7.11/**. Não usar Blender instalado. Não recriar pastas de teste espalhadas na raiz do D. Não remover o worktree da 1.8 enquanto a preparação aguarda decisão.
