# Blender Plugins

Install individual extension ZIPs from [`addons/`](addons) using Blender's **Install from Disk**. Sources are in [`src/`](src), tests in [`tests/`](tests). The repository ZIP is not an addon installer.

## Better Item 1.5.3

[Download ZIP](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.5.3.zip) | [Manual](src/better_item/README.md) | [Source](src/better_item) | [Tests](tests/better_item)

### Patch 1.5.3

Reject unsupported Default Euler API calls on Quaternion/Axis-Angle without changing the object, report unsupported Dimensions types correctly, and show Unavailable for failed reference trace readings instead of zero vectors. Native Quaternion/Axis-Angle widgets, valid zero readouts, Bounding Box Center, frame enum identities and deletion behavior remain unchanged. Four unused imports were removed. Targeted guards/trace tests, a real UI check and existing precision/reference/arrangement regressions pass in Blender 5.2.3 LTS.

A spatial-precision Transform, Reference Frames and Align/Distribute addon for Blender 5.0+, tested in Blender 5.2.3 LTS. English compact XYZ fields support proportional links, projected Dimensions, origin alignment and signed distribution.

- **Default / Local** reads and edits the actual Item channels. **Reference** measures and edits using selected Location and Orientation references.
- Reference selectors are shared by Transform, Align/Distribute and frame components. Dropdown groups are **Better Item** and **Default**, with familiar icons. Default pivots are directly selectable.
- Object, Frame, Global, the standard pivots/axes and explicitly named custom orientations cover reference choices. Parent shortcuts are removed from the visible list; existing shortcuts migrate to explicit Object sources. There is no capture-from-viewport control.
- **Rotate Around Reference Location** uses the chosen Location reference as the rotation center; otherwise Rotation preserves the object's own origin.
- **Use Orientation in Viewport** still exports a frame as native custom axes for G/R. Native-menu deletion ends the export; the 0.2-second detector now explicitly redraws affected viewports without mouse interaction.
- The BI-T006 rounding budget now retains separate parent and Parent Inverse terms before cancellation. Tests pass for 1,200 such cases and 842 moves across -210..210 mm with the reported manual frame settings, alongside 1,500 locked-parent cases and existing reference/arrangement regressions.

### Current scope and archived animation prototype

The active 1.5.3 ZIP has no Better Item keyframe operators, relative-animation properties, playback handlers, animation panel or bake controls. The full 1.5.1 prototype, its tests and its original ZIP are preserved separately in [`archive/better_item-animation-1.5.1`](archive/better_item-animation-1.5.1). Existing relative authoring data is retained but not evaluated by 1.5.3; use the archived version to bake an existing clip before switching. This is a deliberate scope boundary.

Restart Blender after updating, then open **N > Better Item**. The runtime ZIP contains source, manifest, license and manual; development tests and the archive are outside it.

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
