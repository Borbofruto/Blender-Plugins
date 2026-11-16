# Matemática, precisão, Dimensions e Frames

[Índice](README.md) · [Manual integral](../CONTINUIDADE-IA.md)

> Leia primeiro [Contexto atual](../CONTEXTO-ATUAL.md). Este capítulo é histórico; não representa sozinho o estado vigente.

Base: Better Item 1.7.3, commit `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.

Gerado de CONTINUIDADE-IA.md, SHA-256 `e2f4f2a643dfa3fb1edb364d29cbfda1b70e157af8f732cb94c781a9439573e9`. Não editar este capítulo isoladamente; altere o manual integral e execute `gerar.py`.

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
