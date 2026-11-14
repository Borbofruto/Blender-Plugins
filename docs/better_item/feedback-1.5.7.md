# Better Item 1.5.7 — revisão dos três feedbacks sobre a 1.5.5

Data: 14/11/2026. Base de implementação: 1.5.6. Ambiente executado: Blender 5.2.3 LTS, Windows. Esta entrega trata os três feedbacks anexados na conversa, sem acrescentar ferramentas de animação, novos manipuladores ou distribuição geométrica.

## Resultado e contrato

Uma edição numérica deve atingir o resultado solicitado dentro da precisão declarada, ou rejeitar com diagnóstico e restaurar o estado anterior. Os testes verificam tanto os sucessos quanto as rejeições. Rejeitar uma rotação que não cabe nos canais nativos sem deformar a geometria não é contado como uma implementação dessa rotação.

O critério de tolerância foi separado por responsabilidade:

- Canais nativos: verificar a representação float32 efetivamente solicitada, sem um piso absoluto que aceite perder todo um valor pequeno.
- Posição mundial: usar o orçamento de produtos pai/Parent Inverse/deltas, sem piso absoluto genérico de 1e-8. Eixos locais travados usam o orçamento da resolução inversa, sem o antigo piso absoluto de 1e-12.
- Dimensions: projeção e álgebra afim em float64, preservando o armazenamento Blender float32. Uma dimensão positiva deve permanecer positiva e diferir no máximo em 32 epsilons float32 relativamente ao alvo. Valores não representáveis devem ser rejeitados; não se amplia a tolerância para aceitar a perda de uma dimensão inteira.

Esse contrato não recupera detalhe já perdido nos vértices float32 e não promete precisão física arbitrária em coordenadas enormes.

## Feedback 1 — problemas e documentação

| Item | Verificação | Tratamento |
|---|---|---|
| 1.1 — Rotation/Gimbal não relê o valor digitado | Confirmado em Y/Z e em diferentes ordens Euler. A própria base muda durante a edição | Verificação da rotação no referencial final; BI-T009 e rollback quando não conserva a leitura. Não se altera a fórmula dos eixos nem se congela a referência silenciosamente. Aplicar a orientação num Frame independente permite usar uma base estável |
| 1.2 — BI-T005 acusa o pai quando o filho tem escala zero | Confirmado para a obtenção da base efetiva em BONE/VERTEX | Mensagem identifica a matrix_basis singular do filho e o tipo de parentesco. Testes com os quatro tipos de pai e três filhos colapsados |
| 1.3 — Projeção em float32 | Confirmado comparando projeção dos mesmos vértices armazenados com float64 | Projeção e produtos matriciais em dupla precisão; cache de coordenadas continua compacto |
| 1.4 — Dimension = 0 é uma armadilha | Confirmado: o colapso é singular e não pode ser reaberto por razão de dimensões | BI-T010 antes de colapsar uma largura positiva. Dimensões geométricas já nulas continuam legíveis. Scale nativo continua disponível para colapso deliberado |
| 1.5 — Erros sem código | Confirmado | Códigos específicos para novas condições e BI-V001 para validações gerais; BI-V002 para rejeição da API no campo. O texto complementar continua necessário para diagnóstico |
| 1.6 — Bounding Box Center com usos diferentes | Política existente e documentada do módulo de arranjo, com risco real de interpretação | Preservado o nome nativo. Painel passa a explicitar “Range: selected object origins”. Min/Center/Max e intervalos de distribuição continuam usando limites de origens. O pivô de Transform é geométrico; não se acrescenta distribuição por geometrias |
| 1.7 — Limpeza | Import sem uso e cabeçalhos ausentes confirmados | Import removido; SPDX acrescentado. Não há runtime do protótipo de animação. Dados/ações/drivers antigos que já existam num arquivo são deixados intactos, não gerenciados nem apagados automaticamente |
| TOML | Válido; versão mínima não foi executada | Acrescentados website e copyright. Mantida a declaração 5.0+, com distinção explícita entre compatibilidade declarada e versão efetivamente testada. Não se afirma execução em 5.0/5.2.4 |
| Instalação e manual | Correções de instalação já iniciadas na 1.5.6; histórico misturado ao uso confirmado | README atualizado; registros históricos movidos para CHANGELOG.md. Reinício é indicado apenas se um módulo anterior continuar carregado |

