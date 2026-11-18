# Better Draft (nome provisório) — especificação da v0

Documento de implementação, 18/11/2026. Autoria do desenho: Gabriel. Este documento é a fonte do escopo; o que não estiver aqui não entra na v0.

## 1. Por que este addon existe

O Better Item posiciona objetos com precisão, mas a exportação continua sendo malha. Os vértices saem no lugar certo; o que se perde é a **intenção geométrica**: "isto é um arco de raio 5", "isto é um furo circular", "isto é uma reta de 40 mm". Este addon recupera essa intenção a partir da malha e a exporta como entidades técnicas (LINE, ARC, CIRCLE) em DXF.

Princípio: **o algoritmo sugere, a pessoa decide.** Uma sequência de poucas faces pode ter sido feita para ser facetada de propósito. O addon nunca transforma em arco algo que a pessoa marcou como linhas, e nunca altera a geometria da malha.

Lacuna de mercado (pesquisa de 18/11/2026): exportadores de DXF a partir de malha no Blender escrevem segmentos (polilinhas); ferramentas que escrevem ARC/CIRCLE reais partem de curvas, não de malha. Não foi encontrado addon que reconheça arcos em malha com bevel.

## 2. Convenções do repositório

- Mesmo repositório do Better Item (`Borbofruto/Blender-Plugins`), mesma organização: `src/better_draft/`, `addons/better_draft.zip`, `tests/better_draft/`, `docs/better_draft/`.
- Branch de trabalho própria (sugestão: `feature/better-draft-v0`). Não tocar no Better Item nem no Paper.
- Código novo, escrito do zero. **Não copiar código do Paper/Export Paper Model.** Licença GPL-3.0-or-later, como todo addon que usa a API do Blender.
- Nome do addon, rótulos e prefixos de operador centralizados (um módulo de constantes), porque o nome ainda não foi decidido. Prefixo provisório dos operadores: `better_draft.`.
- Versão mínima do Blender: **4.2** (igual ao Better Item, para o kit). Se algo exigir mais, parar e perguntar.
- Mesma disciplina do Better Item: recusa sem efeito parcial, mensagens que dizem o motivo e o que fazer, evidência registrada por SHA do ZIP, limites declarados no relatório. Texto público sem narrativa de processo.

## 3. Escopo da v0

**Tema:** exportar o contorno de uma peça plana em DXF, com arcos e círculos reconhecidos a partir da malha.

### 3.1 Entrada

- Objetos de malha selecionados, em Object Mode. Usa a malha **avaliada** (modificadores aplicados em cópia temporária), sem alterar o original.
- Para cada objeto, a v0 trata **uma região plana**:
  - se a malha inteira é plana (chapa sem espessura, típica de corte), usa todas as faces;
  - se a malha tem espessura, usa as faces coplanares à face ativa, ou, sem face ativa, à maior face. (Escolha da face por Edit Mode antes de exportar.)
- Contornos = laços de arestas de borda da região: um laço externo e zero ou mais furos.
- Malha não plana dentro da tolerância, região sem laço fechado, ou laços que se cruzam → recusa com mensagem; nada é escrito.

### 3.2 Sistema de coordenadas

- Plano da região → base 2D (origem e dois eixos ortonormais). Regra determinística para escolher os eixos (por exemplo, eixo U = projeção do X do objeto no plano; se degenerado, do Y).
- Opção de exportar no plano local da peça (padrão) ou projetado no plano XY do mundo quando a região for paralela a ele.
- Unidades: converter pela escala da cena para **milímetros**. Escala 1:1.

### 3.3 Reconhecimento

Para cada laço, em float64:

1. **Retas por subdivisão:** vértices com ângulo de giro abaixo da tolerância de reta são absorvidos (subdivisão sem ângulo vira uma reta só).
2. **Cantos:** giro acima do limite de canto separa trechos.
3. **Candidatos a arco:** sequências de 3 ou mais segmentos com giro pequeno, no mesmo sentido.
4. **Ajuste de círculo:** ajuste algébrico (Kåsa ou Taubin) seguido de refinamento geométrico (Gauss-Newton). Guardar centro, raio, ângulos inicial e final, desvio máximo dos vértices ao círculo.
5. **Laço inteiro em arco** → CIRCLE.
6. **Confiança (0 a 1)** por candidato, combinando:
   - número de segmentos versus o mínimo;
   - regularidade do giro entre segmentos;
   - regularidade do comprimento dos segmentos;
   - desvio do ajuste relativo à tolerância.
   A fórmula é provisória e **deve ser calibrada pelos testes** (seção 6), não escolhida por gosto. Documentar a fórmula final e os dados que a justificam.
7. **Decisão:** vira ARC se confiança ≥ limite e o trecho não estiver marcado como "linhas"; vira linhas se confiança < limite ou se marcado. Marcado como "arco" vira ARC se o ajuste ficar dentro da tolerância; senão, recusa aquele trecho com mensagem (não inventa arco).

Parâmetros expostos no diálogo de exportação, com padrões a calibrar:

| Parâmetro | Função | Padrão inicial |
| --- | --- | --- |
| Limite de confiança | A partir de quanto vira arco | a calibrar |
| Mínimo de segmentos | Abaixo disso nunca vira arco automaticamente | 4 |
| Tolerância de reta (graus) | Giro abaixo disso é subdivisão | a calibrar |
| Tolerância de ajuste (mm) | Desvio máximo aceito entre vértice e arco | a calibrar |

### 3.4 Marcação manual (mínimo da v0)

A janela de revisão é da v1. Na v0, a pessoa já pode corrigir casos pontuais:

