================
Secure Passwords
================

.. WARNING::

  2013/08/16: `Secure Passwords` (package ``secpass``) is currently
  under active development, i.e. it is not ready for use. Unless you
  like living on the edge, of course. So, until further notice,
  secpass is explicitly in "beta", functionally incomplete, and you
  should only use it if you make lots of backups and don't mind losing
  data. Cheers!


TL;DR
=====

If you only want the command-line `secpass` program:

.. code-block:: bash

  $ pip install secpass
  $ secpass --help

If you want the GUI, things (unfortunately) get a bit more
complicated.

For Windows and Mac users, install the wxPython 2.9 with python 2.7
binaries linked to from http://wxpython.org/download.php, then skip to
the paragraph "Then, for all platforms".

For Linux, things get even more complicated (surprise!)... you need to
install from source (sorry!):

.. code-block:: bash

  sudo apt-get install libwxgtk2.8-dev libgconf2-dev libgtk2.0-dev
  sudo apt-get install libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev
  wget http://downloads.sourceforge.net/wxpython/wxPython-src-2.9.4.0.tar.bz2
  wget http://downloads.sourceforge.net/project/wxpython/wxPython/2.9.4.0/wxPython-src-2.9.4.1.patch
  tar xvjf wxPython-src-2.9.4.0.tar.bz2
  cd wxPython-src-2.9.4.0
  patch -p0 < ../wxPython-src-2.9.4.1.patch
  cd wxPython

  # if installing globally:
  #   ==> warning: compiling wxpython can take 30+ minutes... whoa!
  python build-wxpython.py --build_dir=../bld --install

  # if installing into a virtualenv:
  #   ==> warning: compiling wxpython can take 30+ minutes... whoa!
  python build-wxpython.py --build_dir=../bld --prefix=$VIRTUAL_ENV --install
  export LD_LIBRARY_PATH=$VIRTUAL_ENV/lib

TODO: there has *got* to be a better way than building from source!...

TODO: it would be great to build wxwidgets as a static library (that way
LD_LIBRARY_PATH would not be needed), but --disable-shared broke... with

::

  /usr/bin/ld: .../lib/libwx_baseu_net-2.9.a(netlib_fs_inet.o): relocation R_X86_64_32 against `_ZN26wxFileSystemInternetModule12ms_classInfoE' can not be used when making a shared object; recompile with -fPIC
  .../lib/libwx_baseu_net-2.9.a: could not read symbols: Bad value
  collect2: error: ld returned 1 exit status
  error: command 'g++' failed with exit status 1
  ERROR: failed building wxPython.

Then, for all platforms:

.. code-block:: bash

  $ pip install secpass
  $ secpass-gui &

Overview
========

TODO: add docs
