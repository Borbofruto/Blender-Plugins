# Better Item 1.7.9 — complemento de validação

Registro técnico de 17/11/2026, ZIP `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`. Os dados abaixo pertencem à 1.7.9; a versão atual é a 1.7.10.

## Compatibilidade

| Build Windows x64 | Execução nova no ZIP estável |
| --- | --- |
| 4.3.2 | 25/25 |
| 4.4.3 | 25/25 |
| 4.5.16 | 25/25 |
| 5.0.1 | 25/25 |
| 5.1.2 | 25/25 |
| 5.2.4 | 25/25 |

Total desta rodada: **150 processos de teste**, todos aprovados. Os JSONs individuais, logs, manifests e verificações de portáteis estão em [remaining-builds](../../tests/better_item/results/1.7.9/remaining-builds/README.md). Os checksums oficiais em cache foram reutilizados e os arquivos foram verificados novamente; isso não equivale a dizer que todos os arquivos de checksum foram baixados agora.

Proveniência das demais linhas: 4.2.0, 4.2.23 e 5.3.0 continuam com a matriz completa anterior de **24 entradas** no mesmo ZIP, mais a qualificação posterior de unidades executada separadamente. Não foram renomeadas como novas matrizes completas de 25. As 23 entradas do artefato anterior no ZIP c053f366… continuam sendo outro artefato. Há agora evidência do runtime final nas nove builds, com essas contagens/datas explícitas; não certifica macOS/Linux ou digitação física.

## Unidades e precisão visual

As comparações frias de 4.2.0/5.3.0 mostraram 12,3 mm na 1.7.9 em Unit Scale 1 e 0,001, contra 12,346 mm nativo. A inferência anterior de que 0,001 eliminava a diferença não foi confirmada; as capturas originais foram preservadas. O orçamento de algarismos da formatação de unidade explica o resultado frio, mas não isola a causa da captura antiga.

A 1.7.10 alinha Location/Rotation/Dimensions em 5 e Scale em 3; os valores armazenados não mudam. A [qualificação de unidades](units-1.7.9.md) mantém os limites físicos observados. O [inventário do mínimo](minimum-naming-1.7.9.md) documenta os rótulos existentes.

## Limites dos testes

gui173 passou a aguardar uma condição com prazo máximo em vez de um intervalo fixo; isso foi correção do teste, com controles preservados em release-1.7.9.md. Capturas, parser e setters não certificam teclado/mouse. A 1.7.10 protege o acesso às janelas e corrige o título da pausa de sincronização; não há alegação de causa conclusivamente isolada para os crashes de sondagens artificiais.
