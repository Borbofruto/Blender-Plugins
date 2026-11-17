# Evidência da 1.7.9 consolidada — 17/11/2026

ZIP `6a01eb809165347e94668d259a492b922b69f0c368657cae48599a2f57a9f029`. [Relatório](../../../../../docs/better_item/release-1.7.9.md).

- `matrix/`: 24 entradas em cada uma de 4.2.0, 4.2.23 e 5.3.0. Execuções novas, 72/72.
- `infrastructure/`: 14 verificações Python separadas, sem executar Blender.
- `extra/`: validação nativa, persistência por método, fixture 4.2.0→5.3.0, falhas esperadas contra a branch anterior e controle do teste GUI sob atraso injetado.
- `benchmark/`: novas medições sequenciais com os mesmos scripts em 1.7.8 e no consolidado. `comparison.json` reúne os dados.
- `test-development/`: primeira matriz 4.2.23 reprovada em uma entrada assíncrona, recheck e controles. Evidência de desenvolvimento, separada da aceitação final.
- `suite.json` e `workspace-inputs.json`: identificação exata do ZIP e dos inputs usados. `acceptance.json` consolida os resultados, sem somar contagens de categorias diferentes.

Não são incluídos perfis, cópias do runtime, bytecode ou arquivos .blend. A execução dos setters não certifica arrasto físico do mouse. Os diretórios irmãos de matriz/benchmark da outra branch permanecem com os próprios hashes e datas.
