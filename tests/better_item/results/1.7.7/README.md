# Evidência Better Item 1.7.7

Execuções novas de 16/11/2026; não substituem nem renomeiam resultados históricos. [Relatório completo](../../../../docs/better_item/release-1.7.7.md).

- `matrix/`: execução final das 21 entradas por build, 4.2.23 e 5.3.0, no ZIP SHA256 `b6e0d7cdc6bd6e55ecfab57494bb5003f934548793e00d422254340fe0fe2c1b`. Todos passaram; logs e JSONs atuais estão preservados.
- `new-operator/`: resultados da regressão nova separados da suíte anterior, copiados das mesmas execuções finais; não são execuções adicionais somáveis.
- `baseline-1.7.6/`: controles negativos no ZIP original. `passed:false` é esperado: o teste demonstra Origins no lugar de Bounds Center.
- `migration-persistence/`: fixture legado criado pela 1.7.2 real, lido em novo processo 1.7.7; arquivo atual lido em outro processo para conferir escolhas independentes e Live transitório. O summary registra comandos e códigos de saída.
- `test-development/`: tentativas anteriores do novo harness que falharam por expectativas sobre wrappers/histórico de operadores. Não são aceitação final e não motivaram alterações adicionais de runtime.
- `package-validation.json`: verificações do artefato definitivo e paridade com fontes.

Fixtures `.blend`, módulos extraídos e perfis não são incluídos. São gerados pelos testes. A automação de GUI não certifica uma passada física completa de mouse/F9. As demais builds do relatório 1.7.6 não foram repetidas agora.

Os registros textuais foram normalizados para LF; espaços terminais das linhas de flags em `blender-version.txt` foram removidos. Valores, mensagens e resultados foram preservados.
