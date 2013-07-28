# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/27
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class Driver(object):

  def create(self, entry):
    raise NotImplementedError()

  def read(self, entry_id):
    raise NotImplementedError()

  def update(self, entry):
    raise NotImplementedError()

  def delete(self, entry_id):
    raise NotImplementedError()

  def find(self, expr=None):
    raise NotImplementedError()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
