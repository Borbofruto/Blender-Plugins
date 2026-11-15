"""Regenerate the reading chapters from the canonical handoff manual (UTF-8)."""
from pathlib import Path
import hashlib,json,re

folder=Path(__file__).resolve().parent
parent=folder.parent
source=parent/'CONTINUIDADE-IA.md'
text=source.read_text(encoding='utf-8')
snapshot=json.loads((parent/'handoff-1.7.3.json').read_text(encoding='utf-8'))
digest=hashlib.sha256(source.read_bytes()).hexdigest()
sections=list(re.finditer(r'<a id="s(\d{2})"></a>',text))
assert [int(m.group(1)) for m in sections]==list(range(1,26))
parts=[(1,6,'01-produto-historico-arquitetura.md','Produto, histórico, arquitetura e persistência'),
       (7,11,'02-matematica-dimensions-frames.md','Matemática, precisão, Dimensions e Frames'),
       (12,16,'03-distribuicao-live-diagnostico.md','Distribuição, Live, caches, UI e diagnóstico'),
       (17,20,'04-testes-no-blender.md','Ambiente e testes headless/GUI no Blender'),
       (21,25,'05-entrega-pendencias-referencias.md','Entrega, manutenção, pendências e passagem de contexto')]
rows=[]
for first,last,name,title in parts:
    start=sections[first-1].start()
    end=sections[last].start() if last<25 else len(text)
    body=text[start:end].strip().replace('](handoff-1.7.3.json)','](../handoff-1.7.3.json)')
    header=f'# {title}\n\n[Índice](README.md) · [Manual integral](../CONTINUIDADE-IA.md)\n\n'
    header+=f"Base: Better Item {snapshot['runtime_version']}, commit `{snapshot['baseline_commit']}`.\n\n"
    header+=f'Gerado de CONTINUIDADE-IA.md, SHA-256 `{digest}`. Não editar este capítulo isoladamente; altere o manual integral e execute `gerar.py`.\n\n'
    out=folder/name;out.write_text(header+body+'\n',encoding='utf-8',newline='\n')
    rows.append((first,last,name,title,len(body.split())))
index='# Better Item — continuidade para outra IA\n\n'
index+='Comece pelo [manual integral](../CONTINUIDADE-IA.md), ou use os capítulos abaixo para leitura gradual. A fonte de edição é o manual integral; os capítulos são gerados, não versões independentes.\n\n'
index+=f"Base auditada: **{snapshot['runtime_version']}**, commit `{snapshot['baseline_commit']}`. Documentação não altera a versão nem o instalador do add-on.\n\n"
index+='| Parte | Conteúdo | Seções | Palavras aproximadas |\n|---|---|---|---:|\n'
for i,(first,last,name,title,words) in enumerate(rows,1):index+=f'| {i} | [{title}]({name}) | {first}–{last} | {words} |\n'
index+='\nO [snapshot JSON](../handoff-1.7.3.json) contém hashes, inventário dos módulos, testes e referências. A [verificação documental](../VERIFICACAO-DOCUMENTAL.json) registra integridade, links e execução dos exemplos.\n\n'
index+='A seção 25 do último capítulo inclui uma mensagem pronta para iniciar outra conversa. Leia escopo e limitações antes de implementar. Resultados de versões anteriores são históricos, não validação automaticamente repetida.\n\n'
index+='Para regenerar os capítulos: `python docs/better_item/continuidade/gerar.py`, usando Python 3 com suporte aos argumentos de pathlib utilizados. O script só escreve os cinco capítulos e este índice ao lado dele.\n'
(folder/'README.md').write_text(index,encoding='utf-8',newline='\n')
print(json.dumps({'source_words':len(text.split()),'source_sha256':digest,'parts':[{'file':r[2],'words':r[4]} for r in rows]},ensure_ascii=False,indent=2))
