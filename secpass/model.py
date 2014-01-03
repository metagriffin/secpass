# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/08/10
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

from aadict import aadict

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
        callback(aadict(type=type, **kw))

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

    # TODO: this is *terrible*... the problem is that the GUI is given
    #       the value '-' when the password is not available... thus if
    #       the user makes a no-change change (ie. double clicks on the
    #       password but does not change it, then we effectively set the
    #       password to '-', which is clearly NOT the intended effect).
    if key == 'password' and value == '-' and \
        self.__dict__['data'].get(key, None) is None:
      return
    # /TODO

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
  def __repr__(self):
    return '<secpass.model.Entry %r>' % ({
      k: v for k, v in self.__dict__.items() if k != 'password'})

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
