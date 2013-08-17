# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/28
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import os, os.path, ConfigParser
from . import api
from .util import adict, asbool, resolve

# TODO: add support for encrypting parts of the configuration file...

#------------------------------------------------------------------------------
class ConfigError(Exception): pass

#------------------------------------------------------------------------------
class Engine(object):

  #----------------------------------------------------------------------------
  def __init__(self, config, profile=None):
    self.cpath = config
    self.profname = profile
    self.profiles = dict()
    self.settings = None
    self._loadConfig()
    if self.settings:
      self._loadDriver()

  #----------------------------------------------------------------------------
  def switchProfile(self, profile):
    if profile not in self.profiles:
      raise ValueError('no such profile ID "%s"' % (profile,))
    if self.profname == profile:
      return self
    self.profname = profile
    self.settings = self.profiles[profile]
    self._loadDriver()
    return self

  #----------------------------------------------------------------------------
  def _loadConfig(self):
    self.config = ConfigParser.SafeConfigParser()
    self.config.optionxform = str
    self.config.read(self.cpath)
    if self.profname is None:
      try:
        self.profname = self.config.get('DEFAULT', 'profile.default')
      except ConfigParser.NoOptionError:
        self.profname = None
    for section in self.config.sections():
      if not section.startswith('profile.'):
        continue
      profile = adict(self.config.items(section))
      profile.id = section[8:]
      self.profiles[profile.id] = profile
      if not self.profname:
        self.profname = profile.id
    if not self.profname:
      return
    self.settings = self.profiles.get(self.profname, None)
    if self.settings:
      return
    for profile in self.profiles.values():
      if profile.name == self.profname:
        self.settings = profile
        return
    for profile in self.profiles.values():
      if profile.name.lower() == self.profname.lower():
        self.settings = profile
        return
    raise ConfigError('profile "%s" not found' % (self.profname,))

  #----------------------------------------------------------------------------
  def _loadDriver(self):
    driver = resolve(self.settings.get('driver', api.DEFAULT_DRIVER))
    params = adict()
    for param in getattr(driver, 'PARAMS', []):
      if 'driver.' + param.name not in self.settings:
        if 'default' in param:
          params[param.name] = param.default
          continue
        raise ConfigError('required configuration "driver.%s" missing'
                          % (param.name,))
      val = self.settings['driver.' + param.name]
      if param.type == 'bool':
        params[param.name] = asbool(self.resolveVars(val))
      elif param.type == 'path':
        params[param.name] = self.resolvePath(val)
      else:
        params[param.name] = self.resolveVars(val)
    self.driver = driver(params)

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

  #----------------------------------------------------------------------------
  def create(self, *args, **kw):    return self.driver.create(*args, **kw)
  def read(self, *args, **kw):      return self.driver.read(*args, **kw)
  def update(self, *args, **kw):    return self.driver.update(*args, **kw)
  def delete(self, *args, **kw):    return self.driver.delete(*args, **kw)
  def find(self, *args, **kw):      return self.driver.find(*args, **kw)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
