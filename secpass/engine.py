# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/07/28
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
import logging
import six
from six.moves import configparser as CP
from aadict import aadict
import morph
import asset
import textwrap

from . import api, util

# TODO: add support for encrypting parts of the configuration file...
# todo: with the current `Profile` settings approach, you cannot specify
#       default "generator.*" settings in the "DEFAULT" section that override
#       the system defaults... this is unfortunate. fix!

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
class ConfigError(Exception): pass

#------------------------------------------------------------------------------
def loadDriver(spec):
  drvcall = asset.symbol(spec)
  if not callable(drvcall):
    drvcall = asset.symbol(spec + '.Driver')
  return drvcall()

#------------------------------------------------------------------------------
class Profile(api.ProxyStore):

  #----------------------------------------------------------------------------
  def __init__(self, engine, pid, settings, *args, **kw):
    super(Profile, self).__init__(*args, **kw)
    self.engine   = engine
    self.id       = pid
    self.settings = settings
    self.driver   = None
    self.store    = None

  @property
  def name(self):
    return self.settings.name

  #----------------------------------------------------------------------------
  def init(self):
    if self.driver:
      return self
    self.driver = loadDriver(self.settings.get('driver', api.DEFAULT_DRIVER))
    params = aadict()
    settings = morph.pick(self.settings, prefix='driver.')
    for param in self.driver.params:
      if param.name not in settings:
        if 'default' not in param:
          raise ConfigError(
            'required configuration "driver.%s" missing in profile "%s"'
            % (param.name, self.id))
        val = param.default.replace('%(__name__)s', 'profile.' + self.id)
        params[param.name] = val
      else:
        val = settings[param.name]
      if param.type == 'bool':
        params[param.name] = morph.tobool(self.engine.resolveVars(val))
      elif param.type == 'path':
        params[param.name] = self.engine.resolvePath(val)
      else:
        params[param.name] = self.engine.resolveVars(val)
    # todo: check that all "driver.*" configs were consumed...
    self.store = self.driver.getStore(params)
    self.proxy = self.store
    return self

#------------------------------------------------------------------------------
def configNameKey(name):
  if name == 'name':
    return 5
  if name == 'locale':
    return 10
  return name

#------------------------------------------------------------------------------
class Config(object):
  '''
  A configparser.SafeConfigParser wrapper that:

  * allows blank lines to exist in option values (by inserting and
    removing a single "."  on a line by itself).

    TODO: it is insanely retarded that INI files don't have a better
    codec, so that any value (including blank lines) can be
    encoded... ugh.

  * decorates sections and options with documentation (as comments).
  '''
  def __init__(self, spec=None, load=True):
    self.spec    = spec
    self.config  = CP.SafeConfigParser()
    self.config.optionxform = str
    if self.spec and load:
      self.load(self.spec)
  def exists(self):
    return os.path.exists(self.spec)
  def load(self, src):
    if morph.isstr(src):
      self.config.read(src)
    else:
      self.config.readfp(src)
    for section in self.config.sections():
      for key, val in self.config.items(section):
        self.config.set(section, key, self._decode(val))
    for key, val in self.config.defaults().items():
      self.config.set(CP.DEFAULTSECT, key, self._decode(val))
    return self
  def save(self, dst=None):
    if dst is None or morph.isstr(dst):
      with open(dst or self.spec, 'wb') as fp:
        self._save(fp)
    else:
      self._save(dst)
    return self
  def _save(self, fp):
    # todo: i18n...
    fp.write(asset.load('secpass:res/help/config-preamble.rst').read())
    for section in [CP.DEFAULTSECT] + self.sections():
      self._saveSection(fp, section)
    fp.write(asset.load('secpass:res/help/config-epilog.rst').read())
  def _saveSection(self, fp, section):
    fp.write('\n#' + '-' * 78 + '\n[')
    # todo: escape section name?...
    fp.write(section)
    fp.write(']\n')
    # note: not using config.options() because it breaks on CP.DEFAULTSECT...
    options = [opt for opt, val in self.items(section)]
    options = sorted(options, key=configNameKey)
    for opt in options:
      self._saveOption(fp, section, opt)
  def _saveOption(self, fp, section, option):
    if section != CP.DEFAULTSECT and self.has_option(CP.DEFAULTSECT, option) \
        and self.get(CP.DEFAULTSECT, option) == self.get(section, option):
      return
    help = self._getOptionHelp(section, option)
    if help is not None:
      fp.write('\n')
      fp.write(textwrap.fill(
          '`{}`: {}'.format(option, help), width=70,
          initial_indent='# ', subsequent_indent='# '))
    fp.write('\n{:<23} = '.format(option))
    fp.write(self._encode(self.get(section, option)).replace('\n', '\n\t'))
    fp.write('\n')
  def _getOptionHelp(self, section, option):
    if section == CP.DEFAULTSECT:
      names = ['default']
    else:
      names = ['driver-base', 'default']
      if self.has_option(section, 'driver'):
        names = ['driver-' + self.get(section, 'driver').split('.')[-1]] \
          + names
    # todo: i18n...
    for name in names:
      try:
        ast = 'secpass:res/help/config-{}-{}.rst'.format(name, option)
        return asset.load(ast).read()
      except (asset.NoSuchAsset, IOError):
        continue
    return None
  def _encode(self, val):
    val = val.replace('\n.', '\n..').replace('\n\n', '\n.\n')
    if val.endswith('\n'):
      val += '.'
    return val
  def _decode(self, val):
    return val.replace('\n.', '\n')
  def __getattr__(self, attr):
    return getattr(self.config, attr)

#------------------------------------------------------------------------------
class Engine(object):

  #----------------------------------------------------------------------------
  def __init__(self, config):
    self.cpath    = config
    self.profiles = dict()
    self.config   = self._loadConfig()

  #----------------------------------------------------------------------------
  def getProfile(self, profile=None):
    '''
    Returns the specified profile (by ID or by name). If `profile` is
    ``None`` or omitted, returns the default profile.
    '''
    if profile is None:
      # todo: what if the configuration `profile.default` does not exist?
      profile = self.config.get('DEFAULT', 'profile.default')
    if profile in self.profiles:
      return self.profiles[profile].init()
    for prof in self.profiles.values():
      if prof.name == profile:
        return prof.init()
    for prof in self.profiles.values():
      if prof.name.lower() == profile.lower():
        return prof.init()
    raise KeyError(profile)

  #----------------------------------------------------------------------------
  def _loadConfig(self):
    config = Config(self.cpath)
    firstprof = None
    for section in config.sections():
      if not section.startswith('profile.'):
        continue
      pconf = aadict(config.items(section))
      pid   = section[8:]
      self.profiles[pid] = Profile(self, pid, pconf)
      if not firstprof:
        firstprof = pid
    if not config.has_option('DEFAULT', 'profile.default') and firstprof:
      log.info('setting default profile to first found profile: %s', firstprof)
      config.set('DEFAULT', 'profile.default', firstprof)
    return config

  #----------------------------------------------------------------------------
  def resolvePath(self, path):
    return util.resolvePath(path, reldir=os.path.dirname(self.cpath))

  #----------------------------------------------------------------------------
  def resolveVars(self, val):
    return util.resolveVars(val)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
