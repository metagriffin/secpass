# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/23
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import unittest, tempfile, os, csv, shutil
from StringIO import StringIO
from secpass import api
from secpass.util import adict
from secpass.driver import file
from secpass.test_helpers import TestSecPassHelper

#------------------------------------------------------------------------------
class TestFileDriver(TestSecPassHelper):

  #----------------------------------------------------------------------------
  def test_file(self):
    tdir = tempfile.mkdtemp(prefix='test-smp-driver-file.')
    path = os.path.join(tdir, 'data.csv')
    self.assertFalse(os.path.exists(path))
    driver = file.FileDriver(adict(path=path))
    self.assertEqual(len(list(driver.find())), 0)
    self.assertFalse(os.path.exists(path))
    driver.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    entries = list(driver.find())
    self.assertEqual(len(entries), 1)
    entry = driver.read(entries[0].id)
    self.assertEqual(entry.service, 'testservice')
    entry.password = 'newpass'
    driver.update(entry)
    driver.create(api.Entry(
      service='testservice2', role='testrole2', password='testpass2', notes='testnotes2'))
    driver.delete(entry.id)
    chk = '''\
"id","seq","created","updated","lastused","deleted","service","role","password","notes"
:UUID:$ID1,0,:~NOW:$CTS1,:~NOW,:~NOW,:NULL,"testservice","testrole","testpass","testnotes"
:=ID1,1,:=CTS1,:~NOW,:~NOW,:NULL,"testservice","testrole","testpass","testnotes"
:=ID1,2,:=CTS1,:~NOW,:~NOW,:NULL,"testservice","testrole","newpass","testnotes"
:UUID:$ID2,0,:~NOW,:~NOW,:~NOW,:NULL,"testservice2","testrole2","testpass2","testnotes2"
:=ID1,3,:=CTS1,:~NOW,:~NOW,:~NOW,"testservice","testrole","newpass","testnotes"
'''
    self.assertSecPassCsvEqual(open(path, 'rb').read(), chk)
    shutil.rmtree(tdir)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
