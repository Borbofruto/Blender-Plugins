# Blender Plugins

Installable extension ZIPs are in [`addons/`](addons); sources are in [`src/`](src). Install an individual add-on ZIP with Blender's **Install from Disk**, not the repository ZIP.

## Better Item 1.3.0

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.3.0.zip) · [Manual](src/better_item/README.md) · [Source](src/better_item) · [Dimensions benchmark](tests/better_item/performance.md)

One compact, English **Transform** panel with live Location, Rotation, Scale and Dimensions. Drag or type to edit immediately. Choose axes and origin independently: Global, Local, another Object, Viewport or a Saved Frame. Dimensions uses evaluated vertex extrema; oblique mesh dimension edits preserve the base mesh with an affine modifier when necessary.

Panel order: **Transform > Align and Distribute > Reference Frames**.

### Alignment, distribution and diagnostics

Version 1.3.0 fixes floating-point cancellation that falsely rejected ordinary align/distribute combinations. Position targets are solved directly, with parent-space precision checks and rollback.

Choose arrangement axes independently from Transform: Global, Active Local, Object, Saved Frame or Viewport. Align/distribute by Selection Bounds, fixed active Key Object, or Reference Origin. Reference Origin also permits an independent origin object/frame or cursor.

To arrange targets along a rotated reference line: choose **Align To: Reference Origin**, **Axes: Object** or **Saved Frame**, select a single X/Y/Z axis, set signed Spacing, enable **On Reference Axis**, and click Distribute. This is a straight axis arrangement with no continuing relationship to the reference.

Minimum Distance defaults to **0.00001 mm**. Invalid spacing and ambiguous starting coordinates are rejected before movement, with error codes, object names, affected axes and corrective guidance. Errors remain visible in the panel. Regression tests cover 630 arrangement combinations plus reference lines, parenting, drivers, constraints, mixed frames and persistence.

### Reference Frames

The **+** next to a frame selector creates a named Manual, Object (Independent) or Object (Linked) frame and selects it immediately. Location and Orientation are separate components of the same frame. Manual Location + linked Orientation and linked Location + manual Orientation can be entered directly during creation. Each component can be used without requiring the unused component to be valid.

Frames and reference selections are saved in the .blend; a fresh-process save/reopen test verifies persistence. Apply Reference stores current source values and ends links. Frame links never create parenting or constraints on targets.

Dimensions uses vectorized, bounded caches. Version and description are maintained only in the extension manifest. Tested in Blender 5.2.3 LTS; minimum Blender 5.0. Restart Blender after updating, then open **N > Better Item**.

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
