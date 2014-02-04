# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/07/27
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

import os
from StringIO import StringIO
from contextlib import contextmanager
from aadict import aadict

from . import stream
from .stream import AbstractStreamDriver, AbstractStreamStore

#------------------------------------------------------------------------------
DEFAULT_PATH = '~/.config/secpass/data.csv'

#------------------------------------------------------------------------------
class Store(AbstractStreamStore):

  #----------------------------------------------------------------------------
  def __init__(self, driver, config, *args, **kw):
    super(Store, self).__init__(*args, **kw)
    self.driver = driver
    self.path   = config.path

  #----------------------------------------------------------------------------
  def openReadStream(self):
    if not os.path.isfile(self.path):
      return self.openEmptyReadStream()
    return open(self.path, 'rb')

  #----------------------------------------------------------------------------
  @contextmanager
  def openEmptyReadStream(self):
    yield StringIO('')

  #----------------------------------------------------------------------------
  def openWriteStream(self):
    if not os.path.isfile(self.path):
      cdir = os.path.dirname(self.path)
      if not os.path.isdir(cdir):
        os.makedirs(cdir)
    return open(self.path, 'wb')

#------------------------------------------------------------------------------
class Driver(AbstractStreamDriver):

  name = '*UNENCRYPTED* CSV File Storage'

  #----------------------------------------------------------------------------
  def __init__(self, *args, **kw):
    super(Driver, self).__init__(*args, **kw)
    self.features.secpass = 1
    self.params += (
      aadict(name='path', type='path', default=DEFAULT_PATH),
    )

  #----------------------------------------------------------------------------
  def getStore(self, config):
    return Store(self, config)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
