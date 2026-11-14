# Blender Plugins

Install individual extension ZIPs from [`addons/`](addons) using Blender's **Install from Disk**. Sources are in [`src/`](src), tests in [`tests/`](tests). The repository ZIP is not an addon installer.

## Better Item 1.5.7

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.5.7.zip) | [Manual](src/better_item/README.md) | [Feedback review and remaining issues](docs/better_item/feedback-1.5.7.md) | [Source](src/better_item) | [Tests](tests/better_item)

A spatial-precision Transform, Reference Frames and Align/Distribute addon for Blender 5.0+, tested in Blender 5.2.3 LTS. Compact English XYZ fields support proportional links, physical projected Dimensions, origin alignment and signed distribution.

### Feedback-driven correction release

- Use float64 Dimensions projection and affine calculations; verify tiny results without a fixed absolute tolerance. Native channels and world positioning have separate precision checks.
- Verify Location/Rotation readback against moving references and verify Rotation's final pivot position. Invalid results reject and roll back; self-following references are never silently frozen.
- Validate affine node structure and retain independent modifier identity. Guard zero-dimension collapse, unrealized instances and edited driver components; preserve the conservative constraint policy.
- Execute all 11 suggested test groups, including 9,216 round-trip cases, 192 native Rotation comparisons, 1,000 linked edits, bone/vertex parenting, 100-frame chains and real UI/timer checks. Detailed limits and results are in the feedback report.
- Keep animation outside the runtime scope; move historical validation notes out of the current usage manual.

### Current capabilities

**Default / Local** shows actual Item channels; **Reference** measures and edits with independent Location/Orientation choices or one saved Frame. Selectors use **Better Item / Default** groups and standard icons. Scale remains native. Reference Dimensions projects evaluated geometry along unit directions and may use a final affine GN modifier when native Scale cannot represent the edit. Location coordinates and exported axes retain their full basis.

Frames store manual or linked components independently. **Use Orientation in Viewport** publishes live native custom axes for G/R; deletion through Blender's menu ends the export. Transform and Align/Distribute use references without adding parenting or constraints. Alignment/distribution operates on origins, not gaps between geometric bounds.

Measurement caches invalidate on frame/subframe evaluation without writing transforms or animation. Normal sampling optimization, constraint flexibility and interactive frame manipulators remain separate future decisions.

Tests cover stack rejection/atomicity, source preservation, stable enum serials, old reference-file migration, old authoring-data isolation, native exports, current UI, cache freshness, physical dimensions and the prior precision/arrangement regressions. If an older module remains loaded after updating, restart Blender. Open **N > Better Item**.

## Export Paper Model - Medidas 1.5.1

Add-on para gerar PDFs vetoriais de peças com cotas em milímetros, escala declarada e régua de conferência.

Derivado do **Export Paper Model 1.4.2**, de Adam Dominec. Esta versão é uma modificação independente, sem vínculo com a publicação oficial do autor original.

### Instalação

1. [Baixe o ZIP da versão 1.5.1](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/export_paper_model_medidas-1.5.1.zip).
2. No Blender, abra **Edit > Preferences > Add-ons > Install from Disk** e selecione o ZIP.
3. Ative **Export Paper Model - Medidas**. Mantenha somente uma cópia do add-on ativa.
4. Reinicie o Blender se estiver atualizando uma instalação existente.

Compatibilidade declarada: **Blender 5.0 ou superior**. Testado no **Blender 5.2.3 LTS**.

O pacote usa o mesmo identificador `export_paper_model` da extensão original e a substitui.

### Uso

Selecione a peça e abra **N > Paper > Export** ou **File > Export > Paper Model (.pdf)**.

Escolha o modo:

- **Perfil de corte (ignorar espessura)**: padrão para chapas planas. Extrai uma superfície principal, preservando contorno, furos e rasgos passantes, sem abrir frente, verso e paredes da espessura.
- **Desdobramento completo**: abre todas as faces do sólido, com opções de abas, numeração de montagem e texturas.

Mantenha **Maior trecho reto na vertical (90 graus)** para orientar a peça por um trecho reto contínuo, mesmo quando ele é composto por várias arestas. O contorno não é dissolvido ou modificado. Altura e largura são medidas pelos extremos da peça após a rotação.

As cotas mostram a dimensão real em mm. O rodapé informa a escala efetivamente utilizada e oferece uma régua para conferir importação e impressão. A saída é exclusivamente PDF, inclusive para documentos com várias páginas.

O controle **N > Paper > Unfold > Tolerância da geometria > Limite (ppm)** ajusta a detecção de arestas e faces degeneradas. O padrão é 1 ppm; valores menores aceitam detalhes menores. Esse controle não altera a geometria nem a verificação de faces não planas.

### Limites relevantes

- O perfil automático é destinado a chapas planas de espessura uniforme com recortes passantes. Rebaixos e furos cegos não são interpretados como cortes passantes.
- Modificadores não aplicados não são avaliados; é usada a malha-base do objeto.
- Arredondamentos continuam sendo os segmentos da malha, sem reconstrução automática de arcos ou Bézier.
- Uma ilha grande não é automaticamente dividida em folhas menores. Ajuste a página ou a escala.
- Confira cotas e escala no editor gráfico e remova as anotações antes de preparar o corte.

Veja as [instruções completas](src/export_paper_model/LEIA-ME.md).

### Código e pacote

- [Código-fonte do add-on](src/export_paper_model)
- [ZIP instalável](addons/export_paper_model_medidas-1.5.1.zip)
- [SHA-256 do pacote](dist/SHA256SUMS)

Para reconstruir o pacote na raiz do repositório:

```powershell
blender --background --factory-startup --command extension build --source-dir src/export_paper_model --output-dir addons
```

### Créditos e licença

Autor original: **Adam Dominec**, projeto [Export Paper Model](https://extensions.blender.org/add-ons/export-paper-model/).

Os avisos de autoria originais e o manifesto foram preservados. Licença **GPL-3.0-or-later**, conforme o manifesto do add-on; o texto da GPL v3 está em [LICENSE](LICENSE).
