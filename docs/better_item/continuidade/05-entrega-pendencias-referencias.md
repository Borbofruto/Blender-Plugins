# Entrega, manutenção, pendências e passagem de contexto

[Índice](README.md) · [Manual integral](../CONTINUIDADE-IA.md)

> Leia primeiro [Contexto atual](../CONTEXTO-ATUAL.md). Este capítulo é histórico; não representa sozinho o estado vigente.

Base: Better Item 1.7.3, commit `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.

Gerado de CONTINUIDADE-IA.md, SHA-256 `3aa559e3c3679f3a3488d2f82041f1a0c7e7638313a53f9794d93abea316b928`. Não editar este capítulo isoladamente; altere o manual integral e execute `gerar.py`.

<a id="s21"></a>
## 21. Empacotamento, GitHub e publicação

### 21.1. Checklist do instalador

Para uma alteração de runtime:

1. Atualizar a versão em `blender_manifest.toml`, que é a fonte de versão da extensão. Não reintroduzir `bl_info` duplicado.
2. Revisar README, CHANGELOG e códigos de diagnóstico afetados.
3. Empacotar apenas runtime, manifesto, licença e documentação do pacote.
4. Manter nome `addons/better_item.zip`; não criar uma coleção de ZIPs numerados em `addons` ou na raiz.
5. Verificar integridade do ZIP, conteúdo e ausência de testes, fixtures, `.blend`, logs, `__pycache__`, protótipo de animação ou dependências locais não planejadas.
6. Rodar validação de extensão.
7. Extrair o ZIP para outro diretório e executar testes contra o **conteúdo extraído**, confirmando o módulo importado.
8. Calcular SHA-256 e atualizar somente a linha pertinente de `dist/SHA256SUMS`, preservando outros add-ons.
9. Publicar fontes, testes, evidências e instalador coerentes.
10. Ler de volta o commit/manifesto e verificar o blob do ZIP remoto.

Para uma alteração apenas documental como este manual, não há razão para recompilar o instalador ou aumentar a versão do add-on. O commit de documentação pode ser posterior ao commit de runtime.

### 21.2. Esboço de build portátil

Os scripts de staging usados nas últimas entregas ainda eram utilitários locais com caminhos/listas específicos. Um build portátil consolidado é uma oportunidade de manutenção, não algo que se deva afirmar já existir.

Este exemplo demonstra o formato do pacote atual; adapte a política de assets se o pacote ganhar subdiretórios:

```python
from pathlib import Path
import hashlib, os, sys, tomllib, zipfile

