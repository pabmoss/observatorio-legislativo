#!/usr/bin/env python3
"""Importa un documento de fichas legislativas a datos estructurados, sin consultar fuentes externas.
El documento se interpreta como corte documental, no información legislativa en tiempo real.
"""
from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.ns import qn
import json, re, sys, unicodedata, hashlib
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
SRC=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'files'/'fichas-legislativas-2026-10-28.docx'
HEADINGS={'Breve exposición de motivos':'motivos','Objeto del texto radicado':'objeto','Análisis del soporte actual':'analisis','Ponentes':'ponentes','Documentos oficiales':'documentos'}

def slugify(t):
    t=unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+','-',t).strip('-')

def hyperlinks(p,d):
    out=[]
    for el in p._element.xpath('.//w:hyperlink'):
        rid=el.get(qn('r:id'))
        if not rid or rid not in d.part.rels: continue
        url=d.part.rels[rid].target_ref
        label=''.join(x.text or '' for x in el.xpath('.//w:t')).strip()
        if url.startswith('https://') and (label or url):
            out.append({'etiqueta':label or url, 'url':url})
    return out

def is_project(t): return bool(re.match(r'^(?:PL|PAL)\s+\d',t))

def process():
    d=Document(SRC)
    records=[]; group='Sin comisión verificada'; current=None; field=None; table_count=0
    for node in d.element.body.iterchildren():
        if node.tag==qn('w:p'):
            p=Paragraph(node,d)
            t=p.text.strip()
            if not t: continue
            if p.style.name=='Heading 1':
                group=t; field=None
            elif p.style.name=='Heading 2' and is_project(t):
                current={'id':slugify(t), 'radicado':t, 'titulo':'', 'grupo_origen_documento':group, 'orden_documento':len(records)+1,
                         'tipo_ley':'Pendiente de verificar', 'estado':'Pendiente de verificar', 'origen':'Pendiente de verificar', 'comision':group,
                         'sesion':'Pendiente de verificar','motivos':'','objeto':'','analisis':'','ponentes':'',
                         'documentos':[],'notas_documentales':[],'corte_documental':'2026-10-28', 'fuente':'Fichas legislativas del 28/10/2026'}
                records.append(current);field='titulo'
            elif p.style.name=='Heading 2' and t in HEADINGS:
                field=HEADINGS[t]
            elif current:
                if field in ('titulo','motivos','objeto','analisis','ponentes'):
                    current[field]+= ('\n\n' if current[field] else '')+t
                elif field=='documentos':
                    links=hyperlinks(p,d)
                    for link in links:
                        if not any(x['etiqueta']==link['etiqueta'] and x['url']==link['url'] for x in current['documentos']):
                            current['documentos'].append(link)
                    if not links: current['notas_documentales'].append(t)
            else: pass
        elif node.tag==qn('w:tbl') and current is not None:
            table_count+=1
            tab=Table(node,d)
            key_map={'Tipo de ley':'tipo_ley','Estado actual':'estado','Origen':'origen','Comisión':'comision','Sesión y actividad':'sesion'}
            for row in tab.rows:
                cells=[c.text.strip() for c in row.cells]
                if len(cells)>=2 and cells[0] in key_map:
                    current[key_map[cells[0]]]=cells[1]
    assert len(records)==table_count, (len(records),table_count)
    for r in records:
        if not r['titulo']: r['titulo']=r['radicado']
        r['id']=slugify(r['radicado'])
        r['documento_word']='documentos/'+r['id']+'.docx'
        s=r['sesion']
        r['fecha_sesion']=next((f'{m.group(3)}-{m.group(2)}-{m.group(1)}' for m in [re.search(r'\b(\d\d) de (octubre|noviembre|septiembre) de (2026)\b',s,re.I)] if m),None) # corrected below
        match=re.search(r'\b(\d{1,2}) de (octubre|noviembre|septiembre|agosto) de (20\d\d)',s,re.I)
        months={'octubre':'10','noviembre':'11','septiembre':'09','agosto':'08'}
        r['fecha_sesion']=f'{match.group(3)}-{months[match.group(2).lower()]}-{int(match.group(1)):02d}' if match else None
        r['estado_sesion']='Citada' if 'citada' in s.lower() else ('Realizada' if 'realizada' in s.lower() else 'Sin confirmar')
    payload={'titulo':'Observatorio Legislativo','despacho':'Despacho del H.S. Carlos Eduardo Enríquez Caicedo',
             'corte_documental':'2026-10-28','advertencia':'Corte documental de fuentes oficiales. La programación de una sesión o publicación de ponencia no acredita votación ni aprobación.',
             'total_proyectos':len(records), 'proyectos':records}
    (ROOT/'data'/'proyectos.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Importados',len(records),'proyectos y',sum(len(r['documentos']) for r in records),'enlaces documentales')
    return payload
if __name__=='__main__': process()
