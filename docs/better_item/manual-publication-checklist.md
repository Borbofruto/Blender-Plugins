# Checklist manual — publicação Better Item

Status: **pendente de execução humana**. A 1.7.10 foi aprovada como versão oficial; isso não marca os itens abaixo como executados. Usar o SHA oficial registrado em release-1.7.10.md. Os testes GUI com setters, parser via API e screenshots não substituem teclado/mouse nos widgets. Registrar build, commit, SHA do ZIP, idioma/interface, separador decimal, Unit System, Unit Scale e Length Unit. Usar cena de teste e perfil isolado; não arquivos de clientes.

## Entrada explícita de unidade — inclusão solicitada

- [ ] Em Metric / Millimeters / Unit Scale 1, criar dois alvos sem parent, locks, drivers ou links proporcionais: controle nativo e addon em Default/Local.
- [ ] Com teclado/mouse, digitar **“12,3456789 mm”** no X de Location e confirmar. Registrar exatamente o texto e o comportamento em cada campo. Se o idioma/configuração exigir ponto, repetir **“12.3456789 mm”** como controle; não normalizar silenciosamente nem atribuir uma regra de locale ao addon sem comparar com o nativo.
- [ ] Comparar os valores armazenados com o controle nativo e o comprimento físico em mm. Separar arredondamento do campo fechado de alteração real do valor. Registrar screenshot e, se possível, leitura RNA apenas como observador — a entrada deve ter sido física.
- [ ] Repetir em **Unit Scale 0,001**, preparando fixtures fisicamente equivalentes. Não alterar apenas Unit Scale e presumir que a geometria manteve o tamanho físico.
- [ ] Repetir em Dimensions, com cópias equivalentes e a mesma orientação. Conferir escala resultante, dimensão medida e ausência de alteração indevida de malha/dados compartilhados.
- [ ] Digitar o equivalente em metros e uma entrada em inches no sistema métrico. Comparar com o nativo; testar também entrada sem sufixo para verificar a unidade padrão do widget.
- [ ] Conferir Rotation contra o campo Euler nativo e Scale como fator adimensional. Não aplicar conversão de comprimento ao Scale.
- [ ] Cancelar com Esc durante edição/arrasto; depois testar Undo/Redo, links, passagem por zero e troca de referências. Confirmar que o estado anterior é restaurado quando pertinente.
- [ ] Registrar o arredondamento fechado em Unit Scale 1 e 0,001. A baseline fria atual pode mostrar 12,3 mm onde o nativo mostra 12,346 mm. Na 1.7.10, verificar equivalência visual por grupo; a precisão declarada já foi alinhada ao nativo.

## Demais fluxos

- [ ] Ligar/editar/desligar Live, trocar seleção e manipular fontes independentes, sem retargetar os alvos capturados.
- [ ] Endpoint/Offset, quatro bases de pontos e Geometry Bounds apenas em Offset; escolhas persistentes por método e configurações de F9/redo.
- [ ] Undo/Redo, salvar/reabrir, troca de cena e unregister; reobter wrappers após load/Undo.
- [ ] Normal em malha densa: clique, box select e troca por outro vértice com mesma contagem; conferir eixos e pausas perceptíveis.
- [ ] Dimensions com referência oblíqua e estágio GN; manter dados compartilhados e pilha íntegros.
- [ ] Larguras de painel e mensagens. Para BI-F006, usar a fixture de falha controlada; distinguir o título atual da baseline do título proposto, sem gerar falhas em arquivos de produção.
- [ ] Malha aberta com Volume e referências válidas: conferir a explicação de geometria inválida, recusa sem efeitos parciais e desaparecimento do aviso após reparar a malha.

Não há contrato universal de erro físico absoluto em mm. Registrar resíduos em mm e recusas; não usar Minimum Separation como erro máximo admissível. A precisão visual foi alinhada na 1.7.10. Uma eventual garantia física absoluta continua exigindo definição de contrato.
