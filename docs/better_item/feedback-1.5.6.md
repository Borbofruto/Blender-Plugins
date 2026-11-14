# Better Item 1.5.5 — triagem dos feedbacks e correção 1.5.6

## Escopo desta entrega

Corrigir o caso relatado de Location relativo que não permanece visualmente em zero e de links proporcionais que usam o resíduo como denominador. Não implementar em lote todas as sugestões das auditorias. Não reintroduzir animação, flexibilizar constraints nem alterar a semântica de Gimbal durante esta correção.

## Reprodução e causa observada

No Blender 5.2.3 LTS, um objeto usando outro como origem e orientação, rotacionado em (.37, -.26, .61) radianos e localizado em (3.21, -2.13, 1.7), recebeu Location relativa (0, 0, -.86).

A versão 1.5.5 leu (-1.010484993e-7, 5.029141903e-8, -.8600000143). O vínculo dos três eixos, ao editar X para 1, calculou Z = 8510764.829493087. É uma reprodução concreta do salto relatado, não apenas uma possibilidade do predicado matemático.

Havia dois problemas combinados: conversões intermediárias em float32 e uso de qualquer resíduo diferente de zero como denominador confiável. A presença de uma coordenada não nula obriga uma ida e volta por uma base rotacionada; quando as três são zero, a operação pode coincidir diretamente com a origem e evitar parte desse arredondamento.

## Correção

- Resolver leitura relativa e construção do alvo mundial em float64, usando os dados que o Blender efetivamente armazenou.
- Não ignorar uma edição de Location apenas porque sua diferença é menor que o limite genérico anterior de 1e-12.
- Registrar zeros explicitamente solicitados após uma edição bem-sucedida. O zero exato só aparece se o resíduo estiver no orçamento de arredondamento e se matriz mundial, eixos, origem e canais nativos de posição continuarem iguais ao estado verificado.
- Invalidar esse significado quando o objeto ou o referencial resolvido mudar. Não substituir medidas não nulas pelo valor digitado, nem aplicar arredondamento global a valores pequenos.
- Rejeitar uma razão indefinida ou numericamente não resolvida com BI-T008, antes de alterar o objeto. O orçamento depende da magnitude das coordenadas e da transformação herdada; não é um número fixo em milímetros.

Isso não elimina a limitação float32 do Blender. Se uma coordenada pequena não é distinguível do erro de conversão naquele contexto, multiplicá-la por uma razão arbitrária não recupera precisão. O usuário deve desvincular o eixo, dar a ele uma coordenada não nula resolvível e então voltar a vincular.

O estado de zero é um dado de leitura verificado; não é constraint, driver, pose congelada ou controlador de animação. O cálculo bruto permanece disponível ao núcleo e é conferido antes da apresentação do zero.

## Validação executada

`test_better_item_zero_location156.py`: 200 casos de referências rotacionadas, pais com rotação/escala, Parent Inverse, Delta Location e duas escalas de unidade. Inclui zeros independentes de X/Y com Z não nulo, rejeição de denominador incerto sem alteração de canais, invalidação por mudança externa, valores legítimos de 1e-13, vínculos comuns e salvar/reabrir o .blend.

As suítes existentes também passaram: funcionalidades básicas, regressões de escala espelhada e rotação, 1.500 casos de arredondamento de eixos locais travados, paridade de referências, alinhamento/distribuição, frames, Directions 1.5.4 e manutenção 1.5.5. A comparação nativa voltou a passar em 48 operações Gimbal, além de Normal em Edit Mode. Logs ficam junto dos testes locais.

Não foi feita uma nova validação visual interativa do painel nesta entrega. Os testes executam o núcleo e operadores no Blender em background. O armazenamento nativo continua float32.

## Feedbacks: o que se confirmou ou precisa ser separado