repo = Path(sys.argv[1]).resolve()
source = repo / 'src' / 'better_item'
manifest = tomllib.loads((source / 'blender_manifest.toml').read_text(encoding='utf-8'))
assert manifest['id'] == 'better_item'
assert manifest['version']
names = {p.name for p in source.glob('*.py')}
names |= {'blender_manifest.toml', 'README.md', 'CHANGELOG.md', 'LICENSE'}
assert '__init__.py' in names
out = repo / 'addons' / 'better_item.zip'
out.parent.mkdir(parents=True, exist_ok=True)
temporary = out.with_name('better_item.zip.tmp')
with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(names):
        path = source / name
        assert path.is_file()
        archive.write(path, name)
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    assert 'blender_manifest.toml' in archive.namelist()
os.replace(temporary, out)
print(hashlib.sha256(out.read_bytes()).hexdigest())
```

Esse é um exemplo de instrução, não uma ferramenta de release adicionada por esta documentação. O código deve ser revisado e testado antes de substituir a cadeia de entrega. Metadados/timestamps do ZIP podem alterar o hash de uma reconstrução mesmo com conteúdo equivalente; o SHA publicado identifica o arquivo exato da entrega, não toda reconstrução futura possível.

### 21.3. Validação pelo Blender

```powershell
$zipPath = Join-Path $repoPath 'addons/better_item.zip'
& $blenderExe --background --factory-startup --command extension validate $zipPath
if ($LASTEXITCODE -ne 0) { throw 'Pacote de extensão inválido.' }
Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath
```

`validate` verifica o pacote/metadados conforme o comando da versão; não prova funcionamento matemático ou desenho da UI. A documentação oficial aceita um diretório de pacote ou arquivo como SOURCE_PATH. [CLI de extensões 5.2](https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html).

### 21.4. Git convencional e o método utilizado nesta produção

Com checkout autenticado e ferramentas adequadas, um fluxo normal de diff/commit/push é preferível a reconstruir um sistema paralelo de versionamento. As últimas entregas usaram o conector GitHub/Git Data porque a fonte trabalhada estava em staging local sem `.git`.

O procedimento efetivamente utilizado foi:

1. Ler `refs/heads/main` e o commit corrente.
2. Obter a árvore real do commit e seu inventário recursivo.
3. Preparar uma lista `{path, local, encoding, sha}` dos arquivos desejados.
4. Comparar com os blobs remotos e enviar somente alterações. Um blob já presente no repositório pode ser reutilizado em outro caminho.
5. Criar blobs UTF-8 para texto ou Base64 para o ZIP. Conferir o SHA retornado.
6. Criar nova árvore usando **base_tree_sha**, preservando os arquivos não relacionados, inclusive Export Paper Model.
7. Criar commit com o HEAD lido como pai.
8. Atualizar a referência com o HEAD esperado como lease e `force=false`.
9. Conferir HEAD final, manifesto e hash/tamanho do ZIP na árvore publicada.

Não confunda SHA de commit, SHA de árvore e SHA de blob. Para este repositório, o SHA de blob Git usa o cabeçalho e os bytes do arquivo, diferente de um SHA-1 simples do arquivo:

```python
blob_sha = sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
```

O arquivo de checksums de distribuição usa SHA-256, outra finalidade. O conector utilizado não era adequado para buscar o ZIP como texto; a conferência binária remota foi feita por metadados de árvore/blob e pelo payload enviado, além do teste local do ZIP.

### 21.5. Conflitos, limites de ferramentas e segurança operacional

Se o HEAD mudar antes do update da referência, releia o commit e avalie as alterações concorrentes. Não use force para contornar a lease nem reconstrua uma árvore vazia apagando arquivos alheios.

Ferramentas/conectores podem mudar de nome ou formato. Descubra as capacidades disponíveis em vez de presumir que os nomes internos da sessão anterior continuarão iguais. Se houver recusa de autorização, limitação ou falha de publicação, não anuncie push concluído: diga o que ficou preparado e o que permanece bloqueado.

Leia conteúdo multiline a partir de arquivos ou argumentos estruturados. Não trate `JSON.stringify` como escape de shell nem monte comandos que possam executar `$()`/backticks contidos num texto. Não exponha tokens nem despeje Base64 do instalador no relatório.

Não faça limpeza recursiva ampla para preparar um build. Confirme o diretório absoluto e use operações nativas com `LiteralPath` no Windows. O staging não deve depender de remover pastas do perfil do Blender ou projetos reais.

<a id="s22"></a>
## 22. Procedimento para corrigir um problema

### 22.1. Ficha mínima de reprodução

Peça ou registre somente o que falta:

```text
Versão do Blender / Better Item e caminho do módulo carregado:
Sistema operacional:
Scene Unit Scale e unidade exibida:
Objeto ativo e seleção:
Pais, Parent Inverse, deltas e sinais de Scale:
Constraints/drivers relevantes:
Modo Default / Local ou Reference:
Location e Orientation resolvidas (ou Frame + componentes):
Operação, eixos, Spacing, Placement, Start/End e caminho:
Live habilitado? Alvos/Active capturados diferentes da seleção atual?
Resultado esperado, resultado obtido e mensagem completa:
Arquivo sintético/script de reprodução:
```

Não peça um arquivo de cliente se consegue reproduzir com cinco cubos. Não atribua automaticamente a falha a “malha do usuário” sem medir qual precondição realmente falta.

### 22.2. Ordem de diagnóstico

1. **Identidade do código:** a versão instalada é a que você acha? O source importado é o correto? Há dois pacotes registrando os mesmos IDs?
2. **Configuração incompleta:** falta fonte/eixo/seleção ou é uma operação efetivamente inválida?
3. **Contrato:** Endpoint por pontos, Geometry Offset, Reference Axis ou Between Points? A expectativa é do modo atual?
4. **Referência:** congelada, vinculada, contextual ou seguindo o próprio alvo?
5. **Planejamento:** registre alvos float64 antes de escrever.
6. **Canal nativo:** qual Location/rotação/Scale foi pedido depois de resolver pai/delta?
7. **Estado avaliado:** o Blender reteve esse canal e a posição/orientação mundial?
8. **Precisão:** compare resíduos com termos de armazenamento e condicionamento, não com um epsilon improvisado.
9. **Dependências:** mover o objeto mudou sua geometria, a fonte ou o pai?
10. **Rollback:** tudo voltou ao estado anterior, inclusive grupos e pilha?

Se o resultado só parece errado visualmente, confira o ponto/intervalo representativo: geometria assimétrica, origem deslocada e projeções em eixos girados podem produzir resultados corretos que não parecem “encostar pelas faces” em 3D.

### 22.3. Pequenos casos que valem ouro

| Caso | O que revelar |
|---|---|
| Pai deslocado e filho com Location zero | Distinguir canal nativo de coordenada mundial. |
| Parent Inverse com termos grandes que se cancelam | Verificação final não pode esquecer erro intermediário. |
| Scale `(-1,1,1)` com pai e referência externa | Não transferir espelho para Euler/Scale errado. |
| Delta Location não zero e edição de Rotation | Não duplicar deslocamento. |
| Location relativa explicitamente zero num eixo, outros não zero | Dica de zero e proteção de proporção. |
| Grupo com três origens em X=3,8,19 e Offset global | Mixed antes; intervalos escolhidos depois; não usar média como estado real. |
| Cubos com Y/Z diferentes, distribuir só X | Preservar os componentes desmarcados. |
| Geometry Offset negativo e depois zero | Manter o sentido negativo. |
| Cinco cubos em Endpoint de comprimento 0,5 | Sobrepor sem redimensionar, se os pontos continuam resolvíveis. |
| Dois Empties externos e alvos desmarcados no Live | Captura e acompanhamento reais, sem mudar seleção. |
| Empty selecionado depois de capturar Active Object | Não retargetar a referência Active inadvertidamente. |
| Mover manualmente um alvo móvel no Live | Pausar, não sobrescrever a alteração do usuário. |
| Criar geometria alheia após habilitar Live | Não normalizar um grupo ainda intocado. |
| Renomear, remover ou recriar um Frame | Identidade, enum estável, strings vivas e limpeza. |
| Inserir modificador depois do estágio Dimensions | Recusar com orientação de reposicionar, sem duplicar. |
| 200 peças e referência em centenas de unidades | Precisão do armazenamento não pode ser tratada como falha indevida. |

### 22.4. Não resolver o problema errado

Uma exceção por instâncias não realizadas não exige implementar um avaliador completo de instâncias. Uma rotação impossível sob escala parental não uniforme não exige introduzir parenting artificial. Uma superfície aberta em Center of Mass (Volume) não exige estimar densidade física por heurística.

Primeiro identifique a promessa do produto. Uma recusa correta, explicada e atômica pode ser a solução certa. O trabalho é resolver o conjunto de casos contratado e diagnosticar seus limites, não cobrir toda geometria possível do Blender.

<a id="s23"></a>
## 23. Pendências, oportunidades e limites de conhecimento

Esta seção é uma agenda de investigação. Nenhum item passa a ser escopo autorizado só porque aparece aqui.

### 23.1. Decisões de produto pendentes

**Referências do Transform compartilhadas.** O usuário sugeriu que a configuração acompanhasse o painel, em vez de variar por objeto, mas a 1.7.3 manteve o armazenamento atual. Se isso voltar à pauta, definir primeiro se o dono será cena, view layer, workspace, janela ou outro contexto. Não mover todos os vínculos/travas junto por acidente. Precisará de migração e política para objetos de cenas diferentes.

**Interações adicionais.** Manipular Frame por gizmo, outro pivô nativo ou operações em massa no Transform não faz parte da entrega corrente. Verificar primeiro se ferramentas nativas ou o cursor já resolvem o caso.

**Congelamento para lançamento.** Houve concordância em priorizar correções e validação antes da primeira publicação comercial. Não usar uma revisão técnica para começar uma nova linha de recursos.

### 23.2. Trabalhos explicitamente separados

**Otimização de Normal.** O timer pode reconstruir uma assinatura grande de elementos selecionados e histórico para descobrir que nada mudou. Uma revisão incremental pode reduzir custo, mas precisa preservar atualização de seleção, modo, undo, múltiplos objetos/cenas e dependências. Não é sinônimo de remover a verificação.

**Flexibilização de constraints.** Há operações válidas que o bloqueio conservador pode recusar. Uma classificação melhor exige saber quais canais e dependências afetam o resultado, não apenas comparar o tipo de constraint. Preservar validação e rollback continua obrigatório.

**Novas interações de viewport.** É uma etapa de produto diferente de melhorar solver/cache. Os indicadores de Frame não são manipuladores, e a exportação nativa já cobre uma parte importante do fluxo.

### 23.3. Melhorias de manutenção justificadas

| Prioridade | Item | Evidência / próximo passo |
|---|---|---|
| Alta para compatibilidade | Matriz de versões/OS | 5.0 é mínimo declarado, mas só 5.2.3/Windows foi executado. Testar explicitamente antes de prometer suporte amplo ou revisar o mínimo. |
| Alta para confiabilidade | Runner unificado com códigos de saída, logs e fixtures | Muitos scripts independentes e algumas fases manuais. Consolidar execução sem apagar evidência histórica nem transformar scripts dependentes em pytest por suposição. |
| Média | Build portátil e verificável | Os builds anteriores têm listas e caminhos locais. Padronizar a partir de `src`, com validação e teste do ZIP. |
| Média | Mensagens com nomes atuais | Há texto de recusa em `placement.py` ainda falando em Volume/Surface Centroid. Revisar também `_GUIDANCE`, que pode esconder a mensagem específica do solver. |
| Média | Política de timers sob erro inesperado | `distribution_preview.poll` possui suspensão/diagnóstico, mas `native_refs.sync` tem caminhos cujo erro inesperado pode escapar. Fazer fault injection e verificar registro/recuperação; não afirmar que uma falha espontânea já foi reproduzida. |
| Média | Testes de interação manual contínua | Há timer real e operadores nativos, mas não uma auditoria completa de drag modal, Esc, seleção durante G, histórico e troca de editor. |
| Média | Fonte/contexto em múltiplas cenas/view layers | Há evidência histórica de exportações em múltiplas janelas. Ainda convém testar objetos compartilhados entre cenas com referências por objeto, view layer removida durante Live e trocas rápidas de contexto. |
| Média | Herança externa durante Live | A captura usa baselines nativos e partes lineares. Exercitar translação/rotação/escala de pais e fontes que sobrepõem alvos, definindo o comportamento esperado antes de ampliar a guarda. |
| Baixa / condicionada a medição | Otimizar observação Live de seleções grandes | Há custo O(n) de assinaturas e possíveis medições frias. Medir workloads reais; não sacrificar frescor para uma taxa de atualização aparente. |
| Baixa | Formatação/clareza de módulos | Existem funções compactas e imports locais para evitar ciclos. Melhorar quando reduzir risco real, não como refactor indiscriminado. |

### 23.4. O que não está demonstrado

- Que todos os scripts históricos passam sem configuração no snapshot atual.
- Que a declaração Blender 5.0+ foi executada em todas as versões ou sistemas.
- Que handlers garantem uma determinada ordem universal em todos os contextos de render/playback.
- Que validação de winding/arestas certifica um volume físico sem autointerseções.
- Que um painel desenhado sem exceção é agradável em toda largura, escala de UI e tema.
- Que contagens altas de testes provam ausência de bugs.
- Que os estudos comerciais/benchmark propostos foram todos concluídos.

### 23.5. Ordem recomendada de continuidade

1. Preservar o contrato atual e reproduzir qualquer novo relato com cena mínima.
2. Corrigir defeitos demonstrados com testes de regressão e efeito colateral.
3. Consolidar a validação reproduzível e o build, sem ampliar funcionalidades.
4. Fazer beta de fluxos humanos reais, incluindo arquivos de projeto tratados com cuidado.
5. Só então discutir decisões novas de armazenamento/UX e trabalhos separados, com casos de uso claros.

<a id="s24"></a>
## 24. Fontes, referências e material histórico

### 24.1. Fontes primárias do próprio projeto

Base congelada de código: [src/better_item no commit 1.7.3](https://github.com/Borbofruto/Blender-Plugins/tree/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/src/better_item).

Testes congelados: [tests/better_item no mesmo commit](https://github.com/Borbofruto/Blender-Plugins/tree/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/tests/better_item).

Instalador exato da base: [better_item.zip pelo commit](https://github.com/Borbofruto/Blender-Plugins/raw/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/addons/better_item.zip). O link por `main` entrega a versão que estiver publicada no momento, não necessariamente a base deste manual.

| Registro | Conteúdo |
|---|---|
| [README do runtime](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/src/better_item/README.md) | Manual de usuário, contratos, limites e códigos atuais. |
| [CHANGELOG](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/src/better_item/CHANGELOG.md) | Mudanças por entrega. |
| [Histórico até 1.6.0](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/delivery-history-through-1.6.0.md) | Registros antigos preservados com ressalva de evidência histórica. |
| [Manutenção 1.5.5](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/maintenance-1.5.5.md) | Limpeza, propriedade do estágio afim e escopo adiado. |
| [Feedback 1.5.6](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/feedback-1.5.6.md) e [1.5.7](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/feedback-1.5.7.md) | Triagem de feedback, precisão, zeros e integridade. |
| [Release 1.6.0](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.6.0.md) | Geometry Offset, orientação e diagnósticos. |
| [Revisão 1.6.1](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/review-1.6.1.md) e [UI 1.6.2](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/ui-1.6.2.md) | Revisão técnica e hierarquia visual. |
| [Release 1.7.0](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.0.md) | Introdução dos métodos/bases/preview; contém comportamento histórico retirado. |
| [Release 1.7.1](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.1.md) | Eixos, direção em zero e checkbox. |
| [Release 1.7.2](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.2.md) | Precisão em cena grande e cache. |
| [Release 1.7.3](https://github.com/Borbofruto/Blender-Plugins/blob/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/docs/better_item/release-1.7.3.md) | Contrato atual de Endpoint, Placement e Live. |
| [Arquivo de animação](https://github.com/Borbofruto/Blender-Plugins/tree/0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9/archive/better_item-animation-1.5.1) | Preservação de um protótipo retirado; não instalar como atualização. |

Hashes de todos os arquivos de runtime e dos relatórios inventariados estão em `handoff-1.7.3.json`. Ele também lista todos os scripts de teste encontrados, inclusive os não detalhados neste texto.

### 24.2. Documentação técnica externa consultada nesta consolidação

Use a documentação da versão efetiva do Blender. Links `current`, `latest` ou `dev` podem apontar para uma versão posterior; a fonte de execução auditada continua sendo o binário e o código do snapshot.

- [Context 5.2](https://docs.blender.org/api/5.2/bpy.types.Context.html): contexto temporário e dependency graph.
- [Application Timers 5.2](https://docs.blender.org/api/5.2/bpy.app.timers.html): registro, retorno de intervalo/None e lifecycle.
- [Application Handlers 5.2](https://docs.blender.org/api/5.2/bpy.app.handlers.html): eventos, contexto de avaliação e cuidados com mudanças de dados.
- [CLI de extensões 5.2](https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html): validar/build de pacote; verificar também `--help` no executável instalado.
- [Argumentos CLI](https://docs.blender.org/manual/en/dev/advanced/command_line/arguments.html): comportamento de `--python-exit-code` e ordem dos argumentos, confirmado localmente na 5.2.3.
- [Object API 5.0](https://docs.blender.org/api/5.0/bpy.types.Object.html) e [Depsgraph API 5.0](https://docs.blender.org/api/5.0/bpy.types.Depsgraph.html): malha temporária avaliada e liberação. São referências da API, não evidência de teste deste add-on na 5.0.
- [Operadores de Object](https://docs.blender.org/api/current/bpy.ops.object.html): nomenclatura nativa de Center of Mass; a consulta do código nativo/operador também confirmou os nomes durante a produção.
- [Modifier.persistent_uid](https://docs.blender.org/api/5.0/bpy.types.Modifier.html): referência citada na revisão 1.5.7 para a identidade do estágio afim; conferir disponibilidade na versão-alvo.
- [Formato e criação de extensões](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html): referência histórica para manifesto e metadados do pacote.

Alguns acessos diretos à documentação retornaram erro no navegador de pesquisa durante esta consolidação; os trechos recuperados por busca oficial e a ajuda do Blender local foram utilizados quando apropriado. Não afirmar que uma página completa foi auditada se ela não carregou. Não foram adotadas receitas de fóruns como fundamento para o solver.

### 24.3. Licença e materiais que não compõem o runtime

O manifesto declara GPL-3.0-or-later e o arquivo LICENSE acompanha o pacote. Preserve licença e autoria na entrega. Este manual não substitui análise jurídica de uma eventual distribuição comercial.

Documentos de roadmap comercial, screenshots e feedbacks colados pelo usuário ajudaram a definir o produto, mas nem todos esses arquivos temporários são parte do repositório. Os relatórios consolidados são a referência durável disponível. Não alegue ter lido novamente anexos antigos que não estão acessíveis.

<a id="s25"></a>
## 25. Roteiro inicial e mensagem de passagem para outra IA

### 25.1. Primeira sessão de trabalho

Antes de produzir uma alteração, a nova IA deve conseguir responder:

1. Qual versão/commit está realmente instalada e qual está sendo editada?
2. A solicitação é uma correção, uma mudança de contrato ou uma hipótese exploratória?
3. A operação usa canais nativos, coordenadas, componente rotacional ou extensões projetadas?
4. Quem é dono dos dados: Object, Scene, Frame, operador ou sessão transitória?
5. Que invariantes precisam permanecer iguais, além do número editado?
6. Qual referência pode mudar com o próprio alvo?
7. Onde há conversão para float32 e qual orçamento foi aceito?
8. Qual teste reproduz o caso e qual oráculo independente verifica o resultado?
9. O teste precisa de janela, timer, fixture antigo ou processo novo?
10. O pacote instalado é exatamente o artefato testado/publicado?

Se não souber, inspecione antes de implementar.

### 25.2. Mensagem pronta para iniciar outra conversa

```text
Você vai continuar o Better Item de Gabriel Webber do Nascimento.

