# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: metagriffin <metagriffin@uberdev.org>
# date: 2013/07/28
# copy: (C) CopyLoose 2013 UberDev <hardcore@uberdev.org>, No Rights Reserved.
#------------------------------------------------------------------------------

import sys, os.path, logging, argparse, pkg_resources
from contextlib import contextmanager
import wx
from wx import xrc, wizard
from wx.lib.wordwrap import wordwrap
import ObjectListView as OLV

from secpass import engine, api, model, util
from secpass.util import resolvePath, asbool, adict, _
from .mainwindow import MainWindow

# todo: how to make an exception open in a window instead of showing
#       on console?...
#       or does wx already take care of that, ie. on windows, it uses a dialog
#       since there is no console?

#------------------------------------------------------------------------------
log = logging.getLogger(__name__)
rootlog = logging.getLogger()
rootlog.setLevel(logging.WARNING)
rootlog.addHandler(logging.StreamHandler())
# TODO: add a logging formatter...

#------------------------------------------------------------------------------
class SecPassGui(wx.App):

  #----------------------------------------------------------------------------
  def __init__(self, config=None, profile=None, *args, **kw):
    self.pid      = profile or None
    self.config   = config or None
    self.engine   = None
    self.wxres    = None
    self.main     = MainWindow(self)

    #--------------------------------------------------------------------------
    # TODO: remove this...
    print 'TODO: remove this force-profile-to-"test"...'
    self.pid = 'test'
    # /TODO
    #--------------------------------------------------------------------------

    super(SecPassGui, self).__init__(*args, **kw)

  #----------------------------------------------------------------------------
  def OnInit(self):
    # TODO: `engine` expects a valid config... hm.
    self.engine = engine.Engine(self.config)
    try:
      self.engine.getProfile(self.pid)
    except KeyError:
      # todo: display error and switch to default profile...
      raise ValueError(_('Profile "{}" not found', self.pid))
    combined = asbool(self.engine.config.get('gui', 'combined'))
    if self.pid is None and not combined:
      self.pid = self.engine.config.get('DEFAULT', 'profile.default')
    # todo: convert to using pkg_resources...
    #         self.wxres = wx.xrc.EmptyXmlResource()
    #         self.wxres.LoadFromString( ...load... )
    #       *but*... how does loading of images, etc work?
    self.locale = self.getConfig('DEFAULT', 'locale', 'en')
    self.wxres = xrc.XmlResource(
      os.path.join(
        os.path.dirname(__file__), 'res', 'wx.%s.xrc' % (self.locale,)))
    if not self.main.init():
      return False
    if len(self.engine.profiles) <= 0:
      self.openProfileWizard()
    return True

  #----------------------------------------------------------------------------
  def getConfig(self, section, name, default=None):
    if not self.engine.config.has_option(section, name):
      return default
    return self.engine.config.get(section, name)

  #----------------------------------------------------------------------------
  def NIY(self, func):
    # TODO: remove this
    wx.MessageBox(
      _('{} not implemented yet.', func), 'Error', wx.OK|wx.ICON_ERROR)

  #----------------------------------------------------------------------------
  def OnCheckUpdate(self, e):
    # TODO: implement
    self.NIY(_('Update checking'))

  #----------------------------------------------------------------------------
  def OnPreferences(self, e):
    # TODO: implement
    self.NIY(_('Preferences'))

  #----------------------------------------------------------------------------
  def OnHelp(self, e):
    # todo: get the homepage url from setup.py...
    url = 'http://github.com/metagriffin/secpass'
    if not wx.LaunchDefaultBrowser(url):
      wx.MessageBox(_('Your browser could not be launched - please go to'
                      ' "{}" manually to get SecPass help content.', url))

  #----------------------------------------------------------------------------
  def openProfileWizard(self):
    # todo: check self.engine.profiles to see if this is the first
    # profile, and if so, add a little more explanation...
    wizard = self.wxres.LoadObject(None, 'wizard.profile', 'wxWizard')
    wizard.RunWizard(wx.xrc.XRCCTRL(wizard, 'wizardpage.generic'))
    wizard.Destroy()
    # TODO: add the profile to the engine...
    # TODO: notify all dependent systems of the new profile...
    #   self.engine.profiles.trigger('add', profile)...

  #----------------------------------------------------------------------------
  def OnQuit(self, e):
    return self.main.close()

  #----------------------------------------------------------------------------
  def OnAbout(self, e):
    # todo: any way to get the url, copyright, description, etc from
    #       setup.py (beyond just the version)?...
    pkg = pkg_resources.require('secpass')[0]
    info = wx.AboutDialogInfo()
    info.Name        = _('Secure Passwords')
    info.Version     = pkg.version
    info.Copyright   = _('Copyright (C) {}-{} {}', '2013', 'EOT', 'metagriffin')
    info.Description = wordwrap(
      _('Helping you very securely manage very secure credentials since 2013'
        ' (street cred optional).'),
      350, wx.ClientDC(self.main.frame)) \
      + '\n\n' \
      + 'SecPass/' + info.Version + '\n' \
      + 'ObjectListView/' + OLV.__version__ + '\n' \
      + 'wxPython/' + wx.VERSION_STRING + '\n' \
      + 'Python/' + sys.version.split()[0] + '\n'
    info.WebSite     = ('http://github.com/metagriffin/secpass',
                        _('Official Website'))
    info.Developers  = ('metagriffin <metagriffin@uberdev.org>',)
    info.Artists     = ('metagriffin <metagriffin@uberdev.org>',)
    # todo: how to fetch this using pkg_resources?...
    # todo: use a better re-formatting system...
    text = open(
      os.path.join(os.path.dirname(__file__), '..', '..', 'LICENSE.txt'),
      'rb').read()
    text = text.replace('\n\n', '[REALNEWLINEREALNEWLINEREALNEWLINE]')
    text = text.replace('\n', ' ')
    text = text.replace('[REALNEWLINEREALNEWLINEREALNEWLINE]', '\n\n')
    info.License     = wordwrap(text, 350,wx.ClientDC(self.main.frame))
    wx.AboutBox(info)

#------------------------------------------------------------------------------
def main(argv=None):

  defconf = os.environ.get('SECPASS_CONFIG', api.DEFAULT_CONFIG)

  cli = argparse.ArgumentParser(
    description = _('Secure Passwords Graphical User Interfale'),
    )

  cli.add_argument(
    '-v', '--verbose',
    action='count', default=0,
    help=_('increase verbosity (can be specified multiple times)'))

  cli.add_argument(
    '-c', '--config', metavar='FILENAME',
    default=defconf,
    help=_('configuration filename (default: "{}")', '%(default)s'))

  cli.add_argument(
    '-p', '--profile', metavar='PROFILE',
    help=_('configuration profile id or name (defaults to configuration)'))

  options = cli.parse_args(args=argv)

  if options.verbose == 1:
    rootlog.setLevel(logging.INFO)
  elif options.verbose > 1:
    rootlog.setLevel(logging.DEBUG)

  options.config = resolvePath(options.config)

  gui = SecPassGui(config=options.config, profile=options.profile)
  gui.MainLoop()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