| Tema | Resultado da investigação | Encaminhamento |
|---|---|---|
| Resíduo de Location e explosão do link | Reproduzido na 1.5.5; correção e regressão nesta entrega | Corrigido em 1.5.6 |
| Fórmula dos eixos Gimbal estaria invertida | Não confirmado. O caso de X puro devolve identidade e os 48 deslocamentos reais com orientação Gimbal concordam com o Blender | Não alterar a fórmula com base nessa crítica |
| Valor digitado em Rotation/Gimbal difere do relido | Confirmado em Y e Z. A base depende da rotação do próprio alvo e se move durante a edição; no ensaio, Y solicitado .450792 volta .306257 rad | Pendência real de contrato de edição; requer decisão própria. Uma referência aplicada em Frame oferece base independente, sem trocar a semântica silenciosamente |
| Projeção de Dimensions em float32 | Confirmada perda adicional de precisão aritmética em geometria local deslocada para 1e5: extensão X 3.34375 contra 3.339345872 em projeção float64 dos mesmos vértices armazenados | Correção separada de medição. Promover a aritmética não recupera detalhe já perdido no armazenamento dos vértices |
| Tolerância absoluta de Dimensions aceita perdas relativas grandes perto de zero | O predicado permite isso; a auditoria não demonstrou que a execução produziu tais geometrias | Revisar validação por operação com teste que force resultado incorreto, sem reduzir tolerâncias globalmente |
| Dimensions = 0 impede reabrir via Scale | Comportamento real: transformação singular perde uma dimensão | Decidir entre rejeitar zero antes da edição ou aceitar com diagnóstico explícito. Não alterar silenciosamente nesta correção |
| Rotation não valida a posição final do pivô como o solver de Location | Ausência da pós-condição confirmada por leitura | Adicionar teste dirigido e verificação espacial com rollback numa correção própria |
| BI-T005 em parentesco por osso/vértice | A inversão usa matrix_basis do filho; a mensagem pode atribuir ao pai uma singularidade do filho | Corrigir diagnóstico com teste de parentesco não OBJECT |
| Marcador removido ou conexões GN adulteradas | Proteção atual não é validação integral do grafo | Fortalecer identidade/estrutura e testar rollback antes de modificar grupos; não reconstruir nem reordenar silenciosamente |
| Guard de modificador antes do caminho de Scale | Política documentada e deliberada: rejeita uma etapa própria inválida antes de qualquer edição Reference Dimensions | Não é defeito só por ser conservadora |
| Drivers bloqueados por propriedade inteira | Restrição real e conservadora | Manter separada da flexibilização de constraints; resolver canal/índice e dependências com testes próprios |
| Cache com driver/dependência indireta no mesmo frame | Hipótese plausível; a auditoria não forneceu reprodução integrada | Testar o consumidor avaliado e os eventos reais antes de mudar a invalidação |
| Bounding Box Center em Align versus Transform | Align trata o caso como distribuição/alinhamento dos limites das origens; o pivô usa limites geométricos | Ambiguidade semântica real. Exige decidir contrato/nome; não adicionar distribuição geométrica por consequência |
| Manual com base aplicada mostra offset de rotação | Comportamento documentado para preservar a base, inclusive não ortogonal | Não equivale a Euler absoluto. Melhorar apresentação exige manter explícita a distinção |
| Dropdown novo não teria update callback | O setter escreve propriedades subjacentes com callbacks de atualização | A mera ausência de update no seletor adaptador não prova o defeito descrito |
| Sync ficaria suspenso para sempre | O loop inspecionado tenta publish em frames habilitados mesmo suspensos; o guard citado não está nesse ponto do código atual | Não confirmado pela causa apresentada |
| Enum muda de tipo em uma futura versão hipotética | Não é reprodução de falha atual; persistência e seriais continuam passando | Compatibilidade futura deve ser testada na versão concreta |
| Nome externo de orientação exportada | Nome é a identidade atual; renomear pode encerrar o vínculo sem apagar a orientação renomeada | Não apagar dados nativos por adivinhar propriedade; definir política antes de mudar |
| Cabeçalhos, import não usado, códigos de erro incompletos, manual histórico | Existem itens de manutenção legítimos | Lote de limpeza separado e verificável |
| Normal, interações novas e constraints | Questões já conhecidas de desempenho/escopo | Continuam separadas; não são justificativa para expandir esta entrega |

O comentário sobre Gimbal mistura duas questões diferentes. Em Euler XYZ, a composição faz o eixo Z de Gimbal permanecer global; não se pode exigir que todos os eixos acompanhem a rotação completa do objeto como numa base Local. Já a impossibilidade de manter um alvo absoluto num campo cujo referencial muda com o próprio alvo é uma questão de edição real, e foi reproduzida.

Também não é correto tratar toda ocorrência de driver, keyframe ou mudança de frame nos testes como implementação de animação do addon. Testar medição de geometria avaliada que muda com o Blender é necessário. O runtime atual não deve criar/controlar esses dados; a suíte de limpeza confirma essa separação.

## Próxima ordem recomendada

1. Medição/validação de Dimensions e posição final de Rotation: correção numérica com pós-condições e rollback.
2. Integridade e atomicidade do Geometry Nodes sob adulteração real, mantendo a política da pilha explícita.
3. Contrato de edição de Rotation em referência Gimbal móvel e consistência semântica de Bounding Box Center.
4. Diagnósticos, códigos faltantes e limpeza documental.

Nenhum desses itens justifica introduzir animação, novos pivôs ou novas interações enquanto a previsibilidade do que existe não estiver consolidada.
