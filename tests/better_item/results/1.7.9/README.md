# Evidência Better Item 1.7.9

A entrega atual é a [consolidação de 17/11/2026](integration/README.md), com ZIP, matriz e benchmarks novos. Os registros abaixo são a contribuição anterior da branch, preservados com seu próprio SHA; não são resultados do ZIP consolidado.

# Contribuição anterior — 16/11/2026

Execuções novas de 16/11/2026 em Windows x64 (PC da Gabriel), com o runner existente. [Relatório e interpretação](../../../../docs/better_item/release-1.7.9.md).

- `matrix/`: 23 entradas por build contra o mesmo ZIP final (SHA256 `c053f366…`): 4.2.0, 4.2.23, 4.3.2, 4.4.3, 4.5.16, 5.0.1, 5.1.2, 5.2.4 e 5.3.0 portáteis oficiais, e `installed-5.3` (Blender 5.3.0 instalado, perfil isolado, `--factory-startup`). 230/230.
- `portable-downloads/`: URL, bytes e SHA256 de cada portátil, conferidos com o arquivo `.sha256` oficial antes da extração.
- `benchmark/before-1.7.8/`: medição nova do ZIP imutável 1.7.8 (`369fb55c…`) com os mesmos scripts de benchmark da 1.7.9.
- `benchmark/after-1.7.9/`: medição do ZIP 1.7.9 anterior à correção da chave linkada (`beb561ad…`). A correção posterior altera só `transform_view.edit_component`, que os benchmarks não executam, por isso eles não foram repetidos. A rodada da matriz desse ZIP anterior (também 230/230) está no commit `dd012cf`.
- `comparison.json`: linhas do benchmark de cache (sem os detalhes de `updates`), `cold_rows`, polling e o estudo de Edit Mode, para as duas versões e as duas builds.
- `extra/`: o teste novo rodado contra a 1.7.8 (falha esperada no caso de deriva) e a reprodução do problema de âncora com troca de Frame (`repro_frame_anchor.py` e as saídas 1.7.8 / 1.7.9 antes da correção), e o caso `reference_switch` falhando no pacote anterior à correção.
- `package-validation.json`: hashes, `extension validate` e paridade com a fonte.

Os registros textuais usam LF; espaços terminais de `blender-version.txt` foram removidos. Não são incluídos `.blend`, perfis, cópias do runtime ou wrappers. As medianas descrevem cenários sintéticos sem limite de aprovação. Os benchmarks rodaram em sequência, sem outros testes concorrentes.