A verificação de leitura também encontrou o mesmo defeito em Location quando um pivô acompanha o alvo: calcular com o pivô anterior e aceitar um readout final diferente é inconsistente. A mesma pós-condição/BI-T009 agora protege esse caso. É uma rejeição explícita, não uma tentativa de resolver automaticamente todo referencial que depende do próprio alvo.

## Feedback 2 — classificação de cada alegação

| Item | Conclusão |
|---|---|
| 1.1 — A fórmula de Gimbal estaria errada porque X puro deveria girar Y/Z | Não se confirmou. A hipótese usa outra interpretação da composição Euler. A base foi confrontada com operações nativas em 54 configurações de eixo único, além da suíte anterior de 48 direções. Isso é distinto do bug de leitura em uma base móvel, que foi corrigido por pós-condição |
| 1.2 — Cache obsoleto com driver no mesmo frame | Hipótese testável, não defeito demonstrado no feedback. Foram executadas cinco mudanças de uma propriedade controlando shape key e cinco controlando uma fonte de Object Info/GN, sem avançar frame. Leituras acompanharam a geometria. A suíte existente cobre grupos aninhados, subframes, mudanças de parâmetros, modificadores e Undo/Redo. Não foi acrescentada invalidação ampla sem reprodução |
| 1.3 — Guard de modificador ocorre antes do caminho de Scale | Política intencional: não operar com uma etapa própria inválida na pilha. Mantida e documentada; não reordenar nem contornar a pilha silenciosamente |
| 1.4 — Manual com base aplicada mostra offset | Comportamento necessário para preservar uma base não ortogonal, já identificado no painel. Tooltip passa a explicar que os Euler são offset, não pose absoluta reconstruída |
| 1.5 — Seletor adaptador não teria callback | Não basta verificar a declaração do seletor. Seu setter escreve as propriedades subjacentes, que possuem callbacks. Trocas continuam passando nas regressões. A lacuna concreta de erro após mudar links foi corrigida; mudar ordem Euler também limpa o erro/hint |
| 1.6 — Sync ficaria suspenso para sempre | O guard alegado não está no loop atual. Um teste com interface real verificou fonte válida, fonte removida, suspensão, recuperação e renomeação, usando o timer real |
| 1.7 e 1.8 — Tipo de enum/get poderia mudar em outra versão | Hipóteses de compatibilidade, não reprodução de falha atual. Migração de seletores antigos, remoção intermediária de Frames e persistência passaram. Outras versões do Blender continuam fora da execução desta entrega |
| 1.9 — to_quaternion não seria definido para matriz não ortogonal | Não se demonstrou um defeito de runtime. A rotação escolhida pelo Blender não é necessariamente a decomposição polar por SVD; substituí-la redefiniria a semântica. Mantido o contrato atual, com testes de escalas extremas e rejeição das rotações não rígidas sob herança anisotrópica |
| 1.10 — Malha fina perderia detalhes no cache | A projeção agora é float64. O armazenamento de vértices float32 continua sendo limite real. Os testes distinguem detalhe já ausente dos dados de perda adicional introduzida pela projeção |
| 1.11 — Setter não captura TypeError | Incluída a captura de falhas internas da API com BI-V002. Atribuir None a uma propriedade Float pode falhar no RNA antes de chamar o setter; isso é rejeição de tipo da API, não falha de transformação |
| 1.12 — API pura aceita spacing=0 | Corrigido no ramo por chave/referência com BI-D001; distribuição entre extremos continua calculando seu intervalo a partir dos limites |
| 1.13 — Chave poderia sair da seleção filtrada | O próprio feedback reconhece que os ramos se excluem. Não foi reproduzida falha. Casos com pai e filho selecionados foram acrescentados à bateria |
| 1.14 — Pai osso/vértice com constraint mistura avaliação | Restrição conhecida de decompor uma matriz já avaliada. Transformações com constraints ativas continuam conservadoramente bloqueadas; não foi tentada uma flexibilização nesta entrega |
| 1.15 — Renomear orientação externamente deixa “órfão” | Encerrar o vínculo sem apagar a orientação renomeada é uma política de preservação de dados do usuário. Não há base segura para apagar uma orientação que o usuário passou a editar/renomear fora do addon |
| 1.16 — Tupla de enum seria frágil caso alguém passasse string | O número atual é inteiro e persistência foi testada. Uma mudança futura hipotética de tipo não é defeito atual |
| 1.17 — Check duplicado em align_positions | A cópia examinada faz a validação em _inputs; a duplicação descrita não está presente nesse caminho |

