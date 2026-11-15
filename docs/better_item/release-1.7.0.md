# Better Item 1.7.0 — distribuição por referências e edição interativa

## Entrega

Instalador no mesmo caminho `addons/better_item.zip`; versão interna 1.7.0. Execução validada em Blender 5.2.3 LTS / Windows. O mínimo 5.0 do manifesto continua declarado, sem execução adicional nessas versões ou em outros sistemas.

### Métodos e referências

- **Offset** mantém espaçamento com sinal, os eixos e a Location da referência compartilhada. A escolha de Bounding Box Center deixa de trocar implicitamente o algoritmo nas operações novas.
- **Endpoint / Between Points** usa o segmento Start→End e ignora a Orientation e os eixos externos. Start herda a Location do painel; Override Start permite outra fonte.
- **Endpoint / Reference Axis** projeta End em exatamente um eixo da Orientation por Start. Não é um efeito oculto do checkbox de origem.
- Cada extremo aceita coordenadas mundiais, Global, Object, Frame Location, cursor ou objeto ativo. A Orientation não utilizada de um Frame pode estar incompleta.
- Objetos selecionados usados como fontes dos extremos ficam fixos e ocupam as respectivas posições. Nos critérios geométricos, considera-se o ponto/intervalo correspondente da âncora; não se força seu centro a coincidir com uma origem deslocada.
- Empty e outros objetos sem superfície são âncoras válidas. Em Geometry Bounds delimitam espaço, mas não contam como uma peça geométrica.

### Critérios

Origins, Bounds Center (caixa mundial avaliada), Surface Centroid, Volume Centroid e Geometry Bounds. Os quatro primeiros são pontos representativos; o último considera intervalos ocupados para calcular vãos iguais. Nenhum muda a origem nativa, Rotation, Scale, malha-base ou pilha de modificadores dos alvos.

Volume Centroid integra uma superfície triangulada fechada com densidade uniforme. Valida incidência de arestas, orientação e volume não nulo. Não certifica ausência de auto-interseções ou validade física de cascas aninhadas. A geometria precisa satisfazer essas condições; o addon não faz reparação automática.

Em Geometry Bounds / Between Points, o centro da caixa mundial fornece a posição transversal, e o ponto médio dos extremos projetados fornece a posição axial. Isso permite mover o ponto representativo para a linha sem inventar uma orientação de roll para o objeto. Vértices soltos contam para bounds, mas não têm peso de área/volume.

Endpoint por limites usa a soma das larguras projetadas para calcular o vão interno. Se faltar espaço, informa a falta e recusa atomicamente; não comprime ou sobrepõe automaticamente. Exemplo validado: larguras 100/200/300 mm em 1.000 mm resultam em vão 200 mm e centros 50/400/850 mm, enquanto Origins resulta em 0/500/1.000 mm.

Endpoint ordena primeiro o semiespaço contrário a Start→End, depois por distância espacial ao início em cada semiespaço. Essa escolha técnica permite distribuir objetos inicialmente num plano perpendicular à nova linha. Distâncias indistinguíveis são recusadas com nomes, preservando a exigência de uma ordem definida. Offset mantém a ordenação axial anterior.

### Medição e prévia

Offset informa o espaçamento medido quando uniforme e **Mixed spacing** quando não há um valor único. Não fabrica média ou zero. O estado considera critério, eixos, direção e intervalo entre a âncora e a primeira peça. Fora de prévia, Set Spacing continua sendo o valor solicitado; dentro dela, o campo lê o resultado uniforme atual. Valores muito pequenos são formatados sem arredondamento enganoso para zero.

Live Preview inicia sem mover nada; a primeira edição aplica a uniformidade. Replaneja a partir das localizações iniciais e da seleção capturada. Confirm conserva o resultado; Cancel restaura as localizações iniciais. Recusas mantêm a última prévia válida. Mudanças de seleção/transformação externa exigem fechar a sessão; exclusão de alvo não impede cancelar. Undo/Redo nativos descartam o estado transitório da sessão e restauram poses normais.

Isso não é um vínculo persistente, um modificador ou um controlador de animação. Atualiza por edição dos controles, sem novo timer de poses, drivers, constraints ou keyframes. A sessão não é salva no `.blend`; as poses comuns são. Só uma prévia pode estar ativa por vez. Selection Median/Bounding Box dependente dos alvos deve ser capturada num Frame antes de usar Live; uma operação pontual pode usar a seleção inicial.

