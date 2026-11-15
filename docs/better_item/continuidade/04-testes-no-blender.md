# Ambiente e testes headless/GUI no Blender

[Índice](README.md) · [Manual integral](../CONTINUIDADE-IA.md)

Base: Better Item 1.7.3, commit `0421e9df30b13e4cf062d9ffcd5b30759c5b2ca9`.

Gerado de CONTINUIDADE-IA.md, SHA-256 `7720acf82a9b59d748d078f386f316efa945aea1aa383e258ac58eacb3a2be8b`. Não editar este capítulo isoladamente; altere o manual integral e execute `gerar.py`.

<a id="s17"></a>
## 17. Ambiente de desenvolvimento reproduzível

### 17.1. Ferramentas efetivamente usadas

- Blender executável completo, tanto em background quanto em janela real.
- Python distribuído com o Blender para utilitários, AST, JSON, ZIP e hashes.
- NumPy do Blender e mathutils do runtime; não depender de um bpy de sistema com versão diferente.
- PowerShell para iniciar processos e guardar logs no Windows.
- `rg` para localizar símbolos/strings e inventariar arquivos.
- GitHub conectado/Git Data API para publicar quando o workspace não tinha checkout Git.
- Captura de tela do próprio Blender para verificar desenho, recortes e aparência.

Blender/Python usados na máquina original:

```text
C:/Program Files/Blender Foundation/Blender 5.2/blender.exe
C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe
```

Use os executáveis da máquina atual. Não suponha que o diretório, versão ou permissões sejam os mesmos. A pasta do projeto inicialmente mostrada pelo aplicativo não era necessariamente o workspace onde Better Item foi produzido.

O diretório de trabalho precisa existir antes de iniciar o processo; tentar criá-lo dentro de um comando cujo `cwd` ainda não existe falha antes da execução. No Windows, especifique `encoding='utf-8'` ao ler os documentos com Python: o default pode ser uma code page diferente e provocar UnicodeDecodeError. Para busca, prefira `rg PADRAO DIRETORIO -g '*.py'` a depender da expansão de `pasta/*.py` pelo shell.

### 17.2. Checkout e baseline

Num checkout convencional, registre:

```powershell
git status --short
git remote -v
git rev-parse HEAD
git log -5 --oneline
```

Não descarte alterações do usuário para “limpar” o repositório. Se precisar de uma reprodução isolada, use cópia/worktree apropriada e fixtures sintéticos.

Para localizar o runtime, prefira a estrutura `src/better_item`. O pacote importado em testes deve vir do checkout esperado. Registre `better_item.__file__` e `bpy.app.version_string` quando houver suspeita de estar testando outra instalação.

### 17.3. Não testar em arquivos reais do cliente

Vários testes apagam objetos, criam modificadores, salvam e reabrem `.blend`. Eles devem rodar num **novo processo com cena sintética**. Não execute no Blender de trabalho do usuário com o projeto aberto.

Não publique arquivos `.blend` de clientes, screenshots com dados desnecessários, logs com tokens ou caminhos privados. Os fixtures atuais são construídos pelos scripts, normalmente com cubos, empties, malhas pequenas e node groups sintéticos.

### 17.4. Bootstrap Python

Um teste na pasta canônica `tests/better_item` normalmente insere o diretório `src` em `sys.path`, depois usa `addon_utils.enable('better_item')`. O pai do pacote deve estar no path, não a pasta `better_item` em si.

```python
import sys
from pathlib import Path
sys.dont_write_bytecode = True
repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'src'))
import bpy, addon_utils
addon_utils.enable('better_item')
import better_item
print(bpy.app.version_string, better_item.__file__)
```

Nem todo teste histórico usa o mesmo bootstrap. Alguns aceitam `--source`; outros foram criados para uma organização anterior. Inspecione os primeiros blocos do script antes de rodar em massa.

`--factory-startup` reduz dependência do startup do usuário, mas não substitui verificar que os módulos e o ambiente realmente são os esperados. Se houver interferência de outro add-on/perfil, isole o ambiente conforme a versão do Blender em vez de desregistrar arbitrariamente classes de terceiros.

<a id="s18"></a>
## 18. Como executar testes e interpretar resultados

### 18.1. Não confiar apenas no exit code padrão

Um erro Python lançado por script de linha de comando pode aparecer no console e ainda deixar exit code zero se a opção correspondente não for configurada. Isso foi observado durante a produção.

