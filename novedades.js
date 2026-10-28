(()=>{'use strict';
const $=s=>document.querySelector(s);
const D=window.OBS_NOVEDADES||{},S=window.OBS_FUENTES||{},items=Array.isArray(D.novedades)?D.novedades:[];
const norm=x=>String(x??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const el=(name,cl,text)=>{const n=document.createElement(name);if(cl)n.className=cl;if(text!=null)n.textContent=text;return n};
const fecha=x=>{if(!x)return 'Sin registro';const d=new Date(x);return isNaN(d)?x:d.toLocaleString('es-CO',{timeZone:'America/Bogota',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})+' (Bogotá)'};
const meses={enero:1,febrero:2,marzo:3,abril:4,mayo:5,junio:6,julio:7,agosto:8,septiembre:9,octubre:10,noviembre:11,diciembre:12};
function fechaDocumento(x){
  const direct=x.fecha_documento_normalizada;
  if(typeof direct==='string'&&/^20\d{2}-\d\d-\d\d$/.test(direct))return direct;
  const str=norm([x.fecha_documento,x.titulo,x.url].filter(Boolean).join(' ').replaceAll('_','-'));
  let m=str.match(/\b(20\d{2})-(\d\d?)-(\d\d?)\b/);if(m)return `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
  m=str.match(/\b(\d\d?)[/-](\d\d?)[/-](20\d{2})\b/);if(m)return `${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}`;
  m=str.match(new RegExp('(?:^|\\D)(\\d{1,2})[-\\s]+(?:de[-\\s]+)?('+Object.keys(meses).join('|')+')[-\\s]+(?:de[-\\s]+)?(20\\d{2})'));
  return m?`${m[3]}-${String(meses[m[2]]).padStart(2,'0')}-${m[1].padStart(2,'0')}`:null;
}
function prettyTitle(x){
  const source=String(x.titulo||'');if(norm(source)!=='documento'&&norm(source)!=='descargar')return source;
  const paths=new URL(x.url).pathname.split('/').filter(Boolean).filter(z=>z!=='file');
  return (paths.at(-1)||source).replace(/^\d+-/,'').replaceAll('-',' ').replaceAll('_',' ');
}
function sameNumber(a,b){const m=String(a).match(/^(\d{1,4})\s*[/\-]\s*((?:20)?\d{2})$/), n=String(b).match(/\b(\d{1,4})\s+de\s+(20\d{2})\b/);if(!m||!n)return false;return Number(m[1])===Number(n[1])&&(m[2].length===2?'20'+m[2]:m[2])===n[2]}
function maybeProjects(x){const refs=x.referencias_proyectos||[];return (window.OBS_DATA?.proyectos||[]).filter(p=>refs.some(r=>sameNumber(r,p.radicado))) }
if(S.ultima_consulta){let total=S.total_fuentes||0,ok=S.fuentes_ok||0,linked=(S.fuentes||[]).filter(f=>f.estado==='ok').length;
 $('#estado-actualizacion').textContent=`Consulta realizada · ${ok}/${total} fuentes respondieron; ${linked} con documentos indexados`;
 $('#fecha-actualizacion').textContent='Última consulta: '+fecha(S.ultima_consulta)}
function render(){
 const q=norm($('#buscar-novedades').value),t=$('#tipo-novedad').value,days=$('#antiguedad-novedad').value;
 const cutoff=new Date();cutoff.setHours(0,0,0,0);if(days!=='all'&&days!=='unknown')cutoff.setDate(cutoff.getDate()-Number(days));
 const rows=items.filter(x=>{const iso=fechaDocumento(x);const inPeriod=days==='all'||(days==='unknown'?!iso:(iso&&new Date(iso+'T12:00:00')>=cutoff));return inPeriod&&(!t||t===x.clase)&&(!q||norm([x.titulo,x.fuente,x.clase,x.fecha_documento,x.url].join(' ')).includes(q))})
   .sort((a,b)=>(fechaDocumento(b)||'').localeCompare(fechaDocumento(a)||'')||(b.primera_deteccion||'').localeCompare(a.primera_deteccion||''));
 $('#total-novedades').textContent=rows.length;
 $('#alcance-novedades').textContent=days==='all'?`Archivo indexado: ${rows.length} registros visibles de ${items.length}. Detectado no significa publicado recientemente.`:
  days==='unknown'?`${rows.length} registros sin fecha documental identificable: no se clasifican como publicaciones recientes.`:
  `${rows.length} registros con fecha documental dentro de los últimos ${days} días, de ${items.length} enlaces almacenados. No se utiliza la fecha de primera detección para declarar actualidad.`;
 const target=$('#lista-novedades');target.replaceChildren();if(!rows.length){target.append(el('p','','No se encontraron publicaciones fechadas para este periodo. Puedes elegir «Todo el archivo» o revisar las fuentes.'));return}
 for(const x of rows.slice(0,160)){const article=el('article','update-item'),meta=el('div','update-meta'),title=el('a','update-title',prettyTitle(x));
 title.href=x.url;title.target='_blank';title.rel='noopener noreferrer';meta.append(el('span','',x.fuente),el('span','',x.clase==='gaceta'?'Gaceta':x.clase==='orden_del_dia'?'Orden del día':'Agenda'));
 const d=fechaDocumento(x);if(d)meta.append(el('span','','Fecha documental: '+d.split('-').reverse().join('/')));
 article.append(meta,title,el('p','update-date','Indexado por primera vez: '+fecha(x.primera_deteccion)));
 if(x.documentos_adjuntos?.length){const links=el('div','update-files');for(const url of x.documentos_adjuntos.slice(0,4)){const a=el('a','','Abrir documento oficial');a.href=url;a.rel='noopener noreferrer';a.target='_blank';links.append(a)}article.append(links)}
 if(x.referencias_proyectos?.length){article.append(el('p','update-check','Referencias extraídas automáticamente (sin verificación jurídica): '+x.referencias_proyectos.join(', ')));
  const matches=maybeProjects(x);if(matches.length){const buttons=el('div','update-files');for(const p of matches.slice(0,5)){const btn=el('button','project-related','Consultar ficha relacionada: '+p.radicado);btn.type='button';btn.addEventListener('click',()=>window.OBS_ABRIR_PROYECTO?.(p));buttons.append(btn)}article.append(buttons)}}
 article.append(el('p','update-check','Publicación indexada, sin presunción de votación o aprobación'));target.append(article)}
 if(rows.length>160)target.append(el('p','update-check',`Se muestran los primeros 160 de ${rows.length} resultados. Usa los filtros para acotar la búsqueda.`));
}
$('#buscar-novedades').addEventListener('input',render);
$('#tipo-novedad').addEventListener('change',render);
$('#antiguedad-novedad').addEventListener('change',render);render();
const status=$('#estado-fuentes');status.replaceChildren();const sources=Array.isArray(S.fuentes)?S.fuentes:[];
if(!sources.length)status.append(el('p','','No se ha ejecutado el monitor. Las fichas documentales siguen disponibles.'));
else for(const f of sources){const item=el('div','source-item');item.append(el('strong','',f.nombre),el('span','',f.estado==='ok'?'Documentos indexados':f.estado==='sin_documentos_detectables'?'Respondió sin documentos detectables':'Error de consulta'));
 if(f.error)item.append(el('small','',f.error));status.append(item)}
})();
