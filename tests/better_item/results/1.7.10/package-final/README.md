# Better Item 1.7.10 — validação do pacote oficial

Instalação pelo teste existente e validação nativa da extensão passaram em **nove builds Windows x64**: 4.2.0, 4.2.23, 4.3.2, 4.4.3, 4.5.16, 5.0.1, 5.1.2, 5.2.4 e 5.3.0. São **18 processos Blender**, mais **14 guards de infraestrutura** separados.

O SHA oficial está em validation.json e provenance.json. A diferença em relação ao ZIP da matriz de runtime é somente CHANGELOG.md; todos os módulos Python e demais arquivos são iguais. Não se trata de repetir ou renomear a matriz completa de 28 entradas.

Cada pasta tem registros completos em records.zip, índice com hashes, log de validação nativa e resultado do instalador. Os bytes arquivados foram conferidos. Nenhum perfil, runtime ou arquivo de cena foi publicado. A matriz anterior e as verificações manuais não executadas mantêm seu escopo original.
