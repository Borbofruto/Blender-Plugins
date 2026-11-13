# Export Paper Model — Medidas, versão local 1.5.1

Modificação do Export Paper Model 1.4.2, de Adam Dominec, sob a licença GPL-3.0-or-later original. Esta versão local exporta somente PDF. Os relatórios e as opções de outros formatos foram removidos.

## Orientação de retas subdivididas (1.5.1)

A opção de orientação agora se chama Maior trecho reto na vertical (90 graus). Reconhece segmentos consecutivos e colineares do mesmo contorno como uma única referência de direção, sem dissolver arestas nem alterar o desenho. Isso evita escolher um chanfro curto apenas porque a borda longa da peça foi dividida em várias arestas menores.

Curvas e contornos separados não são concatenados. O cálculo usa tolerâncias numéricas pequenas para admitir o ruído das coordenadas da malha, e as cotas continuam sendo as extensões totais após a rotação. A orientação continua definindo o eixo vertical, não o topo semântico da peça.

No Corte3, uma borda longa composta por segmentos de aproximadamente 18,52 mm perdia a referência para um segmento inclinado de 25,48 mm. A versão corrigida orientou a peça do arquivo salvo na vertical, com 87,50 x 500,00 mm na malha base. O modificador de renderização não é aplicado ao perfil, conforme a regra do modo de corte.

## Modos de exportação (1.5.0)

Escolha o modo em N > Paper > Export > Modo de exportação ou no início do diálogo de exportação.

- **Perfil de corte (ignorar espessura)**, padrão: extrai uma superfície plana principal da chapa, preservando o contorno externo e os recortes passantes. Descarta frente duplicada, paredes externas, paredes dos furos e espessura. Gera o perfil nas duas dimensões principais, com as cotas e a régua. Não cria abas, numeração de montagem, texturas ou mapa UV no objeto original. Dispensa executar Unfold antes.
- **Desdobramento completo**: mantém o comportamento anterior de abrir todas as faces do sólido, incluindo espessura, verso e paredes dos furos. As opções de abas, numeração, textura e mapa UV continuam disponíveis nesse modo.

O perfil é calculado em uma malha temporária, respeitando a rotação e a escala do objeto. As coordenadas, faces, marcas de costura e mapas UV do modelo usado para renderização são preservados. As superfícies de maior área paralela determinam o plano principal, mesmo quando a face foi triangulada. O modo valida que a dimensão descartada corresponde à espessura menor da chapa. A espessura não é desenhada nem somada às cotas.

Esse modo é destinado a chapas planas com espessura uniforme e recortes passantes. Rebaixos, furos cegos, superfícies externas que não cobrem o perfil completo e volumes sem uma espessura menor identificável são recusados em vez de gerar um corte presumido. Nessas situações, separe manualmente a superfície de corte. Modificadores não aplicados não são avaliados: é usada a malha original, como no desdobramento anterior. Uma chapa plana com espessura apenas no modificador de renderização pode ser exportada diretamente pela superfície original.

No teste com Estrutura.007, de 490 x 510 x 10 mm, o Perfil de corte gerou uma ilha de 490 x 510 mm com os quatro rasgos. O modo completo abriu o sólido, gerando uma ilha principal com 1000 mm de extensão. A orientação pelo maior trecho reto continua sendo aplicada ao perfil final, sem confundir essa referência com a altura total.

## Abas com ângulos degenerados (1.4.10)

Corrige uma divisão por zero no cálculo de abas de colagem quando os ângulos das pontas ficam colapsados ou numericamente indistinguíveis de zero. Os cossenos são limitados ao intervalo válido e os denominadores são verificados antes da divisão.

Quando não há espaço para uma aba com área útil, apenas essa aba é omitida. O PDF continua sendo exportado, com um aviso indicando a quantidade de abas omitidas. O trecho segue o contorno de corte sem aba e não recebe um número de montagem órfão. Abas normais continuam sendo geradas. Se houver compensação de espessura solicitada, o contorno segue essa compensação; a omissão não equivale a desfazer o ajuste de espessura.

Também evita a divisão por zero na compensação de espessura entre faces com normais paralelas, mantendo a costura sem deslocamento nesse caso. Arestas soltas sem faces são ignoradas ao planejar as abas.

Para exportar apenas a peça para corte, use Tabs > None no diálogo de exportação. Esse ajuste evita a geração de abas por completo. O controle de tolerância em ppm do painel N trata a validação da malha; ele não resolve uma singularidade angular no cálculo das abas.

## Controle da tolerância no painel N (1.4.9)

Na vista 3D, pressione N e abra Paper > Unfold > Tolerância da geometria. O campo Limite (ppm) controla a detecção de arestas e faces degeneradas. A mesma configuração da cena é usada no Unfold e na exportação PDF, e é preservada ao salvar o .blend.

