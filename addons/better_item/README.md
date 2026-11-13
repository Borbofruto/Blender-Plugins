# Better Item 1.0.1

Painel de transformações proporcionais, alinhamento e distribuição por origens para Blender. Autor: Gabriel Webber do Nascimento. Licença GPL-3.0-or-later.

## Instalação

Em Edit > Preferences > Add-ons > Install from Disk, escolha `better_item-1.0.1.zip` e ative Better Item. No viewport, pressione N e abra a aba Better Item. Funciona no Modo Objeto. Compatibilidade declarada: Blender 5.0 ou superior; testes executados no Blender 5.2.3 LTS.

## Transformações

O painel acompanha os valores nativos do objeto ativo: posição local, rotação com seletor de modo, escala e dimensões. Os cadeados são os bloqueios nativos do Blender; as correntes definem quais componentes participam de uma alteração proporcional. O botão no título vincula ou desvincula XYZ; as correntes de cada linha permitem vincular apenas dois eixos.

Com XYZ vinculados, dimensões de (100, 200, 600) mm passam para (300, 600, 1800) mm quando X muda para 300 mm. A mesma regra de multiplicação vale para posição, escala e ângulos Euler. Um eixo desvinculado muda sozinho. Alterar dimensões altera a escala nativa; são duas representações da mesma transformação.

Para posição, escala e dimensões, um valor de origem zero não define uma proporção para um novo valor diferente de zero: desvincule o eixo para alterá-lo independentemente. Uma dimensão geometricamente nula exige editar a geometria. Se um eixo vinculado estiver bloqueado, a alteração inteira é cancelada e uma mensagem aparece no painel. Campos controlados por drivers precisam ser liberados antes da edição.

Na proporção de rotação, 0° é interpretado como 360°, tanto no valor anterior quanto no novo valor e nos demais eixos vinculados. O campo editado mantém o valor digitado. Por exemplo, (0°, 0°, 0°) com XYZ vinculados passa a (90°, 90°, 90°) ao editar X para 90°. Voltas explícitas, como 720°, e ângulos negativos são preservados. Essa convenção remove a divisão por zero; não torna a razão contínua perto de 0°, portanto valores próximos de zero ainda podem produzir fatores grandes.

Vínculos de rotação funcionam nos seis modos Euler, multiplicando os ângulos armazenados. Quaternion e eixo-ângulo continuam disponíveis como campos nativos, sem vínculo proporcional. Multiplicar ângulos Euler não representa uma interpolação da orientação espacial.

Os vínculos pertencem a cada objeto e ficam salvos no arquivo .blend. As unidades seguem a cena; entradas como `300 mm` também são aceitas. Edições no painel nativo aparecem no Better Item, mas somente edições feitas no Better Item aplicam suas correntes.

## Alinhamento

Escolha X, Y e/ou Z globais. Todas as referências são as **origens**, sem usar as bordas das malhas.

- Limites da seleção: alinhar à menor coordenada, ao centro entre os extremos ou à maior coordenada das origens selecionadas.
- Objeto-chave: o objeto ativo selecionado é a chave; sua origem permanece fixa e as demais são alinhadas a ela.

## Distribuição

Cada eixo marcado é calculado independentemente usando as posições anteriores à operação.

- Limites da seleção: mantém as duas origens extremas e distribui as intermediárias em intervalos iguais. Exige pelo menos três objetos.
- Objeto-chave: mantém a chave parada e posiciona os demais em `chave + ordem × passo`. O sinal do passo determina a direção de todos os objetos.

Na distribuição por chave, os objetos que estão do lado contrário ao sinal do passo têm prioridade. Dentro desse grupo, a ordem vai do mais próximo ao mais distante da chave. Depois vêm os objetos do mesmo lado, também do mais próximo ao mais distante. Empates são resolvidos pelo nome do objeto.

Exemplo: chave X=-600 mm; outros objetos em -800, -650 e -590 mm; passo +30 mm. A ordem é -650, -800, -590, resultando respectivamente em -570, -540 e -510 mm. Passo negativo inverte a direção e a prioridade de lado. Passo zero coloca todas as origens sobre a chave nos eixos escolhidos.

Alinhamento e distribuição preservam rotação e escala e resolvem a posição global mesmo com parentesco. Cadeados locais são respeitados. Constraints ativas e drivers de posição em objetos que precisam mover são recusados; se uma operação falhar, os deslocamentos anteriores são revertidos. Filhos não selecionados acompanham seus pais normalmente.

## Validação

Testes automatizados no Blender cobrem proporções, vínculos parciais, zeros, bloqueios, persistência em .blend, ordenação com passos positivos e negativos, múltiplos eixos, parentesco rotacionado e com escala não uniforme, rollback, drivers, registro e desfazer/refazer com snapshots. A estrutura dos painéis e referências RNA foi verificada por um simulador de layout; não foi feita uma sessão manual de arraste dos campos na interface gráfica.

Código: `math_core.py` contém os cálculos sem dependência do Blender; `engine.py` aplica transformações e valida o resultado; `__init__.py` registra propriedades, operadores e painéis.
