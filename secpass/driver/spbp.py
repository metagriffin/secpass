# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/01/03
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

import os
import morph
from aadict import aadict
import json
from requests.auth import AuthBase, HTTPBasicAuth
import requests
import gnupg
import tempfile
import shutil
import time
import logging
from six.moves import urllib
import base64

from secpass import api
from secpass.util import _

# TODO: move to using a PID-lifetime-persistent spbp GPG dir?...
#       ==> but make sure that the keys are password-protected then.

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

class RemoteError(api.DriverError): pass

#------------------------------------------------------------------------------
class GpgEnv():
  def __enter__(self):
    self.gpgdir = tempfile.mkdtemp(prefix='secpass-spbp-gpgdir.')
    self.gpg = gnupg.GPG(gnupghome=self.gpgdir)
    return self
  def __exit__(self, type, value, tb):
    shutil.rmtree(self.gpgdir)
    return False

#------------------------------------------------------------------------------
def signData(privkey, data):
  with GpgEnv() as genv:
    genv.gpg.import_keys(privkey)
    res = genv.gpg.sign(data, clearsign=False, detach=True, binary=True)
    return base64.b64encode(res.data)

#------------------------------------------------------------------------------
def q(data):
  return urllib.parse.quote(str(data))

#------------------------------------------------------------------------------
class Entry(api.Entry):

  #----------------------------------------------------------------------------
  @staticmethod
  def fromJson(data):
    ret = Entry()
    for key, value in data.items():
      setattr(ret, key, value)
    return ret

