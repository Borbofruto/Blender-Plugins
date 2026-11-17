# Revisão complementar da 1.7.9 — compatibilidade e propostas visuais

17/11/2026. Resposta aos dois feedbacks recebidos após `02f6728`. **O código da main e o instalador estável não mudaram.** SHA256 do ZIP: `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`.

## 1. Lacuna de builds: execução concluída

O ponto de revisão era correto: não se devia atribuir a este ZIP a matriz de outro artefato. Foram executadas agora as **25 entradas da suíte atual** nas seis builds que faltavam, com os portáteis oficiais e o runner existente, perfis isolados e novos processos. Verificação de SHA256 do download/extrator e conferência contínua do artefato/imports pelo runner.

| Build Windows x64 | Execução nova no ZIP estável |
| --- | --- |
| 4.3.2 | 25/25 |
| 4.4.3 | 25/25 |
| 4.5.16 | 25/25 |
| 5.0.1 | 25/25 |
| 5.1.2 | 25/25 |
| 5.2.4 | 25/25 |

Total desta rodada: **150 processos de teste**, todos aprovados. Os JSONs individuais, logs, manifests e verificações de portáteis estão em [remaining-builds](../../tests/better_item/results/1.7.9/remaining-builds/README.md). Os checksums oficiais em cache foram reutilizados e os arquivos foram verificados novamente; isso não equivale a dizer que todos os arquivos de checksum foram baixados agora.

Proveniência das demais linhas: 4.2.0, 4.2.23 e 5.3.0 continuam com a matriz completa anterior de **24 entradas** no mesmo ZIP, mais a qualificação posterior de unidades executada separadamente. Não foram renomeadas como novas matrizes completas de 25. As 23 entradas da antiga branch no ZIP c053f366… continuam sendo outro artefato. Há agora evidência do runtime final nas nove builds, com essas contagens/datas explícitas; não certifica macOS/Linux ou digitação física.

## 2. Proposta de precisão por grupo e título BI-F006

