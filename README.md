# Blender Plugins

Install individual extension ZIPs from [`addons/`](addons) using Blender's **Install from Disk**. Sources are in [`src/`](src), tests in [`tests/`](tests). The repository ZIP is not an addon installer.

Each addon uses a stable installer filename. Updates replace that file; earlier contents remain available in Git history.

## Better Item 1.7.4

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item.zip) | [Manual](src/better_item/README.md) | [Release report](docs/better_item/release-1.7.4.md) | [Review and limitations](docs/better_item/review-1.6.1.md) | [Source](src/better_item) | [Tests](tests/better_item)

[AI maintainer handoff — Portuguese](docs/better_item/continuidade/README.md) | [Full engineering manual](docs/better_item/CONTINUIDADE-IA.md) | [Audited source snapshot](docs/better_item/handoff-1.7.3.json)

A spatial-precision Transform, Reference Frames and Align/Distribute addon for Blender 5.0+, tested in Blender 5.2.3 LTS. Compact English XYZ fields support proportional links, physical projected Dimensions, origin alignment and signed distribution.

### Distribution by references, points and occupied geometry

1.7.4 adds a scene-aware Custom Orientation picker and informative setup guidance to the shared reference UI. Existing Endpoint, Offset and Live behavior is retained. See the correction report for the Blender API compatibility limitation and executed tests.

- Explicit Offset / Endpoint. Between Points uses Start-to-End direction; Reference Axis projects End onto one chosen reference axis.
- Start inherits shared Location or uses an override. End accepts world coordinates, Object, Frame Location, cursor, Global or active object. The distributor does not move endpoint objects; users may move them as Live inputs.
- Endpoint uses Origins, Bounds Center and Center of Mass (Surface / Volume) points, permitting overlap without resizing. Offset also offers Geometry Bounds for physical gaps.
- Inspect actual spacing or Mixed. Live captures targets and Active Object without movement, follows cursor / Object / Frame references even after selecting an Empty, and stops when disabled. It is transient editing, not animation. Offset preserves unselected coordinates and zero Geometry Bounds gap keeps the last nonzero direction. This is not a permanent relationship or animation runtime.
- Contextual Frame sources are explicit Capture actions; native Bounding Box Center uses origins. The old single-reference Individual Origins choice is retired while legacy saved data remains readable.

[1.7.3 behavior and validation](docs/better_item/release-1.7.3.md). [1.7.0 behavior and test history](docs/better_item/release-1.7.0.md). Tested on Blender 5.2.3 LTS / Windows: 256 Endpoint batches, 140 Offset batches, 96 Live batches / 192 reference updates, independent centroid/bounds checks, preview/undo, dependency rollback, fresh-process persistence, legacy-file compatibility and real UI. The 9,216-case numerical grid belongs to earlier validation records and was not repeated in this correction. Declared minimum Blender 5.0 has not been runtime-tested here.

The sidebar retains Location before Orientation, the Gimbal category icon and indented dependent fields. Frames store independent Manual or linked Location/Orientation and can publish axes to Blender's native custom orientations for G/R. Transform edits the active object; alignment/distribution works on the selection.

Install from Disk using the stable ZIP above. Restart Blender if an older module remains loaded. Open **N > Better Item**. The [manual](src/better_item/README.md) covers volume conditions, native precision, unsupported parent/constraint cases, preview lifecycle and migration. No tests or animation prototype are included in the installer.

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

