#!/usr/bin/env python3
"""Genera un Word único por sesión plenaria documentada, listo para impresión.

Nunca incorpora enlaces web clicables en el documento imprimible.
Agrupa por corporación, fecha y hora; no declara exhaustividad de órdenes del día.
"""
from __future__ import annotations
import json
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from tempfile import NamedTemporaryFile
from collections import defaultdict
from datetime import date
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT=Path(__file__).resolve().parents[1]
DATOS=ROOT/'data'/'proyectos.json'
INDEX=ROOT/'data'/'sesiones.json'
NAVY=RGBColor(32,56,69)
GRAY=RGBColor(107,121,129)
DARK=RGBColor(30,43,51)
MONTHS=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']


def session_info(p):
    raw=(p.get('sesion') or '').strip()
    m=re.search(r'\bPlenaria\s+(?:del|de la)\s+(Senado|C[aá]mara(?: de Representantes)?)\s+del\s+(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(20\d{2})(?:,\s*(\d{1,2}:\d{2}))?',raw,re.I)
    if not m:return None
    chamber='Senado' if 'senado' in m.group(1).lower() else 'Cámara'
    month=m.group(3).lower()
    if month not in MONTHS:return None
    iso=f'{int(m.group(4)):04}-{MONTHS.index(month)+1:02}-{int(m.group(2)):02}'
    try:date.fromisoformat(iso)
    except ValueError:return None
    hour=m.group(5) or 'hora-no-indicada'
    slug=f'plenaria-{chamber.lower()}-{iso}'+('T'+hour.replace(':','') if m.group(5) else '')
    return {'id':slug,'fecha':iso,'hora':m.group(5),'corporacion':chamber,
            'titulo':f'Plenaria del {chamber} · {int(m.group(2))} de {month} de {m.group(4)}',
            'tipo':'plenaria'}


def keep_with_next(p, keep=True):
    p.paragraph_format.keep_with_next=keep


def shade(cell,color='EFF2F3'):
    tcPr=cell._tc.get_or_add_tcPr();shd=OxmlElement('w:shd');shd.set(qn('w:fill'),color);tcPr.append(shd)


def repeat_header(row):
    trPr=row._tr.get_or_add_trPr();el=OxmlElement('w:tblHeader');el.set(qn('w:val'),'true');trPr.append(el)


def add_page_number(p):
    r=p.add_run();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)


def write_cell(cell,text,bold=False,color=DARK,size=8.5):
    cell.text=''
    paras=str(text or 'No consta en el corte consultado').split('\n\n')
    for idx,block in enumerate(paras):
        p=cell.paragraphs[0] if idx==0 else cell.add_paragraph()
        p.paragraph_format.space_after=Pt(2 if idx<len(paras)-1 else 0)
        p.paragraph_format.line_spacing=1.05
        run=p.add_run(block.strip());run.bold=bold;run.font.size=Pt(size);run.font.name='Aptos';run.font.color.rgb=color


def add_row(t,label,value,label_width=3.1):
    cells=t.add_row().cells
    cells[0].width=Cm(label_width);cells[1].width=Cm(15.7-label_width)
    for cell in cells:cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
    shade(cells[0]);write_cell(cells[0],label.upper(),True,GRAY,7.5)
    write_cell(cells[1],value,False,DARK,8.25)
    return cells


def page_setup(d,info,stamp):
    sec=d.sections[0];sec.page_height=Cm(29.7);sec.page_width=Cm(21)
    sec.top_margin=Cm(1.55);sec.bottom_margin=Cm(1.45);sec.left_margin=Cm(1.75);sec.right_margin=Cm(1.75)
    sec.header_distance=Cm(.7);sec.footer_distance=Cm(.75)
    normal=d.styles['Normal'];normal.font.name='Aptos';normal.font.size=Pt(8.5)
    normal.font.color.rgb=DARK;normal.paragraph_format.space_after=Pt(3)
    hdr=sec.header.paragraphs[0]
    hdr.text='OBSERVATORIO LEGISLATIVO  |  DESPACHO DEL H.S. CARLOS EDUARDO ENRÍQUEZ CAICEDO'
    hdr.style=d.styles['Normal'];hdr.paragraph_format.space_after=Pt(4)
    for run in hdr.runs:run.bold=True;run.font.size=Pt(7);run.font.color.rgb=GRAY
    foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=foot.add_run(f'Corte documental {stamp}  ·  Ficha para impresión  ·  Pág. ')
    r.font.size=Pt(7);r.font.color.rgb=GRAY
    add_page_number(foot)


