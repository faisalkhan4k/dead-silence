import unittest
from breath_decoder import CODES, DELETE_CODE, Decoder

def code(d,value):
 out=[]
 for digit in value:
  out+=d.advance('INHALE' if digit=='1' else 'EXHALE',.1)
  out+=d.advance('SILENCE',.05)
 return out

def silence(d,n):
 out=[]
 for _ in range(n):out+=d.advance('SILENCE',.05)
 return out

class FixedCodes(unittest.TestCase):
 def test_mapping(self):
  self.assertEqual(len(CODES),26);self.assertEqual(set(CODES.values()),set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
  self.assertTrue(all(len(k)==5 for k in CODES));self.assertEqual(DELETE_CODE,'22121');self.assertNotIn(DELETE_CODE,CODES)
  for k,v in CODES.items():self.assertIn(('letter',v),code(Decoder(),k))
 def test_commits_immediately_and_ignores_sixth_during_cooldown(self):
  d=Decoder();events=code(d,'11111');self.assertIn(('letter','A'),events)
  self.assertFalse(any(e[0]=='digit' for e in code(d,'2')))
  silence(d,16);self.assertEqual(d.code,'')
  self.assertIn(('letter','B'),code(d,'11112'))
 def test_incomplete_never_makes_letter_or_send(self):
  d=Decoder();events=code(d,'12')+silence(d,40)
  self.assertIn(('incomplete','12'),events);self.assertFalse(any(k in ('letter','send','space') for k,v in events))
 def test_word_and_send_once(self):
  d=Decoder();events=code(d,'11111')+silence(d,79)
  self.assertIn(('space',None),events);self.assertIn(('send',None),events)
  self.assertNotIn(('send',None),silence(d,100))
 def test_delete_and_unassigned(self):
  self.assertIn(('delete',None),code(Decoder(),DELETE_CODE))
  self.assertIn(('invalid','22222'),code(Decoder(),'22222'))
 def test_timing_validation(self):
  with self.assertRaises(ValueError):Decoder(letter_gap=2,word_gap=2)

if __name__=='__main__':unittest.main()