Leia o manual CONTINUIDADE-IA.md e o snapshot handoff-1.7.3.json antes
de alterar código. A base documentada é 1.7.3, commit
0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9, no repositório
Borbofruto/Blender-Plugins. Compare com o HEAD real, porque o projeto
pode ter evoluído.

Não reintroduza animação relativa, vínculo permanente de distribuição,
opção redundante de capturar o pivô/orientação ativo da viewport,
nem Geometry Bounds em Endpoint. Endpoint distribui pontos e permite
sobreposição sem redimensionar. Offset preserva eixos desmarcados,
usa o sinal de Spacing e conserva o último sentido ao chegar a zero.

Live captura alvos e Active Object, acompanha referências enquanto
habilitado e termina ao desligar/frame/render/load/undo. Transform
continua com referências por objeto; mudar isso exige uma decisão
separada. Frames guardam Location e Orientation independentes.

Entenda os módulos, reproduza a solicitação atual, classifique defeito
versus escopo, faça alteração pequena e teste invariantes/rollback.
Use Blender real quando necessário, --python-exit-code 1 em testes
CLI, JSON atual e logs. Não anuncie testes históricos como executados
agora. O instalador é sempre addons/better_item.zip; a versão fica
no manifesto. Não modifique o outro add-on do repositório.

Depois de ler, apresente o entendimento do problema atual e prossiga
dentro da autorização do usuário, explicitando incertezas relevantes.
```

### 25.3. Critério de entrega de uma continuação

Uma entrega está pronta quando o comportamento pedido está concreto, o usuário consegue entender a mudança, os testes pertinentes e seus limites foram registrados e o artefato correspondente foi conferido. Uma resposta dizendo apenas que “a arquitetura está boa” ou que “provavelmente funciona” não substitui isso.

Este manual deve ser atualizado quando uma decisão estrutural ou de escopo mudar. Preserve os motivos e as regressões que explicam a solução; remova instruções obsoletas do caminho principal, deixando o histórico claramente identificado.
