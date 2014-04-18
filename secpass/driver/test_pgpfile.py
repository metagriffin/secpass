# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/03/16
# copy: (C) Copyright 2014-EOT metagriffin -- see LICENSE.txt
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
import textwrap

from secpass import api
from secpass.driver import pgpfile, spbp
from secpass.test_helpers import TestSecPassHelper

#------------------------------------------------------------------------------
class TestPgpFileDriver(TestSecPassHelper):

  #----------------------------------------------------------------------------
  def setUp(self):
    # note: not using FSO since pgpfile uses an external program (gnupg)
    # self.fso = fso.push()
    self.tmpdir = tempfile.mkdtemp(prefix='test-secpass-driver-pgpfile.')

  #----------------------------------------------------------------------------
  def tearDown(self):
    shutil.rmtree(self.tmpdir)

  #----------------------------------------------------------------------------
  testkey = aadict(
    public = textwrap.dedent('''\
      -----BEGIN PGP PUBLIC KEY BLOCK-----
      Version: GnuPG v1.4.11 (GNU/Linux)

      mI0EUqHsTAEEANR+X10NmhPHecSjGPkUpqk2B3iJaftS/zMJ4cd3fqER/QG9hkXk
      oYvHZvlzgljQvWybvEVJtWIUGlugvYei0cYxeO9XXo5LoYFQVQkADM5ZvHT5Rihn
      O+o5uk4ds8sl05GU1KvQJRVPIawyYRqFdNCaYNkCvP2LhSZ8MjKUZBf5ABEBAAG0
      NXRlc3Qgc2VjcGFzcyBjbGllbnQgPHRlc3Quc2VjcGFzcy5jbGllbnRAZXhhbXBs
      ZS5jb20+iLgEEwECACIFAlKh7EwCGwMGCwkIBwMCBhUIAgkKCwQWAgMBAh4BAheA
      AAoJEJydYB29bVZwzT0D+wcoKl5Mj0Zd7Oi+M1Crb9etEi8ZG3POrnyqeKKuX1Sf
      I+bV9iHAq0sDWteghos1XG7q0T9KuloQWBHQmvfmxz77C/RZWsyKD91FVn+XJLrz
      iFonjfmpLFNpEEOlxgVXTb6347t3QKUdHgwqkQUf7ctMOAm5SLRdT7L3Ujzm4V5J
      uI0EUqHsTAEEAO27GE38XYk3y/+b/xTbRZlQxmY+CX9oX2t1S3KQUeAduVTO8Bqa
      ZCbU0qZ5dmD8N2h3l6hmltZdyyQpHj3Vq2qLvsngJQsRA7mj3z2G2fQeO7Kis3fF
      dy3IMZA5ql8OIfXai8nnXgfG9Q3FU0Wtn7gqd1T0OI9cbNEUqR+S4nlNABEBAAGI
      nwQYAQIACQUCUqHsTAIbDAAKCRCcnWAdvW1WcJ4HA/0SNarbHthodUvJ1dCG0+m8
      Tyd1I4kO9OQ06ZtJ0yFwDg41FX77/8C+/35CjhUvxS5bPOJA6PAg4blMfSRqAg0x
      MKoqRX5xyd3sScf5Gs766d+DB1Z/Pz2J+10rvNrevYmH+AZ71KuPFZhl3izFhEqs
      i9OeSaTkGT0kLE4qW00jQA==
      =e1of
      -----END PGP PUBLIC KEY BLOCK-----
      '''),
    fingerprint = '180834674CBAEE5388F344509C9D601DBD6D5670',
    identity = 'test.secpass.client@example.com',
    private = textwrap.dedent('''\
      -----BEGIN PGP PRIVATE KEY BLOCK-----
      Version: GnuPG v1.4.11 (GNU/Linux)

      lQHYBFKh7EwBBADUfl9dDZoTx3nEoxj5FKapNgd4iWn7Uv8zCeHHd36hEf0BvYZF
      5KGLx2b5c4JY0L1sm7xFSbViFBpboL2HotHGMXjvV16OS6GBUFUJAAzOWbx0+UYo
      ZzvqObpOHbPLJdORlNSr0CUVTyGsMmEahXTQmmDZArz9i4UmfDIylGQX+QARAQAB
      AAP8CjSNiO8LzNJiNz7sBp5myK6nGjNjSyY3ynA5jzZedwbho1FCXx31Yjyv5eAV
      zQUta8do+dzp4K19fJQSNi7sKyWy5YFWwWYw/ZSEwlIQi86j1WRcrh0e8LgjYs6G
      CJDtc9nU5b/8QzqAI0Zc+6eNS1NYtOQO62xFu8lrhupsSP8CAOi6n7BLinFL9yW8
      EfSyQ+qQ3le7QJaM7aUtUk8hHRhTx35yva344pkV7txBRtzZuik53KuadQpMu4h4
      mGZ9nosCAOm9xBBMvjwl0KRT2AeVHKiKTLkK2LQCPtIcvyOKLFPaFq5qv5Q+PKc2
      lJZ6wdfyVCnRxMR2t0GlE2IR/EXL2AsCANan8GfncVY9yggF8iAHTRv2MxxBKPtP
      WDtTjVjHApB7zGnI3y3vtU02vV/YrWmSOnTspGgfn4dWzucDB4Akj4OhX7Q1dGVz
      dCBzZWNwYXNzIGNsaWVudCA8dGVzdC5zZWNwYXNzLmNsaWVudEBleGFtcGxlLmNv
      bT6IuAQTAQIAIgUCUqHsTAIbAwYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AACgkQ
      nJ1gHb1tVnDNPQP7BygqXkyPRl3s6L4zUKtv160SLxkbc86ufKp4oq5fVJ8j5tX2
      IcCrSwNa16CGizVcburRP0q6WhBYEdCa9+bHPvsL9FlazIoP3UVWf5ckuvOIWieN
      +aksU2kQQ6XGBVdNvrfju3dApR0eDCqRBR/ty0w4CblItF1PsvdSPObhXkmdAdgE
      UqHsTAEEAO27GE38XYk3y/+b/xTbRZlQxmY+CX9oX2t1S3KQUeAduVTO8BqaZCbU
      0qZ5dmD8N2h3l6hmltZdyyQpHj3Vq2qLvsngJQsRA7mj3z2G2fQeO7Kis3fFdy3I
      MZA5ql8OIfXai8nnXgfG9Q3FU0Wtn7gqd1T0OI9cbNEUqR+S4nlNABEBAAEAA/wM
      tAiych/Va0PdXsqcpLLtZGGVqQ783ejrZxMnBgs5/JygqYYvBb0ATjMLbkYjHJch
      X/Kcrw60WcK3JfNVvoswRfXwkCkhWvZQPzC7u/Jp1gBp2ibtWpc2FucafB31dT1O
      VTjm74gmfb4vmMfjtXVJam0Yt3vCiBTPAiDi/GUkCQIA9p5YBF5YAvs7SltWI71B
      MgyIReyBgvWDLtYd/S7+O0sQyNHPn7i65RlIsK+Bi78dQr1ZBrlaLUYibZ7o2m8N
      PwIA9sYzIWQMYKlfrvjMSj8376zDintD7ar97Qs52/TB0HHBEJzfM2PyPqW5KuZm
      BpxpN6lhNBPk7kkbNlNhK/D6cwH+JbmEap1niVWW6jhCkoC4EBhzu57CUmx5O6Ob
      n8cvhO14FJUJy5HdcduvjpV0l07/01lP4/8zgSWhIgzLFJrlOp5XiJ8EGAECAAkF
      AlKh7EwCGwwACgkQnJ1gHb1tVnCeBwP9EjWq2x7YaHVLydXQhtPpvE8ndSOJDvTk
      NOmbSdMhcA4ONRV++//Avv9+Qo4VL8UuWzziQOjwIOG5TH0kagINMTCqKkV+ccnd
      7EnH+RrO+unfgwdWfz89iftdK7za3r2Jh/gGe9SrjxWYZd4sxYRKrIvTnkmk5Bk9
      JCxOKltNI0A=
      =yBIx
      -----END PGP PRIVATE KEY BLOCK-----
      '''),
  )

  #----------------------------------------------------------------------------
  def test_pgpfile(self):
    ghome = os.path.join(self.tmpdir, 'gpg-home-dir')
    path  = os.path.join(self.tmpdir, 'data.csv.pgp')
    os.makedirs(ghome)
    with spbp.GpgEnv(gpghome=ghome) as gpg:
      gpg.importKey(self.testkey.private)
    self.assertFalse(os.path.exists(path))
    store = pgpfile.Driver().getStore(aadict(
      path     = path,
      agent    = True,
      identity = self.testkey.identity,
      gpghome  = ghome,
    ))
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
    out = open(path, 'rb').read()
    mgk = '-----BEGIN PGP MESSAGE-----'
    self.assertEqual(out[:len(mgk)], mgk)
    with spbp.GpgEnv(gpghome=ghome) as gpg:
      out = gpg.gpg.decrypt(out)
    self.assertSecPassCsvEqual(out, chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
