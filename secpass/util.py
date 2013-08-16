# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/25
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import os, re, time, random, base64
from .adict import adict
from .resolve import resolve
from .glob2re import glob2re

#------------------------------------------------------------------------------
DEFAULT_GENERATOR_MIN = 24
DEFAULT_GENERATOR_MAX = 32
DEFAULT_GENERATOR_HEX = False

#------------------------------------------------------------------------------
def resolvePath(name, rel=None):

  # TODO: use:
  #  - os.path.expanduser
  #  - os.path.expandvars
  #  - os.path.relpath

  # todo: this is pretty simplistic...
  return name.replace('~', os.environ.get('HOME', ''))

#------------------------------------------------------------------------------
truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))
def asbool(s):
  # shamelessly scrubbed from pyramid.settings:asbool
  if s is None:
    return False
  if isinstance(s, bool):
    return s
  s = str(s).strip()
  return s.lower() in truthy

#------------------------------------------------------------------------------
def zulu(ts=None, ms=True):
  '''
  Returns the specified epoch time (or current time if None or not
  provided) as an ISO 8601 string in zulu time (with millisecond
  precision), e.g. zulu(1362187446.553) => '2013-03-02T01:24:06.553Z'.
  If `ms` is True (the default), milliseconds will be included, otherwise
  truncated.
  '''
  if ts is None:
    ts = time.time()
  ms = '.%03dZ' % (ts * 1000 % 1000,) if ms else 'Z'
  return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(ts)) + ms

#------------------------------------------------------------------------------
def localtime(ts=None, ms=True):
  if ts is None:
    ts = time.time()
  ms = '.%03d' % (ts * 1000 % 1000,) if ms else ''
  return time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(ts)) + ms

#------------------------------------------------------------------------------
def generatePassword(config):
  gmin = int(config.get('generator.min', DEFAULT_GENERATOR_MIN))
  gmax = int(config.get('generator.max', DEFAULT_GENERATOR_MAX))
  glen = random.randint(gmin, gmax)
  # note: this generates more data than necessary... oh well. if i am
  # *really* bored one day, it could be fixed...
  seq = ''
  for i in range(glen):
    seq += chr(random.randint(0, 255))
  if asbool(config.get('generator.hex', DEFAULT_GENERATOR_HEX)):
    seq = seq.encode('hex')[:glen]
  else:
    seq = base64.b64encode(seq, 'Fh')[:glen]
  return seq


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
