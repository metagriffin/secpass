# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/07/23
# copy: (C) Copyright 2013-EOT metagriffin -- see LICENSE.txt
#------------------------------------------------------------------------------
# This software is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#------------------------------------------------------------------------------

import unittest, tempfile, os, csv, shutil
from six import StringIO
from aadict import aadict
import fso

from secpass import api
from secpass.driver import file
from secpass.test_helpers import TestSecPassHelper

#------------------------------------------------------------------------------
class TestFileDriver(TestSecPassHelper):

  #----------------------------------------------------------------------------
  def setUp(self):
    self.fso = fso.push()

  #----------------------------------------------------------------------------
  def tearDown(self):
    fso.pop()

  #----------------------------------------------------------------------------
  def test_file(self):
    tdir = tempfile.mkdtemp(prefix='test-secpass-driver-file.')
    path = os.path.join(tdir, 'data.csv')
    self.assertFalse(os.path.exists(path))
    store = file.Driver().getStore(aadict(path=path))
    self.assertEqual(len(list(store.find())), 0)
    self.assertFalse(os.path.exists(path))
    store.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    entries = list(store.find())
    self.assertEqual(len(entries), 1)
    entry = store.read(entries[0].id)
    self.assertEqual(entry.service, 'testservice')
    entry.password = 'newpass'
    store.update(entry)
    store.create(api.Entry(
      service='testservice2', role='testrole2', password='testpass2', notes='testnotes2'))
    store.delete(entry.id)
    chk = '''\
"id","seq","created","updated","lastused","deleted","service","role","password","notes"
:UUID:$ID1,0,:~NOW:$CTS1,:~NOW,:~NOW,:NULL,"testservice","testrole","testpass","testnotes"
:=ID1,1,:=CTS1,:~NOW,:~NOW,:NULL,"testservice","testrole","testpass","testnotes"
:=ID1,2,:=CTS1,:~NOW,:~NOW,:NULL,"testservice","testrole","newpass","testnotes"
:UUID:$ID2,0,:~NOW,:~NOW,:~NOW,:NULL,"testservice2","testrole2","testpass2","testnotes2"
:=ID1,3,:=CTS1,:~NOW,:~NOW,:~NOW,"testservice","testrole","newpass","testnotes"
'''
    self.assertSecPassCsvEqual(open(path, 'rb').read(), chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
