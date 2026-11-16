# Diagnóstico do operador de distribuição — 1.7.6

Executado em 16/11/2026, Windows x64, código da 1.7.6. Dois JSONs registram 11 chamadas por build (4.2.23 e 5.3.0), tanto valores no execute quanto posições reais. 8 chamadas por build receberam base diferente da solicitada, incluindo Geometry inválido. O controle com endpoint_placement=4 executou Volume.

O script intercepta execute somente para registrar propriedades e delega ao método original, registrado no Blender. Não modifica arquivos do addon. Usa cubos com geometria deslocada da origem para distinguir representantes. Esta instrumentação e um resultado FINISHED não são teste de aceitação: o diagnóstico registra uma falha existente. Uma correção precisa de assertions sobre o comportamento esperado.

Em checkout do repositório, usa src automaticamente. Em pacote apenas de documentação, defina BETTER_ITEM_REPO para o checkout completo. Exemplo PowerShell:

```powershell
$env:BETTER_ITEM_REPO='C:/work/Blender-Plugins'
& 'C:/path/blender.exe' --background --factory-startup --python-exit-code 1 --python 'C:/work/Blender-Plugins/docs/better_item/continuidade/evidencias-1.7.6/reproduce_operator.py'
```

Use cena/perfil de teste, não um projeto aberto. O script usa factory startup, cria uma cena sintética e grava operator-VERSAO.json ao lado dele. Os JSONs publicados são evidência da 1.7.6, não devem ser sobrescritos e rebatizados como testes de uma versão nova. Para nova execução, copie o diagnóstico para diretório de trabalho e ajuste BETTER_ITEM_REPO.

SHA256 do ZIP revisado: a4182db99196e502768cae288781546d6c89619f3c7172cfbf78abc8fcadd382. O código-fonte original foi conferido contra os blobs Git da base antes desta consolidação. Nenhuma conclusão depende dos avisos de memória no encerramento do Blender.
