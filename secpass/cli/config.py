# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/01/29
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

from __future__ import print_function

import os
import sys
import asset
import ConfigParser
import morph
from aadict import aadict
import formencode
from formencode import validators
import requests
import threading
import uuid
import re
import pkg_resources
import six

from secpass import engine
from secpass.util import _
from secpass.driver.spbp import GpgEnv
from secpass.driver.file import DEFAULT_PATH as FILE_DEFAULT_PATH
from secpass.driver.pgpfile import DEFAULT_PATH as PGPFILE_DEFAULT_PATH
from .base import out, ask, confirm, pause, print_options, layout, ProgramExit

OPIYUM_CERTCHAIN    = 'secpass:res/opiyum-cert-chain.pem'
OPIYUM_URL          = 'https://www.opiyum.net/secpass/'

#------------------------------------------------------------------------------
def addConfigCommand(commands, common):
  subcli = commands.add_parser(
    _('config'),
    parents=[common],
    help=_('create and/or manage secpass/secnote configuration file'))
  subcli.set_defaults(call=cmd_config)

#------------------------------------------------------------------------------

# TODO: make these 'tokens' that are then referenced by the 'en-US' locale...
helpmsg = dict()
for ast in asset.load('secpass:res/help/**.rst'):
  helpmsg[ast.name[9:-4]] = ast.read()

