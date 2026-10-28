#!/usr/bin/env python3
"""Verifica el JSON y genera la versión JS independiente del diseño, operativa incluso sin servidor."""
from pathlib import Path
import json,datetime
ROOT=Path(__file__).resolve().parents[1]
f=ROOT/'data'/'proyectos.json'
d=json.loads(f.read_text(encoding='utf-8'))
items=d.get('proyectos',[])
assert isinstance(items,list) and items
ids=[x['id'] for x in items];assert len(ids)==len(set(ids)), 'IDs repetidos'
for x in items:
 for k in ['radicado','titulo','estado','origen','comision','motivos','objeto','documentos']:
  assert k in x,(x.get('radicado'),k)
 for link in x['documentos']:
  assert link['url'].startswith('https://'),link
 assert (ROOT/x['documento_word']).exists(),f"Word no encontrado {x['documento_word']}"
js='/* Datos generados por compilar_datos.py. Editar data/proyectos.json, no este archivo. */\nwindow.OBS_DATA='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n'
(ROOT/'data'/'proyectos.js').write_text(js,encoding='utf-8')
print('Compilados',len(items),'registros y',sum(len(x['documentos']) for x in items),'referencias. Corte',d['corte_documental'])
