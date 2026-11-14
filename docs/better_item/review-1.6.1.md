# Better Item 1.6.1 — confronto dos dois feedbacks

Revisão baseada no código publicado da 1.6.0 e nos dois textos fornecidos. Execução local: Blender 5.2.3 LTS, Windows. Os resultados relatados pelas outras IAs não foram contabilizados como testes executados nesta revisão.

## Conclusões por ponto

| Ponto | Evidência e decisão |
|---|---|
| Normal/Gimbal Rotation | Há uma limitação real de referenciais que acompanham o alvo: o valor absoluto relativo não permanece após certas edições. A recusa BI-T009 protege esse contrato. No painel real os campos estão ativos e uma recusa aparece como aviso, não como falha crítica. Não se substituiu a operação por incrementos nem se desativaram todas as fontes Normal/Gimbal. |
| Bloquear Normal/Gimbal por nome | Rejeitado como regra geral: nesta matriz Euler, 3 de 18 edições funcionaram e 15 foram recusadas com restauração. Quaternion sem pai também funcionou. Um Frame independente criado a partir de Normal permitiu a edição. Há capacidade válida a preservar. A indicação antecipada de quais campos editar é uma discussão de UX ainda aberta, não uma impossibilidade geral decretada pelo addon. |
| Ordem da distribuição | É a regra explicitamente solicitada: semiespaço contrário ao sinal primeiro; proximidade dentro de cada grupo; objeto-chave parado. O README 1.6.0 já a descrevia. Foram acrescentados exemplos positivos e negativos para evitar a interpretação de ordenação crescente global. Não se alterou o algoritmo. |
| CHANGELOG | Confirmado: misturava instruções, arquitetura e longos registros de testes. Agora contém mudanças por versão; os registros anteriores foram preservados em `delivery-history-through-1.6.0.md`. Links para evidências externas ao ZIP são explícitos. |
| Mensagens sem BI- | A alegação de ausência de código na saída não se confirma: `BetterItemError` acrescenta BI-V001 automaticamente. O teste verifica isso e que o resumo visual omite o código. Algumas validações de arranjo receberam códigos específicos já existentes (A001/A003/A004/D001), sem mudar a operação matemática. Não se criaram dezenas de códigos só para satisfazer a contagem de strings. |
| Import ReferencePending | Confirmado como não utilizado em `__init__.py`; removido. Outros módulos continuam utilizando a classe. |
| Compatibilidade 5.0 | Continua sendo uma lacuna de validação, não um erro demonstrado. O mínimo declarado é 5.0 e o ambiente executado aqui é 5.2.3. Não se ampliou a alegação de compatibilidade nem se concluiu que 5.0 funciona ou falha. |
| Object versus Gimbal | Confirmada a diferença de semântica e a falta de explicação explícita: Object extrai uma base rotacional ortonormal; Gimbal pode reter eixos oblíquos herdados. Um teste com ancestral de escala não uniforme e pai rotacionado demonstra a diferença. O README agora a explica. |

Gimbal não evita Gimbal lock. A mudança da base acompanha o mecanismo de rotação; uma base singular continua sendo rejeitada. E uma rotação que não cabe nos canais nativos preservando Scale e a rigidez da geometria não é uma impossibilidade física universal: é uma limitação da representação/contrato escolhidos pelo addon.

## Testes adicionais executados

| Sugestão do feedback original | Execução desta revisão |
|---|---|
| Normal/Gimbal na UI | Blender com janela real: tentativa em Normal, aviso BI-T009, rollback; Frame independente aceita o ângulo; Gimbal quaternion editável. Capturas locais inspecionadas. Matriz headless adicional das seis ordens Euler e três componentes. |
| Geometria dependente de posição | Novo teste GN com Object Info em espaço Relative e offset derivado de Location: BI-G003 e restauração. A suíte anterior de GN com parâmetro dirigido pela posição também foi repetida. Displace por textura não foi testado nesta revisão. |
| Referência que acompanha alvo | Suíte 1.6 repetida: referência filha do alvo rejeita com BI-G004; Scale dependente de Location rejeita com BI-G005; canais restaurados. |
| Undo/Redo e persistência | Distribuição geométrica com 240 objetos: Undo, Redo e salvar/reabrir. Repetidos os testes 1.6 de orientação em lote com Undo/Redo e persistência dos controles. |
| Unit Scale e imperial | Quatro cenas: Metric 1 e 0,001; Imperial 1 e 0,3048. Entrada textual `30 mm` convertida pelo parser nativo e verificada contra lacunas medidas por projeção dos vértices. |
| Mais de 200 objetos | 240 cubos com larguras diferentes. Planejar, aplicar e verificar levou cerca de 0,28 s na execução registrada; erro medido de lacuna = 0 nesse cenário. Não é promessa de desempenho para qualquer malha ou cena. |

Repetidas nesta entrega: testes de features 1.6, edge cases, matriz de 168 combinações geométricas e 72 lotes de orientação (288 alvos), 630 combinações antigas de arranjo, limpeza 1.5.5 e suíte básica de transformação/persistência. Não foi repetida a matriz completa de 9.216 casos da entrega anterior; os cálculos de transformação não foram alterados nesta manutenção.

Scripts novos: `test_better_item_review161.py`, `test_better_item_arrangement161.py`, `test_better_item_gui161.py`. Evidências JSON em `tests/better_item/results/1.6.1/`. O ZIP final também passa pela validação de extensão e pelo teste de revisão executado a partir dos seus arquivos extraídos.

## Limites desta entrega

- Não há base para declarar que os erros foram esgotados, que o addon nunca quebra cenas ou que uma revisão finita encerra a validação comercial.
- Os resultados de 360/576 casos e layouts simulados citados no feedback original são relatos da outra avaliação; não foram reproduzidos com os mesmos scripts, que não acompanharam o texto.
- Não houve mudança de layout, animação, constraints, otimização de Normal ou novos manipuladores.
- A documentação esclarece o comportamento atual. Melhor indicação antecipada de referências autoacompanhantes e os demais refinamentos visuais continuam para discussão.
- Instalador atualizado no mesmo caminho: `addons/better_item.zip`, versão interna 1.6.1. Não há novo ZIP versionado na pasta de addons.
