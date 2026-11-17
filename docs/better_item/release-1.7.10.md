# Better Item 1.7.10 VG — candidato de manutenção

Branch **release/1.7.10-vg**, base `f9180b6`, fonte/testes em `caba3716302069af763f4169e728b21cf060b9bc`. VG identifica esta contribuição GPT; a versão técnica é 1.7.10. A remota release/1.7.9 foi excluída após confirmar que todos os seus commits eram ancestrais da main. **Sem merge na main; qualificação automatizada concluída, interação manual pendente.** Não apresentar este candidato como publicação estável aprovada.

ZIP da branch: `addons/better_item.zip`, SHA256 **53ea12dee71f48cf755964405111688b15fa943ffb1bfb07ba4a67301a63fbef**. Fingerprint dos 15 módulos Python: `d9a02770dc57b25836de826a0031fe5cabb38e83e3ae6ce3699fa2afc58bd1f0`. O instalador na main permanece 1.7.9 / 6a01eb80…; seus resultados não foram reclassificados como validação desta versão.

## Correções delimitadas

- **Sincronização nativa:** a obtenção de Window/Scene nos redraws de falha e recuperação fica protegida; janelas removidas são verificadas contra a coleção viva antes do acesso e de temp_override. Continua a intenção de exportação, diagnóstico BI-F006, retentativa limitada, isolamento de Frames e política de suspensão da fonte inválida.
- **Inspeção de espaçamento:** uma recusa conserva sua causa como Diagnostic, sem guardar exceção, traceback Python ou RNA no cache. O resultado continua um tuple de dois elementos `(status, value)`, com causa adicional nos resultados indisponíveis. O painel explica Volume inválido, referência incompleta ou ausência de eixos conforme a causa. Aplicação e solver permanecem independentes do cache e mantêm as recusas atômicas.
- **Transform:** precisão declarada 5 para Location/Rotation/Dimensions, 3 para Scale, conforme os campos nativos verificados. Não altera valores armazenados, setters, conversão de unidades ou erro matemático tolerado. Foram aproveitados somente os dois arquivos de código da proposta visual e sua fixture, sem mesclar a branch inteira.
- **BI-F006:** título Orientation sync paused; preservados severidade, corpo, demais títulos e métodos string de Diagnostic.

Só quatro módulos Python mudaram. Declarações RNA de classes e funções de migração são idênticas às da base, verificado por AST. Não há alteração de IDs, esquema, Placement por método, algoritmo geométrico, contrato de precisão, mínimo Blender 4.2.0 ou novos recursos.

## Execuções novas no ZIP acima

Runner existente, entradas congeladas, perfis isolados, novos processos e conferência de artefato/imports antes de cada processo. Foram reutilizados os portáteis oficiais anteriormente verificados; não houve novo download nem alegação de revalidar agora todos os arquivos de download. Identificação real de cada executável está nos registros.

| Blender Windows x64 | Suíte completa |
| --- | --- |
| 4.2.0 | 28/28 |
| 4.2.23 | 28/28 |
| 4.3.2 | 28/28 |
| 4.4.3 | 28/28 |
| 4.5.16 | 28/28 |
| 5.0.1 | 28/28 |
| 5.1.2 | 28/28 |
| 5.2.4 | 28/28 |
| 5.3.0 | 28/28 |

**252 entradas de matriz**, incluindo api_probe: as 25 existentes mais três regressões novas por build. As 14 verificações de infraestrutura passaram separadamente; não são processos Blender da matriz.

Os três scripts novos verificam: causa geométrica e tuple compatível; referência realmente ausente; eixos; correção de malha com mesmas identidades; invalidade/refrescamento via cache, Undo/Redo e Live; publicação/remoção com RuntimeError e TypeError; atualização do Frame saudável; intenção, suspensão e recuperação; wrapper inválido sintético na recuperação global; fechamento de janela real durante erro injetado sem remover o timer; metadados de precisão e compatibilidade string do diagnóstico.

Quatro execuções GUI frias adicionais: 4.2.0/5.3.0 × Unit Scale 1/0,001. Capturas do painel comparativo e do painel original, igualdade de valores RNA e preservação dos demais títulos. **Não são digitação com teclado/mouse.** Os 590 cenários de unidades também foram executados dentro de cada matriz, incluindo recusas esperadas; não representam 590 operações aceitas.

Validações auxiliares novas, com os fixtures existentes e o mesmo ZIP:

