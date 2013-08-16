# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/27
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class LimitExceeded(Exception): pass
class EntryNotFound(Exception): pass
class IntegrityError(Exception): pass

#------------------------------------------------------------------------------
DEFAULT_CONFIG          = '~/.config/secpass/config.ini'
DEFAULT_SECTION         = 'default'
DEFAULT_DRIVER          = 'file'

#------------------------------------------------------------------------------
class Sequence(object):
  def __init__(self, sid, *args, **kw):
    super(Sequence, self).__init__(*args, **kw)

Sequence.CURRENT = Sequence('current')
Sequence.ALL     = Sequence('all')

#------------------------------------------------------------------------------
class Entry(object):

  PROFILE_ITEMS = ('service', 'role', 'password', 'notes')

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
  def __repr__(self):
    return '<secpass.Entry %r>' % ({
      k: v for k, v in self.__dict__.items() if k != 'password'})

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