A proposta está em [proposal/better-item-ui-precision](https://github.com/Borbofruto/Blender-Plugins/tree/proposal/better-item-ui-precision), commit `65971a2`, **sem merge**. [Explicação, hashes e capturas](https://github.com/Borbofruto/Blender-Plugins/blob/proposal/better-item-ui-precision/docs/better_item/ui-precision-proposal.md).

| Grupo | Main estável | Nativo conferido | Proposta |
| --- | ---: | ---: | ---: |
| Location | 3 | 5 | 5 |
| Rotation | 3 | 5 | 5 |
| Scale | 3 | 3 | 3 |
| Dimensions | 3 | 5 | 5 |

Frame e Spacing permanecem em 5. A proposta muda apenas os metadados desses campos e dá a BI-F006 o título **Orientation sync paused**. Preserva corpos das mensagens, severidades, títulos dos outros diagnósticos, métodos string de Diagnostic, getters/setters, estado persistido e política do sincronizador.

Baseline e candidato foram comparados em **processos frios** de 4.2.0 e 5.3.0, Unit Scale 1 e 0,001, com captura de painel lado a lado e do painel real. No candidato também passaram native-sync e os 590 cenários de unidades em cada build. Isso não é uma matriz completa de release do candidato. O seu ZIP temporário tem outro SHA e **não substitui** addons/better_item.zip. A escolha entre manutenção 1.7.9 e 1.8.0 permanece com Gabriel.

### Correção da inferência sobre Unit Scale 0,001

Meu relatório anterior inferiu uma dependência de Unit Scale a partir de duas capturas sequenciais. Essa conclusão causal foi forte demais. As novas capturas frias, inclusive do painel real, mostram **12,3 mm na baseline em ambas as escalas**, enquanto o nativo mostra 12,346 mm. O desaparecimento na imagem antiga não foi reproduzido de modo controlado; a causa específica continua incerta. A imagem e os registros antigos foram preservados, sem reclassificá-los.

No código de formatação de unidades do Blender, a precisão visível é tratada como orçamento de algarismos significativos, ajustado pelos algarismos inteiros do valor convertido. Para 12,3456789 mm: orçamento 3 → uma casa decimal → 12,3; orçamento 5 → três casas → 12,346. Mudar Unit Scale e manter o mesmo comprimento físico não altera esse valor convertido em mm nem torna o campo precision 3 equivalente a precision 5. O parâmetro não significa cinco casas decimais fixas nem mais precisão de armazenamento.

Fontes primárias conferidas: [unit.cc 4.2.0](https://github.com/blender/blender/blob/v4.2.0/source/blender/blenkernel/intern/unit.cc#L1597), [UI 4.2.0](https://github.com/blender/blender/blob/v4.2.0/source/blender/editors/interface/interface.cc#L3709), [unit.cc 5.3.0](https://github.com/blender/blender/blob/v5.3.0/source/blender/blenkernel/intern/unit.cc#L1665) e [UI 5.3.0](https://github.com/blender/blender/blob/v5.3.0/source/blender/editors/interface/interface.cc#L4204). Scale não tem unidade de comprimento e mantém a precisão nativa 3.

## 3. Nome do mínimo: mapeado, sem renomear o pacote

O [inventário](minimum-naming-1.7.9.md) lista propriedade da Scene, override do painel, propriedade/execução do operador, F9, mensagens BI-D001/D002/D003/E001, README e fluxo de conversão. Preserva os identificadores `minimum_distance_mm` e `minimum_mm` e distingue o estado da Scene da cópia do operador. Nenhuma unificação de nomes foi implementada, nem na main nem na proposta visual.

## 4. Sincronização: política intencional, texto proposto separado

No estável, fonte inválida reconhecida por BetterItemError segue a política de remover/suspender a exportação e recuperar quando a fonte voltar. Falhas inesperadas de leitura/publicação, incluindo RuntimeError/TypeError, são isoladas e entram em retentativa com BI-F006, sem fingir que a orientação foi apagada externamente ou que a fonte foi provadamente inválida. `native_enabled` representa a intenção de exportar; não prova que os eixos estão atualizados. Isso deve continuar visível.

Uma falha inesperada ao remover também chega ao isolamento do Frame em vez de ser engolida. O título atual Reference unavailable é inadequado para esse estado; a proposta visual o troca sem alterar essa política. Não houve alteração do sincronizador enquanto a matriz do estável era executada.

## 5. gui173 e janela fechada: separar evidência de hipótese

O primeiro gui173 falhou no candidato anterior por verificar o resultado após um intervalo fixo. A espera por condição, com prazo máximo, foi uma correção do teste, não do produto Live. O controle de atraso injetado, a primeira falha preservada e a repetição completa continuam descritos no [relatório da consolidação](release-1.7.9.md). A nova rodada de seis builds usa a mesma versão corrigida do teste; não houve nova tolerância relaxada nesta revisão.

O acesso `window.scene` nos laços de recuperação do observador está efetivamente fora do try interno de _redraw_scene. Uma falha nessa avaliação poderia escapar do tratamento final. **Não foi reproduzido aqui um usuário fechando uma janela e derrubando esse timer.** É um ponto estático de robustez, não evidência de crash atual nem motivo para reclassificar a matriz. Não foi incluído silenciosamente na branch visual ou no ZIP. Uma eventual proteção deve ser tratada e validada separadamente.

## 6. Peso da evidência e checklist humano

Não foram apagados registros anteriores ou reescrita a história. Para os dados novos, os summaries guardam referências com hash aos JSONs individuais, evitando duplicar todas as árvores de resultados. A reconstrução sem perda foi verificada. Nesta rodada, os seis summaries passaram de **2,855,535 para 61,336 bytes** publicados, mantendo cada resultado individual e os logs. Não foram incluídos perfis, runtime, downloads ou .blend. Isso reduz duplicação sem tornar os resultados opacos em um arquivo compactado único.

O [checklist manual](manual-publication-checklist.md) agora inclui entrada física **“12,3456789 mm”**, o controle com ponto conforme idioma, comparação nativa, Unit Scale 1/0,001, Dimensions, entrada sem sufixo, Esc e Undo/Redo. Está marcado como **pendente**, não como executado. Parser via API e screenshots não substituem teclado/mouse.

A pasta handoff-1.7.9 permanece sinalizada como histórica. Não houve nova ação sobre ela. Os limites físicos observados na [qualificação de unidades](units-1.7.9.md) permanecem: precisão visual alinhada ao nativo não cria uma garantia absoluta de erro em mm.
