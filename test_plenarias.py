import sys
import json
import unittest
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'herramientas'))
import generar_plenarias as gp

class TestPlenarias(unittest.TestCase):
 def test_agrupa_plenarias_y_no_comisiones(self):
  db=json.loads((ROOT/'data'/'proyectos.json').read_text(encoding='utf-8'))
  meetings={}
  for p in db['proyectos']:
   s=gp.session_info(p)
   if s:meetings.setdefault(s['id'],[]).append(p)
  self.assertEqual(len(meetings['plenaria-senado-2026-10-27T1500']),19)
  self.assertEqual(len(meetings['plenaria-senado-2026-10-19T0900']),1)
  self.assertEqual(len(meetings),2)

 def test_consolidados_tienen_tablas_sin_hipervinculos(self):
  data=json.loads((ROOT/'data'/'sesiones.json').read_text(encoding='utf-8'))
  self.assertTrue(data['sesiones'])
  for sesion in data['sesiones']:
   file=ROOT/sesion['documento_word']
   self.assertTrue(file.is_file(),file)
   with ZipFile(file) as z:
    relationships=z.read('word/_rels/document.xml.rels').decode()
    document=z.read('word/document.xml').decode()
   self.assertNotIn('TargetMode="External"',relationships)
   from docx import Document
   doc=Document(file)
   printable=' '.join(c.text for t in doc.tables for row in t.rows for c in row.cells)
   self.assertNotIn('http://',printable)
   self.assertNotIn('https://',printable)
   self.assertIn('w:tbl',document)

if __name__=='__main__':unittest.main()