## Feedback 3 — correção, integridade e limites

| Achado | Tratamento |
|---|---|
| Tolerância de Dimensions aceita perdas relativas grandes perto de zero | Corrigida a condição de aceitação. Testes verificam explicitamente que perder 75%, 90% ou toda uma dimensão pequena não passa. Native channels e posição mundial também receberam critérios próprios, em vez de reduzir uma tolerância global |
| Driver em um componente bloqueia os demais | Corrigido para Scale e edições Default/Local: componentes alterados são identificados. Driver constante em Scale Z não bloqueia Scale X, mas editar Z é recusado e uma mudança avaliada inesperada continua falhando. Rotation não bloqueia apenas por ler Scale/delta Scale; verifica sua preservação |
| Rotation não verifica a posição final do pivô | Passa pelo solver transacional/verificação mundial. Uma falha injetada na resolução de posição produziu BI-T006 e restauração completa de Location/Rotation/Scale |
| Remoção do marcador GN pode causar duplicação | Identidade independente pelo persistent_uid do modificador, armazenada nas configurações do objeto. O grupo ainda precisa ser válido. Remover marcador, desconectar grupo ou alterar conexões/operação/seleção rejeita antes de mutação; não cria um segundo estágio |
| A05/A13 — Estrutura GN e falhas antes do rollback | Validada a estrutura completa usada pela etapa: tipos, operações, links, valores de seleção/offset e coerência da matriz. Inicialização, cópia compartilhada e escrita são cobertas por cleanup/rollback. Falhas injetadas não deixaram cópias/grupos temporários |
| A06 — Precisão da projeção | Corrigida, com referência calculada a partir dos vértices efetivamente armazenados |
| A07 — Determinante como critério de singularidade | Substituído pela razão dos valores singulares. Reescalar uniformemente uma base não muda sua validade. Bases com condição inadequada para os dados float32 são rejeitadas com BI-F005 |
| A08 — Modo legado LOCAL | Não é oferecido no seletor atual. A migração captura uma referência aplicada, em vez de reinterpretar silenciosamente o arquivo. Migração executada em processo novo e reabertura |
| A09 — Erro permanece após desvincular | Callback dos links limpa o erro. Há teste direto |
| A10 — different ignora valores pequenos | Comparação de canais solicitados passa a ser exata; a tolerância de avaliação fica nos verificadores apropriados. Um eixo travado não aceita uma edição apenas por ser menor que 1e-12 |
| A11/A12 — Normal e período de atualização nativa | Mantidos como limites de desempenho/latência documentados. Não foram acrescentadas novas interações nem otimizações de Normal |
| A14 — Compatibilidade mínima | Lacuna registrada, sem alegar teste de uma versão indisponível |
| A15 — Use Frame em objeto não editável | Guard de editabilidade acrescentado |
| A16 — Instâncias GN não realizadas | Confirmada necessidade de tratamento. A medição recusa um conjunto incompleto com BI-M005 e orienta a usar Realize Instances. Após realizar as instâncias, a leitura correta foi verificada |

