# Evidência Better Item 1.7.8

Execuções novas de 16/11/2026 em Windows x64, com o runner existente. [Relatório e interpretação](../../../../docs/better_item/release-1.7.8.md).

- `matrix/`: 22 entradas por build, 4.2.23 e 5.3.0, contra o mesmo ZIP final. Inclui a nova regressão de invalidação e as 21 entradas anteriores.
- `benchmark/before-1.7.7/`: medição nova do ZIP imutável 1.7.7 com o mesmo script de benchmark usado na 1.7.8.
- `benchmark/after-1.7.8/`: medição do ZIP final, separada da matriz para que um summary não sobrescreva o outro.
- `comparison.json`: medianas antes/depois, contadores de inspeção/tree matching e custo explícito de sync. As amostras de eventos são sequenciais e os testes não foram executados concorrentemente com o benchmark.
- `package-validation.json`: integridade, sintaxe e paridade do artefato.

Os registros textuais usam LF; espaços terminais das flags de `blender-version.txt` foram removidos. Não são incluídos `.blend`, perfis, cópias do runtime ou relatórios externos integrais. Desempenho não é critério de aprovação por milissegundos: a regressão verifica frescor e número de inspeções. As medianas descrevem um cenário sintético, não uma promessa de FPS ou de desempenho universal em malhas densas.
