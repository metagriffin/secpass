# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/04/25
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import re

#------------------------------------------------------------------------------
def glob2re(pattern, exact=False):
  '''
  Converts a glob-matching pattern (using Apache Cocoon style rules)
  to a regular expression, which basically means that the following
  characters have special meanings:

  * ``?``:  matches any single character
  * ``*``:  matches zero or more characters excluding the slash ('/') character
  * ``**``: matches zero or more characters including the slash ('/') character
  * ``\``:  escape character used to precede any of the others for a literal

  todo: the backslash-escaping is not implemented.

  If `exact` is truthy, then the returned regex will include a leading
  '^' and trailing '$', meaning that the regex must match the entire
  string, from beginning to end.
  '''
  # todo: this is a poor-man's implementation... this could be
  #         a) more efficient
  #         b) implement escaping
  #         c) be more LR-parsing rigorous...

  # 'encode' the special characters into non-regex-special characters
  pattern = pattern.replace('Z', 'ZI').replace('?', 'ZQ') \
      .replace('**', 'ZA').replace('*', 'ZD')

  # escape all regex-sensitive characters
  pattern = re.escape(pattern)

  # and undo the 'encoding'
  pattern = pattern.replace('ZD', '[^/]*?').replace('ZA', '.*?') \
      .replace('ZQ', '.').replace('ZI', 'Z')

  if exact:
    return '^' + pattern + '$'
  return pattern

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
