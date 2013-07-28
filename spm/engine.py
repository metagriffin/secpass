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

#------------------------------------------------------------------------------
class ConfigError(Exception): pass

#------------------------------------------------------------------------------
class Engine(object):

  #----------------------------------------------------------------------------
  def __init__(self, config=None, section=None):
    self.cpath = config or api.DEFAULT_CONFIG
    self.section = section or api.DEFAULT_SECTION
    self.loadConfig()
    self.loadDriver()

  #----------------------------------------------------------------------------
  def loadConfig(self):
    self.config = ConfigParser.SafeConfigParser()
    self.config.optionxform = str
    self.config.read(self.cpath)
    self.settings = adict(self.config.items(self.section))

  #----------------------------------------------------------------------------
  def loadDriver(self):
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