- Padrão: 1 ppm, equivalente ao limite relativo da versão 1.4.8.
- Valor menor, como 0,1 ppm: aceita detalhes menores.
- Valor maior: considera mais detalhes pequenos como degenerados; torna a validação mais rigorosa.
- Zero: rejeita apenas arestas de comprimento exatamente zero e faces de área exatamente zero.

Uma parte por milhão (ppm) equivale a 0,000001 da maior extensão local da malha. O limite de área é o quadrado do limite de comprimento. O campo não é uma tolerância dimensional de fabricação e não altera a geometria. A verificação de faces não planas permanece separada e não é relaxada por esse controle.

Ao alterar a tolerância, execute Unfold ou exporte novamente para validar com o novo valor. Falhas de validação removem o mapa UV temporário antes de sair do modo de edição, preservando os mapas UV existentes.

## Validação de faces pequenas (1.4.8)

Corrige falsos avisos de área zero em malhas pequenas ou trianguladas. A versão herdada comparava comprimentos e áreas ao mesmo valor fixo de 0,000001 nas coordenadas locais. A tolerância de comprimento agora é proporcional à maior extensão local da malha; a de área usa o quadrado dessa tolerância, respeitando as unidades e a escala geométrica.

Faces realmente colapsadas, arestas nulas e polígonos não planos continuam sendo rejeitados. A validação não une, dissolve, apaga nem triangula faces automaticamente. As regiões problemáticas também são selecionadas quando o erro ocorre na exportação.

A triangulação produz faces menores e pode aumentar falsos avisos em versões anteriores. Aumentar a distância de Merge by Distance ou continuar dissolvendo a malha não resolve esse erro de tolerância e pode remover detalhes válidos. A versão 1.4.8 foi testada com faces válidas e degeneradas em cinco escalas, com o logo do arquivo salvo em uma malha temporária, e com exportação de uma malha de 400 triângulos pequenos que a validação antiga rejeitava.

## Uso

1. Reinicie o Blender após a atualização.
2. Selecione a peça, escolha o modo e use File > Export > Paper Model (.pdf).
3. Mantenha Orientação da peça: Maior trecho reto na vertical (90 graus).
4. Ative Dimensões gerais por ilha e Escala e régua de conferência.
5. Exporte o PDF. Cotas de arestas continuam opcionais.

A exportação gera um único PDF, inclusive para várias páginas. As cotas, a régua e a geometria ficam no mesmo documento, sem camadas separadas. Texturas, quando utilizadas, são incorporadas ao PDF.

## Orientação e medidas

O maior trecho reto contínuo do contorno define a direção vertical, excluindo diagonais da triangulação e abas. Ele é apenas a referência: altura e largura são as extensões totais da peça depois da rotação, sem abas. A rotação não altera comprimentos, recortes nem o desdobramento. O modo anterior, Ajustar automaticamente na página, continua disponível para permitir inclinação livre.

Retas subdivididas são reconhecidas em conjunto somente para calcular a direção; a geometria continua subdividida. Empates são resolvidos pelos índices da malha, dentro da tolerância numérica. A regra define o eixo vertical, não identifica semanticamente o topo da peça.

As cotas mostram mm reais, considerando unidades da cena e escala do objeto. Em escala 1:2, uma aresta real de 100 mm ocupa 50 mm no papel e continua cotada como 100 mm. A régua informa seu tamanho no papel e a dimensão real correspondente. Mais casas decimais não aumentam a precisão da malha.

As cotas reservam pelo menos 8 mm à direita e acima de cada ilha e a régua reserva 18 mm no rodapé. Se a peça não couber, aumente a página ou reduza a escala de impressão. A escala automática considera a orientação selecionada. Não há inclinação automática no modo Maior trecho reto na vertical nem divisão automática de uma ilha em várias folhas.

Arredondamentos continuam formados pelos segmentos da malha, sem ajuste automático de arcos ou Bézier. Cotas opcionais de segmentos curtos ou sem espaço suficiente são omitidas.

## Edição e gravação

No editor gráfico, confira uma dimensão total ou a régua. Meça os extremos da geometria sem incluir cotas e régua na seleção. Para restaurar 1:1, use o fator dimensão real cotada / dimensão geométrica importada, igual nos eixos X e Y. Remova as anotações antes de preparar o corte.

Se o Windows negar acesso ao destino, feche o PDF no leitor/editor ou escolha outro nome ou pasta. A exportação será informada como não concluída. Não há troca automática de destino nem necessidade de executar como administrador.

Ative somente uma cópia do add-on. Atualizações oficiais podem substituir esta versão local; guarde o ZIP para reinstalação. O pacote tem o mesmo identificador da extensão original e a substitui.
