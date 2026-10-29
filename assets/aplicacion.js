(()=>{'use strict';
const DB=window.OBS_DATA;
const $=sel=>document.querySelector(sel);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const searchNorm=s=>String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es');
const el=(tag,attrs={},text)=>{const e=document.createElement(tag);for(const[k,v]of Object.entries(attrs)){if(k==='class')e.className=v;else e.setAttribute(k,v)}if(text!==undefined)e.textContent=text;return e};
const data=DB?.proyectos??[];
if(!data.length){$('#lista-proyectos').textContent='No se pudieron cargar los datos del observatorio.';return;}
$('#total-proyectos').textContent=data.length;
// Todas las fechas visibles proceden de la versión de datos; nunca del HTML.
const corte=String(DB.corte_documental??'');
const matchCorte=/^(\d{4})-(\d{2})-(\d{2})$/.exec(corte);
const formalCorte=matchCorte?new Date(corte+'T12:00:00').toLocaleDateString('es-CO',{day:'numeric',month:'long',year:'numeric'}):corte;
const cortoCorte=matchCorte?`${matchCorte[3]}.${matchCorte[2]}.${matchCorte[1]}`:corte;
const cortoSlash=matchCorte?`${matchCorte[3]}/${matchCorte[2]}/${matchCorte[1]}`:corte;
$('#corte').textContent='Corte documental: '+formalCorte;
$('#version-corte').textContent=cortoCorte;
$('#edicion').textContent='Edición documental · '+formalCorte;
$('#agenda-corte').textContent=cortoSlash;
$('#archivo-corte').textContent=formalCorte;
$('#modal-corte').textContent=cortoCorte;
const comisiones=[...new Set(data.map(x=>x.grupo_origen_documento))];
comisiones.forEach(x=>$('#comisiones').append(el('option',{value:x},x)));
const summary=x=>x.objeto&&x.objeto.length>220?x.objeto.slice(0,214).replace(/\s+\S*$/,'')+'…':x.objeto;
const shortState=s=>{if(/sin aprobación verificada|no se presume|no acredita|anuncio|presentaci[oó]n/i.test(s))return 'Estado documental';if(/segundo debate/i.test(s))return 'Segundo debate';if(/primer debate/i.test(s))return 'Primer debate';return 'En seguimiento'};
function renderCards(){let search=searchNorm($('#buscar').value),com=$('#comisiones').value,sort=$('#orden').value;let rows=data.filter(x=>(!com||x.grupo_origen_documento===com)&&(!search||searchNorm([x.radicado,x.titulo,x.objeto,x.motivos,x.analisis,x.comision,x.origen].join(' ')).includes(search)));
 if(sort==='numero')rows=[...rows].sort((a,b)=>a.radicado.localeCompare(b.radicado,'es',{numeric:true}));
 if(sort==='fecha')rows=[...rows].sort((a,b)=>(b.fecha_sesion??'').localeCompare(a.fecha_sesion??'')||a.orden_documento-b.orden_documento);
 const target=$('#lista-proyectos');target.replaceChildren();$('#resultados').textContent=rows.length;$('#sin-resultados').hidden=!!rows.length;
 for(const p of rows){const article=el('article',{class:'project-card'}),main=el('div',{class:'card-main'}),top=el('div',{class:'card-overline'});
 top.append(el('span',{class:'bill-number'},p.radicado),el('span',{class:'status-tag'},shortState(p.estado)));
 main.append(top,el('h3',{},p.titulo));let meta=el('div',{class:'card-meta'});meta.append(el('span',{},p.grupo_origen_documento),el('span',{},p.fecha_sesion?'Sesión: '+p.fecha_sesion.split('-').reverse().join('.'):'Actividad archivada'));main.append(meta,el('p',{class:'card-summary'},summary(p)));
 let acts=el('div',{class:'card-actions'});let detail=el('button',{type:'button',class:'outline-btn'},'Ver ficha completa');detail.addEventListener('click',()=>openDetail(p));
 let word=el('a',{href:p.documento_word,class:'text-btn',download:''},'Word editable ↗');acts.append(detail,word);article.append(main,acts);target.append(article)}
 }
function detailField(parent,title,value){const wrap=el('div',{class:'detail-field'});wrap.append(el('b',{},title),el('p',{},value||'Pendiente de verificar'));parent.append(wrap)}
function detailSection(parent,title,text){if(!text)return;const s=el('section',{class:'detail-section'});s.append(el('h3',{},title));for(const part of text.split('\n\n'))s.append(el('p',{},part));parent.append(s)}
function openDetail(p){$('#detalle-titulo').textContent=p.radicado;$('#detalle-subtitulo').textContent=p.titulo;
 const body=$('#detalle-contenido');body.replaceChildren();const grid=el('div',{class:'detail-grid'});for(const [label,key] of [['Tipo de ley','tipo_ley'],['Estado actual documentado','estado'],['Origen','origen'],['Comisión','comision'],['Sesión y actividad','sesion']])detailField(grid,label,p[key]);body.append(grid);
 for(const [title,key]of [['Breve exposición de motivos','motivos'],['Objeto del texto radicado','objeto'],['Análisis del soporte actual','analisis'],['Ponentes','ponentes']])detailSection(body,title,p[key]);
 if(p.documentos.length){const sect=el('section',{class:'detail-section'});sect.append(el('h3',{},'Documentos oficiales y fuentes'));const links=el('div',{class:'detail-links'});for(const link of p.documentos){let a=el('a',{href:link.url,target:'_blank',rel:'noopener noreferrer'},link.etiqueta+' ↗');links.append(a)}sect.append(links);body.append(sect)}
 if(p.notas_documentales?.length)detailSection(body,'Notas de verificación',p.notas_documentales.join('\n\n'));
 const acts=el('div',{class:'detail-actions'});acts.append(el('span',{},'Corte documental: '+formalCorte),el('a',{href:p.documento_word,download:''},'Descargar ficha Word editable'));body.append(acts);
 const dialog=$('#detalle');dialog.showModal();dialog.scrollTop=0;}
window.OBS_ABRIR_PROYECTO=openDetail;
$('#cerrar').addEventListener('click',()=>$('#detalle').close());$('#detalle').addEventListener('click',e=>{if(e.target===$('#detalle'))$('#detalle').close()});
function renderAgenda(){
 const target=$('#agenda-lista');target.replaceChildren();
 const full=window.OBS_SESIONES?.sesiones||[];
 const used=new Set();
 for(const sess of full){
   const wrap=el('section',{class:'session-download'});
   const head=el('div',{class:'session-head'}),info=el('div',{class:'session-title'});
   info.append(el('div',{class:'label-overline'},'PLENARIA DOCUMENTADA'),el('h3',{},sess.titulo),el('p',{},`${sess.cantidad_fichas} fichas individuales · corte ${sess.corte_documental}`));
   const link=el('a',{href:sess.documento_word,class:'session-word',download:''},'Descargar todas las fichas en Word');
   head.append(info,link);wrap.append(head);
   wrap.append(el('p',{class:'session-caveat'},'Documento único, organizado en tablas, diseñado para impresión y sin enlaces web. Incluye solo los proyectos documentados en el corte; no acredita exhaustividad ni resultados de votaciones.'));
   const rows=el('div',{class:'session-items'});
   for(const id of sess.ids_proyectos){const p=data.find(x=>x.id===id);if(!p)continue;used.add(id);
     const card=el('div',{class:'session-item'});card.append(el('span',{},p.radicado+' · '+p.titulo));
     const btn=el('button',{type:'button'},'Ver ficha');btn.addEventListener('click',()=>openDetail(p));card.append(btn);rows.append(card)}
   wrap.append(rows);target.append(wrap)
 }
 const rest=data.filter(p=>!used.has(p.id));
 if(rest.length){const section=el('section',{class:'other-sessions'});section.append(el('h3',{},'Otras sesiones del archivo'));
   const grouped=new Map();for(const p of rest){const key=p.sesion.split('. Citada.')[0].split('. Realizada.')[0]||'Sesión documentada';if(!grouped.has(key))grouped.set(key,[]);grouped.get(key).push(p)}
   for(const [key,items] of grouped){const container=el('div',{class:'other-session'});container.append(el('h4',{},key));for(const p of items){const row=el('div',{class:'session-item'});row.append(el('span',{},p.radicado+' · '+p.titulo));const b=el('button',{type:'button'},'Ver ficha');b.addEventListener('click',()=>openDetail(p));row.append(b);container.append(row)}section.append(container)}target.append(section)}
}
$('.tabs').addEventListener('click',e=>{const b=e.target.closest('button[data-tab]');if(!b)return;let active=b.dataset.tab;for(const v of ['proyectos','agenda','novedades','metodologia'])$('#panel-'+v).hidden=v!==active;document.querySelectorAll('.tab').forEach(tab=>{let activeTab=tab===b;tab.classList.toggle('active',activeTab);if(activeTab)tab.setAttribute('aria-current','page');else tab.removeAttribute('aria-current')});});
$('#buscar').addEventListener('input',renderCards);$('#comisiones').addEventListener('change',renderCards);$('#orden').addEventListener('change',renderCards);
renderCards();renderAgenda();
})();
