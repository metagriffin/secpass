# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/04/27
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

# TODO: fix this so that i am not buffering in memory so much...

import os, copy
from StringIO import StringIO
from contextlib import contextmanager
import gnupg
from aadict import aadict

from . import file
from secpass.util import _

#------------------------------------------------------------------------------
DEFAULT_PATH = file.DEFAULT_PATH + '.pgp'
class EncryptionError(Exception): pass
class DecryptionError(Exception): pass

#------------------------------------------------------------------------------
def newdefpath(params):
  params = copy.deepcopy(params)
  for param in params:
    if param.name == 'path':
      param.default = DEFAULT_PATH
  return params

#------------------------------------------------------------------------------
class Store(file.Store):

  #----------------------------------------------------------------------------
  def __init__(self, driver, config, *args, **kw):
    super(Store, self).__init__(driver, config, *args, **kw)
    self.gpg  = gnupg.GPG(use_agent=config.agent, gnupghome=config.gpghome)
    self.rcpt = config.identity or None

  #----------------------------------------------------------------------------
  def openReadStream(self):
    if not os.path.isfile(self.path):
      return self.openEmptyReadStream()
    with super(Store, self).openReadStream() as fp:
      # note: can't simply do this:
      #         return self.openDecryptStream(fp)
      #       because the context is closed (and therefore the
      #       stream) before `openDecryptStream` has a chance to
      #       read it...
      return self.openDecryptStream(StringIO(fp.read()))

  #----------------------------------------------------------------------------
  @contextmanager
  def openDecryptStream(self, fp):
    crypt = self.gpg.decrypt_file(fp)
    if not crypt.ok:
      raise DecryptionError(
        _('Is identity "{}" loaded in your GPG agent?', self.rcpt,))
    yield StringIO(str(crypt))

  #----------------------------------------------------------------------------
  @contextmanager
  def openWriteStream(self):
    # todo: it would be better to encrypt on the fly... but gnupg makes
    #       that difficult. as a result, write errors occur only *after*
    #       all records have been serialized, buffered, and encrypted...
    buf = StringIO()
    yield buf
    buf = buf.getvalue()
    crypt = self.gpg.encrypt(buf, self.rcpt, always_trust=True)
    if not crypt.ok:
      raise EncryptionError(
        _('Is identity "{}" loaded in your GPG agent?', self.rcpt))
    # todo: is this 'str()' safe for binary data?... perhaps
    #       just use `crypt.data`?...
    encbuf = str(crypt)
    # do a round-trip decryption to ensure that no data was lost...
    with self.openDecryptStream(StringIO(encbuf)) as fp:
      assert fp.read() == buf
    with super(Store, self).openWriteStream() as fp:
      fp.write(encbuf)

#------------------------------------------------------------------------------
class Driver(file.Driver):

  name = 'Encrypted CSV File Storage'

  #----------------------------------------------------------------------------
  def __init__(self, *args, **kw):
    super(Driver, self).__init__(*args, **kw)
    self.params = newdefpath(self.params) + (
      aadict(label=_('Use GPG agent'), name='agent', type='bool', default=True),
      aadict(label=_('Identity'), name='identity', type='str', default=None),
    )

  #----------------------------------------------------------------------------
  def getStore(self, config):
    return Store(self, config)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
