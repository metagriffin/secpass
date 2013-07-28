# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/25
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def resolve(spec):
  spec = spec.split('.')
  used = spec.pop(0)
  found = __import__(used)
  for cur in spec:
    used += '.' + cur
    try:
      found = getattr(found, cur)
    except AttributeError:
      __import__(used)
      found = getattr(found, cur)
  return found

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
