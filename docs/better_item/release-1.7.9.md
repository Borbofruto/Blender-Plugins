# Better Item 1.7.9 — consolidação e estabilização

Entrega de **17/11/2026**, sobre a 1.7.8 `97a676d6e320742fa83185f62296c9d1730116d5`. Integra `release/1.7.9` (`de73eaa`) e a manutenção local (`0ef6b94`), preservando seus históricos. Instalador único no mesmo caminho `addons/better_item.zip`. Mínimo: **Blender 4.2.0**.

## O que entrou

- Razões linkadas não acumulam o erro de cada releitura float32 nas edições sucessivas e continuam através de zero enquanto a referência e os valores observados permanecem compatíveis.
- A leitura fria identifica emissores de instâncias uma vez por estado avaliado, preservando a recusa BI-M005; deixa de percorrer todas as instâncias para cada objeto.
- A assinatura dos elementos de Normal é reutilizada nos ticks ociosos; eventos, conjunto de objetos e a rede de segurança de 2 s continuam provocando uma leitura completa.
- Falha inesperada de um Frame não encerra o timer nativo nem bloqueia outros Frames. Falhas de cena/observador também têm diagnóstico transitório BI-F006 e retentativas de 1/2/4/8 s. Exclusão externa não recria a orientação; fonte inválida preserva a suspensão anterior. Undo/load/unregister limpam a saúde transitória.
- Prepare/runner conferem versão, SHA, fingerprint, inventário e bytes do runtime e dos inputs. Recusam contaminação sem apagar resultados ou perfis. Um erro de integridade no meio da execução invalida o summary. O gate de release confere README, changelog, snapshot, checksum e paridade ZIP/fonte.

Preservados schema, migração, enum IDs, escolhas de Placement por método, contratos espaciais e solvers. Dos 15 módulos, oito mudaram e sete permanecem idênticos à 1.7.8. Não há redesign de UI, descoberta Custom, animação ou alvos Edit Mode novos. A mensagem BI-F006 pertence ao tratamento de uma falha objetiva, sem reformular os demais fluxos do painel.

## Correções encontradas na integração

1. **Default Euler:** a chave da razão não incluía `obj.rotation_mode`. Zerar uma rotação linkada, trocar XYZ→ZYX e editar X reutilizava a razão anterior e alterava Y/Z. A chave agora inclui a ordem nativa.
2. **Links off/on:** mudar a configuração e voltar à anterior, sem editar, recuperava uma âncora antiga. O callback RNA já existente agora remove as âncoras daquele objeto. A recusa BI-T008 ao partir de zero sem razão válida permanece.
3. **Checksum:** `dist/SHA256SUMS` voltou a corresponder ao ZIP atual.

As duas novas regressões falham separadamente no ZIP original da branch (`c053f366…`) e passam no consolidado. [Falhas esperadas](../../tests/better_item/results/1.7.9/integration/extra/before-branch/expected-failures.json). O teste de gestos tem nove casos; Dimensions não admite atravessar uma singularidade física apenas porque Location/Scale admitem zero.

## Artefato e evidência nova

SHA256: `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`. Python combinado: `b468b68b34354621378140325cc0c40c96655788d40dc332b24aa04e041dcccd`. [Snapshot](handoff-1.7.9.json), [aceitação](../../tests/better_item/results/1.7.9/integration/acceptance.json), [suite e resultados](../../tests/better_item/results/1.7.9/integration/README.md).

| Executado nesta consolidação, Windows x64 | Resultado |
| --- | --- |
| Blender 4.2.0 | 24/24 |
| Blender 4.2.23 LTS | 24/24 |
| Blender 5.3.0 | 24/24 |
| Verificações Python externas da infraestrutura | 14/14, contagem separada |
| Validação nativa da extensão | Aprovada nas três builds |
| Persistência de Placement em processo novo | Endpoint Volume / Offset Geometry / Live desligado nas três builds |
| Fixture escrita em 4.2.0 e aberta em 5.3.0 | Referências, Frame vinculado, valores e estágio GN preservados |

Perfis e TEMP/TMP isolados no D:, processos novos, GUI real nas entradas pertinentes e `--python-exit-code 1`. Os testes não alteraram instalações ou arquivos de clientes. A instalação pelo operador nativo também faz parte de cada matriz. Não se somam os 14 testes externos às 24 entradas Blender.

## Medição nova antes/depois

O ZIP 1.7.8 imutável foi medido novamente contra **este ZIP consolidado**, com os mesmos dois scripts atuais e o runner consolidado. Processos sequenciais, sem outras execuções Blender em paralelo. [JSON completo](../../tests/better_item/results/1.7.9/integration/comparison.json). São cenários sintéticos sem limite de aprovação temporal, não uma promessa de FPS.