O UID é uma identidade fornecida pelo Blender, estável em renomeações/reordenações e entre sessões; não depende do nome visível do modificador. Referência: [Modifier.persistent_uid](https://docs.blender.org/api/5.0/bpy.types.Modifier.html). Não é uma proposta de segurança contra apagar deliberadamente toda evidência de identidade e metadados do arquivo.

## Matriz dos 11 grupos do Feedback 1

Todos os grupos abaixo tiveram casos executados; “grupo executado” não significa testar infinitas cenas possíveis ou cada configuração de todos os recursos do Blender.

| Grupo sugerido | Casos executados e resultado |
|---|---|
| 1. Round-trip | 9.216 combinações: oito fontes de orientação; oito fontes de localização/pivô; seis modos Euler, Quaternion e Axis-Angle; com/sem espelho; três situações de pai; Location/Rotation/Dimensions. 6.240 sucessos com leitura conferida e 2.976 rejeições com estado preservado: 1.952 BI-T009 por referência móvel, 1.024 por rotação herdada não representável no contrato atual |
| 2. Rotação nativa como oráculo | 192 comparações com bpy.ops.transform.rotate: todos os oito modos de armazenamento, os três campos de Rotation, Global/Object, pai uniforme e espelho. Também 54 comparações de direção Gimbal com configurações de rotação em eixo único |
| 3. Pais exóticos | OBJECT, BONE, VERTEX, VERTEX_3; três filhos com escala zero; cadeia com cinco pais, escalas negativas, Parent Inverse e deltas. Resultado ou rejeição atômica conferidos |
| 4. Escalas extremas | 16 casos com 1e-4/1e4 e as oito combinações de sinal; bateria adicional de Dimensions entre 1e-12 e 1e4 |
| 5. Coordenadas grandes | Geometria local em 0, 1e5 e 1e7, comparada com projeção float64 dos mesmos vértices armazenados |
| 6. Links em cadeia | 1.000 edições alternando XYZ; desvio máximo observado das razões de aproximadamente 1,49e-7. Edição ligada com eixo travado rejeita sem alteração |
| 7. Zero e ângulos especiais | Cinco sequências com zero, ±90° e ±180°, e rejeição de Gimbal lock. A suíte de regressão anterior cobre os demais casos de zero/turn/crossing |
| 8. Frames compostos | Cadeias de 2, 20 e 100 Frames; posição e rotação independentes; renomeação, remoção intermediária e ciclo explícito |
| 9. Arranjo em lote | Oito combinações entre coordenadas 1e-6 a 1e9 e duas unidades; coincidências BI-D002; colapso por precisão BI-D003 com rollback; pai e filho simultaneamente selecionados em Align/Distribute. Suíte anterior de 630 combinações também executada |
| 10. Modificadores externos | Array, Mirror e shape keys; GN externo dirigido por outro objeto, grupos aninhados, alternância de modificadores e instâncias. Não foi adicionado suporte a todo tipo de Geometry Set |
| 11. Undo/Redo e arquivo | Criação de etapa afim, desfazer/refazer, copy-on-write de grupo compartilhado e salvar/reabrir; persistência dos zeros da 1.5.6 e identidade do modificador |

Os resultados numéricos estão em `tests/better_item/results/1.5.7/`. Scripts novos: `test_better_item_stress157.py`, `test_better_item_feedback157.py`, `test_better_item_dependencies157.py` e `test_better_item_gui157.py`.

## Testes adicionais executados

- 200 casos específicos da correção de zero em Location, incluindo mudança externa de referência, números legítimos de 1e-13 e salvar/reabrir.
- 1.500 casos de pais rotacionados/escalados com eixos locais travados.
- 1.200 cancelamentos de Parent Inverse e 842 movimentos no intervalo −210 a +210 mm em duas convenções de unidade.
- Regressões de escalas espelhadas, deltas, constraints/drivers, paridade dos seletores, migração, grupos indisponíveis e registro.
- Cache: atualizações indiretas no mesmo frame, grupos GN aninhados, shape keys, alterações externas nativas, frames/subframes, ida e volta no tempo, alternância de modificadores, Undo/Redo e reutilização após translação.
- Interface real em processo separado: painéis Transform/Align/Frames, diálogo New Frame, timer de orientação, exclusão pelo menu nativo, fonte inválida, recuperação e renomeação. Capturas foram inspecionadas. Não é um teste exaustivo de arraste manual, teclado ou todos os layouts de janela.
- Arquivo criado com o protótipo arquivado: abriu sem o runtime antigo recriar/apagar ações/drivers ou modificar poses. Os dados antigos permanecem do usuário.

## Limites e pendências explícitos

1. Blender 5.0, 5.1, 5.2.4, Linux e macOS não foram executados nesta entrega. Compatibilidade declarada não deve ser confundida com a matriz efetivamente testada.
2. Rotation sob pai anisotrópico continua rejeitada quando não pode produzir uma rotação rígida com preservação dos canais. Não se acrescentou Geometry Nodes para rotação nem uma nova decomposição por SVD.
3. Referências que acompanham o próprio alvo continuam válidas para inspeção; algumas edições absolutas são incompatíveis com essa dependência e agora rejeitam claramente. Não há resolução automática de todas as dependências móveis.
4. A política de intervalo de Align/Distribute continua baseada em origens. Alterar essa política para limites geométricos exige decisão de produto separada; o painel/manual agora deixam isso explícito.
5. Flexibilização de constraints, otimização de Normal, manipulação interativa de Frames e animação relativa não entraram nesta entrega.

O manifesto recebeu metadados opcionais seguindo o [formato oficial de extensões](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html). O ZIP e o manifesto são validados pelo comando de extensões do próprio Blender antes da publicação.
