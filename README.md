# Blender Plugins

Installable extension ZIPs are in [`addons/`](addons); sources are in [`src/`](src). Install an individual add-on ZIP with Blender's **Install from Disk**, not the repository ZIP.

## Better Item 1.5.1

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.5.1.zip) | [Manual](src/better_item/README.md) | [Source](src/better_item) | [Tests](tests/better_item)

Panel order: **Reference Frames > Transform > Align and Distribute**. Compact English Location, Rotation, Scale and Dimensions fields support live edits and proportional XYZ links. Transform and Align and Distribute share the full **Reference: Individual / Frame** system.

### Reference UI revision in 1.5.1

Transform, Align and Distribute, and the frame editor use the same component selectors. Location directly lists Global, Frame, Object, Parent and all five native pivots, with familiar native icons. Orientation lists the supported native axes and addon sources directly. Local and Viewport shortcuts are excluded from these readouts; Custom Orientation... explicitly opens a named source field. Frames add only Manual storage, keeping Location and Orientation independent.

Align and Distribute has no extra Align To selector. Bounding Box Center exposes origin-bound Min/Center/Max and fixed-extreme distribution; other Location choices anchor alignment and signed Spacing to the chosen point. Active Element keeps the active selected source fixed. Frame pointers inherit their Location component's behavior.

Older Local/Viewport orientation choices migrate to a fixed saved orientation; Viewport Pivot becomes the concrete selected native pivot. Validation covers 81 reference combinations, all three rendered panels, matching component controls, source parity, point/bounds arrangements, old-file migration and save/reopen. Runtime animation behavior is unchanged by this revision.

### Relative animation

Expand **Animation**, choose Location and/or Rotation, then **Start Relative Animation**. The usual transform rows become real animatable relative channels: key a component with I, or use the group diamond. Moving the reference changes the animated trajectory. Ordinary transform operations retain their existing independent behavior until relative animation is explicitly enabled.

Object, Parent, Cursor, named native custom orientations and context-independent saved-frame components can stay live. Viewport/selection-dependent sources are captured when animation starts. Missing sources apply the last valid cached component to the owned animation frame without modifying shared public frames. References and caches persist in the .blend.

**Bake to Native Keyframes** samples the active actor into a separate native action, retains the authoring action, and pauses relative control. Bake actors needed by the hierarchy before removing the addon or exporting. Native parenting remains in place; unrelated native Scale/Delta curves are retained. Conflicting native pose animation, target constraints/drivers, NLA and cyclic references produce diagnostics.

Outside relative mode, group diamonds insert native keys, including owned affine Geometry Nodes rows for oblique Dimensions. Alt-click deletes the group's keys at the current frame.

### Parent and spatial trace

**Parent** is now an independent Location/Orientation choice, also available as a saved frame component. Labels identify a missing parent, direct parent or nested hierarchy. The frame uses the parent's world origin and scale-free axes; it is not a substitute for the native Location channels when Parent Inverse, Scale or Delta transforms are involved.

Expand **Transform Information** for read-only world, reference, native and Delta readings, source hierarchy, effective parent/inverse origin, transformed local contribution and evaluation residual. Optional matrices expose the affine calculation behind those readings.

### Frames and native orientations

New Frame asks only for a name. Edit Location and Orientation independently with manual values, separate object sources, saved frames, native pivots or native orientations. Frames and consumer choices are saved in the .blend. Use Orientation in Viewport publishes synchronized native custom axes for G/R. Removing that orientation through Blender's native menu ends the export without deleting its scene frame.

### Validation

Tested in Blender 5.2.3 LTS: real UI playback and same-frame reference changes; animated/deleted controllers; native orientation deletion; fresh-process save/reopen; signed Scale, Delta and parented rotation storage; native bake with the addon unregistered; native/affine Dimensions keying; and actual CPU render pixel movement with a hidden controller in an excluded collection. Earlier coverage includes 1,500 locked-parent roundoff cases, 81 reference combinations, 630 arrangements and 128 signed-scale rotation cases.

The runtime ZIP contains source, manifest, license and manual; development tests stay in the repository. Minimum Blender 5.0. Restart Blender after updating, then open **N > Better Item**.

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
