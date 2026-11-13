# Blender Plugins

**Instalar Better Item:** [baixe better_item-1.1.0.zip](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.1.0.zip) e escolha esse arquivo em **Preferences > Add-ons > Install from Disk**. Os ZIPs instaláveis estão em `addons/`; os fontes estão em `src/`. o ZIP do botão Code > Download ZIP contém o repositório inteiro e não é o pacote de instalação.

## Better Item 1.1.0

Orientação de transformações: **Global**, **Local do objeto** ou **Local de outro objeto**, com conta-gotas. Movimento, rotação incremental, escala e dimensões na orientação escolhida. A posição da referência não define o pivô.

Correção: vínculos de rotação interpretam 0° como 360° no cálculo proporcional, permitindo chegar e sair de zero. O valor digitado é mantido no campo.

Transformações com vínculos proporcionais por eixo, alinhamento e distribuição por origens. Painel **N > Better Item**, no Modo Objeto.

- Posição, rotação Euler, escala e dimensões com correntes independentes para XYZ e bloqueios nativos.
- Alinhamento ao mínimo, centro e máximo das origens selecionadas ou à origem do objeto ativo.
- Distribuição entre extremos ou com passo assinado a partir do objeto-chave, que permanece fixo.
- Eixos globais independentes; prioridade ao lado contrário ao passo e ordenação pela distância à chave.

[Baixar ZIP 1.1.0](https://github.com/Borbofruto/Blender-Plugins/raw/refs/heads/main/addons/better_item-1.1.0.zip) · [Manual e limitações](src/better_item/README.md) · [Código](src/better_item)

Instale pelo **Edit > Preferences > Add-ons > Install from Disk** e ative **Better Item**. Blender 5.0 ou superior; testado no Blender 5.2.3 LTS. Quaternion e eixo-ângulo possuem edição nativa, sem vínculos proporcionais.


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