Use `--python-exit-code 1` para scripts de linha de comando. A ajuda do Blender instalado foi consultada e um controle negativo foi executado na preparação deste manual: um RuntimeError proposital encerrou com código 1. Isso valida o runner; não é uma falha do add-on. [Argumentos de linha de comando](https://docs.blender.org/manual/en/dev/advanced/command_line/arguments.html).

Essa opção não torna automaticamente exceções de timers/redraws posteriores em falhas do processo. Para UI, valide o JSON de término, o log e as exceções capturadas do draw.

### 18.2. Execução mínima confirmada

Exemplo PowerShell para um checkout real; ajuste `$repoPath` e o Blender:

```powershell
$blenderExe = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$repoPath = 'C:/caminho/Blender-Plugins'
$testPath = Join-Path $repoPath 'tests/better_item/test_better_item_173.py'
& $blenderExe --background --factory-startup --python-exit-code 1 --python $testPath
if ($LASTEXITCODE -ne 0) { throw 'Teste headless falhou.' }
```

Repita para `test_better_item_live173.py` e para os scripts relacionados ao módulo modificado. O mesmo formato foi reexecutado na preparação desta documentação, com a estrutura de repositório reconstruída a partir da entrega auditada.

Critérios de aprovação:

1. Processo terminou com código esperado.
2. Script concluiu suas asserções e escreveu seu marcador/resultado atual.
3. JSON corresponde à execução atual, não a um arquivo antigo que ficou no diretório.
4. Não há traceback inesperado nem erro de script do Blender no log.
5. A quantidade de casos, recusas e invariantes corresponde ao que o teste realmente cobre.

Não use um JSON “passed” remanescente depois que o script morreu antes de sobrescrevê-lo. Registre horário/mtime, use um diretório limpo de execução ou um mecanismo explícito de identificação de run.

### 18.3. O que testar de uma operação numérica

O teste precisa verificar, conforme o caso:

- leitura no referencial correto;
- valor aplicado e leitura após avaliação;
- posição mundial e canais nativos;
- sinais de Scale, Delta Scale e modos de rotação;
- campos/eixos não selecionados;
- preservação de malha base, usuários compartilhados e shape keys;
- pilha de modificadores, vínculos de grupos e matrizes armazenadas;
- referências e seleção real que não deveriam ser alteradas;
- comportamento diante de fonte ausente, singularidade, trava, driver e constraint;
- rollback completo quando um participante falha.

Um teste que apenas chama o planejador e compara sua própria saída com o mesmo planejador não é um oráculo independente.

### 18.4. Oráculos usados no projeto

- Pontos de cubos simétricos/deslocados: transformar o centro conhecido pela matriz mundial.
- Bounds: transformar vértices por NumPy float64 e projetar diretamente, medindo min/max sem chamar o helper em teste.
- Centro de superfície: triangulação e pesos de área independentes.
- Centro de volume: tetraedro fechado de centro conhecido, com transformações e espelhamento.
- Rotação: comparação com operadores nativos ou diferença angular de quaternions; não exigir uma representação Euler única para toda orientação equivalente.
- Estado nativo: comparar tuplas de Scale, deltas, ponteiros de dados e pilha antes/depois.
- Efeito colateral: injetar falha ou dependência que invalide o resultado e verificar que nada ficou parcialmente aplicado.

Evite introduzir outra etapa mathutils float32 no próprio oráculo quando o objetivo é medir o erro de armazenamento da transformação. Houve testes que usaram vértices e matrizes convertidos a NumPy para não acrescentar arredondamento do produto vetor/matriz.

### 18.5. Fixtures e processos independentes

Persistência real exige salvar e abrir em outro processo quando o objetivo é garantir reconstrução por registro/migração. Salvar/reabrir no mesmo processo é útil, mas pode ocultar cache ou módulo ainda carregado.

Para a migração 1.7.2 → 1.7.3:

```powershell
$migration = Join-Path $repoPath 'tests/better_item/test_better_item_migration173.py'
$oldSourceParent = 'C:/outro-checkout/src'
& $blenderExe --background --factory-startup --python-exit-code 1 --python $migration -- --prepare --source $oldSourceParent
if ($LASTEXITCODE -ne 0) { throw 'Falhou ao criar o fixture antigo.' }
& $blenderExe --background --factory-startup --python-exit-code 1 --python $migration
if ($LASTEXITCODE -ne 0) { throw 'Falhou a migração em processo novo.' }
```

O diretório antigo precisa realmente conter a implementação antiga. Para 1.7.2, o commit de runtime é `4db16357101b08c540f4313e31434ab9ce99db2c`. Não gere o fixture com a classe nova e depois anuncie teste de migração de versão antiga.

`test_better_item_persistence170.py` possui outras fases: preparar o caso corrente, preparar o legado com `--legacy [--source ...]` e conferir com `--check`. Leia o script e execute as fases na ordem; fixtures ausentes não são um defeito de persistência do add-on.

### 18.6. Paralelismo e arquivos de saída

Processos independentes de testes diferentes podem rodar em paralelo quando seus fixtures e arquivos não colidem. Não execute duas cópias do mesmo script ao mesmo tempo se ambas escrevem o mesmo `.results.json` ou `.blend`.

Não tire conclusões de desempenho a partir de uma execução simultânea com outras cargas sem registrar isso. Os números de cold/warm inspection variam conforme hardware e concorrência.

<a id="s19"></a>
## 19. Testes com interface, Undo/Redo e timers

### 19.1. Background não prova UI

Os seguintes pontos precisam de uma janela real do Blender para validação adequada:

- desenho/recorte de painéis e dropdowns;
- publicação/remoção de orientação nativa;
- região de View3D e contexto de operadores;
- observer/timers sendo realmente agendados;
- interação com seleção e operações nativas;
- fluxo do checkbox Live;
- Undo/Redo associado ao uso normal da interface.

Chamar `live.poll()` em um teste headless prova a lógica do callback, mas não que o Blender realmente o agendou corretamente. O teste GUI173 espera intervalos e verifica as mudanças feitas pelo timer real.

### 19.2. Inicialização de um teste GUI

Exemplo PowerShell que espera o processo e captura logs; as aspas internas preservam o caminho do script se ele tiver espaços:

```powershell
$scriptPath = Join-Path $repoPath 'tests/better_item/test_better_item_gui173.py'
$logDir = 'C:/caminho/resultados-ui'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$argumentLine = '--factory-startup --python-exit-code 1 --python "{0}"' -f $scriptPath
$process = Start-Process -FilePath $blenderExe -ArgumentList $argumentLine `
    -WindowStyle Hidden -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $logDir 'stdout.log') `
    -RedirectStandardError (Join-Path $logDir 'stderr.log')
if ($process.ExitCode -ne 0) { throw 'Blender GUI terminou com erro.' }
```

