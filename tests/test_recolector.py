import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'herramientas'))
import recopilar_novedades as r

class FakeResponse:
 def __init__(self,url,text):self.url=url;self.text=text;self.content=text.encode()import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'herramientas'))
import recopilar_novedades as r

class FakeResponse:
 def __init__(self,url,text):self.url=url;self.text=text;self.content=text.encode()
 def raise_for_status(self):pass

class FakeSession:
 def __init__(self,pages):self.pages=pages
 def get(self,url,headers=None,timeout=None,allow_redirects=None):
  if url not in self.pages:raise r.requests.ConnectionError('desconectado')
  return FakeResponse(url,self.pages[url])

class Tests(unittest.TestCase):
 def test_fecha_documental_no_confunde_archivo_con_deteccion(self):
  self.assertEqual(r.fecha_documental('7664-orden-del-dia-05-de-diciembre-de-2023/file'),'2023-12-05')
  self.assertEqual(r.fecha_documental('Orden del día 28 de octubre de 2026'),'2026-10-28')
  self.assertEqual(r.fecha_documental('28/10/2026'),'2026-10-28')
  self.assertIsNone(r.fecha_documental('Archivo Senado 2026'))
 def test_orden_camara_ignora_enlaces_sin_fecha(self):
  src={'id':'camara-c4','nombre':'Cámara IV','url':'https://www.camara.gov.co/comision-cuarta-o-presupuesto/orden-del-dia-comision-cuarta-constitucional/'}
  html='<nav><a href="/evento/orden-del-dia-28-de-octubre-de-2026/">Orden del día 28 octubre 2026</a></nav><main><a href="/evento/orden-del-dia-28-de-octubre-de-2026/">Orden del día 28 octubre 2026</a><a href="/comision-cuarta">Orden del día</a></main>'
  data=r.extract_anchors(html,src)
  self.assertEqual(len(data),1)
  self.assertTrue(data[0]['url'].startswith('https://www.camara.gov.co/'))

 def test_gacetas_no_confunde_estado_con_aprobacion(self):
  src={'nombre':'Imprenta','id':'gacetas','url':'https://svrpubindc.imprenta.gov.co/senado/view/gestion/gacetasPublicas.xhtml'}
  html='<table><tr><td>1664</td><td>Senado de la República</td><td>28/10/2026</td><td>Archivo</td></tr></table>'
  result=r.parse_gacetas(html,src)
  self.assertEqual(len(result),1)
  self.assertIn('1664',result[0]['titulo'])
  self.assertEqual(result[0]['url'],src['url'])

 def test_crawler_renueva_y_deduplica(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);(root/'data').mkdir()
   senate='https://www.senado.gov.co/index.php/documentos/comisiones/constitucionales/comision-cuarta'
   category=senate+'/orden-del-dia-16'
   gaceta='https://svrpubindc.imprenta.gov.co/senado/view/gestion/gacetasPublicas.xhtml'
   sites={senate:'<a href="'+category+'">Carpeta Orden del Día</a>',category:'<a href="'+category+'/orden-2026/file">ORDEN DEL DIA 28 DE OCTUBRE DE 2026</a>',gaceta:'<table><tr><td>1664</td><td>Senado de la República</td><td>28/10/2026</td><td>PDF</td></tr></table>'}
   sources=[{'id':'senado-c4','nombre':'Senado IV','url':senate,'kind':'senado-archivo'},{'id':'gacetas','nombre':'Imprenta','url':gaceta,'kind':'gacetas'}]
   with patch.multiple(r,ROOT=root,DEST=root/'data'/'novedades.json',ESTADO=root/'data'/'estado_fuentes.json',SOURCES=sources):
    a,b=r.run(FakeSession(sites),at='2026-10-28T21:00:00+00:00')
    self.assertEqual(b['nuevos_en_esta_consulta'],2)
    self.assertEqual(a['fuentes_ok'],2)
    _,b2=r.run(FakeSession(sites),at='2026-10-28T21:15:00+00:00')
    self.assertEqual(b2['nuevos_en_esta_consulta'],0)
    self.assertEqual(b2['novedades'][0]['primera_deteccion'],'2026-10-28T21:00:00+00:00')
    with self.assertRaises(RuntimeError):r.run(FakeSession({}),at='2026-10-28T21:30:00+00:00')
    self.assertEqual(json.loads((root/'data'/'novedades.json').read_text())['ultima_consulta'],'2026-10-28T21:15:00+00:00')