- Atributo inteiro nas **arestas** da malha (nome provisório `better_draft_arc_mode`): 0 automático, 1 forçar arco, 2 forçar linhas. Criado só quando a pessoa marca algo.
- Operadores em Edit Mode, no menu de contexto (botão direito) e no menu Edge: "Marcar como arco", "Marcar como linhas", "Voltar para automático", aplicados às arestas selecionadas. Um passo de Undo cada.
- Um trecho com arestas de modos diferentes: regra explícita e documentada (proposta: "linhas" vence "arco", que vence "automático").
- O atributo é a única escrita na malha e só acontece por ação explícita.

### 3.5 Saída DXF

- Entidades: LINE, ARC, CIRCLE. Camadas: `OUTER` (contorno externo) e `INNER` (furos). Nada de POLYFACE, 3DFACE ou malha.
- Unidade declarada como milímetros no cabeçalho.
- Biblioteca: preferir **ezdxf** (licença MIT, Python puro) empacotada como wheel no manifesto da extensão; confirmar que a instalação pelo ZIP funciona sem internet. Se o empacotamento falhar, alternativa: escritor próprio mínimo. Registrar a escolha e o motivo.
- Um arquivo por objeto ou um arquivo com todos (opção), sem sobreposição: na opção "um arquivo", peças lado a lado com espaçamento configurável.

### 3.6 Relatório

Após exportar, relatório por trecho: tipo final, raio, centro, número de segmentos, desvio máximo, confiança, se foi marcado manualmente. Resumo no aviso do Blender e relatório completo num bloco de texto do Blender (Text Editor) ou arquivo `.txt` ao lado do DXF.

### 3.7 Onde aparece

Seguindo o retorno de usuários do Better Item (falta de menus e atalhos):

- File > Export > "Technical Profile (.dxf)" (rótulo provisório), com os parâmetros no diálogo.
- Operadores de marcação no menu de contexto do Edit Mode.
- Sem painel lateral na v0, salvo se for indispensável.

## 4. Fora da v0

- Janela de revisão com cores (v1, seção 7).
- Mais de uma região por objeto, vistas ortogonais, cortes, cotas no desenho.
- 3D (DXF 3D, STEP), superfícies, chapa dobrada (fator K), nesting otimizado.
- Elipses, splines, raio variável (ficam como linhas).
- Importação de DXF.
- Medidas na viewport (candidato da v2, reaproveitando a detecção).

## 5. Pronto quando

- Testes da seção 6 passando em 4.2, 4.5 e 5.x (Linux headless aceitável para a v0; Windows conforme a rotina de Gabriel).
- DXF de cada caso relido por uma biblioteca independente do escritor (ezdxf como leitor no teste) e conferido contra a geometria conhecida.
- Pelo menos um DXF aberto por Gabriel num programa de CAD ou de corte (passo manual, fora do alcance dos testes).
- Fórmula de confiança e padrões documentados com a tabela de calibração.
- ZIP instalável, `docs/better_draft/` com README curto e relatório da v0 com limites declarados.

## 6. Testes e calibração

Formas geradas por código, com geometria conhecida (gerar com bmesh e também com o modificador/operador Bevel real do Blender, porque a posição dos vértices do bevel é o que importa):

| Caso | Variação | O que verificar |
| --- | --- | --- |
| Retângulo com cantos arredondados | raio R, segmentos 2, 3, 4, 6, 8, 16, 32 | classificação por número de segmentos; erro de raio e de centro |
| Furo circular | segmentos 6 a 64 | CIRCLE, raio e centro |
| Oblongo (rasgo) | dois semicírculos e duas retas | dois ARC + duas LINE, tangência |
| Facetado intencional | 3 segmentos de giro igual | com mínimo 4: linhas; marcado como arco: ARC |
| Reta subdividida | 1 aresta dividida em 10 sem giro | uma LINE |
| Misto | arco seguido de chanfro de 1 segmento | separação correta |
| Escalas | escala de cena 1 e 0,001; objeto escalado e rotacionado | mm corretos |
| Longe da origem | peça a 1 km | erro registrado (float32 da malha) |
| Recusas | malha não plana, laço aberto, laços que se cruzam | nenhum arquivo escrito, mensagem com motivo |
| Marcação | atributo em arestas, Undo | prioridade entre modos; malha sem outra alteração |

**Calibração:** gerar a tabela confiança × número de segmentos × desvio para os casos acima e escolher os padrões a partir dela. Entregar a tabela no relatório.

## 7. v1 (registrada, não implementar)

Janela de revisão desenhada por Gabriel:

- Antes de concluir a exportação, abre uma janela (ou workspace temporário, se a janela nova se mostrar instável) com vista de topo ortográfica e rotação travada, mostrando o contorno da região.
- Retas em preto; trechos candidatos coloridos por confiança, vermelho quando vão virar arco. A cor muda ao vivo conforme o limite e as marcações.
- A pessoa seleciona vértices ou arestas e ajusta o índice do trecho para mais ou para menos, ou força arco/linhas; pode dividir e unir trechos.
- Desenho por cima via módulo `gpu` sobre uma malha temporária em Edit Mode (seleção nativa), em vez de objetos Curve com um material por trecho.
- As decisões gravam no mesmo atributo da v0, então a v1 não muda o formato de dados.

Por isso a v0 já deve separar o reconhecimento (puro, testável, sem `bpy` onde possível) da interface.

## 8. Perguntas para Gabriel (não decidir sozinho)

- Nome final do addon.
- Se a região plana deve vir da face ativa ou de outra regra.
- Qualquer parâmetro cujo padrão a calibração não consiga justificar.
