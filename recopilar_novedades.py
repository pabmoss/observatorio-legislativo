#!/usr/bin/env python3
"""Consulta fuentes primarias; registra enlaces sin inferir aprobaciones.

La periodicidad real depende de GitHub Actions. NUNCA modifica el estado
jurídico de un proyecto o una ficha sin evaluación documental.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import logging
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
import xml.etree.ElementTree as ET

import requests
from pypdf import PdfReader
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data' / 'novedades.json'
ESTADO = ROOT / 'data' / 'estado_fuentes.json'
BASE = 'https://www.senado.gov.co/index.php'
CAM = 'https://www.camara.gov.co'
IMPRENTA = 'https://svrpubindc.imprenta.gov.co/senado/view/gestion/gacetasPublicas.xhtml'
ORDINALES = ['primera', 'segunda', 'tercera', 'cuarta', 'quinta', 'sexta', 'septima']
CAM_URLS = [
 'comision-primera-constitucional-permanente/orden-del-dia-comision-primera-constitucional-permanente/',
 'comision-segunda-o-de-relaciones-internacionales/orden-del-dia-comision-segunda-constitucional/',
 'comision-tercera-o-de-hacienda-y-credito-publico/orden-del-dia-comision-tercera-constitucional/',
 'comision-cuarta-o-presupuesto/orden-del-dia-comision-cuarta-constitucional/',
 'comision-quinta-constitucional-permanente/orden-del-dia-comision-quinta-constitucional/',
 'comision-sexta-o-de-transportes-y-comunicaciones/orden-del-dia-comision-sexta-constitucional/',
 'comision-septima-constitucional-permanente/orden-del-dia-comision-septima-constitucional/',
]
# La cobertura se hace explícita por fuente y los fallos no se ocultan.
SOURCES = (
 [{'id':f'senado-c{i+1}', 'nombre':f'Senado · Comisión {x.capitalize()}', 'url':f'{BASE}/documentos/comisiones/constitucionales/comision-{x}', 'kind':'senado-archivo'} for i,x in enumerate(ORDINALES)] +
 [{'id':'senado-agenda', 'nombre':'Senado · Agenda legislativa', 'url':f'{BASE}/component/sppagebuilder/?id=155&view=page', 'kind':'senado'},
  {'id':'senado-plenaria', 'nombre':'Senado · Orden del día de plenaria', 'url':'https://www.secretariasenado.gov.co/index.php/orden-del-dia-senado', 'kind':'senado'},
  {'id':'camara-plenaria', 'nombre':'Cámara · Orden del día de plenaria', 'url':f'{CAM}/secretaria-general/orden-del-dia-secretaria-general/', 'kind':'camara'},
  {'id':'camara-eventos', 'nombre':'Cámara · Eventos y órdenes del día', 'url':f'{CAM}/wp-sitemap.xml', 'kind':'camara-sitemap'}] +
 [{'id':f'camara-c{i+1}', 'nombre':f'Cámara · Comisión {x.capitalize()}', 'url':f'{CAM}/{url}', 'kind':'camara'} for i,(x,url) in enumerate(zip(ORDINALES,CAM_URLS))] +
 [{'id':'gacetas', 'nombre':'Imprenta Nacional · Gacetas del Congreso', 'url':IMPRENTA, 'kind':'gacetas'}]
)
HEADERS = {'User-Agent':'ObservatorioLegislativo/2.1 (+https://github.com/pabmoss/observatorio-legislativo; monitoreo de fuentes públicas)'}
TIMEOUT = (7, 20)
MAX_ITEMS = 750


def now_utc():
 return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def norm(text):
 return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')


def clean(text):
 return ' '.join(str(text).split())[:240]


def valid_url(url):
 p=urlparse(url)
 return p.scheme=='https' and p.hostname and any(p.hostname==x or p.hostname.endswith('.'+x) for x in ('senado.gov.co','camara.gov.co','imprenta.gov.co'))


def href(base,value):
 if not value or value.startswith(('javascript:', 'data:', '#', 'mailto:')):return None
 url=urldefrag(urljoin(base,value))[0]
 return url if valid_url(url) else None


MESES={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'setiembre':9,'octubre':10,'noviembre':11,'diciembre':12}

def fecha_documental(text):
 """Solo acepta fechas completas identificables en el título o ruta; nunca fecha de detección."""
 value=norm(str(text).replace('_','-'))
 value=re.sub(r'(?<=\d)(?=[a-z])','-',value)
 patterns=[
  r'(?<!\d)(20\d{2})[-/.](0?[1-9]|1[0-2])[-/.]([0-2]?\d|3[01])(?!\d)',
  r'(?<!\d)([0-2]?\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2})(?!\d)',
  r'(?<!\d)([0-2]?\d|3[01])[-\s]+de?[-\s]+('+'|'.join(MESES)+r')[-\s]+de?[-\s]+(20\d{2})(?!\d)',
  r'(?<!\d)([0-2]?\d|3[01])[-\s]+('+'|'.join(MESES)+r')[-\s]+(20\d{2})(?!\d)',
 ]
 for i,pat in enumerate(patterns):
  m=re.search(pat,value)
  if not m:continue
  try:
   if i==0:year,month,day=map(int,m.groups())
   elif i==1:day,month,year=map(int,m.groups())
   else:day=int(m.group(1));month=MESES[m.group(2)];year=int(m.group(3))
   return dt.date(year,month,day).isoformat()
  except ValueError:continue
 return None

def titulo_archivo(url):
 parts=[x for x in urlparse(url).path.rstrip('/').split('/') if x and x!='file']
 last=parts[-1] if parts else ''
 last=re.sub(r'^\d{3,6}-','',last)
 return clean(last.replace('-',' ').replace('_',' ').strip()).capitalize()

def key_for(url,extra=''):
 return hashlib.sha256((url+'|'+extra).encode()).hexdigest()[:20]


def fetch(s,url):
 r=s.get(url,headers=HEADERS,timeout=TIMEOUT,allow_redirects=True)
 r.raise_for_status()
 if not valid_url(r.url):raise ValueError('Redirección fuera de dominio oficial')
 if len(r.content)>6_000_000:raise ValueError('Respuesta de índice demasiado grande')
 return r.text


def extract_anchors(html, source, *, force=False):
 soup=BeautifulSoup(html,'html.parser')
 for node in soup(['script','style','nav','footer','header']):node.decompose()
 found=[];seen=set()
 for a in soup.select('a[href]'):
  target=href(source['url'],a.get('href'))
  if not target or target in seen:continue
  title=clean(a.get_text(' ',strip=True) or a.get('title') or '')
  if norm(title) in ('documento','descargar','descarga','archivo','pdf'):
   title=titulo_archivo(target) or title
  alt=norm(title+' '+target)
  if len(title)<9:continue
  if not force and not any(w in alt for w in ('orden del dia','orden-del-dia','agenda legislativa','citacion','plenaria','gaceta del congreso')):continue
  if any(w in alt for w in ('redes sociales','politica de privacidad','terminos y condiciones')):continue
  # Evita el menú de navegación cuando no refiere a una publicación concreta.
  if not force and not re.search(r'20\d{2}|(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)|\d{1,2}[-/]\d{1,2}',alt):continue
  seen.add(target)
  found.append({'titulo':title,'url':target,'fuente':source['nombre'],'fuente_id':source['id'],'clase':'orden_del_dia' if 'orden' in alt else 'agenda','identificador':key_for(target),'fecha_documento_normalizada':fecha_documental(title+' '+target)})
 return found[:150]


def parse_senate_archive(session, source):
 # La jerarquía Joomla cambia según la comisión; recorrer carpetas oficiales
 # sin asumir un sufijo de carpeta ni visitar otras comisiones.
 prefix=source['url'].rstrip('/')
 queue=[(source['url'],0)]; visited=set(); found=[]; child_errors=[]
 while queue and len(visited)<12:
  url,depth=queue.pop(0)
  if url in visited:continue
  visited.add(url)
  try:html=fetch(session,url)
  except (requests.RequestException,ValueError) as err:
   child_errors.append(clean(f'{url}: {err}'));continue
  page_source={**source,'url':url}
  found.extend(extract_anchors(html,page_source))
  if depth>=3:continue
  soup=BeautifulSoup(html,'html.parser')
  for a in soup.select('a[href]'):
   u=href(url,a.get('href'))
   if not u or not u.startswith(prefix+'/') or u in visited:continue
   label=norm(clean(a.get_text(' ',strip=True)))
   child=norm(u)
   # Recorre solo carpetas de orden del día o de legislaturas actuales.
   if ('carpeta' in label or 'orden' in label or 'legislatura' in label or '2026' in label) and (
    any(w in label for w in ('orden','2026','carpeta','legislatura')) or 'orden-del-dia' in child
   ) and not child.endswith('/file'):
    if ('orden' in label or 'orden-del-dia' in child or '2026' in label or 'legislatura' in label) and u not in [v for v,_ in queue]:queue.append((u,depth+1))
 if not visited or (child_errors and not found and len(visited)==1):raise ValueError('; '.join(child_errors)[:280])
 return found


def parse_sitemap(session, source, *, limit=6):
 # WordPress: puede exponerse como wp-sitemap.xml o sitemap_index.xml.
 urls=[];last_error=None
 for base in (source['url'],CAM+'/sitemap_index.xml'):
  try:
   raw=fetch(session,base);root=ET.fromstring(raw)
   urls=[v.text.strip() for v in root.findall('.//{*}loc') if v.text]
   if urls:break
  except (requests.RequestException,ValueError,ET.ParseError) as err:last_error=err
 if not urls:raise ValueError('No se pudo leer el índice de mapas oficiales: '+str(last_error))
 maps=[u for u in urls if ('evento' in u.lower() or 'event' in u.lower()) and 'sitemap' in u.lower()]
 if not maps:
  maps=[u for u in urls if 'post' in u.lower() and 'sitemap' in u.lower()][:2]
 if not maps: raise ValueError('No se encontró sitemap público de eventos')
 out=[]; failures=[]
 for mp in maps[:limit]:
  try:
   r=ET.fromstring(fetch(session,mp))
   children=[x.text.strip() for x in r.findall('.//{*}loc') if x.text]
   for url in children[-110:]:
    if not valid_url(url) or '/evento/' not in url:continue
    p=urlparse(url).path.rstrip('/').split('/')[-1].replace('-',' ')
    if not any(k in norm(p) for k in ('orden del dia','plenaria','sesion conjunta','agenda comision')):continue
    out.append({'titulo':p[:240].capitalize(),'url':url,'fuente':'Cámara · Eventos y órdenes del día','fuente_id':'camara-eventos','clase':'orden_del_dia','identificador':key_for(url),'fecha_documento_normalizada':fecha_documental(p+' '+url)})
  except Exception as e: failures.append(f'{mp}: {type(e).__name__} {e}')
 if failures and not out: raise ValueError('Fallaron sitemaps: '+ '; '.join(failures)[:180])
 return out


def parse_gacetas(html, source):
 soup=BeautifulSoup(html,'html.parser')
 out=[]
 # JSF puede imprimir filas de tabla o cargar el listado vía AJAX. En el segundo caso
 # la fuente se marca como no accesible (sin simular que se descargaron Gacetas).
 for tr in soup.find_all('tr'):
  vals=[clean(td.get_text(' ',strip=True)) for td in tr.find_all(['td','th'],recursive=False)]
  if not vals:continue
  joined=' '.join(vals)
  match=re.search(r'(?<!\d)(\d{3,5})\s+(Senado de la Rep[uú]blica|C[aá]mara de Representantes)\s+(\d{1,2}/\d{1,2}/20\d{2})',joined,re.I)
  if not match:continue
  num,entidad,fecha=match.groups();link=source['url']
  # Si JSF ofrece URL real de documento, conservarla; de lo contrario indexar ficha del registro.
  for a in tr.select('a[href]'):
   u=href(source['url'],a.get('href'))
   if u:link=u;break
  out.append({'titulo':f'Gaceta {num} · {entidad} · {fecha}','url':link,'fuente':source['nombre'],'fuente_id':'gacetas','clase':'gaceta','identificador':key_for('gaceta',num+'|'+entidad+'|'+fecha),'fecha_documento':fecha,'fecha_documento_normalizada':fecha_documental(fecha)})
 if not out:raise ValueError('El portal no expuso filas de Gacetas en HTML; requiere integración adicional con su formulario JSF')
 return out[:110]


def related_documents(session, record):
 # Evento de Cámara: conservamos los enlaces adjuntos originales, no inferimos su contenido.
 url=record['url']
 if '/evento/' not in url:return []
 page=fetch(session,url)
 soup=BeautifulSoup(page,'html.parser');found=[]
 for a in soup.select('a[href]'):
  dst=href(url,a.get('href'))
  if dst and re.search(r'\.pdf(?:$|\?)',dst,re.I) and dst not in found:found.append(dst)
 return found[:8]


def pdf_references(session, url):
 # Extracción auxiliar, sin OCR, con límites estrictos de páginas y descarga.
 if not valid_url(url):return []
 try:
  response=session.get(url,headers=HEADERS,timeout=TIMEOUT,stream=True,allow_redirects=True)
  response.raise_for_status()
  if not valid_url(response.url):return []
  max_bytes=6_000_000; buf=bytearray()
  for chunk in response.iter_content(32768):
   buf+=chunk
   if len(buf)>max_bytes:return []
  if not buf.startswith(b'%PDF'):return []
  rd=PdfReader(io.BytesIO(buf),strict=False)
  txt=' '.join((pg.extract_text() or '') for pg in rd.pages[:min(6,len(rd.pages))])
  pattern=r'proyecto\s+de\s+(?:ley|acto\s+legislativo)\s*(?:n[oú]m(?:ero)?\.?|n[º°\.]\s*)?\s*(\d{1,4})\s*[/\-]\s*((?:20)?\d{2})'
  hits=re.findall(pattern,norm(txt),re.I)
  return list(dict.fromkeys(f'{a}/{b}' for a,b in hits))[:20]
 except Exception as e:
  logging.info('Sin extracción textual PDF %s: %s',url,str(e)[:90]);return []


def load(path,default):
 if not path.exists():return default
 try:return json.loads(path.read_text(encoding='utf-8'))
 except (ValueError,OSError):return default


def run(session=None,*,at=None):
 session=session or requests.Session()
 when=at or now_utc()
 old=load(DEST,{'novedades':[]})
 existing={e['identificador']:e for e in old.get('novedades',[]) if 'identificador' in e}
 status=load(ESTADO,{'fuentes':[]})
 previous={x['id']:x for x in status.get('fuentes',[]) if 'id' in x}
 sources=[];new_count=0;all_seen={};successes=0
 for source in SOURCES:
  prev=previous.get(source['id'],{})
  info={'id':source['id'],'nombre':source['nombre'],'url':source['url'],'ultima_consulta':when,'ultima_consulta_exitosa':prev.get('ultima_consulta_exitosa'),'estado':'error'}
  try:
   if source['kind']=='camara-sitemap':items=parse_sitemap(session,source)
   elif source['kind']=='senado-archivo':items=parse_senate_archive(session,source)
   elif source['kind']=='gacetas':items=parse_gacetas(fetch(session,source['url']),source)
   else:items=extract_anchors(fetch(session,source['url']),source)
   # Empty public index is distinguishable from a connection failure; never claim
   # it proves no publication was made elsewhere.
   info['estado']='ok' if items else 'sin_documentos_detectables'
   info['ultima_consulta_exitosa']=when;info['registros_en_indice']=len(items);successes+=1
   for x in items:
    k=x['identificador']
    if k not in all_seen:all_seen[k]=x
  except (requests.RequestException,ValueError,ET.ParseError) as e:
   info['error']=clean(f'{type(e).__name__}: {e}')
   logging.warning('%s: %s',source['id'],info['error'])
  sources.append(info)
 # If all sources fail, do not overwrite prior records or mark run successful.
 if not successes:raise RuntimeError('No respondió ninguna fuente oficial: se conserva la versión anterior')
 for k,record in all_seen.items():
  if k not in existing:
   existing[k]={**record,'primera_deteccion':when,'estado_verificacion':'Enlace detectado; contenido y efectos jurídicos no verificados'}
   new_count+=1
  else:
   # Keep original detection date and any analyst annotations.
   for field in ('titulo','url','fuente','fuente_id','clase','fecha_documento','fecha_documento_normalizada'):
    if field in record:existing[k][field]=record[field]
 # Los metadatos adicionales se extraen solo de un subconjunto por ejecución.
 # No se publican como interpretación jurídica de los proyectos.
 enriched=0
 for rec in sorted(existing.values(),key=lambda x:(x.get('fecha_documento_normalizada') or '0000',x.get('primera_deteccion','')),reverse=True):
  if enriched>=7:break
  if rec.get('revisado_para_anexos'):continue
  if rec['identificador'] not in all_seen:continue
  rec['revisado_para_anexos']=when
  pdf_urls=[]
  if re.search(r'\.pdf(?:$|\?)',rec.get('url',''),re.I) or rec.get('url','').endswith('/file'):
   pdf_urls=[rec['url']]
  elif '/evento/' in rec.get('url',''):
   try:pdf_urls=related_documents(session,rec)
   except (requests.RequestException,ValueError) as e:logging.info('Anexos de evento sin acceso: %s',e)
  if pdf_urls:
   rec['documentos_adjuntos']=pdf_urls
   # Solo extrae de un PDF reciente por registro, no procesa todos los anexos.
   rec['referencias_proyectos']=pdf_references(session,pdf_urls[0])
   rec['leyenda_extraccion']='Referencias textuales automáticas; no acreditan trámite, aprobación ni lectura completa'
  enriched+=1
 items=sorted(existing.values(),key=lambda x:x.get('primera_deteccion',''),reverse=True)[:MAX_ITEMS]
 result={'metodologia':'Índices oficiales; primera detección no equivale a fecha de publicación ni aprobación','ultima_consulta':when,'nuevos_en_esta_consulta':new_count,'novedades':items}
 new_status={'ultima_consulta':when,'fuentes_ok':successes,'total_fuentes':len(SOURCES),'fuentes':sources}
 # Los cambios de fecha en estos archivos publican verificación de latido; el histórico es versionado.
 DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 ESTADO.write_text(json.dumps(new_status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 compile_js()
 print(f'Fuentes procesadas: {successes}/{len(SOURCES)}; nuevos registros: {new_count}; total histórico: {len(items)}')
 return new_status,result


def compile_js():
 for filename,global_name in [('novedades.json','OBS_NOVEDADES'),('estado_fuentes.json','OBS_FUENTES')]:
  f=ROOT/'data'/filename
  d=load(f,{})
  (ROOT/'data'/filename.replace('.json','.js')).write_text('/* Generado: no editar manualmente */\nwindow.'+global_name+'='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--compilar',action='store_true',help='Compila sin consultar fuentes (útil en pruebas offline)');args=parser.parse_args()
 if args.compilar:compile_js()
 else:run()
