# Better Item — contexto atual e passagem de trabalho

Atualizado em **16/11/2026**. Leia este arquivo **antes** do manual histórico. Ele consolida as decisões posteriores à 1.7.3 e a revisão da 1.7.6. Não altera o runtime nem autoriza novas funcionalidades por si só.

## 1. Estado exato a assumir

- Repositório: [Borbofruto/Blender-Plugins](https://github.com/Borbofruto/Blender-Plugins).
- Base de código revisada: commit `a664cbf1b671db2bbb5ae521af05d65898b55960`, versão **1.7.6**. Confirme o HEAD real antes de trabalhar: um commit posterior de documentação não implica mudança do produto.
- Fonte editável: `src/better_item/`. Instalador estável: `addons/better_item.zip`.
- SHA256 desse ZIP: `a4182db99196e502768cae288781546d6c89619f3c7172cfbf78abc8fcadd382`.
- Os 15 arquivos Python são byte a byte iguais aos da 1.7.5. O hash combinado registrado pela matriz é `37848ddc104c3c10dfcedb8758b2e16e9d40c5811feb1568b85ab11603aa3b5f`; o inventário individual está no [snapshot atual](handoff-1.7.6.json).
- Mínimo do manifesto: **Blender 4.2.0**. A versão 1.7.6 mudou versão, mínimo e documentação, sem adaptar os algoritmos Python.
- A última atividade foi revisão técnica e reprodução de um bug. **As correções descritas abaixo ainda não foram implementadas.** Esta passagem é documentação, não uma versão 1.7.7.

### Ordem de leitura e autoridade

1. Solicitação atual de Gabriel e instruções do workspace.
2. Este contexto: contratos atuais, pendências e limites da evidência.
3. [Manual de engenharia](CONTINUIDADE-IA.md), com 25 seções, ou [capítulos gerados](continuidade/README.md). Sua base continua explicitamente **1.7.3**; detalhes históricos não anulam atualizações deste contexto.
4. [Compatibilidade 1.7.6](compatibility-1.7.6.md), [estudo Edit Mode 2.0](edit-mode-2.0-feasibility.md), README do pacote e código no commit efetivamente usado.
5. Relatórios antigos como evidência de suas respectivas versões, não como requisitos atuais.

O manual histórico explica arquitetura, matemática, casos já resolvidos, bootstrap e estratégia de testes. Ele NÃO deve ser substituído apenas por este resumo. As divergências conhecidas estão explicitadas na seção 9 abaixo. Nunca faça uma atualização global de números de versão em relatórios históricos para aparentar validação atual.

## 2. Produto, escopo e colaboração

Better Item amplia **leitura, interpretação, edição numérica e reutilização de referenciais espaciais**, junto com alinhamento e distribuição. Não pretende substituir todas as ferramentas de transformação do Blender nem resolver toda combinação matemática que o Blender consegue representar.

Gabriel prefere entender responsabilidades, fluxo de dados, trade-offs e limites. Não aceite feedback de outra IA como prova. Diferencie reprodução, inspeção estática, hipótese, registro histórico e decisão de escopo. Antes de alterar o sistema, entenda o caminho existente. Não comece com refatoração geral ou implementação de todas as sugestões de um relatório.

### Decisões que devem ser preservadas

- **Sem animação relativa, keyframes próprios, bake de animação ou runtime de playback.** O experimento antigo permanece apenas em `archive/better_item-animation-1.5.1/`; não o reintegre. Testes que animam dados nativos para validar invalidação de cache NÃO são uma funcionalidade de animação do produto.
- **Sem descoberta/listagem de Custom Orientations da cena como fonte direta.** Essa capacidade foi removida na 1.7.5 por fragilidade de acesso à lista na API. Não restaurar parsing de texto de exceções, sondagens que dependam de mensagens ou outro contorno equivalente.
- **Exportar a orientação de um Frame para uma Transform Orientation nativa continua suportado.** É uma operação diferente da descoberta acima. Permite usar G/R e ferramentas nativas com os eixos do Frame. A exclusão externa da orientação deve ser reconhecida pelo addon.
- Não reintroduzir a escolha redundante de usar o pivô atualmente selecionado na viewport como mais uma fonte genérica de Location. Distinguir isso de uma orientação nativa View e da exportação de Frame.
- **Geometry Nodes afim de Dimensions é aceito.** Não é um novo produto genérico de modificadores. Ele cobre transformações geométricas que não cabem nos três canais de Scale; deve preservar malha, dados compartilhados e integridade da pilha.
- Transform edita o **objeto ativo**. Não transformar esse painel num editor em massa. Operações de seleção pertencem às ferramentas nativas e Align/Distribute.
- Referenciar não cria parenting, Child Of ou constraint permanente nos alvos. Mudar a fonte depois de uma edição comum não move o alvo. **Live** é a exceção explícita e temporária de edição, não animação.
- Restrições matemáticas legítimas devem ser diagnosticadas e recusadas sem efeitos parciais. Não eliminar proteções apenas para aumentar a taxa de sucesso.
- Preparar publicação com estabilização e revisão de UI, sem usar essa fase para ampliar silenciosamente funcionalidades. Otimização de Normal, flexibilização de constraints e novas interações de viewport ficaram em trabalhos separados.

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

- O usuário voltou a perguntar sobre Min/Max/Center e Selection Bounds; depois concordou com a explicação do fluxo atual. **Não interpretar essa pergunta como autorização pendente para restaurar menus redundantes.** Leia o painel e os caminhos legados antes de modificar a semântica.
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
- Mensagens devem explicar condição e ação do usuário. Código BI ajuda diagnóstico, mas não substitui orientação. Não agrupar causas diferentes num except amplo com mensagem enganosa.

## 4. Mapa técnico e cuidados já aprendidos

| Módulo | Responsabilidade / ponto de atenção |
|---|---|
| `__init__.py` | Classes RNA, operadores, UI e registro/remoção de handlers. Bug atual no recebimento dos argumentos do operador de distribuição. |
| `references.py` | Resolver referências e desenhar seletor compartilhado; separar estado persistente de contexto avaliado. |
| `frames.py` | Frames, fontes independentes, ciclos, persistência, aplicação e indicadores visuais. Setas não são manipuladores interativos. |
| `native_refs.py` | Pivôs/orientações nativos e publicação/sincronização de orientação de Frame. A descoberta Custom removida não deve voltar. |
| `transform_view.py` | Get/set de transformações interpretadas, leitura avaliada, Dimensions e estágio GN afim. |
| `math_core.py` | Matemática pura, vínculos e erros; testes puros não validam estado avaliado do Blender. |
| `engine.py` | Aplicação em canais/matrizes, hierarquias, travas/drivers, precisão, verificação e rollback. |
| `arrange.py` | Alinhamento e caminhos de distribuição/compatibilidade legados. |
| `distribution.py` | Planejamento atual, fontes Start/End, aplicação e inspeção de espaçamento; cache escalar amplo. |
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
- O cache de **geometria/Dimensions** e o cache de **inspeção de espaçamento** são coisas diferentes. O primeiro possui invalidação de dependências de geometria; o segundo é um cache escalar pequeno, compartilhado por draw/getter, invalidado amplamente. Não anunciar um como otimização do outro.
- Getters e draw devem evitar escrita persistente e operações de cena. Migração precisa ocorrer em contexto permitido, não disfarçada como leitura.
- Não reter wrappers de Custom Orientation, Object removido, BMesh ou outros dados RNA ao atravessar Undo, reload ou callbacks. Reobter com identidade validada; armazenar cópias numéricas quando apropriado.

## 5. Pendências atuais: estado e próximo passo

### A. Confirmado e ainda sem correção — parâmetros Python do Endpoint

Reprodução em Windows, Blender **4.2.23 LTS e 5.3.0**, fonte publicada 1.7.6. Foram 11 chamadas por build, total 22, com registro dos valores efetivamente recebidos em execute e das posições finais.

`bpy.ops.better_item.distribute(method='ENDPOINT', distribution_mode='VOLUME')` retorna FINISHED, mas execute recebe ORIGINS. O mesmo ocorre com BOUNDS_CENTER e SURFACE. GEOMETRY também cai em ORIGINS em vez de recusar. Trocar a ordem dos dois kwargs não resolveu. Informar a propriedade interna `endpoint_placement=4` produziu VOLUME e posições diferentes, como esperado para uma malha deslocada de sua origem.

O operador tem enum proxy com get/set em `placement.operator_read/operator_write`, e inteiros ocultos por método. `invoke` copia o estado da Scene; a chamada EXEC direta é outro caminho. **A reprodução demonstra a perda do parâmetro, não estabelece por si só toda a sequência interna do RNA que a causa.** Não prometer que basta reordenar duas declarações antes de testar.

Material reproduzível e resultados: [evidências desta revisão](continuidade/evidencias-1.7.6/README.md). Script é diagnóstico que captura o comportamento atual, NÃO uma regressão verde que prova o comportamento correto. A futura correção precisa de assertions de equivalência entre pedido e resultado.

Ao corrigir: cobrir as quatro bases válidas via chamada direta, ambas as ordens de kwargs, GEOMETRY inválido sem mover objetos, Offset, invoke do painel, F9/redo e memória de Placement por método. Usar geometrias com origem deslocada: cubos centrados na origem não distinguem Origins de centroides. Preservar migração e IDs dos enums salvos.

### B. Confirmado e ainda sem correção — changelog

`src/better_item/CHANGELOG.md` começa com 1.7.6/1.7.5 antes do título e não contém entrada 1.7.4. Corrigir ordem e reconstruir a entrada a partir de `release-1.7.4.md`, identificando que a capacidade foi removida na versão seguinte. Não reintegrá-la. Conferir versão de manifesto, `bl_info`, primeiro bloco e paridade do ZIP quando houver entrega.

### C. Confirmado por código — invalidação ampla da inspeção

`distribution.invalidate_inspection` executa `clear_inspection()` se houver qualquer atualização no Dependency Graph. Evita dados obsoletos, mas atualizações não relacionadas também descartam resultado. O revisor externo mediu 0,3–0,5 s/600 objetos e 1,2–1,7 s/1500 em alguns modos; **esses tempos não foram reproduzidos localmente nesta revisão**.

Investigar com contadores/perfil e cenas representativas antes de impor limite de objetos. Qualquer seletividade precisa acompanhar modificadores, shape keys, Geometry Nodes e fontes indiretas, cursor, seleção, Undo e Live. Uma aplicação nunca deve confiar numa validação em cache antiga.

### D. Validação humana e publicação

Há testes automatizados com GUI real e Undo/Redo no Windows, preservados na matriz. Isso não equivale a uma passada manual completa com mouse. Revisar ligar/editar/desligar Live, troca de fontes, Endpoint, F9, Undo/Redo, larguras do painel e mensagens em 4.2 e versão recente. Testadores externos podem trazer fluxos não cobertos; registrar cenário e contrato esperado.

### E. Pendências separadas, não iniciar automaticamente

- **Normal:** reduzir custo de reconstruir assinaturas de seleção densa, sem perder frescor ou contexto. Não é sinônimo do cache escalar acima.
- **Constraints:** o bloqueio conservador pode recusar constraints que não afetam o canal solicitado. Flexibilizar exige estudar dependências e verificação, não apenas uma whitelist por tipo.
- **Interações novas:** gizmos manipuláveis de Frame/pivô e operações extras são expansão de produto.
- **Transform compartilhado:** decidir dono do estado e migração antes de mudar Object para Scene/Workspace.
- **Benchmark:** o usuário solicitou estudar outros addons CAD/espaciais para reutilizar métodos robustos; não há comprovação, nesta passagem, de um benchmark abrangente concluído. Consultar fontes/licenças e comparar contratos antes de copiar soluções.
- **Comercial:** existe material de roadmap externo; não confundir recomendações comerciais com novas features aprovadas. Não afirmar que loja/publicação já foi concluída.
- Riscos antigos sobre timers, múltiplas cenas e contexto continuam pistas de investigação; não os anunciar como bugs atuais sem reprodução. Ver seção 23 do manual histórico e priorizar os itens confirmados acima.

## 6. Compatibilidade atual e o que foi realmente testado

Relatório autoritativo e resultados: [compatibility-1.7.6.md](compatibility-1.7.6.md), `tests/better_item/results/1.7.6/` e [ferramentas de reprodução](../../tests/better_item/compatibility/README.md).

| Builds Windows x64 | Origem da evidência |
|---|---|
| 4.2.0 e 5.3.0 | Matriz completa no ZIP final 1.7.6, 19 API/regressão + instalação. |
| 4.2.23, 4.3.2, 4.4.3 | Candidato 1.7.6, mesmo Python e mínimo; diferença final documental. |
| 4.5.16 | 19 regressões do mesmo Python na 1.7.5 e instalação repetida com ZIP final 1.7.6. |
| 5.0.1, 5.1.2, 5.2.4 | Evidência 1.7.5 reutilizada porque Python é idêntico; não afirmar execução completa do novo ZIP nessas builds. |

Cobertura inclui Location/Rotation/Dimensions, hierarquias e sinais, deltas, Geometry Nodes, caches, isolamento de dados, distribuição e Live, GUI, Undo/Redo e persistência. Grade de estado: 8.064 combinações por build, incluindo recusas esperadas. Os números são casos finitos, não prova de todos os estados possíveis. Consulte JSON e suite em vez de somar resultados de épocas diferentes como uma execução nova.

Fixture 4.2.0→5.3.0 passou com Frame vinculado, referência relativa, configurações de distribuição e GN. Não é promessa de compatibilidade universal de arquivos nem de abertura de arquivo novo em versão antiga.

Sem certificação macOS/Linux/GPU/backends/todos os patches. O revisor externo usou Linux/bpy PyPI e trouxe evidência adicional, mas não substituiu a matriz Windows nem testou mouse. Relatórios podem ter builds 5.2.3 externas versus 5.2.4 da matriz; não trocar esses números.

## 7. Como testar sem repetir erros de infraestrutura

Use clone/checkout e workspace isolados. A pasta exibida como cwd pode ser o antigo projeto Mixer e não contém necessariamente o fonte atual. Não modificar instalação nem arquivos `.blend` de clientes.

```powershell
python tests/better_item/compatibility/prepare_matrix.py --repository C:/work/Blender-Plugins --workspace C:/work/better-item-matrix
python C:/work/better-item-matrix/download_portables.py 5.3.0
python C:/work/better-item-matrix/extract_portable.py 5.3.0
python C:/work/better-item-matrix/run_matrix.py --exe C:/work/better-item-matrix/portable/blender-5.3.0-windows-x64/blender.exe --version 5.3.0
```

Python 3.11+; se o Python de sistema for 3.8, use o distribuído com Blender para os utilitários que exigem recursos novos de pathlib/tomllib. O runner fixa o SHA256 do instalador em `suite.json`: uma correção nova precisa de workspace/suite preparados para o **novo artefato**, sem substituir relatórios históricos. `--only` e o estudo opcional estão documentados no README do runner.

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

### Ambiente local existente — verificar disponibilidade

- Fonte publicada congelada: `C:/Users/gabri/Documents/Codex/better-item-176/publish176/src/better_item/`.
- ZIP final: `C:/Users/gabri/Documents/Codex/better-item-176/publish176/addons/better_item.zip`.
- Workspace de matriz: `C:/Users/gabri/Documents/Codex/better-item-compatibility/`.
- Executáveis preservados em `portable/blender-4.2.23-windows-x64/blender.exe` e `portable/blender-5.3.0-windows-x64/blender.exe` dentro desse workspace.
- Blender instalado do usuário: `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe` (5.2.3 neste ambiente).
- Python bundled usado para utilitários: `C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe`.
- Revisão com script e resultados: `C:/Users/gabri/Documents/Codex/better-item-review176-report/`.
- Este pacote de documentação: `C:/Users/gabri/Documents/Codex/better-item-handoff-176/`.

São conveniências locais, não pré-requisitos portáveis. Alguns portáteis antigos foram removidos para liberar disco; preserve resultados, URLs e checksums. Confira espaço antes de extrair outra build (aproximadamente 1 GB por extração, além do ZIP). Não apagar instalações do usuário. Em outro computador, use os comandos de preparação oficiais em vez de presumir esses caminhos.

## 8. Edit Mode 2.0 — estudo concluído, produto não implementado

Gabriel pediu viabilidade para transformar, alinhar e distribuir vértices/arestas/faces usando referências de componentes, objetos e Frames. Quer discutir como fazer antes de começar uma grande versão 2.0.

O [estudo](edit-mode-2.0-feasibility.md) e `test_editmode_foundations.py` demonstraram primitivas BMesh em 4.2.0/4.2.23/4.3.2/4.4.3/5.3.0. Não foi identificada exigência de API exclusiva 4.5/5.x para o escopo pretendido. Isso permitiu suportar 4.2 nas capacidades atuais sem bloquear a futura proposta. Não significa que a 2.0 esteja pronta.

Reutilizar resolvedor de referências, matemática e planejadores quando contratos coincidirem; criar caminho de escrita BMesh separado da escrita de canais Object. Para transformar ponto local pela transformação mundial T: `x_novo = M.inverted() @ T @ M @ x`. Não refatorar todos os motores antecipadamente para uma abstração universal.

Definir ANTES da UI:

- significado de Rotation/Scale de uma seleção sem TRS intrínseco;
- unidade de distribuição (vértice, componente, ilha) e destinos incompatíveis de vértices compartilhados;
- orientação de ponto/aresta/face: normal sozinha não define todos os graus de liberdade;
- identidade persistente: índices e wrappers não sobrevivem à edição; duplicação copia IDs customizados, logo um inteiro não resolve sozinho;
- referências capturadas versus vinculadas e reação a exclusão/reindexação/merge;
- multiobjeto e Mesh compartilhada: não escrever dois destinos conflitantes nem duplicar dados silenciosamente;
- malha editável versus resultado avaliado dos modificadores, shape keys, seleção oculta e desempenho.

Sequência sugerida, ainda dependente de definição: vértices em uma malha com referências existentes/Frames capturados → validação de Undo/precisão → multiobjeto/ilhas → arestas/faces → referências persistentes. Um probe pequeno de BMesh não valida sliders, todas as features ou malhas densas.

## 9. O que mudou desde o manual 1.7.3

| Informação antiga | Leitura correta hoje |
|---|---|
| Mínimo 5.0 e testes concentrados em 5.2.3 | Mínimo 4.2.0, matriz e proveniência da seção 6. |
| Compatibilidade é apenas uma pendência | Investigação e matriz foram executadas; expansão de plataformas ainda não certificada. |
| Possibilidade de buscar Custom Orientation da cena | Implementada experimentalmente na 1.7.4 e removida na 1.7.5; não restaurar. Exportação de Frame preservada. |
| Capítulos/JSON antigos são estado mais recente | São snapshot 1.7.3. Este contexto e snapshot 1.7.6 têm prioridade para o estado atual. |
| Pendências genéricas de runner unificado | Há toolkit em `tests/better_item/compatibility/`. Inspecioná-lo antes de propor recriação. |
| Tudo que passa nos testes é coberto por script | O bug de kwargs diretos passou despercebido; caminho invoke não cobre EXEC_DEFAULT. |
| Endpoint com Geometry Bounds | Já retirado na 1.7.3; não confundir testes anteriores com contrato vigente. |

## 10. Entrega, repositório e continuidade

O usuário já autorizou publicação da documentação em GitHub público. Não enviar documentos externos de terceiros integralmente sem necessidade: esta passagem registra análise própria, referências locais e evidências reproduzidas.

Manter `addons/better_item.zip` atualizado **no mesmo caminho**; não criar uma coleção de ZIPs de novas versões na raiz ou em addons. O código editável continua em src e os testes fora do instalador. Artefatos históricos preexistentes em dist/archive não devem ser apagados por essa regra sem uma tarefa específica.

Em entrega de runtime: conferir manifesto/bl_info/README/changelog; pacote sem bytecode, outputs de teste ou segredos; comparar bytes empacotados com src, SHA256 e instalação nativa; executar regressões adequadas e matriz de compatibilidade conforme impacto. Atualizar toolkit para apontar ao novo ZIP. Não rebatizar evidência antiga como teste da versão nova. Em documentação-only, NÃO incrementar versão nem reconstruir instalador sem motivo.

Ferramenta usada em sessões anteriores: conector GitHub para ler árvore/blobs e publicar commit com base tree e atualização protegida do ref. Git convencional também é adequado em checkout correto. Sempre conferir HEAD e arquivos alterados; não sobrescrever mudanças concorrentes. Só publicar o escopo autorizado. Este trabalho de documentação não autoriza editar o runtime como parte oculta da preparação.

### Primeiro trabalho recomendado à próxima IA

1. Confirmar HEAD, versão, fonte/ZIP e ler os documentos nesta ordem.
2. Reproduzir o bug direto de Endpoint no ambiente disponível, sem confundir script diagnóstico com teste de aceitação.
3. Apresentar diagnóstico e menor correção, preservando UI/invoke/F9/Placement/migração. Observar o pedido atual de Gabriel para definir se a execução está autorizada.
4. Tratar changelog e validações de entrega junto de uma correção de manutenção, sem inventar uma versão de features.
5. Investigar desempenho apenas com evidência, mantendo escopo congelado. Separar depois discussão de UI, teste humano e futura 2.0.

Uma mensagem pronta está em [MENSAGEM-NOVA-CONVERSA.md](MENSAGEM-NOVA-CONVERSA.md). Não é necessário transferir o histórico inteiro da conversa, mas a próxima IA precisa realmente conseguir abrir os documentos e o repositório; se não conseguir, deve declarar a falta de acesso antes de afirmar que revisou.