#------------------------------------------------------------------------------
class ConfigManager(object):

  #----------------------------------------------------------------------------
  def __init__(self, options):
    self.options   = options
    self.config    = None
    self._genv     = None
    self._crtpem   = None

  #----------------------------------------------------------------------------
  def run(self):
    self.config = engine.Config(self.options.config)
    if not self.config.exists():
      out(layout(_(helpmsg['welcome'])))
      verbose = confirm(
        _('Continue in verbose mode ("yes" or "no"; default is "yes")'),
        default=True)
      if verbose:
        out(layout(_(helpmsg['intro'])))
      self.clientSetup(show_help=verbose)
      if verbose:
        out(layout(_(helpmsg['profile-create'])))
      self.profileCreate(show_help=verbose)
    return self.mainLoop()

  #------------------------------------------------------------------------------
  def mainLoop(self):
    while True:
      if not filter(None, [
          self.getConfig('default', attr, None)
          for attr in ('locale', 'client.id', 'client.name', 'client.risk')]):
        self.clientSetup()
        continue
      if not self.getProfileIDs():
        out(layout(_(helpmsg['noprofile'])))
        self.profileCreate()
        continue

      action = self.select([
        ('show',    _('Show configured profiles')),
        ('create',  _('Add new profile')),

        # TODO: implement:
        #('update',  _('Modify profile')),
        #('delete',  _('Delete profile')),
        #('default', _('Set default profile')),
        #('move',    _('Move data between profiles')),

        ('save',    _('Save changes')),
        ('exit',    _('Exit')),
      ], default = 'show',
         title   = _('SecPass configuration action options'),
         subject = 'action')

      if action == 'show':
        options = []
        for pid in self.getProfileIDs():
          lbl = self.getConfig('profile.' + pid, 'name')
          if pid == self.getConfig('default', 'profile.default'):
            lbl = _('{name} (default)', name=lbl)
          else:
            lbl = _('{name}', name=lbl)
          options.append(lbl)
        print_options(options, title=_('Current configured profiles:'))
        continue

      if action == 'create':
        self.profileCreate()
        continue

      if action == 'save':
        self.config.save()
        continue

      if action == 'exit':
        self.exit()
        break

    return 0

  #----------------------------------------------------------------------------
  def exit(self):
    tmp = engine.Config(self.options.config)
    if not tmp.exists():
      return self.confirmExit(new=True)
    bufcur = six.StringIO()
    tmp.save(bufcur)
    bufnew = six.StringIO()
    self.config.save(bufnew)
    if bufcur.getvalue() != bufnew.getvalue():
      return self.confirmExit(new=False)
    return

  #----------------------------------------------------------------------------
  def confirmExit(self, new=False):
    if new:
      msg = _('Configuration was not saved -- save before exiting')
    else:
      msg = _('Configuration changes were not saved -- save before exiting')
    if confirm(msg, default=True):
      self.config.save()

  #----------------------------------------------------------------------------
  @property
  def genv(self):
    if self._genv is None:
      self._genv = GpgEnv(user=True).__enter__()
      # todo: what about calling __exit__?...
    return self._genv

  #----------------------------------------------------------------------------
  @property
  def crtchain(self):
    if self._crtpem is None:
      # note: using `pkg_resources` instead of `asset` since it will
      # copy the resource to the filesystem if inside an egg (since
      # the cert is being used by an external program, this is
      # required).
      self._crtpem = pkg_resources.resource_filename(*OPIYUM_CERTCHAIN.split(':'))
    return self._crtpem

  #----------------------------------------------------------------------------
  def getIdentity(self, help=None):
    keys = self.genv.gpg.list_keys(True)
    if len(keys) == 1:
      return keys[0]['fingerprint']
    if len(keys) <= 0:
      return None
    choice = self.select(
      [key['uids'][0] for key in keys],
      default=0, subject=_('encryption identity'), help=help)
    self.keyfp = keys[choice]['fingerprint']
    return self.keyfp

  #----------------------------------------------------------------------------
  def getConfig(self, section, option, default=None):
    if section in (None, 'default'):
      section = 'DEFAULT'
    try:
      return self.config.get(section, option)
    except ConfigParser.NoOptionError:
      return default

  #----------------------------------------------------------------------------
  def setConfig(self, section, option, value):
    if section in (None, 'default'):
      section = 'DEFAULT'
    self.config.set(section, option, value)

  #----------------------------------------------------------------------------
  def select(self, options, default=None, subject=None,
             title='Please choose among the following {subject} options',
             prompt='Your {subject} choice',
             help=None):
    title  = _(title, subject=subject or '')
    if default is None:
      title = layout(_('{title}:', title=title))
    else:
      title = layout(_('{title} (default marked with "*"):', title=title))
    print_options(options, title=title, default=default)
    # todo: move to use validator...
    prompt = _(prompt, subject=subject or '')
    if help is None and default is None:
      prompt = _('{prompt} (number)', prompt=prompt)
    elif help is not None and default is None:
      prompt = _('{prompt} (number or "?")', prompt=prompt)
    elif help is None and default is not None:
      prompt = _('{prompt} (number or enter for default)', prompt=prompt)
    else:
      prompt = _('{prompt} (number, "?", or enter for default)', prompt=prompt)
    while True:
      choice = ask(prompt)
      if help is not None and choice == '?':
        out(layout(_(help)))
        print_options(options, title=title, default=default)
        continue
      if default is not None and choice == '':
        return default
      try:
        choice = int(choice) - 1
      except ValueError:
        out(layout(_('Hmm. I expected a number... please try again.')))
        continue
      if choice < 0 or choice >= len(options):
        out(layout(_('Hmm. The number appears to be out of range... please try again.')))
        continue
      option = options[choice]
      if morph.isstr(option):
        return choice
      return option[0]

  #----------------------------------------------------------------------------
  def getProfileIDs(self):
    return [sec[len('profile.'):]
            for sec in self.config.sections() if sec.startswith('profile.')]

  #----------------------------------------------------------------------------
  def clientSetup(self, show_help=False):
    if show_help:
      out(layout(_(helpmsg['client-setup'])))
    if not self.getConfig('default', 'client.id'):
      self.setConfig('default', 'client.id', str(uuid.uuid4()))
    # todo: when other locales exist...
    # todo: if the locale is changed, update `_`...
    self.setConfig('default', 'locale', 'en')
    # todo: do some kind of heuristics to determine likely computer type...
    self.setConfig(
      'default', 'client.name',
      ask(_('Client name'), default=_('My Laptop Computer'),
          validator=validators.String(strip=True, not_empty=True)))
    if show_help:
      out(layout(_(helpmsg['client-setup-risk'])))
    self.setConfig(
      'default', 'client.risk',
      self.select([
        ('high-risk',     _('High (e.g. mobile device)')),
        ('medium-risk',   _('Medium (e.g. laptop, shared desktop)')),
        ('low-risk',      _('Low (e.g. secure home server)')),
        ('unbreakable',   _('Secure (e.g. detached moon vault)')),
      ], subject='risk level', default='medium-risk', help=helpmsg['client-setup-risk']))

  #------------------------------------------------------------------------------
  def profileCreate(self, show_help=False):
    if show_help:
      out(layout(_(helpmsg['profile-create-type'])))
    while True:
      res = self.select([
        ('secpass.driver.spbp',    _('Networked via the SecPass Broker Protocol')),
        ('secpass.driver.pgpfile', _('PGP-encrypted local CSV file')),
        ('secpass.driver.file',    _('Unencrypted local CSV file')),
      ], default='secpass.driver.spbp',
         subject='storage', help=helpmsg['profile-create-type'])
      if res == 'secpass.driver.file':
        if not confirm(
          _('Are you sure you want to create an *UNENCRYPTED* storage'),
          default=False):
          continue
      break
    meth = 'profileCreate_' + res.split('.')[-1]
    params = getattr(self, meth)(show_help=show_help)
    if params is None:
      return
    if show_help:
      out(layout(_(helpmsg['profile-create-name'])))
    profnames = [self.getConfig('profile.' + pid, 'name')
                 for pid in self.getProfileIDs()]
    defname = _('Personal')
    cnt = 1
    while defname in profnames:
      if cnt == 1:
        defname = _('New Profile', count=cnt)
      else:
        defname = _('New Profile ({count})', count=cnt)
      cnt += 1
    params['name'] = ask(
      _('New profile name'), default=defname,
      validator=validators.String(strip=True, not_empty=True))
    pid     = str(uuid.uuid4())
    section = 'profile.' + pid
    self.config.add_section(section)
    for key, val in params.items():
      self.setConfig(section, str(key), str(val))
    out(layout(_('Profile "{profile}" created.', profile=params['name'])))
    if len(self.getProfileIDs()) == 1:
      self.setConfig('default', 'profile.default', pid)
    return

  #----------------------------------------------------------------------------
  def profileCreate_file(self, show_help=False):
    out(layout(_(helpmsg['profile-create-options-file'])))
    path = ask(_('Path to CSV file'), default='')#FILE_DEFAULT_PATH)
    params = dict(driver='secpass.driver.file')
    if path and path != FILE_DEFAULT_PATH:
      params['driver.path'] = path
    return params

  #----------------------------------------------------------------------------
  def profileCreate_pgpfile(self, show_help=False):
    out(layout(_(helpmsg['profile-create-options-pgpfile'])))
    path = ask(_('Path to CSV+PGP file'), default='')#PGPFILE_DEFAULT_PATH)
    if show_help:
      out(layout(_(helpmsg['profile-create-encrypt-pgpfile-needkey'])))
    ident = self.getIdentity(help=helpmsg['profile-create-encrypt-pgpfile-needkey'])
    params = dict({
      'driver'          : 'secpass.driver.pgpfile',
      'driver.agent'    : 'true',
      'driver.identity' : ident,
    })
    if path and path != PGPFILE_DEFAULT_PATH:
      params['driver.path'] = path
    return params

  #----------------------------------------------------------------------------
  def profileCreate_spbp(self, show_help=False):
    if show_help:
      out(layout(_(helpmsg['profile-create-options-spbp'])))
    res = self.select([
      ('new', _('Create a new account (on Opiyum.net)')),
      ('cur', _('Use an existing SPBP-enabled account')),
    ], default='new', subject='account', help=helpmsg['profile-create-options-spbp'])
    if res == 'new':
      return self.profileCreate_spbp_new(show_help=show_help)
    return self.profileCreate_spbp_cur(show_help=show_help)

  #----------------------------------------------------------------------------
  def generateKey(self, name, email, bits=2048):
    out(layout(_(helpmsg['keygen'])))
    with GpgEnv() as genv:
      prog = None
      stop = False
      def progress():
        if not stop:
          sys.stderr.write('.')
          prog = threading.Timer(1, progress)
          prog.start()
      prog = threading.Timer(1, progress)
      prog.start()
      key = genv.gpg.gen_key(
        genv.gpg.gen_key_input(
          key_type     = 'RSA',
          key_length   = bits,
          name_real    = name,
          name_comment = '',
          name_email   = email,
        ))
      stop = True
      prog.cancel()
      sys.stderr.write('\n')
      out(_('Generated key fingerprint: {fp}', fp=key.fingerprint))
      return aadict(
        fingerprint = key.fingerprint,
        publickey   = genv.gpg.export_keys(key.fingerprint),
        privatekey  = genv.gpg.export_keys(key.fingerprint, True),
      )

  #----------------------------------------------------------------------------
  def request(self, method, url, params=None, status=None, service=None, **kw):
    if params is not None:
      kw['params'] = params
    try:
      res = requests.request(method, url, **kw)
      if status in (None, res.status_code):
        return res
      out(_('Hmm. {service} failed unexpectedly with status code {code}',
            service=service or url, code=res.status_code))
      out(_('Response body: {content}', content=res.content))
      out(_('Perhaps try again later?'))
      out()
      pause()
      return None
    except requests.exceptions.SSLError as err:
      kw['verify'] = self.crtchain
      return self.request(method, url, status=status, service=service, **kw)

  #----------------------------------------------------------------------------
  def profileCreate_spbp_new(self, show_help=False):
    if show_help:
      out(layout(_(helpmsg['profile-create-options-spbp-new'])))
    username = ask(
      _('New account email address'),
      # TODO: remove this default
      # default='mg.TODO.secpass-dev-test-' + str(uuid.uuid4())[:8] + '@metagriffin.net',
      validator=validators.Email(strip=True, not_empty=True))
    while True:
      password = ask(
        _('New account password'), echo=False,
        validator=validators.String(strip=False, not_empty=True))
      chk = ask(_('Repeat password'), echo=False)
      if password != chk:
        out(_('Passwords do not match! Please try again.'))
        continue
      break
    cid    = self.getConfig('default', 'client.id')
    cname  = self.getConfig('default', 'client.name')
    crisk  = self.getConfig('default', 'client.risk')
    locale = self.getConfig('default', 'locale')

    url = OPIYUM_URL
    res = self.request('post', url + 'register', {
      'locale'        : locale,
      'username'      : username,
      'password'      : password,
      'passwordcheck' : password,
    })
    if res.status_code == 400:
      out(_('Hmm. Opiyum.net had problems creating your account; it said:'))
      out(layout(_('{message}:', message=res.json()['message']), indent='  '))
      for fld, error in res.json()['field'].items():
        out(layout(_('{field}: {error}.', field=fld, error=error), indent='    '))
      out(_('Please try again.'))
      out()
      pause()
      return self.profileCreate_spbp_new(False)
    if res.status_code == 503:
      out(_('Unfortunately, the Opiyum.net service is currently unavailable; it said:'))
      out(layout(_('{message}', message=res.json()['message']), block=True))
      pause()
      return None
    if res.status_code != 200:
      out(_('Hmm. Opiyum.net failed unexpectedly with status code {code}',
              code=res.status_code))
      out(_('Response body: {content}', content=res.content))
      out(_('Perhaps try again later?'))
      out()
      pause()
      return None
    msg = res.json().get('message', '').strip()
    if msg:
      out(_('Message from Opiyum.net:'))
      out(layout(msg, block=True))
      pause()
    auth = (username, password)

    key = self.generateKey(cname, cid + '@cid.opiyum.net')

    if not self.request('post', url + 'client', {
      'label'      : cname,
      'publickey'  : key['publickey'],
      'profile'    : crisk,
    }, auth=auth, status=200, service='Opiyum.net'):
      return None

    if show_help:
      out(layout(_(helpmsg['profile-create-options-spbp-new-vault'])))
    vname = ask(
      _('New vault name'), default=_('Personal'),
      validator=validators.String(strip=False, not_empty=True))
    vpath = re.sub('(^-*|-*$)', '', re.sub('[^a-z0-9]+', '-', vname.lower()))
    if not vpath:
      # really drastic fallback...
      vpath = str(uuid.uuid4())

    if not self.request('post', url + 'vault', {
      'label'   : vname,
      'name'    : vpath,
      'clients' : 'all',
    }, auth=auth, status=200, service='Opiyum.net'):
      return None

    if show_help:
      out(layout(_(helpmsg['profile-create-encrypt-spbp-needkey'])))
    encfp = self.getIdentity(help=helpmsg['profile-create-encrypt-spbp-needkey'])
    if encfp is None:
      out(layout(_(helpmsg['noagent'])))
      raise ProgramExit(15)
    def encrypt(data):
      ret = self.genv.gpg.encrypt(data, encfp, armor=True, always_trust=True)
      if not ret.ok:
        # todo: do more elegant error handling...
        raise ValueError('Error: ' + str(ret.status))
      return str(ret)
    return {
      'driver'             : 'secpass.driver.spbp',
      'driver.url'         : url,
      'driver.username'    : username,
      'driver.password'    : encrypt(password),
      'driver.publickey'   : key['publickey'],
      'driver.privatekey'  : encrypt(key['privatekey']),
    }

  #----------------------------------------------------------------------------
  def profileCreate_spbp_cur(self, show_help=False):
    # TODO: implement
    out(layout(_('Unfortunately, joining an existing account is'
                 ' not implemented yet.')))
    pause()
    return None

    # url = ask(
    #   _('SPBP Server URL'),
    #   default='www.opiyum.net/secpass',
    #   validator=validators.URL(strip=True, not_empty=True, add_http=True))
    # if not validators.URL.scheme_re.match(url):
    #   url = 'https://' + url


#------------------------------------------------------------------------------
def cmd_config(options):
  # USAGE: config
  return ConfigManager(options).run()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
