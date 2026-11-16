# Better Item 2.0 — estudo de viabilidade de Edit Mode

Estado: estudo de arquitetura e primitivas, não implementação da funcionalidade. O instalador 1.7.6 continua destinado às capacidades atuais em Object Mode. Não foram adicionados campos de edição de vértices/arestas/faces ao produto.

## Conclusão sobre o mínimo de Blender

A base necessária para Mesh Edit Mode existe publicamente na 4.2: `bmesh.from_edit_mesh`, acesso a BMVert/BMEdge/BMFace, seleção/histórico/face ativa, camadas de dados, `bmesh.ops.transform`, atualização da malha de edição e multi-object Edit Mode. Não foi identificado um requisito técnico de 4.5/5.x para o escopo proposto. GeometrySet, introduzida na 4.5, pode ajudar outras leituras de geometria avaliada, mas não é necessária para editar o BMesh original.

Um programa isolado, sem importar Better Item, foi executado em versões registradas nos resultados do estudo. Ele confirmou seleção em duas malhas, escrita sob matrizes de objeto rotacionadas/escaladas/espelhadas, captura de orientação nativa de uma face com conferência da normal, Undo/Redo e salvar/reabrir atributos. Isso confirma as primitivas; não certifica o futuro produto completo, a experiência dos sliders ou desempenho em malhas grandes.

O custo relevante da 2.0 está na semântica de seleção, conectividade, identidade persistente e transações. Esses problemas existem também no Blender 5.3. Elevar o mínimo não os elimina.

## Como encaixar na arquitetura existente

1. **Manter o resolvedor de referências.** Location e Orientation continuam independentes, resolvidas como origem e base no mundo. Frames continuam um pacote desses dois componentes, e podem apontar para fontes diferentes. Acrescentar fontes de componente de malha nessa resolução é suficiente conceitualmente; não é necessário criar um sistema de Frames paralelo.
2. **Adicionar um caminho de escrita para a seleção da malha.** O engine atual transforma objetos e protege canais nativos, drivers e hierarquias. Edit Mode deve editar coordenadas BMesh. Não copiar todas as restrições de canais do objeto: mover um vértice não equivale a editar `obj.location`.
3. **Reutilizar matemática pura e planejadores quando o contrato coincidir.** Projeção em referências, alinhamento de pontos, ordenação e intervalos podem trabalhar com arrays. Captura de seleção, identificação dos alvos, geração de intervalos e aplicação precisam de implementação própria para geometria. Evitar uma refatoração geral antecipada; funções claras em um módulo de edição de malha são suficientes para iniciar.
4. **Manter a UI de referência compartilhada.** A interface continua Location/Orientation ou Frame. A seleção de um componente precisará identificar objeto e elemento, preferencialmente por captura da seleção ativa em vez de listas enormes de índices. O desenho definitivo dessa captura deve ser discutido antes da implementação.

Uma fonte de componente pode estar em outro objeto, sem obrigar esse objeto a entrar em Edit Mode: ler a malha original em Object Mode e o BMesh quando ela estiver em edição. Não alternar o modo do usuário apenas para atualizar uma referência. Guardar o objeto-fonte também é necessário, pois dois objetos podem compartilhar uma Mesh e possuir matrizes mundo diferentes.

Multi-object Edit Mode oferece uma lista de dados únicos, mas uma Mesh compartilhada não pode receber duas escritas independentes para suas duas instâncias. Precisamos preservar a semântica de dados vinculados, escolher um espaço de edição explícito e detectar planos incompatíveis, sem duplicar a Mesh silenciosamente.

## Transformação de coordenadas

Os vértices são armazenados no espaço local da malha. O painel pode continuar usando referências no mundo. Para um ponto local `x`, `M` é a matriz mundo do objeto e `T` a transformação planejada no mundo:

`x_local_novo = M.inverted() @ T @ M @ x_local`

O programa de estudo aplicou esse caminho a objetos com escala não uniforme e espelhamento, preservando vértices fora da seleção. Para destinos individuais, convertemos cada ponto mundial planejado por `M.inverted()` e escrevemos o resultado em `BMVert.co`.