- Validação nativa de extensão em 4.2.0, 4.2.23 e 5.3.0.
- Placement em processo novo nas nove builds: Endpoint Volume, Offset Geometry, Live desligado ao reabrir.
- Fixture real 1.7.2 Geometry Endpoint escrita pelo fonte antigo e migrada em novo processo para o candidato em 4.2.0, 4.2.23 e 5.3.0; aviso e escolha legada de Offset preservados.
- Cena representativa escrita em 4.2.0 e lida em 5.3.0: referências/Frame, matrizes, TRS relativo e Dimensions afim GN preservados.

São **20 processos auxiliares**, contados separadamente da matriz e das capturas. O gate fonte/ZIP, metadados e links foi conferido novamente. [Dados e hashes](../../tests/better_item/results/1.7.10/qualification.json), [índice das evidências](../../tests/better_item/results/1.7.10/README.md) e [snapshot](handoff-1.7.10.json).

Para conter o peso do repositório, logs/JSONs/scripts completos ficam em ZIPs padrão com índices e hashes; as três regressões novas também têm JSONs diretamente legíveis. Publicadas as oito capturas frias e duas de sincronização representativas; outras capturas ficam no D, com hashes e disponibilidade declarada. Nenhum perfil, .blend ou runtime Blender foi incluído.

## Falhas de desenvolvimento e limites da investigação de janela

A primeira tentativa detectou um erro novo no teste de pertencimento a bpy_prop_collection e um simulador de layout incompleto. Ambos foram corrigidos antes do artefato final; seus FAILs foram preservados. Uma matriz anterior deste mesmo ZIP passou 28/28 em 4.2.0/4.2.23, mas caiu em 4.3.2 na leitura Window.scene do teste, que ainda acessava diretamente o wrapper após fechar a janela. Essa matriz não foi renomeada como aceite final.

Na primeira rodada auxiliar, a persistência passou na 4.2.0, mas seu JSON foi escrito ao lado do script dentro das entradas congeladas. O guard bloqueou a chamada seguinte. O resultado foi movido, sem descarte, para evidência; os scripts auxiliares passaram a executar de cópias fora das entradas. A rodada corrigida de 20 processos passou integralmente. O registro first-attempt e o resultado deslocado permanecem no arquivo de extras; nenhuma proteção foi desativada e nenhum fonte/ZIP foi alterado nessa correção de orquestração.

O teste foi corrigido para fechar uma única vez e verificar remoção pela coleção viva, sem ler Scene da janela removida. A verificação isolada passou em 4.3.2; depois foi executada de novo a matriz completa nas nove builds com a mesma versão final do teste. O ZIP/runtime não mudou nessa correção de teste.

Os controles sem addon não repetiram o crash: reutilizar uma janela fechada deu TypeError em 4.2.0/5.3.0; a leitura imediata de Scene no controle 4.3.2 retornou sem crash. **A causa exata dos crashes artificiais anteriores não foi conclusivamente isolada.** Não afirmar que o addon reproduziu uma corrida cotidiana nem que um except cura falhas nativas. Os registros/crash permanecem em development; o acesso inválido direto do teste não faz parte do cenário final aceito. A brecha Python original do observador foi demonstrada separadamente por wrapper sintético e tem regressão própria.

As duas regressões iniciais de apresentação falharam contra o ZIP 1.7.9 nos controles, como esperado. Esses FAILs são diagnóstico anterior à correção, não testes aprovados do candidato. As versões exatas de scripts dos controles/tentativas permanecem nos arquivos ZIP de evidência.

## Pendências antes de considerar publicação estável

1. Executar o [checklist de interação real](manual-publication-checklist.md), incluindo digitação de unidade com separadores conforme idioma, Esc/arrasto, Undo/Redo, F9, Live, Normal e troca normal de janelas. Permanece explicitamente não executado por esta qualificação automatizada.
2. Revisar o candidato e decidir o merge/publicação. Esta solicitação autorizou desenvolver na branch; a main não foi alterada.
3. Manter registrada a incerteza do crash artificial. Se reaparecer no uso normal ou no cenário final válido, interromper o fechamento e reduzir a reprodução antes de publicar.

Não há promessa universal de erro físico máximo em mm. Minimum Separation é um parâmetro do solver, não tolerância máxima. A [qualificação de unidades](units-1.7.9.md) permanece válida como limite da base matemática preservada; contratar erro físico absoluto exige decisão e faixa de operação, sem introdução silenciosa nesta manutenção. Nomenclatura geral do mínimo, redesenho UX/UI, novos trabalhos de desempenho, constraints e estado compartilhado não entraram. Animação continua fora; novos alvos Edit Mode continuam estudo para 2.0.