Primeira inspeção após limpar todos os caches de runtime, mediana de três amostras:

| Build | Cenário | 1.7.8 | Consolidado |
| --- | --- | ---: | ---: |
| 4.2.23 | GEOMETRY / 1.500 | 0.614 s | 0.166 s |
| 4.2.23 | VOLUME / 1.500 | 0.865 s | 0.387 s |
| 5.3.0 | GEOMETRY / 1.500 | 0.800 s | 0.162 s |
| 5.3.0 | VOLUME / 1.500 | 1.122 s | 0.456 s |

Normal em seleção densa (130.562 vértices), mediana de 30 ticks explícitos em GUI:

| Build | Tick ocioso 1.7.8 | Consolidado | Varreduras em 30 ticks |
| --- | ---: | ---: | ---: |
| 4.2.23 | 35.919 ms | 0.045 ms | 30 → 0 |
| 5.3.0 | 61.338 ms | 0.054 ms | 30 → 0 |

Trocar por outro vértice com a mesma contagem continuou alterando a amostra Normal. A varredura de segurança após 2 s permanece. Transformações alheias e updates de geometria seguem a política conservadora da 1.7.8; não foi criado um rastreador universal de dependências.

## Ocorrência durante a validação do teste GUI

A primeira matriz 4.2.23 do candidato `015d87d6…` teve uma falha em `test_better_item_gui173.py`: depois de 0,8 s a distribuição Live ainda estava no estado inicial. A repetição isolada e os controles instrumentados em 1.7.8/consolidado passaram. A causa exata daquele atraso não foi comprovada.

O teste assumia que seu callback ocorreria depois de um tick Live. Se os dois estão vencidos após um bloqueio da UI, o callback de teste registrado primeiro pode verificar antes do Live. Uma injeção controlada de bloqueio de 1,2 s reproduziu a falha com a espera fixa, no mesmo runtime em que a espera pela condição passou. O teste agora aguarda a condição observável com prazo de 10 s; não chama o timer manualmente, não ignora erros do addon e preserva as mesmas asserções. A matriz final inteira foi repetida nas três builds com esses inputs congelados. [Controle](../../tests/better_item/results/1.7.9/integration/extra/delayed-gui/controlled-delay.results.json).

O primeiro resultado reprovado, o recheck e os controles permanecem em `integration/test-development/`. Não foram convertidos em aprovação nem misturados às 72 entradas da matriz final.

Uma tentativa auxiliar de fixture também falhou antes de carregar o addon, porque um caminho raso no D: não tinha o terceiro ancestral pressuposto pelo script antigo. O auxiliar foi executado a partir da pasta de resultado já preparada pelo runner, com seu runtime verificado, e passou nas duas etapas. Essa saída inicial foi preservada separadamente; o código do produto e o teste não foram alterados para contorná-la.

## Proveniência anterior e pendências

Os registros anteriores de 23 entradas × 10 executáveis continuam em `results/1.7.9/matrix/`, com SHA `c053f366…`. Os benchmarks anteriores usam outro ZIP (`beb561ad…`). [Relatório anterior preservado](release-1.7.9-branch.md) e [snapshot anterior](handoff-1.7.9-branch.json). Eles não certificam este novo instalador nas builds intermediárias.

Os probes anteriores à manutenção local estão em `integration/before-fix-assessment/`: a exceção nativa foi injetada uma vez na 1.7.8 e deixou o timer desregistrado com exportação ainda habilitada e eixos velhos; não foi um crash espontâneo de produção. Esses registros da avaliação anterior não foram reexecutados nesta consolidação. A regressão GUI atual valida isolamento e recuperação no novo ZIP.

Permanecem para a próxima etapa: passada humana de mouse/F9/cancelamento/larguras, diagnósticos e clareza de estados da 1.8.x. Foi reproduzida uma mensagem inadequada de Volume em malha aberta (“Complete references…” com referências válidas); a correção fica no bloco de diagnósticos. Não se certificaram macOS/Linux GUI, todas as builds intermediárias ou todos os backends. Edit Mode é estudo para futura 2.0; animação permanece fora do produto.

## Qualificação posterior, sem alterar o artefato

O [estudo de unidades](units-1.7.9.md) acrescenta testes e achados físicos/visuais ao mesmo ZIP. A regressão padrão foi ampliada para 25 entradas; a matriz de 24 relatada acima continua sendo a execução histórica da consolidação. Não foi repetida nesta rodada.