Isso é diferente de decompor uma matriz de objeto em Location/Rotation/Scale. A geometria pode representar uma transformação afim que não caiba nos canais TRS do objeto. Algumas recusas do caminho de rotação de objetos, portanto, não devem ser transferidas automaticamente para o novo caminho. Continuam necessárias verificações de matriz singular, números finitos, precisão de armazenamento e estabilidade da referência.

As regras já estabelecidas de Location, rotação e projeção de Dimensions devem ser preservadas. Uma base oblíqua não pode ser tratada casualmente como uma rotação ortogonal.

## O que significa referenciar vértice, aresta ou face

| Componente | Location | Orientation exige definir |
| --- | --- | --- |
| Vértice | Coordenada do vértice | Um ponto isolado não define eixos. Pode-se usar normal/tangente da vizinhança quando disponíveis, uma orientação nativa ou uma fonte independente. |
| Aresta | Ponto médio ou outro ponto explicitamente escolhido | A direção da aresta define um eixo, mas não o giro em torno dele. Precisamos de uma segunda direção e uma convenção de sentido. Aresta de comprimento zero não define direção. |
| Face | Centro segundo critério declarado | Normal e tangente estável; a normal sozinha deixa um grau de liberdade. Faces degeneradas e mudanças na aresta usada como tangente precisam de tratamento explícito. |

Para superfícies sob escala não uniforme, transformar uma normal requer a inversa transposta da parte linear da matriz, não o mesmo cálculo de um vetor de posição. Espelhamento também exige uma convenção consistente de orientação. A captura nativa de orientação da face foi usada como comparação no estudo.

A combinação já existente de fontes independentes resolve muitos casos: Location de um vértice e Orientation de um Frame ou outro objeto, por exemplo. Não precisamos inventar uma orientação geométrica para toda seleção.

## Leitura de Rotation e Scale no painel

Uma seleção arbitrária não tem canais Euler e Scale nativos equivalentes aos do objeto. Ler Location e Dimensions de um conjunto é direto depois de escolher o ponto representativo. Apresentar Rotation e Scale como valores absolutos requer definir um referencial do elemento/grupo ou outra convenção verificável.

Essa definição é uma pendência de produto da 2.0. Não mostrar Euler arbitrário como se fosse um dado intrínseco da malha, nem escrever na escala do objeto inteiro quando o alvo declarado é apenas uma seleção. Uma solução pode tratar a orientação do elemento ativo ou de um Frame de trabalho, mas precisa ser discutida e testada antes de determinar a UI.

## Alinhamento e distribuição

- **Vértices:** representantes pontuais são as próprias coordenadas. É o primeiro caso mais simples para reutilizar os planejadores de pontos.
- **Arestas/faces desconectadas:** seus pontos representativos e limites projetados podem alimentar os planejadores. Aplicar uma translação ao elemento significa mover todos os seus vértices, uma única vez.
- **Ilhas conectadas:** uma ilha pode ser uma unidade de distribuição. Seus vértices formam um conjunto bem definido, evitando tratá-los repetidamente.
- **Elementos com vértices compartilhados:** duas faces que pedem translações diferentes podem exigir dois destinos incompatíveis para o mesmo vértice. Não existe um resultado que mantenha ambas rígidas sem alterar conectividade. Precisamos escolher a semântica: editar os pontos, distribuir ilhas, permitir deformação explícita ou recusar planos incompatíveis. Não separar a malha silenciosamente.
- **Âncoras:** o componente usado como chave pode compartilhar vértices com alvos. Essa condição precisa entrar no planejamento, antes da escrita.

O exemplo de faces compartilhadas é uma decisão do produto, não uma limitação da API 4.2. Um mapeamento de destinos por vértice permite detectar conflitos antes de modificar dados. A ordem e o sentido de distribuição devem seguir as regras já aprovadas para o produto, com uma definição explícita de qual componente/grupo é o alvo.

## Referências capturadas e vinculadas

