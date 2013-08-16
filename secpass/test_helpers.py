# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/23
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import unittest, csv, time, urllib
from StringIO import StringIO

#------------------------------------------------------------------------------
class TestSecPassHelper(unittest.TestCase):

  #----------------------------------------------------------------------------
  def assertIsUuid(self, text):
    self.assertRegexpMatches(text, '^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$')

  #----------------------------------------------------------------------------
  def assertIsNear(self, test, check, plusminus=0):
    self.assertTrue(
      test >= check - plusminus and test <= check + plusminus,
      msg='%r is near %r' % (test, check))

  #----------------------------------------------------------------------------
  def assertSecPassCsvEqual(self, test, check):
    out = list(csv.reader(StringIO(test)))
    chk = list(csv.reader(StringIO(check)))
    self.assertEqual(len(out), len(chk))
    self.assertEqual(out[0], chk[0])
    tab = dict()
    for rowidx in range(1, len(chk)):
      for idx, cell in enumerate(chk[rowidx]):
        val = out[rowidx][idx]
        if not cell or not cell.startswith(':'):
          self.assertEqual(val, cell)
          continue
        cell = cell[1:]
        if cell.startswith(':'):
          self.assertEqual(val, cell)
          continue
        for expr in [urllib.unquote(v) for v in cell.split(':')]:
          if expr == 'UUID':
            self.assertIsUuid(val)
          elif expr == 'NULL':
            self.assertTrue(val == '' or val is None)
          elif expr == '!NULL':
            self.assertTrue(val)
          elif expr.startswith('~NOW'):
            pm = 1
            if expr.startswith('~NOW~'):
              pm = float(expr[5:])
            self.assertIsNear(float(val), time.time(), plusminus=pm)
          elif expr.startswith('$'):
            tab[expr[1:]] = val
          elif expr.startswith('='):
            self.assertEqual(val, tab[expr[1:]])
          else:
            raise Exception('unknown test expression %r' % (expr,))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
