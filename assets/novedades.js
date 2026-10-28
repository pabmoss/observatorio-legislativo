(()=>{'use strict';
const $=s=>document.querySelector(s);
const D=window.OBS_NOVEDADES||{},S=window.OBS_FUENTES||{},items=Array.isArray(D.novedades)?D.novedades:[];
const norm=x=>String(x??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const el=(name,cl,text)=>{const n=document.createElement(name);if(cl)n.className=cl;if(text!=null)n.textContent=text;return n};
const fecha=x=>{if(!x)return 'Sin registro';const d=new Date(x);return isNaN(d)?x:d.toLocaleString('es-CO',{timeZone:'America/Bogota',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})+' (Bogotá)'};
$('#total-novedades').textContent=items.length;
if(S.ultima_consulta){let total=S.total_fuentes||0,ok=S.fuentes_ok||0;$('#estado-actualizacion').textContent=`Consulta automática · ${ok}/${total} fuentes accesibles`;$('#fecha-actualizacion').textContent='Última ejecución: '+fecha(S.ultima_consulta)}
function render(){const q=norm($('#buscar-novedades').value),t=$('#tipo-novedad').value,rows=items.filter(x=>(!t||t===x.clase)&&(!q||norm([x.titulo,x.fuente,x.clase,x.fecha_documento].join(' ')).includes(q))).slice(0,120);
 const target=$('#lista-novedades');target.replaceChildren();if(!rows.length){target.append(el('p','','No hay publicaciones registradas con esos filtros. Revisa el estado de las fuentes.'));return}
 for(const x of rows){const article=el('article','update-item'),meta=el('div','update-meta'),title=el('a','update-title',x.titulo);
 title.href=x.url;title.target='_blank';title.rel='noopener noreferrer';meta.append(el('span','',x.fuente),el('span','',x.clase==='gaceta'?'Gaceta':x.clase==='orden_del_dia'?'Orden del día':'Agenda'));
 article.append(meta,title,el('p','update-date','Primera detección: '+fecha(x.primera_deteccion)));
 if(x.documentos_adjuntos?.length){const links=el('div','update-files');for(const url of x.documentos_adjuntos.slice(0,6)){const a=el('a','','Abrir PDF oficial');a.href=url;a.rel='noopener noreferrer';a.target='_blank';links.append(a)}article.append(links)}
 if(x.referencias_proyectos?.length)article.append(el('p','update-check','Números mencionados en el PDF (extracción automática, sujetos a revisión): '+x.referencias_proyectos.join(', ')));
 article.append(el('p','update-check','Enlace detectado; trámite y resultados no verificados'));target.append(article)}}
$('#buscar-novedades').addEventListener('input',render);$('#tipo-novedad').addEventListener('change',render);render();
const status=$('#estado-fuentes');status.replaceChildren();const sources=Array.isArray(S.fuentes)?S.fuentes:[];
if(!sources.length)status.append(el('p','','No se ha ejecutado el monitor. Los archivos de fichas continúan disponibles.'));
else for(const f of sources){const item=el('div','source-item');item.append(el('strong','',f.nombre),el('span','',f.estado==='ok'?'Accesible':f.estado==='sin_documentos_detectables'?'Sin publicaciones indexables':'Error de consulta'));
 if(f.error)item.append(el('small','',f.error));status.append(item)}
})();