def produce_document(info,records,stamp):
    d=Document();page_setup(d,info,stamp)
    for i,r in enumerate(records):
        if i:d.add_page_break()
        kicker=d.add_paragraph()
        kicker.paragraph_format.space_before=Pt(5);kicker.paragraph_format.space_after=Pt(5)
        run=kicker.add_run(f'{info["titulo"].upper()}   /   PROYECTO {i+1} DE {len(records)}')
        run.bold=True;run.font.size=Pt(8);run.font.color.rgb=GRAY
        keep_with_next(kicker)
        p=d.add_paragraph();p.paragraph_format.space_after=Pt(5)
        run=p.add_run(r['radicado']);run.bold=True;run.font.size=Pt(13);run.font.color.rgb=NAVY
        keep_with_next(p)
        p=d.add_paragraph();p.paragraph_format.space_after=Pt(8)
        run=p.add_run(r['titulo']);run.bold=True;run.font.size=Pt(9.5);run.font.color.rgb=NAVY
        keep_with_next(p)
        t=d.add_table(rows=0,cols=2);t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
        t.style='Table Grid';t.columns[0].width=Cm(3.1);t.columns[1].width=Cm(14.4)
        fields=[
          ('Tipo de ley',r.get('tipo_ley')),
          ('Estado documentado',r.get('estado')),
          ('Origen',r.get('origen')),
          ('Comisión',r.get('comision')),
          ('Actividad de la sesión',r.get('sesion')),
          ('Exposición de motivos',r.get('motivos')),
          ('Objeto del proyecto',r.get('objeto')),
          ('Análisis documental',r.get('analisis')),
          ('Ponentes',r.get('ponentes')),
        ]
        for k,v in fields:
            if v:add_row(t,k,v)
        labels=[]
        for link in r.get('documentos',[]):
            label=str(link.get('etiqueta','')).strip()
            if label and label not in labels and not re.match(r'^(Tipo de ley|Estado actual|Origen|Comisi[oó]n|Breve exposici[oó]n de motivos)\s+\d',label,re.I):labels.append(label)
        if labels:add_row(t,'Soportes identificados','; '.join(labels)+'. Consultar expediente digital para acceder a los documentos oficiales.')
        notes=[str(x).strip() for x in r.get('notas_documentales',[]) if str(x).strip()]
        # No se imprimen URLs ni hipervínculos, tampoco las notas que solo consistan en URLs.
        notes=[re.sub(r'https?://\S+','[dirección omitida para impresión]',x) for x in notes]
        if notes:add_row(t,'Notas de verificación','\n\n'.join(notes))
    path=ROOT/'documentos'/'sesiones'/f'{info["id"]}.docx'
    path.parent.mkdir(exist_ok=True,parents=True)
    with NamedTemporaryFile(suffix='.docx',dir=path.parent,delete=False) as f:
        temp=Path(f.name)
    try:
        d.save(temp)
        # ZIP ordenado y marcas temporales fijas para no producir cambios binarios cada 15 minutos.
        with ZipFile(temp,'r') as source, ZipFile(path,'w',ZIP_DEFLATED,compresslevel=6) as target:
            for name in sorted(source.namelist()):
                info=ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED
                info.external_attr=source.getinfo(name).external_attr
                target.writestr(info,source.read(name))
    finally:
        temp.unlink(missing_ok=True)
    return path


def main():
    dataset=json.loads(DATOS.read_text(encoding='utf-8'))
    groups=defaultdict(list);metas={}
    for r in dataset['proyectos']:
        info=session_info(r)
        if info:
            groups[info['id']].append(r);metas[info['id']]=info
    listing=[]
    for key in sorted(groups,key=lambda s:(metas[s]['fecha'],metas[s]['hora'] or '',s),reverse=True):
        info=metas[key];rs=sorted(groups[key],key=lambda x:x.get('orden_documento',0))
        path=produce_document(info,rs,dataset['corte_documental'])
        listing.append({**info,'cantidad_fichas':len(rs),'documento_word':path.relative_to(ROOT).as_posix(),
                        'ids_proyectos':[x['id'] for x in rs], 'corte_documental':dataset['corte_documental'],
                        'alcance':'Fichas incluidas en el corte documentado; la integridad del orden del día requiere cotejo oficial'})
    result={'corte_documental':dataset['corte_documental'],'sesiones':listing}
    INDEX.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'data'/'sesiones.js').write_text('/* Generado automáticamente */\nwindow.OBS_SESIONES='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    print(f'Generadas {len(listing)} plenarias con {sum(i["cantidad_fichas"] for i in listing)} fichas acumuladas')

if __name__=='__main__':main()
