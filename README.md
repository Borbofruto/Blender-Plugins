# Blender Plugins

Installable extension ZIPs are in [`addons/`](addons); sources are in [`src/`](src). Install an individual add-on ZIP with Blender's **Install from Disk**, not the repository ZIP.

## Better Item 1.4.2

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.4.2.zip) | [Manual](src/better_item/README.md) | [Source](src/better_item) | [Tests](tests/better_item) | [Feedback review](tests/better_item/feedback_review_1.4.2.md)

Panel order: **Reference Frames > Transform > Align and Distribute**. Transform keeps Blender's compact English Location, Rotation, Scale and Dimensions fields, with live edits and proportional XYZ links.

### One reference system for both panels

Transform and Align and Distribute now share the same reference choices, resolver and UI. **Individual** selects Orientation and Location independently. **Frame** selects both components once from a saved frame.

Orientation supports Global, Local, another Object, Viewport, Saved Frame, Normal, Gimbal, View, Cursor, Parent and a named Native Orientation. Location supports Global/world origin, Viewport Pivot, Saved Frame, another Object, 3D Cursor and every native Pivot type, including Bounding Box Center. Frame Location also supports a dedicated World source.

In Selection Bounds and Key Object operations, translating the coordinate origin cancels from the final arrangement. Reference Origin uses the chosen Location as the actual alignment/spacing anchor. Both fields remain available in every mode; no separate limited reference UI is used.

### Native orientations and frames

**New Frame** asks only for a name. Edit Location and Orientation independently using manual values, two separate object pickers, pivots, native orientations or other frames. Frames and consumer selections persist in the .blend, including migrations from older versions.

**Use Orientation in Viewport** creates a synchronized native custom orientation for native G/R. Removing it through the add-on or Blender's native menu ends that export; the timer does not recreate a user-deleted entry. The scene frame remains available. Invalid-source suspension is separate and can recover after its source is repaired. Normal sampling occurs only when relevant input changes, and synchronization uses full viewport context overrides across windows/scenes.

### Corrections and validation

The locked-axis inverse-solve roundoff already accepted by the position solver is now propagated into final world verification, fixing false BI-T006 failures. Real locked-axis movement and unexpected target errors still reject and roll back. Signed native Scale and Delta transforms, linked zero-angle fixes, oblique Dimensions and shared geometry remain covered by regression tests.

Tests pass in Blender 5.2.3 LTS: 1,500 rotated/scaled-parent locked-position cases, 66 reference parity combinations, 630 arrangement combinations, 128 signed-scale rotation cases, 48 native Gimbal comparisons, persistence, migration, native deletion, enum identity and conditional Normal sampling. A real two-main-window test verifies scene-specific exports, live timer updates, native-menu deletion and matching reference controls. The English runtime manual is checked for damaged encoding.

Development tests are in the repository, outside the runtime ZIP. Minimum Blender 5.0. Restart Blender after updating, then open **N > Better Item**.

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