O script gera `test_better_item_gui173.results.json` ao lado dele. Verifique `passed`, ausência de `draw_errors` e ausência de traceback inesperado nos dois logs. `-Wait` é importante: um helper iniciado e abandonado pode ser encerrado pelo ambiente quando o processo pai termina.

### 19.3. Estrutura útil do script GUI

1. Registrar o pacote e preparar cena sintética.
2. Encontrar View3D, habilitar sidebar e selecionar a categoria Better Item.
3. Envolver o draw relevante para registrar exceções.
4. Agendar fases com `bpy.app.timers.register`.
5. Em uma fase, mudar entrada; na seguinte, conferir que o observer fez o trabalho, sem chamá-lo manualmente.
6. Fazer screenshots depois que houve tempo para redesenhar.
7. Escrever JSON final mesmo quando a própria rotina captura uma falha.
8. Encerrar o Blender.

Não faça `sleep` bloqueante longo no thread principal do Blender esperando que um timer execute: você pode estar bloqueando o próprio event loop necessário ao teste.

### 19.4. O que GUI173 efetivamente fez

Ele habilitou Live sem mover os objetos; alterou cursor; trocou a seleção para um Empty; moveu esse Empty com um operador nativo de transformação; esperou o timer; verificou os alvos desmarcados e o Active capturado; testou zero após Spacing negativo; alternou método/Placement; desabilitou Live; executou uma distribuição nativa via invoke e verificou F9 e Undo/Redo.

Isso é um smoke test automatizado de interface com leitura visual de screenshots. Não é uma auditoria de todos os gestos físicos de arrastar com mouse, modalidades de G/R, cancelamento com Esc ou todas as posições do painel.

### 19.5. Undo/Redo: detalhes que já causaram confusão

Não declare simplesmente que “background não tem Undo” nem que todo script prova Undo normal. Dependem da configuração e de como o operador é chamado.

Os testes usam, quando necessário:

```python
bpy.context.preferences.edit.use_global_undo = True
bpy.ops.ed.undo_push(message='Before test operation')
bpy.ops.better_item.distribute('INVOKE_DEFAULT', True)
```

O argumento de undo na chamada Python é relevante. Uma sequência de escritas RNA feita pelo script não equivale automaticamente à mesma interação física na UI.

Depois de Undo/Redo ou abrir arquivo, não continue usando cegamente os wrappers de Object/Scene anteriores. Recupere os dados pelo contexto atual ou pela identidade de teste apropriada. O runtime também limpa sessões e caches nesses eventos.

### 19.6. Mensagens de infraestrutura

Foram observados avisos de escrita de thumbnails em perfil sem permissão e, no encerramento de testes GUI, mensagens relacionadas a arquivo salvo com `@`. Esses avisos não impediram determinados testes de concluir suas asserções, mas não constituem uma regra para ignorar qualquer linha ERROR.

Classifique pelo contexto: resultado atual, traceback, integridade do arquivo e etapa em que ocorreu. Não recomende executar como administrador para ocultar um problema de lógica ou apenas para gerar thumbnails de teste.

