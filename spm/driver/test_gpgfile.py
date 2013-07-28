# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/23
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import unittest, tempfile, os, csv, shutil
from StringIO import StringIO
import gnupg
from spm import api
from spm.driver import gpgfile
from spm.test_helpers import TestSpmHelper

#------------------------------------------------------------------------------
class TestGpgDriver(TestSpmHelper):

  #----------------------------------------------------------------------------
  def setUp(self):
    # TODO: change this to be simple password based...
    self.gpgargs = dict(agent=True, identity='test@example.com')

#   #----------------------------------------------------------------------------
#   # TODO: enable this once a way has been created to not depend on the
#   #       presence of a gpg-agent...
#   def test_file(self):
#     tdir = tempfile.mkdtemp(prefix='test-smp-driver-gpgfile.')
#     path = os.path.join(tdir, 'data.csv.gpg')
#     self.assertFalse(os.path.exists(path))
#     driver = gpgfile.GpgFileDriver(path=path, **self.gpgargs)
#     self.assertEqual(len(list(driver.find())), 0)
#     self.assertFalse(os.path.exists(path))
#     driver.create(api.Entry(
#       service='testservice', role='testrole', password='testpass', notes='testnotes'))
#     entries = list(driver.find())
#     self.assertEqual(len(entries), 1)
#     entry = driver.read(entries[0].id)
#     self.assertEqual(entry.service, 'testservice')
#     entry.password = 'newpass'
#     driver.update(entry)
#     driver.create(api.Entry(
#       service='testservice2', role='testrole2', password='testpass2', notes='testnotes2'))
#     driver.delete(entry.id)
#     chk = '''\
# "id","seq","created","updated","lastused","deleted","service","role","password","notes"
# :UUID:$ID1,0,:~NOW~5:$CTS1,:~NOW~5,:~NOW~5,:NULL,"testservice","testrole","testpass","testnotes"
# :=ID1,1,:=CTS1,:~NOW~5,:~NOW~5,:NULL,"testservice","testrole","testpass","testnotes"
# :=ID1,2,:=CTS1,:~NOW~5,:~NOW~5,:NULL,"testservice","testrole","newpass","testnotes"
# :UUID:$ID2,0,:~NOW~5,:~NOW~5,:~NOW~5,:NULL,"testservice2","testrole2","testpass2","testnotes2"
# :=ID1,3,:=CTS1,:~NOW~5,:~NOW~5,:~NOW~5,"testservice","testrole","newpass","testnotes"
# '''
#     with open(path, 'rb') as fp:
#       gpg  = gnupg.GPG(use_agent=self.gpgargs['agent'])
#       self.assertSpmCsvEqual(str(gpg.decrypt(fp.read())), chk)
#     shutil.rmtree(tdir)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
