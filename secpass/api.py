# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2013/04/27
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

import morph

#------------------------------------------------------------------------------
class LimitExceeded(Exception): pass
class EntryNotFound(Exception): pass
class IntegrityError(Exception): pass

#------------------------------------------------------------------------------
DEFAULT_CONFIG          = '~/.config/secpass/config.ini'
DEFAULT_DRIVER          = 'file'

#------------------------------------------------------------------------------
class Sequence(object):
  def __init__(self, sid, *args, **kw):
    super(Sequence, self).__init__(*args, **kw)

Sequence.CURRENT = Sequence('current')
Sequence.ALL     = Sequence('all')

#------------------------------------------------------------------------------
class Entry(object):

  ATTRIBUTES = ('service', 'role', 'password', 'notes')

  # TODO: move `created`, `updated` and `lastused` to here?...

  #----------------------------------------------------------------------------
  def __init__(self,
               id=None, seq=0,
               service=None, role=None, password=None, notes=None,
               *args, **kw):
    super(Entry, self).__init__(*args, **kw)
    self.id       = id or None
    self.seq      = int(seq)
    self.service  = service or None
    self.role     = role or None
    self.password = password or None
    self.notes    = notes or None

  #----------------------------------------------------------------------------
  def update(self, *args, **kw):
    for k, v in morph.pick(dict(*args, **kw), *self.ATTRIBUTES).items():
      setattr(self, k, v)
    return self

  #----------------------------------------------------------------------------
  def asdict(self):
    return dict(self.__dict__)

  #----------------------------------------------------------------------------
  def __repr__(self):
    return '<secpass.Entry %r>' % ({
      k: v for k, v in self.__dict__.items() if k != 'password'})


#------------------------------------------------------------------------------
class Store(object):

  #----------------------------------------------------------------------------
  def create(self, entry):
    '''
    Create a new entry -- returns a fully qualified Entry object (with
    valid ID, timestamps, etc).
    '''
    raise NotImplementedError()

  #----------------------------------------------------------------------------
  def find(self, expr=None):
    '''
    Returns a list of all entries (with passwords removed) in this
    Store that match the specified search expression `expr`. If `expr`
    is None or empty, all entries are returned. If the password for
    a given entry is required, use :meth:`read`.
    '''
    raise NotImplementedError()

  #----------------------------------------------------------------------------
  def read(self, entry_id):
    '''
    Returns the full entry, including password, matching the specified
    `entry_id`. Note that this may modify the underlying storage to
    update the `lastused` field.
    '''
    raise NotImplementedError()

  #----------------------------------------------------------------------------
  def update(self, entry):
    '''
    Update all the attributes of the given `entry`.
    '''
    raise NotImplementedError()

  #----------------------------------------------------------------------------
  def modify(self, entry_id, **kw):
    '''
    Incremental version of :meth:`update`: instead of updating all
    attributes of the entry to the specified values, this method only
    updates the specified keywords. Returns True on success, or raises
    an exception on failure.

    Note: the default implementation assumes fast and sequential access
    and reads the current version, updates the specified values, and
    calls :meth:`update`.
    '''
    entry = self.read(entry_id)
    for k, v in kw.items():
      setattr(entry, k, v)
    self.update(entry)
    return True

  #----------------------------------------------------------------------------
  def delete(self, entry_id):
    '''
    Removes the entry identified by `entry_id` from this storage
    engine.
    '''
    raise NotImplementedError()

#------------------------------------------------------------------------------
class ProxyStore(Store):

  #----------------------------------------------------------------------------
  def __init__(self, proxy=None, *args, **kw):
    super(ProxyStore, self).__init__(*args, **kw)
    self.proxy = proxy

  #----------------------------------------------------------------------------
  def create(self, *args, **kw):    return self.proxy.create(*args, **kw)
  def read(self, *args, **kw):      return self.proxy.read(*args, **kw)
  def update(self, *args, **kw):    return self.proxy.update(*args, **kw)
  def modify(self, *args, **kw):    return self.proxy.modify(*args, **kw)
  def delete(self, *args, **kw):    return self.proxy.delete(*args, **kw)
  def find(self, *args, **kw):      return self.proxy.find(*args, **kw)


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
