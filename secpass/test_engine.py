# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/03/07
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

import unittest
import six

from . import engine

#------------------------------------------------------------------------------
class TestConfig(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def test_save(self):
    conf = engine.Config()
    conf.set('DEFAULT', 'locale',          'en')
    conf.set('DEFAULT', 'client.id',       'xxxx-test-id')
    conf.set('DEFAULT', 'client.name',     'Test Name')
    conf.set('DEFAULT', 'client.risk',     'medium-risk')
    conf.set('DEFAULT', 'profile.default', 'xxxx-test-profile')
    conf.add_section('profile.xxxx-test-profile')
    conf.set('profile.xxxx-test-profile',  'name', 'Test Profile')
    conf.set('profile.xxxx-test-profile',  'driver', 'secpass.driver.file')
    conf.set('profile.xxxx-test-profile',  'driver.path', '/path/to/data.csv')
    conf.set('profile.xxxx-test-profile',  'driver.no-such-config',
             'a multi-line value\n\nwith a blank line.\n.and an initial-dot line.\n')
    buf = six.StringIO()
    conf.save(buf)
    self.assertMultiLineEqual(buf.getvalue(), '''\
# -*- coding: utf-8 -*-
###############################################################################
# This is the SecPass configuration file: it configures how the low-level
# secpass drivers and the secpass command line programs behave.
#------------------------------------------------------------------------------
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/08/16
# copy: (C) Copyright 2013-EOT metagriffin -- see LICENSE.txt
# info: https://pypi.python.org/pypi/secpass
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
###############################################################################


#------------------------------------------------------------------------------
[DEFAULT]

# `locale`: Specifies the localization to apply.
locale                  = en

# `client.id`: Specifies the globally unique ID of this client. This
# value should generally not be changed once this client has started
# to use any networked or distributed service.
client.id               = xxxx-test-id

# `client.name`: The descriptive name of this client, as seen when
# interacting with distributed networked services.
client.name             = Test Name

# `client.risk`: The risk level that this client poses to being lost,
# stolen, or otherwise compromised. Note that this value is generally
# only used when initially connecting to networked services; after
# that, the risk level needs to be changed at the networked service's
# level. Valid values are "high-risk", "medium-risk", "low-risk", and
# "unbreakable". Generally speaking, setting this value conservatively
# (i.e. "higher") is better as it protects your entries better.
client.risk             = medium-risk

# `profile.default`: The default profile to use.
profile.default         = xxxx-test-profile

#------------------------------------------------------------------------------
[profile.xxxx-test-profile]

# `name`: The displayed name of this profile.
name                    = Test Profile

# `driver`: The module name of the implementation driver for this
# profile.
driver                  = secpass.driver.file

driver.no-such-config   = a multi-line value
\t.
\twith a blank line.
\t..and an initial-dot line.
\t.

# `driver.path`: For 'file' based profiles, specifies the path to the
# CSV file that will contain all of the SecPass password entries.
driver.path             = /path/to/data.csv

#------------------------------------------------------------------------------
# end of SecPass configuration
#------------------------------------------------------------------------------
''')

  #----------------------------------------------------------------------------
  def test_load(self):
    src = '''
[profile]
driver.no-such-config   = a multi-line value
\t.
\twith a blank line.
\t..and an initial-dot line.
\t.
'''
    conf = engine.Config()
    conf.load(six.StringIO(src))
    self.assertMultiLineEqual(
      conf.get('profile', 'driver.no-such-config'),
      'a multi-line value\n\nwith a blank line.\n.and an initial-dot line.\n')

  #----------------------------------------------------------------------------
  def test_roundtrip(self):
    src = '''
[profile]
driver.no-such-config   = a multi-line value
\t.
\twith a blank line.
\t..and an initial-dot line.
\t.
'''
    conf = engine.Config()
    conf.load(six.StringIO(src))
    self.assertMultiLineEqual(
      conf.get('profile', 'driver.no-such-config'),
      'a multi-line value\n\nwith a blank line.\n.and an initial-dot line.\n')

    buf = six.StringIO()
    conf.save(buf)
    conf2 = engine.Config()
    conf2.load(six.StringIO(buf.getvalue()))
    self.assertMultiLineEqual(
      conf.get('profile', 'driver.no-such-config'),
      'a multi-line value\n\nwith a blank line.\n.and an initial-dot line.\n')

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
