# Better Item 1.7.11 — candidato de correção

**26/11/2026. Candidato na branch `release/1.7.11`; a main continua na 1.7.10.** Aguarda revisão independente e a matriz completa do ZIP final. Não é anúncio de release aprovada.

## Problema e comportamento resultante

Um objeto local e um objeto vinculado de biblioteca podem compartilhar o nome `Cube`. Na 1.7.10, posições eram indexadas por nome: ao alinhar apenas X, o local podia passar de `(5,0,0)` para `(0,20,30)` e o operador retornar sucesso sem diagnóstico. Dependendo da ordem de inserção, também havia T001 indevido, classificação errada de âncora e alvo Live ausente aceito por causa do homônimo.

O candidato mantém a identidade do objeto por todo o plano, aplicação, verificação e Live. O objeto vinculado fixo permanece fixo; quando ele teria de se mover, T001 continua recusando atomicamente. Eixos não escolhidos, matemática, mínimo e budgets não mudam. As ordenações preservam critérios anteriores sem comparar objetos RNA diretamente nem escolher arbitrariamente uma ordem geométrica ambígua.

New Frame também resolvia por nome o alvo capturado. Uma reprodução separada no ZIP 1.7.10 mostrou atribuição ao homônimo local quando o nome vinha do vinculado ativo. Agora o invoke captura um session_uid transitório; rename/troca de ativo não retargetam e remoção não cai para o nome de um substituto. O argumento legado target_name só resolve quando há um único objeto correspondente.

## Limites de compatibilidade

- Referências salvas continuam sendo PointerProperty; vínculos entre Frames, IDs RNA, enums e schema não mudam. Não há nova migração nem identidade de objeto persistida em texto.
- Helpers antigos que recebem mapas por nome continuam aceitos se os nomes dos alvos forem únicos: a conversão para objetos ocorre antes do cálculo. Um mapa ambíguo já perdeu identidade e é recusado com BI-A004 antes de escrever transformações.
- Dois testes existentes mudaram **somente a forma de consumir chaves internas**: `test_better_item_matrix170.py` usa diretamente os objetos da ordem; `test_better_item_stress157.py` consulta targets pelo objeto. Seus oráculos, tolerâncias e resultados esperados não mudaram.
- O teste independente `test_better_item_identity1711.py`, recebido no commit `a2b1bc0`, permaneceu byte a byte inalterado.
- O seletor modern do Distribute, seu padrão e os caminhos Python legados não mudaram. O manual e seu capítulo derivado agora distinguem explicitamente `modern=True` do padrão legado. Leitura zero, limpeza de cache e a implementação da 1.8 ficam fora.

## Artefato e rastreabilidade

- Base oficial: `f7337d0f2bbd7ab19cc346fb8661a1f8ff52aad3`, ZIP 1.7.10 `d0d06869fcb4e6143116f4acad38912a7530e69303452b109200c9a170a02175`.
- Commit dos módulos Python corrigidos: `693c88872e1d55528ae74458684fb5b1fd04a71b`. A embalagem/versionamento é posterior a esse commit para poder identificá-lo sem referência circular.
- ZIP candidato: `9089c65ca34bfa3f8784e1520485a8f42941d85f4b44ee7d4edd9e60c487330b`; fingerprint Python: `44f7d8f4a06c2c2f972383df0b267719f15e3296ce19829a7cfdffd9df49a120`.
- [Snapshot](handoff-1.7.11.json), [índice de execução](../../tests/better_item/results/1.7.11/candidate/index.json) e [evidências compactadas](../../tests/better_item/results/1.7.11/candidate/executions.json.gz).

O gzip contém um objeto JSON que mapeia caminho lógico para texto original de resultados/logs/inputs. Os summaries por build são índices compactos; os resultados completos do runner estão preservados no gzip. Perfis, portáteis, fixtures `.blend` e capturas antigas não são copiados para o Git. Os ambientes completos ficam em `D:/BetterItem/workspaces/identity1711/`.