<a id="s20"></a>
## 20. Catálogo dos testes e evidências

### 20.1. Entrada recomendada para o estado atual

| Script em `tests/better_item` | Objetivo principal / condição |
|---|---|
| `test_better_item_173.py` | Contrato atual: Placement por método, Endpoint curto com sobreposição, captura Live, fontes, recuperação, persistência e unregister. |
| `test_better_item_live173.py` | 96 lotes / 192 mudanças de referência; quatro bases de ponto, dois caminhos, âncoras, pais, espelho e ordem estável. |
| `test_better_item_gui173.py` | Timer real, cursor/Empty, seleção, contexto, F9, Undo/Redo e desenho. Precisa de janela. |
| `test_better_item_migration173.py` | Fixture criado com 1.7.2 e aberto em processo novo; exige fase de preparação. |
| `test_better_item_matrix170.py` | Matriz atualizada: 256 Endpoint por pontos + 140 Offset. O sufixo do nome não congela sua versão de contrato. |
| `test_better_item_170.py` | Contratos, fontes, oracle de centros, dependências, Frame e persistência; expectativas retiradas foram atualizadas. |
| `test_better_item_preview170.py` | API legada de sessão, undo, cancelamento, captura e mudanças de seleção no contrato atual. |
| `test_better_item_edge170.py` | Dependências GN, cache, fontes removidas e lote geométrico; o caso de 200 peças atual é Offset. |
| `test_better_item_171.py` | Eixos transversais preservados, último sinal, checkbox e persistência. |
| `test_better_item_precision172.py` | 21 cenários de cena grande/cadeia longa, agora com Geometry em Offset e pontos em Endpoint. |
| `test_better_item_collapse172.py` | Recusas atômicas de colapsos reais e mudança geométrica dependente em Offset. |
| `test_better_item_inspection172.py` | Cold/warm inspection, reutilização, invalidação, fontes indiretas e ciclo de registro. |
| `test_better_item_gui_inspection172.py` | Reutilização da inspeção ao longo de redraws/timer reais com 600 objetos. |

### 20.2. Regressões anteriores úteis por área

| Área | Scripts de referência |
|---|---|
| Matemática/transformações | `test_better_item.py`, `test_better_item_regressions.py`, `test_better_item_scope152.py`, `test_better_item_stress157.py` |
| Zero e proporção | `test_better_item_zero_location156.py`, `test_better_item_feedback157.py` |
| Referências/Frames | `test_better_item_references.py`, `test_better_item_frames.py`, `test_better_item_frame_creation.py`, `test_better_item_reference_parity.py`, migrações e testes UI de referência |
| Eixos/pivôs nativos | `test_better_item_native_axes.py`, `test_better_item_directions154.py`, `test_better_item_sync_gui.py` |
| Arredondamento com travas | `test_better_item_locked_roundoff.py` |
| Cache | `test_better_item_cache.py`, `test_better_item_cache154.py`, `benchmark_dimensions.py` |
| Limpeza/legado | `test_better_item_cleanup155.py`, `test_better_item_legacy155.py` |
| Dependências e limites | `test_better_item_dependencies157.py`, `test_better_item_guards153.py` |
| Arranjo/1.6 | `test_better_item_arrange.py`, `test_better_item_arrangement161.py`, `test_better_item_features160.py`, `test_better_item_matrix160.py`, `test_better_item_edge160.py`, `test_better_item_review161.py` |
| UI histórica | Scripts `gui153` a `gui171`, `reference_gui*`, `reference_ui*`, `test_better_item_ui_undo.py` |

O inventário completo está no JSON de snapshot. Leia o bootstrap e as pré-condições dos scripts antigos antes de compor uma suíte automática. Não foi auditado que todos os scripts históricos podem ser tratados como testes pytest independentes, sem fase de preparação ou ajuste de ambiente.

### 20.3. Como interpretar as pastas de resultados

`results/1.7.3/` registra os resultados efetivamente reunidos para essa entrega. As pastas anteriores são preservadas como evidência histórica. Não as sobrescreva com resultados atuais só para fazer os números parecerem consistentes.

Por exemplo:

- 320 lotes Endpoint em resultado antigo incluíam a operação geométrica agora retirada.
- 256 lotes no resultado atual cobrem as quatro bases suportadas.
- A suíte de 9.216 combinações e as comparações nativas amplas foram executadas em etapas anteriores; não foram todas repetidas na 1.7.3.
- Um arquivo `baseline` de precisão pode conter `passed: false` intencionalmente, pois descreve a versão antiga que recusava casos válidos. Não o trate como o resultado do pacote corrigido.

Relate sempre nome, versão/commit, ambiente, número de casos e limites. “Todos os testes passaram” sem definir a suíte não é um relatório útil.