#------------------------------------------------------------------------------
class Driver(api.Store, AuthBase):

  PARAMS = (
    aadict(
      label=_('Server URL'), name='url', type='str',
      placeholder='https://opiyum.net/secpass/vault/NAME',
      help=_('The remote server URL that stores this vault\'s data (must'
             ' support the SPBP protocol version 1.0 or better)')),
    aadict(label=_('Username'), name='username', type='str'),
    aadict(label=_('Password (PGP-encrypted)'), name='password', type='pgp(str)'),
    aadict(label=_('Public key'), name='publickey', type='str'),
    aadict(label=_('Private key (PGP-encrypted)'), name='privatekey', type='pgp(str)'),
    aadict(label=_('Nonce tracker'), name='nonce', type='path', default=None),
    ## todo: ensure that these defaults are evaluated within a ConfigParser context...
    aadict(label=_('Peer database'), name='peerdb', type='path', default='%(__name__)s.peers.db'),
  )

  FIELDS = ('id', 'seq', 'created', 'updated', 'lastused', 'deleted') \
    + api.Entry.ATTRIBUTES

  #----------------------------------------------------------------------------
  def __init__(self, config, *args, **kw):
    super(Driver, self).__init__(*args, **kw)
    self.url        = config.url
    self.username   = config.username
    # note: the password here is stored pgp-encrypted in memory and
    #       decrypted on the fly whenever the password is needed. for
    #       that reason, it is highly recommended to use gpg-agent!...
    self.password   = config.password
    self.peerdb     = config.peerdb
    self.publickey  = config.publickey
    self.privatekey = config.privatekey
    self.nonce      = config.nonce

    # todo: move to using a PID-lifetime-persistent spbp GPG dir?...
    with GpgEnv() as genv:
      res = genv.gpg.import_keys(self.publickey)
      assert res.count == 1
      self.fingerprint = res.fingerprints[0]

    # TODO: load this from self.peerdb...
    self.peerfps = [self.fingerprint]
    self.peerkeys = [self.publickey]

    # TODO: get `use_agent` from the config....
    self.gpg  = gnupg.GPG(use_agent=True)

  #----------------------------------------------------------------------------
  def getPassword(self):
    data = self.gpg.decrypt(self.password)
    if not data.ok:
      raise api.DriverError(
        _('Could not decrypt password - is your GPG agent configured correctly?'))
    return data.data

  #----------------------------------------------------------------------------
  def getPrivateKey(self):
    data = self.gpg.decrypt(self.privatekey)
    if not data.ok:
      raise api.DriverError(
        _('Could not encrypt password - is your GPG agent configured correctly?'))
    return data.data

  #----------------------------------------------------------------------------
  def decrypt(self, data):
    if data is None:
      return data
    with GpgEnv() as genv:
      # todo: check return...
      res  = genv.gpg.import_keys(self.getPrivateKey())
      # TODO: do key referencing...
      data = genv.gpg.decrypt(data)
      if not data.ok:
        # todo: extract error information....
        raise api.DriverError(
          _('Could not decrypt data - has this client been added to the vault?'))
      return data.data

  #----------------------------------------------------------------------------
  def encrypt(self, data):
    if data is None:
      return data
    with GpgEnv() as genv:
      for key in self.peerkeys:
        # todo: check return...
        res  = genv.gpg.import_keys(key)
      # TODO: do key referencing...
      data = genv.gpg.encrypt(data, self.peerfps, always_trust=True, armor=True)
      if not data.ok:
        # todo: extract error information...
        raise api.DriverError(
          _('Could not encrypt data - has this client been added to the vault?'))
      return data.data

  #----------------------------------------------------------------------------
  def j2e(self, data):
    entry = Entry.fromJson(data)
    entry.password = self.decrypt(entry.password)
    return entry

  #----------------------------------------------------------------------------
  def e2j(self, entry):
    data = morph.pick(entry, *api.Entry.ATTRIBUTES)
    data['password'] = self.encrypt(data.get('password'))
    return data

  #----------------------------------------------------------------------------
  def getNonce(self, autoincrement=True):
    if self.nonce is None:
      return time.time()
    if not os.path.exists(os.path.dirname(self.nonce)):
      os.makedirs(os.path.dirname(self.nonce))
    mode = 'r+b' if os.path.exists(self.nonce) else 'w+b'
    with open(self.nonce, mode) as fp:
      try:
        cur = int(fp.read().strip())
      except ValueError:
        cur = 0
      if not autoincrement:
        return cur
      cur += 1
      fp.seek(0)
      fp.write(str(cur) + '\n')
    return cur

  #----------------------------------------------------------------------------
  def __call__(self, req):
    req = HTTPBasicAuth(self.username, self.getPassword())(req)
    auth = 'SPBP-SIGN v=0;f={fp};n={nonce};t={ts}'.format(
      fp=q(self.fingerprint), nonce=q(self.getNonce()), ts=time.time())
    sdata = '\n'.join([req.url, req.body or '', auth])
    auth += ';s=' + q(signData(self.getPrivateKey(), sdata))
    req.headers['x-spbp-authorization'] = auth
    return req

  #----------------------------------------------------------------------------
  def _request(self, path=None, method='get', data=None):
    data = json.dumps(data) if data is not None else None
    path = self.url + ( path or '' )
    auth = (self.username, self.password)
    hdrs = {'content-type': 'application/json'}
    res = getattr(requests, method)(path, data=data, auth=self, headers=hdrs)
    try:
      res.raise_for_status()
    except requests.exceptions.RequestException as err:
      log.debug('spbp request error: %s (%s)', err, res.text)
      msg = None
      try:
        msg = res.json()['message']
      except ValueError:
        msg = None
      if msg is None:
        raise err
      raise RemoteError(msg)
    return res.json()

  #----------------------------------------------------------------------------
  def create(self, entry):
    return self.j2e(
      self._request('/entry', method='post', data=self.e2j(entry)))

  #----------------------------------------------------------------------------
  def find(self, expr=None):
    return [self.j2e(entry)
            for entry in self._request('/entry',
                                       data=dict(q=expr) if expr else None)]

  #----------------------------------------------------------------------------
  def read(self, entry_id):
    return self.j2e(self._request('/entry/' + entry_id))

  #----------------------------------------------------------------------------
  def update(self, entry):
    return self.j2e(
      self._request('/entry/' + entry.id, method='put', data=self.e2j(entry)))

  #----------------------------------------------------------------------------
  def delete(self, entry_id):
    assert self._request('/entry/' + entry_id, method='delete') == dict()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
