# Blender Plugins

Installable extension ZIPs are in [`addons/`](addons); sources are in [`src/`](src). Install an individual add-on ZIP with Blender's **Install from Disk**, not the repository ZIP.

## Better Item 1.4.0

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.4.0.zip) · [Manual](src/better_item/README.md) · [Source](src/better_item) · [Dimensions benchmark](tests/better_item/performance.md)

Panel order: **Reference Frames → Transform → Align and Distribute**. Transform keeps Blender's compact English Location, Rotation, Scale and Dimensions fields, with live edits and proportional XYZ links.

Both consuming panels have a **Reference: Individual / Frame** switch. Frame selects both Location and Orientation once. Individual keeps the two choices independent, including components from different frames.

**New Frame** asks only for a name. Edit Location and Orientation separately afterward: manual values, two independent object pickers, another frame, native pivots for Location, or native transform orientations for Orientation. Existing one-source frames migrate to separate pointers. Apply Location or Apply Orientation captures just that component and ends its link.

**Use Orientation in Viewport** exports a synchronized native custom orientation for **G/R** and axis shortcuts. Frames may source other native custom orientations, including exported frame orientations. Native sources include Global, Local, Normal, Gimbal, View, Cursor and Parent; pivots include all five native types. A single frame represents one origin, so Individual Origins uses the active object's origin. Circular links and missing sources produce diagnostics; invalid exported orientations are suspended until repaired. Native synchronization refreshes every 0.2 seconds.

Frames, separate source pointers, component chains and reference choices are saved in the .blend. Reference changes alter readings and future operations; moving a source never moves an already-transformed target.

Alignment/distribution uses origins in the selected reference axes, with Selection Bounds, fixed Key Object, or Reference Origin. Signed spacing, reference-axis placement, minimum-distance diagnostics and transactional rollback are preserved. Dimensions measures evaluated vertices and preserves the mesh through an affine modifier for oblique edits when needed.

Tested in Blender 5.2.3 LTS: 630 arrangement combinations, native G/R, 48 Gimbal direction comparisons against native transforms, edit-mode Normal, cyclic and missing sources, undo/redo, migration, projected dimensions and new-process save/reopen. The actual panel layout was visually checked. Minimum Blender 5.0; restart Blender after updating, then open **N > Better Item**.

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
