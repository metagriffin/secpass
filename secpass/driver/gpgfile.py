# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/27
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

# TODO: fix this so that i am not buffering in memory so much...

import os, copy
from StringIO import StringIO
from contextlib import contextmanager
import gnupg
from . import file
from .file import FileDriver
from secpass.util import adict

#------------------------------------------------------------------------------
DEFAULT_PATH = file.DEFAULT_PATH + '.gpg'
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
class GpgFileDriver(FileDriver):

  PARAMS = newdefpath(file.FileDriver.PARAMS) + (
    adict(name='agent', type='bool', default=True),
    adict(name='identity', type='str', default=None),
    )

  #----------------------------------------------------------------------------
  def __init__(self, config):
    super(GpgFileDriver, self).__init__(config)
    self.gpg  = gnupg.GPG(use_agent=config.agent)
    self.rcpt = config.identity or None

  #----------------------------------------------------------------------------
  def openReadStream(self):
    if not os.path.isfile(self.path):
      return self.openEmptyReadStream()
    with super(GpgFileDriver, self).openReadStream() as fp:
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
      raise DecryptionError('is identity "%s" loaded in your GPG agent?'
                            % (self.rcpt,))
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
    crypt = self.gpg.encrypt(buf, self.rcpt)
    if not crypt.ok:
      raise EncryptionError('is identity "%s" loaded in your GPG agent?'
                            % (self.rcpt,))
    encbuf = str(crypt)
    # do a round-trip decryption to ensure that no data was lost...
    with self.openDecryptStream(StringIO(encbuf)) as fp:
      assert fp.read() == buf
    with super(GpgFileDriver, self).openWriteStream() as fp:
      fp.write(encbuf)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
