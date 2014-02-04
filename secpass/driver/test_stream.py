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

import unittest, csv, time
from StringIO import StringIO
from contextlib import contextmanager
from secpass import api
from secpass.driver import stream
from secpass.test_helpers import TestSecPassHelper

#------------------------------------------------------------------------------
class BufferStore(stream.AbstractStreamStore):
  def __init__(self, value=''):
    self.value = value
  @contextmanager
  def openWriteStream(self):
    ret = StringIO()
    yield ret
    self.value = ret.getvalue()
  @contextmanager
  def openReadStream(self):
    yield StringIO(self.value)

#------------------------------------------------------------------------------
class TestAbstractStreamDriver(TestSecPassHelper):

  #----------------------------------------------------------------------------
  def test_create(self):
    driver = BufferStore()
    driver.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    chk = '''\
"id","seq","created","updated","lastused","deleted","service","role","password","notes"
:UUID,0,:~NOW,:~NOW,:~NOW,,"testservice","testrole","testpass","testnotes"
'''
    self.assertSecPassCsvEqual(driver.value, chk)

  #----------------------------------------------------------------------------
  def test_read(self):
    driver = BufferStore()
    cent = driver.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    entries = driver.find()
    self.assertEqual(len(entries), 1)
    fent = entries[0]
    self.assertEqual(fent.service, 'testservice')
    self.assertEqual(fent.role, 'testrole')
    self.assertEqual(fent.password, None)
    self.assertEqual(fent.notes, 'testnotes')
    for attr in stream.AbstractStreamStore.FIELDS:
      if attr == 'password':
        continue
      self.assertEqual(getattr(cent, attr), getattr(fent, attr))
    rent = driver.read(fent.id)
    self.assertEqual(rent.password, 'testpass')
    for attr in stream.AbstractStreamStore.FIELDS:
      if attr not in ('seq', 'lastused'):
        self.assertEqual(getattr(cent, attr), getattr(rent, attr))
      else:
        self.assertNotEqual(getattr(cent, attr), getattr(rent, attr))
    self.assertGreater(rent.seq, fent.seq)
    self.assertGreater(rent.lastused, fent.lastused)

  #----------------------------------------------------------------------------
  def test_update(self):
    driver = BufferStore()
    driver.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    eid = list(driver.find())[0].id
    entry = driver.read(eid)
    entry.password = 'newpass'
    entry.notes    += '\nmore notes'
    driver.update(entry)
    chk = '''\
"id","seq","created","updated","lastused","deleted","service","role","password","notes"
:UUID:$ID1,0,:~NOW,:~NOW,:~NOW,,"testservice","testrole","testpass","testnotes"
:=ID1,1,:~NOW,:~NOW,:~NOW,,"testservice","testrole","testpass","testnotes"
:=ID1,2,:~NOW,:~NOW,:~NOW,,"testservice","testrole","newpass","testnotes
more notes"
'''
    self.assertSecPassCsvEqual(driver.value, chk)
    out = list(csv.reader(StringIO(driver.value)))
    chk = list(csv.reader(StringIO(chk)))
    # check id
    self.assertEqual(out[1][0], out[2][0])
    self.assertEqual(out[1][0], out[3][0])
    # check seq
    self.assertGreater(out[2][1], out[1][1])
    self.assertGreater(out[3][1], out[2][1])
    # check created
    self.assertEqual(out[1][2], out[2][2])
    self.assertEqual(out[1][2], out[3][2])
    # check updated
    self.assertEqual(out[1][3], out[2][3])
    self.assertGreater(out[3][3], out[2][3])
    # check lastused
    self.assertGreater(out[2][4], out[1][4])
    self.assertGreater(out[3][4], out[2][4])

  #----------------------------------------------------------------------------
  def test_modify(self):
    driver = BufferStore()
    driver.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    eid = list(driver.find())[0].id
    driver.modify(eid, service='new-testservice')
    chk = '''\
"id","seq","created","updated","lastused","deleted","service","role","password","notes"
:UUID:$ID1,0,:~NOW,:~NOW,:~NOW,,"testservice","testrole","testpass","testnotes"
:=ID1,1,:~NOW,:~NOW,:~NOW,,"new-testservice","testrole","testpass","testnotes"
'''
    self.assertSecPassCsvEqual(driver.value, chk)
    out = list(csv.reader(StringIO(driver.value)))
    chk = list(csv.reader(StringIO(chk)))
    # check id
    self.assertEqual(out[1][0], out[2][0])
    # check seq
    self.assertGreater(out[2][1], out[1][1])
    # check created
    self.assertEqual(out[1][2], out[2][2])
    # check updated
    self.assertGreater(out[2][3], out[1][3])
    # check lastused
    self.assertGreater(out[2][4], out[1][4])

  #----------------------------------------------------------------------------
  def test_delete(self):
    driver = BufferStore()
    driver.create(api.Entry(
      service='testservice', role='testrole', password='testpass', notes='testnotes'))
    eid = list(driver.find())[0].id
    entry = driver.read(eid)
    entry.password = 'newpass'
    entry.notes    += '\nmore notes'
    driver.update(entry)
    driver.delete(entry.id)
    chk = '''\
"id","seq","created","updated","lastused","deleted","service","role","password","notes"
:UUID:$ID1,0,:~NOW,:~NOW,:~NOW,,"testservice","testrole","testpass","testnotes"
:=ID1,1,:~NOW,:~NOW,:~NOW,,"testservice","testrole","testpass","testnotes"
:=ID1,2,:~NOW,:~NOW,:~NOW,,"testservice","testrole","newpass","testnotes
more notes"
:=ID1,3,:~NOW,:~NOW,:~NOW,:~NOW,"testservice","testrole","newpass","testnotes
more notes"
'''
    self.assertSecPassCsvEqual(driver.value, chk)
    out = list(csv.reader(StringIO(driver.value)))
    chk = list(csv.reader(StringIO(chk)))
    # check id
    self.assertEqual(out[1][0], out[2][0])
    self.assertEqual(out[1][0], out[3][0])
    self.assertEqual(out[1][0], out[4][0])
    # check seq
    self.assertGreater(out[2][1], out[1][1])
    self.assertGreater(out[3][1], out[2][1])
    self.assertGreater(out[4][1], out[3][1])
    # check created
    self.assertEqual(out[1][2], out[2][2])
    self.assertEqual(out[1][2], out[3][2])
    self.assertEqual(out[1][2], out[4][2])
    # check updated
    self.assertEqual(out[1][3], out[2][3])
    self.assertGreater(out[3][3], out[2][3])
    self.assertEqual(out[3][3], out[4][3])
    # check lastused
    self.assertGreater(out[2][4], out[1][4])
    self.assertGreater(out[3][4], out[2][4])
    self.assertEqual(out[3][4], out[4][4])
    # check deleted
    self.assertAlmostEqual(float(out[4][5]), time.time(), delta=0.5)
    self.assertEqual(len(list(driver.find())), 0)
    with self.assertRaises(api.EntryNotFound):
      dent = driver.read(eid)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