Capturar o ponto e os eixos em um Frame manual é a opção simples e estável. Uma referência vinculada a um elemento exige mais:

- Índices BMesh não são identificadores persistentes. Podem mudar com edição, reindexação ou reconstrução da malha.
- Handles de BMVert/BMEdge/BMFace não devem atravessar Undo/Redo, troca de modo ou reconstrução de dados. Reobter os dados quando necessário.
- IDs próprios em camadas/atributos ajudam a localizar componentes, mas não resolvem sozinhos a identidade. O estudo confirmou que duplicar geometria também duplica os valores desses IDs.
- Exclusão, extrusão, subdivisão, merge e duplicação precisam de política de identidade. Em caso ambíguo, informar que a referência precisa ser escolhida novamente; não assumir silenciosamente o vizinho mais próximo.
- Position e Orientation do mesmo Frame podem continuar vinculadas a componentes ou objetos diferentes. O vínculo é fonte de leitura, não um Child Of que movimenta permanentemente o alvo.

Escolher a estratégia de persistência e migração dos novos campos será uma etapa da 2.0, antes de oferecer vínculo persistente em arquivos de usuários.

## Malha editável e resultado avaliado

A primeira implementação deve deixar clara a geometria sobre a qual atua. BMesh representa a malha em edição. Mirror, Subdivision, Array ou Geometry Nodes podem gerar faces que não correspondem a elementos editáveis com relação um-para-um.

Medir o resultado avaliado e editar diretamente cada elemento desse resultado são capacidades distintas. Não prometer inversão geral de modificadores. Começar com a malha editável é tecnicamente coerente, e referências a outros objetos/Frames permanecem disponíveis. Shape keys, seleção oculta, objetos compartilhando a mesma Mesh e edição multiobjeto precisam de testes e políticas próprias antes do lançamento.

## Transações, Undo e desempenho

Capturar seleção/referências, planejar em float64, validar o plano, escrever uma vez por vértice e atualizar o Edit Mesh. Mudanças só de coordenadas não são mudanças de topologia; `update_edit_mesh(..., destructive=False)` foi exercitado no estudo. Recalcular normais e triangulação quando necessário, sem alternar de modo a cada slider.

Uma falha deve restaurar coordenadas e preservar seleção, histórico, topologia e dados não relacionados. Uma edição por gesto precisa formar uma operação Undo coerente. Não chamar operadores complexos de maneira indiscriminada em callbacks RNA. O sucesso de Undo no programa de estudo não valida automaticamente o comportamento futuro de arraste dos campos.

Caches devem considerar seleção, coordenadas editáveis, referência, topologia, troca de modo e Undo/Redo. Não reutilizar diretamente um cache que só acompanha a geometria avaliada de Object Mode. O probe usa malhas pequenas; desempenho em seleções densas continua pendente.

## Sequência recomendada para a 2.0

1. Fechar semântica dos campos, do elemento ativo e das unidades de alinhamento/distribuição.
2. Implementar leitura e transformação de seleção de vértices em uma malha, com referências existentes e Frames capturados.
3. Validar Undo, referências que seguem a própria seleção, shape keys e precisão.
4. Acrescentar edição multiobjeto e grupos/ilhas, com detecção de destinos conflitantes.
5. Expandir fontes para arestas/faces com regras de orientação explícitas.
6. Implementar referências persistentes após fechar identidade e reação às operações topológicas.

A sequência organiza risco; não redefine sozinha o escopo final da 2.0 nem autoriza adicionar funcionalidades ao instalador atual.

## Fontes primárias e evidência

[API BMesh 4.2](https://docs.blender.org/api/4.2/bmesh.html), [operadores BMesh 4.2](https://docs.blender.org/api/4.2/bmesh.ops.html), [BMesh e seleção](https://docs.blender.org/api/4.2/bmesh.types.html), [cuidados de modo, memória e Undo](https://docs.blender.org/api/4.2/info_gotcha.html). O comportamento experimental está em `test_editmode_foundations.py` e nos resultados versionados do estudo, fora do instalador.