## Testes executados agora

Somente **Blenders portáteis Windows**, com perfis e temporários isolados. Nenhum Blender instalado foi usado nesta implementação.

| Grupo | Execução nova | Resultado e limite |
| --- | --- | --- |
| Regressão independente na base | ZIP 1.7.10, portáteis 4.2.0 e 5.3.0, pelo runner | Dez controles válidos; nove casos homônimos divergentes por build. A recusa T001 legítima se mantém. São falhas esperadas da base, não PASS do produto. Evidências originais recebidas continuam em `results/1.7.11/identity-on-1.7.10/`; a reprodução local nova está no gzip. |
| Suíte completa no candidato final | **4.2.0: 30/30; 5.3.0: 30/30**, no mesmo SHA acima | Inclui api_probe, regressão independente, cenários existentes de units/rollback/Live/timers/Undo e o novo teste de fronteiras de identidade. Não equivale à matriz de nove builds. |
| Fronteiras de identidade | `test_identity_frame1711.py`, incluído na suíte | New Frame por nome ambíguo, mapa legado ambíguo, presença real na cena, captura renomeada/ativo trocado, captura excluída/substituída e empate BI-D002 nos dois Placement testados. A primeira asserção também falha na base 1.7.10. |
| Integridade do toolkit | **14/14** guards, sem Blender | Preparação, runner e release aceitam dados consistentes e recusam adulteração/stale inputs. Contagem separada da matriz. |
| Persistência/migração | **7 processos auxiliares** aprovados | Writer 1.7.2 (`4db1635`) em 4.2; leitores atuais 4.2/5.3; escolhas Offset Geometry e Endpoint Volume em processos novos nas duas builds; arquivo atual com Frame e estágio GN gravado em 4.2 e lido em 5.3. São os testes auxiliares existentes, com bootstrap de caminho e perfis isolados. |
| New Frame em GUI real | **2 processos auxiliares**, 4.2.0 e 5.3.0 | Invoke real, rename/troca de ativo durante diálogo, F9, reexecução nativa, um Undo/Redo e Esc. Eventos Enter/Esc/F9 simulados pela API nativa; não certificam teclado/mouse físicos. |

O primeiro candidato completo teve duas falhas de compatibilidade de entrada em helpers antigos que forneciam mapas por nome (`matrix160` e `features160`). Essas falhas ficaram preservadas sob o seu SHA original; foram corrigidas na fronteira de entrada, sem alterar os testes para remover as exigências. As execuções finais acima são novas e do novo artefato. Há também rodadas focadas de desenvolvimento, identificadas separadamente no gzip; não são novas matrizes completas.

Para repetir a suíte, usar prepare_matrix.py e run_matrix.py existentes, com a branch e o ZIP exatos. O novo teste GUI é auxiliar (não uma 31ª entrada da matriz), requer perfis isolados e a chamada:

```powershell
& 'CAMINHO/PORTATIL/blender.exe' --enable-event-simulate --factory-startup --python-exit-code 1 --python 'CAMINHO/test_identity_frame_gui1711.py' -- --source 'WORKSPACE/source' --output 'PASTA_ISOLADA'
```

O runner preparado copia esse script como auxiliar. Seus quatro checks validam captura, F9/reexecução, Undo/Redo e cancelamento, e o JSON deve ter passed=true. Os comandos exatos das execuções realizadas estão na evidência.

## Gate pendente

Faltam a revisão independente do diff e a matriz completa nas nove builds declaradas sobre **este SHA**, conforme a divisão de trabalho. O checklist manual continua pendente, incluindo digitação com unidade, mouse e interação física. Não houve merge na main, publicação oficial ou implementação da 1.8. Se a revisão exigir alteração no conteúdo do pacote, será outro SHA e as execuções afetadas precisarão ser refeitas.
