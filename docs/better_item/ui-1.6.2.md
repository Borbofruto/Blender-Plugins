# Better Item 1.6.2 — hierarquia visual das referências

O componente compartilhado passa a distinguir a escolha principal da fonte exigida por ela:

- Orientation usa o ícone de eixos junto ao rótulo; Location usa o ícone de origem junto ao rótulo.
- Object, Frame e Name aparecem na linha seguinte com recuo do rótulo e um marcador `└`.
- Rótulos dependentes não recebem ícones. Os ícones nativos dos itens continuam dentro de seus widgets de seleção.
- Os campos mantêm a mesma coluna de entrada. Ações existentes, como criar Frame pelo botão +, permanecem na linha correspondente.
- Global, Manual e outras escolhas sem uma segunda seleção não ganham linhas de fonte vazias.

O desenho é usado por Transform, Align and Distribute e pelos dois componentes do editor de Frames. A opção combinada Reference > Frame mantém seu seletor único, pois não é um par de escolhas independentes.

## Validação executada

Blender 5.2.3 LTS / Windows:

- 21 estados do componente: consumidores Object/Scene e editor de Frames; Global/Manual, Object, Frame e Custom Orientation/Name; ícones apenas nos rótulos de categoria e ramificação apenas quando existe fonte secundária.
- Desenhar o componente preserva os valores de seleção de fonte.
- Janela real do Blender: captura de Transform e Align and Distribute; editor de Frames aberto pelo operador nativo de painel para inspecionar os mesmos controles; Custom Orientation e Object ainda não escolhidos. Capturas inspecionadas visualmente.
- Repetidas as suítes de features 1.6 e revisão 1.6.1, incluindo fontes incompletas, salvaguardas e persistência. O layout simulado da suíte anterior foi adaptado para aceitar o primitivo nativo `UILayout.split`.
- Validação do instalador e teste dos 21 estados executado novamente com o código extraído do ZIP final.

Esta alteração não muda cálculos, fontes persistidas, interpretação de referências ou transformações dos objetos. A largura disponível continua determinando a truncagem dos nomes nos seletores; não foi imposto um tamanho à sidebar. Instalação pelo mesmo `addons/better_item.zip`, versão interna 1.6.2.
