# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <mg.github@metagriffin.net>
# date: 2014/03/13
# copy: (C) Copyright 2014-EOT metagriffin -- see LICENSE.txt
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

import unittest

from . import base

#------------------------------------------------------------------------------
class TestLayout(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_paras(self):
    src='along came a spider.\n\nAnd sat on the wall.'
    chk='along came\na spider.\n\nAnd sat on\nthe wall.\n'
    self.assertMultiLineEqual(base.layout(src, width=10), chk)

  #----------------------------------------------------------------------------
  def test_block(self):
    src='along came a spider.\n\nAnd sat on the wall.'
    chk='\n  along came\n  a spider.\n\n  And sat on\n  the wall.\n\n'
    self.assertMultiLineEqual(base.layout(src, width=12, block=True), chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