O F9 continua disponível para os parâmetros copiados do operador. Fontes são dados da cena, não propriedades do popup de redo: são ajustadas no painel e aplicadas por uma nova operação ou pela prévia ativa.

### Revisão das fontes

- Individual Origins sai dos seletores de ponto único; os valores antigos armazenados continuam legíveis.
- Opções contextuais de Location em Transform capturam um Frame independente. Em Frames, as opções de seleção e Normal/Gimbal/View são ações Capture que gravam valores Manual.
- Object/Frame explícitos continuam vínculos. Fontes contextuais de Frames antigos não são silenciosamente substituídas; o editor indica o contexto legado e oferece Apply.
- Bounding Box Center em Object Mode passa a usar origens, como o Blender. Bounds Center de posicionamento continua medindo a geometria.
- Escolhas de Frames removidos são limpas também nos campos de Start e End.
- Arquivos antigos com distribuição implícita por seleção conservam um caminho de compatibilidade. Trocar Method ou escolher explicitamente uma nova fonte compartilhada passa ao comportamento novo. Live fica desabilitado nesse caminho legado até a escolha explícita.

## Evidência executada

| Grupo | Resultado |
|---|---|
| Contratos 1.7 | Exemplo ponto/intervalo, 10 combinações oblíquas/reversas dos cinco critérios, âncoras/cursor, Frame com componente não utilizado inválido, override, projeção axial, oráculos de centroide, recusas atômicas, leitura, prévia e persistência |
| Matriz 1.7 | **320 lotes Endpoint + 140 lotes Offset**, com quatro peças por lote, cinco critérios, dois caminhos, quatro padrões de âncora, pais/espelhos, duas escalas de unidade e sete máscaras de eixos no Offset |
| Prévia | Undo/Redo pelo argumento nativo de undo; entrada inválida preserva último resultado; seleção alterada é protegida; Cancel restaura início; captura de seleção em Transform; âncora Empty nos cinco critérios |
| Dependências e cache | GN Object Info dependente da posição rejeitado nos quatro critérios geométricos; 24 leituras comparadas sem cache após shape key/modificador; exclusão de Frames; captura inválida preserva fonte anterior; intervalo não representável rejeitado; cancelamento após exclusão de alvo |
| Lote 200 | Geometry Bounds entre extremos: aproximadamente **0,22 s** para planejar/aplicar/verificar no cenário sintético; erro máximo de vão medido por vértices **4,11×10⁻⁵ unidades Blender** em um intervalo de 1.000 unidades. Não é benchmark da viewport inteira nem garantia de contato exato em números reais. |
| Outro processo | Salvar com fontes Endpoint/Frames, carregar e reaplicar em processo separado; carregar fixture preparada com o código 1.6.3 e preservar os extremos da distribuição antiga |
| Interface real | Invoke nativo, ativo→cursor, Mixed, Begin sem movimento, Offset ao vivo, Confirm/Undo/Redo, edição de End XYZ e Cancel; capturas inspecionadas |

Também passaram as regressões existentes: 168 combinações geométricas e 72 lotes de orientação da 1.6, arranjo antigo de 630 combinações, cache 1.5.4, limpeza 1.5.5, regressões de escala negativa/deltas/zeros/locks, matriz de **9.216** leituras/edições com **6.240 sucessos e 2.976 recusas verificadas**, 192 comparações de rotação nativa, e os 1.200 casos de Parent Inverse/842 movimentos em mm da suíte de escopo. Os testes são finitos e não demonstram ausência universal de defeitos.

O instalador é validado pelo comando de extensões do Blender e os testes novos de contrato/matriz/prévia são repetidos a partir do seu conteúdo extraído.

## Estrutura e limites para a próxima conversa de UI

`placement.py` mede pontos/intervalos; `distribution.py` resolve fontes, planeja e verifica; `distribution_preview.py` mantém exclusivamente a sessão transitória. O motor existente aplica as localizações com reversão. Integrações geométricas e leitura usam NumPy e a malha avaliada temporária, liberada após uso. O cache adicional guarda até 64 resultados pequenos, invalidados por revisão de geometria e matriz linear.

A UI funcional está pronta para avaliação; organização de grupos, nomes finais e densidade de informações podem ser refinados. Não foi implementado seguimento de curvas, alinhamento automático de rotação à linha, densidade física variável, edição de mass properties, distribuição permanente ou animação. Essas capacidades não são implícitas em Endpoint.
