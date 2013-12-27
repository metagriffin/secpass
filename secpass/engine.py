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

import os, os.path, logging, ConfigParser, pkg_resources
from . import api
from .util import adict, asbool, resolve

# TODO: add support for encrypting parts of the configuration file...
# todo: with the current `Profile` settings approach, you cannot specify
#       default "generator.*" settings in the "DEFAULT" section that override
#       the system defaults... this is unfortunate. fix!

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
class ConfigError(Exception): pass

#------------------------------------------------------------------------------
class Profile(api.ProxyStore):

  #----------------------------------------------------------------------------
  def __init__(self, engine, pid, settings, *args, **kw):
    super(Profile, self).__init__(*args, **kw)
    self.engine   = engine
    self.id       = pid
    self.settings = settings
    self.driver   = None

  @property
  def name(self):
    return self.settings.name

  #----------------------------------------------------------------------------
  def ready(self):
    if not self.driver:
      self.driver = self._loadDriver()
      self.proxy  = self.driver
    return self

  #----------------------------------------------------------------------------
  def _loadDriver(self):
    driver = resolve(self.settings.get('driver', api.DEFAULT_DRIVER))
    params = adict()
    for param in getattr(driver, 'PARAMS', []):
      if 'driver.' + param.name not in self.settings:
        if 'default' in param:
          params[param.name] = param.default
          continue
        raise ConfigError(
          'required configuration "driver.%s" missing in profile "%s"'
          % (param.name, self.id))
      val = self.settings['driver.' + param.name]
      if param.type == 'bool':
        params[param.name] = asbool(self.engine.resolveVars(val))
      elif param.type == 'path':
        params[param.name] = self.engine.resolvePath(val)
      else:
        params[param.name] = self.engine.resolveVars(val)
    return driver(params)

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
    ``None``, the returns the default profile.
    '''
    if profile is None:
      # todo: what if the configuration `profile.default` does not exist?
      profile = self.config.get('DEFAULT', 'profile.default')
    return self.profiles[profile].ready()

  #----------------------------------------------------------------------------
  def _loadConfig(self):
    config = ConfigParser.SafeConfigParser()
    config.optionxform = str
    config.read(self.cpath)
    firstprof = None
    for section in config.sections():
      if not section.startswith('profile.'):
        continue
      pconf = adict(config.items(section))
      pid   = section[8:]
      self.profiles[pid] = Profile(self, pid, pconf)
      if not firstprof:
        firstprof = pid
    if not config.has_option('DEFAULT', 'profile.default') and firstprof:
      log.info('setting default profile to first found profile: %s', firstprof)
      config.set('DEFAULT', 'profile.default', firstprof)
    for section in ('common',):
      if section not in config.sections():
        defcfg = ConfigParser.RawConfigParser()
        defcfg.optionxform = str
        defcfg.readfp(pkg_resources.resource_stream('secpass', 'res/config.ini'))
        config.add_section(section)
        for key, val in defcfg.items(section):
          if defcfg.has_option('DEFAULT', key) and defcfg.get('DEFAULT', key) == val:
            continue
          config.set(section, key, val)
    return config

  #----------------------------------------------------------------------------
  def resolvePath(self, path):
    path = os.path.expanduser(path)
    path = self.resolveVars(path)
    if not path.startswith('/'):
      path = os.path.join(os.path.dirname(self.cpath), path)
    return path

  #----------------------------------------------------------------------------
  def resolveVars(self, val):
    while True:
      val2 = os.path.expandvars(val)
      if val2 == val:
        return val2

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
