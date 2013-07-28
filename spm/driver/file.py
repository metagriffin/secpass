# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/27
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import os
from StringIO import StringIO
from contextlib import contextmanager
from . import stream
from .stream import AbstractStreamDriver
from spm.util import adict

#------------------------------------------------------------------------------
DEFAULT_PATH = '~/.config/spm/data.csv'

#------------------------------------------------------------------------------
class FileDriver(AbstractStreamDriver):

  PARAMS = stream.AbstractStreamDriver.PARAMS + (
    adict(name='path', type='path', default=DEFAULT_PATH),
    )

  #----------------------------------------------------------------------------
  def __init__(self, config):
    super(FileDriver, self).__init__(config)
    self.path = config.path

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
# end of $Id$
#------------------------------------------------------------------------------
