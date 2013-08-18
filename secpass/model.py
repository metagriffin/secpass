# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/08/10
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

from .adict import adict

#------------------------------------------------------------------------------
class Notifier(object):
  def __init__(self, *args, **kw):
    super(Notifier, self).__init__(*args, **kw)
    self.__dict__['observers'] = []
  def on(self, eventmask, callback):
    self.__dict__['observers'].append((eventmask, callback))
  def off(self, eventmask=None, callback=None):
    raise NotImplementedError()
  def trigger(self, type, **kw):
    kw['target'] = self
    for eventmask, callback in self.__dict__['observers']:
      if eventmask == type:
        callback(adict(type=type, **kw))

#------------------------------------------------------------------------------
class PubDict(Notifier):
  def __init__(self, *args, **kw):
    super(PubDict, self).__init__(*args)
    self.__dict__['data'] = dict()
    for key, val in kw.items():
      self.__setattr__(key, val)
  def __getattr__(self, key):
    return self.__dict__['data'].get(key, None)
  def __setattr__(self, key, value, trigger=True):
    if key not in self.__dict__['data']:
      self.__dict__['data'][key] = value
      if trigger:
        self.trigger('change', key=key, value=value)
      return
    orig = self.__dict__['data'].get(key, None)
    self.__dict__['data'][key] = value
    if orig != value and trigger:
      self.trigger('change', key=key, value=value, previous=orig)
  def __delattr__(self, key, trigger=True):
    if key not in self.__dict__['data']:
      return
    orig = self.__dict__['data'].pop(key)
    if trigger:
      self.trigger('change', key=key, previous=orig)

#------------------------------------------------------------------------------
class PubList(Notifier):
  def __init__(self, *args, **kw):
    super(PubList, self).__init__(*args, **kw)
    self.list = []
  def __delslice__(self, start, end, trigger=True):
    rem = self.list.__getslice__(start, end)
    self.list.__delslice__(start, end)
    if trigger:
      for item in rem:
        self.trigger('remove', item=item)
  def append(self, item, trigger=True):
    self.list.append(item)
    if trigger:
      self.trigger('add', item=item)
  def __getitem__(self, *args, **kw):
    return self.list.__getitem__(*args, **kw)
  def __getslice__(self, *args, **kw):
    return self.list.__getslice__(*args, **kw)

#------------------------------------------------------------------------------
class EntryList(PubList):
  pass

#------------------------------------------------------------------------------
class Entry(PubDict):
  pass

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