if __name__=='__main__':unittest.main()

 def raise_for_status(self):pass

class FakeSession:
 def __init__(self,pages):self.pages=pages
 def get(self,url,headers=None,timeout=None,allow_redirects=None):
  if url not in self.pages:raise r.requests.ConnectionError('desconectado')
  return FakeResponse(url,self.pages[url])

class Tests(unittest.TestCase):
 def test_orden_camara_ignora_enlaces_sin_fecha(self):
  src={'id':'camara-c4','nombre':'Cámara IV','url':'https://www.camara.gov.co/comision-cuarta-o-presupuesto/orden-del-dia-comision-cuarta-constitucional/'}
  html='<nav><a href="/evento/orden-del-dia-28-de-octubre-de-2026/">Orden del día 28 octubre 2026</a></nav><main><a href="/evento/orden-del-dia-28-de-octubre-de-2026/">Orden del día 28 octubre 2026</a><a href="/comision-cuarta">Orden del día</a></main>'
  data=r.extract_anchors(html,src)
  self.assertEqual(len(data),1)
  self.assertTrue(data[0]['url'].startswith('https://www.camara.gov.co/'))

 def test_gacetas_no_confunde_estado_con_aprobacion(self):
  src={'nombre':'Imprenta','id':'gacetas','url':'https://svrpubindc.imprenta.gov.co/senado/view/gestion/gacetasPublicas.xhtml'}
  html='<table><tr><td>1664</td><td>Senado de la República</td><td>28/10/2026</td><td>Archivo</td></tr></table>'
  result=r.parse_gacetas(html,src)
  self.assertEqual(len(result),1)
  self.assertIn('1664',result[0]['titulo'])
  self.assertEqual(result[0]['url'],src['url'])

 def test_crawler_renueva_y_deduplica(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);(root/'data').mkdir()
   senate='https://www.senado.gov.co/index.php/documentos/comisiones/constitucionales/comision-cuarta'
   category=senate+'/orden-del-dia-16'
   gaceta='https://svrpubindc.imprenta.gov.co/senado/view/gestion/gacetasPublicas.xhtml'
   sites={senate:'<a href="'+category+'">Carpeta Orden del Día</a>',category:'<a href="'+category+'/orden-2026/file">ORDEN DEL DIA 28 DE OCTUBRE DE 2026</a>',gaceta:'<table><tr><td>1664</td><td>Senado de la República</td><td>28/10/2026</td><td>PDF</td></tr></table>'}
   sources=[{'id':'senado-c4','nombre':'Senado IV','url':senate,'kind':'senado-archivo'},{'id':'gacetas','nombre':'Imprenta','url':gaceta,'kind':'gacetas'}]
   with patch.multiple(r,ROOT=root,DEST=root/'data'/'novedades.json',ESTADO=root/'data'/'estado_fuentes.json',SOURCES=sources):
    a,b=r.run(FakeSession(sites),at='2026-10-28T21:00:00+00:00')
    self.assertEqual(b['nuevos_en_esta_consulta'],2)
    self.assertEqual(a['fuentes_ok'],2)
    _,b2=r.run(FakeSession(sites),at='2026-10-28T21:15:00+00:00')
    self.assertEqual(b2['nuevos_en_esta_consulta'],0)
    self.assertEqual(b2['novedades'][0]['primera_deteccion'],'2026-10-28T21:00:00+00:00')
    with self.assertRaises(RuntimeError):r.run(FakeSession({}),at='2026-10-28T21:30:00+00:00')
    self.assertEqual(json.loads((root/'data'/'novedades.json').read_text())['ultima_consulta'],'2026-10-28T21:15:00+00:00')

if __name__=='__main__':unittest.main()
