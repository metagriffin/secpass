# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/28
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import os, os.path, logging, ConfigParser
from . import api
from .util import adict, asbool, resolve

# TODO: add support for encrypting parts of the configuration file...

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
class ConfigError(Exception): pass

#------------------------------------------------------------------------------
class Profile(object):

  #----------------------------------------------------------------------------
  def __init__(self, engine, pid, settings):
    self.engine   = engine
    self.id       = pid
    self.settings = settings
    self.driver   = None

  #----------------------------------------------------------------------------
  def create(self, *args, **kw):    return self.driver.create(*args, **kw)
  def read(self, *args, **kw):      return self.driver.read(*args, **kw)
  def update(self, *args, **kw):    return self.driver.update(*args, **kw)
  def delete(self, *args, **kw):    return self.driver.delete(*args, **kw)
  def find(self, *args, **kw):      return self.driver.find(*args, **kw)

  #----------------------------------------------------------------------------
  def ready(self):
    if not self.driver:
      self._loadDriver()
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
    self.driver = driver(params)

#------------------------------------------------------------------------------
class Engine(object):

  #----------------------------------------------------------------------------
  def __init__(self, config):
    self.cpath    = config
    self.profiles = dict()
    self._loadConfig()

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
    self.config = ConfigParser.SafeConfigParser()
    self.config.optionxform = str
    self.config.read(self.cpath)
    firstprof = None
    for section in self.config.sections():
      if not section.startswith('profile.'):
        continue
      pconf = adict(self.config.items(section))
      pid   = section[8:]
      self.profiles[pid] = Profile(self, pid, pconf)
      if not firstprof:
        firstprof = pid
    if not self.config.has_option('DEFAULT', 'profile.default') and firstprof:
      log.info('setting default profile to first found profile: %s', firstprof)
      self.config.set('DEFAULT', 'profile.default', firstprof)

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
