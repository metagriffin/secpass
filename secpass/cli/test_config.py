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
import fso
import six
import ConfigParser
from aadict import aadict
import __builtin__
import uuid
import gettext
import morph
import requests
import json
import getpass

from . import base, config

#------------------------------------------------------------------------------

for key in config.helpmsg.keys():
  config.helpmsg[key] = '{{' + key + '}}'

#------------------------------------------------------------------------------
# todo: use `stub` package instead?...
class StubbedGpg(object):
  def list_keys(self, secret=False):
    return [
      dict(fingerprint='stubkey-1-fp', uids=['stubkey-1-uid-1']),
      dict(fingerprint='stubkey-2-fp', uids=['stubkey-2-uid-1']),
    ]
  def encrypt(self, data, fingerprint, sign=None, always_trust=False,
              passphrase=None, symmetric=False, armor=True, output=None):
    class Msg:
      ok = True
      def __str__(self):
        return 'FAKE-ENC(%s,%s)' % (fingerprint, data)
    return Msg()

  # def gen_key_input(self, *args, **kw):
  #   return None
  # def gen_key(self, *args, **kw):
  #   return {
  #     'fingerprint': 'DCBEB0DA3B7D5E32EEB77D50BA4CA5F9A0BFAC9A',
  #     'publickey': '-----BEGIN PGP PUBLIC KEY BLOCK-----\nVersion: GnuPG v1.4.11 (GNU/Linux)\n\nmI0EUva0lAEEAL3IHje1AwCpM6iE7o+40sPgeOjpx+iMVRdPg67cwzBDqx9pGwMm\nKLT7zSLNe5EuiQlI6L7TGmbFyzn9tDUucsuyKZV0ygpmc9nPlvAeL2aL0VMLrxJc\nEzpIDLRjnFUGPBqJPdhZsDP/LlEzoAKyQERrbBS5C40o6zwwbWTCBG3LABEBAAG0\nKWZvbyAoR2VuZXJhdGVkIGJ5IGdudXBnLnB5KSA8Zm9vQGZvby5jb20+iLgEEwEC\nACIFAlL2tJQCGy8GCwkIBwMCBhUIAgkKCwQWAgMBAh4BAheAAAoJELpMpfmgv6ya\n0EwEAJI7WnBvARb3A9pcCHpuOu0pwNBz0CpVbXtZcZjlYDOl8g4eHGCi7dqgFt3G\noP6M+nJsmAg9DJ99TMGkJa48PLlPa2bPdU0xA58mIggsl5Dsa6a4eY/rnBbn0aFy\nYBc6nlsT8vueDey6Q1fE5MWrUBRXqLS1LVzlsuyf6MMsk9Fv\n=WtFv\n-----END PGP PUBLIC KEY BLOCK-----\n',
  #     'privatekey': '-----BEGIN PGP PRIVATE KEY BLOCK-----\nVersion: GnuPG v1.4.11 (GNU/Linux)\n\nlQHYBFL2tJQBBAC9yB43tQMAqTOohO6PuNLD4Hjo6cfojFUXT4Ou3MMwQ6sfaRsD\nJii0+80izXuRLokJSOi+0xpmxcs5/bQ1LnLLsimVdMoKZnPZz5bwHi9mi9FTC68S\nXBM6SAy0Y5xVBjwaiT3YWbAz/y5RM6ACskBEa2wUuQuNKOs8MG1kwgRtywARAQAB\nAAP5ASK47Oa+5AVJ2K4kSqTgUf6+X8/CUVBsU+2MYVf9169CpLdOy5KHYindkjc+\nOuIB55XRmrli/47FxrePbqqz/M8UBvPW0WR7Vkhq+V5nF50Jl5RsCWOGRUr1W2Yx\nV+GVAhrbNd7JPtg6eK3REc4aMldyX6M216J+wtBaNZlRsRECAM9J9nWI+JecHCYG\neWVVsJ4LMQajdQ4o48UfcSaoNonnMcqeEVLmD7eeeKluURGKAOGiYC+2crzX01Oh\nJMb2jfECAOpg9gNt9d53728Uyq9pGE5AdAsruXFjVLrcDow3okm0T6WA8t/DvwGd\n1RZ9On3JcuFWiusngcbhfM6jl29i63sB/25YBOqKPWs5U/shGLHy9PgKeVFi0O4A\noobSZNky68/hVc5DRzqQzyXJcO85Egr2DJdTY+EQ2A/mhaatTZ4p3yqlYbQpZm9v\nIChHZW5lcmF0ZWQgYnkgZ251cGcucHkpIDxmb29AZm9vLmNvbT6IuAQTAQIAIgUC\nUva0lAIbLwYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AACgkQukyl+aC/rJrQTAQA\nkjtacG8BFvcD2lwIem467SnA0HPQKlVte1lxmOVgM6XyDh4cYKLt2qAW3cag/oz6\ncmyYCD0Mn31MwaQlrjw8uU9rZs91TTEDnyYiCCyXkOxrprh5j+ucFufRoXJgFzqe\nWxPy+54N7LpDV8TkxatQFFeotLUtXOWy7J/owyyT0W8=\n=615M\n-----END PGP PRIVATE KEY BLOCK-----\n',
  #   }
  # def export_keys(self, fp, private=False):
  #   ...

class StubbedGpgEnv(object):
  def __init__(self, *args, **kw):
    self.gpg = StubbedGpg()
  def __enter__(self):
    return self
  def __exit__(self, type, value, tb):
    return False
config.GpgEnv = StubbedGpgEnv

#------------------------------------------------------------------------------
def stubbed_generateKey(self, name, email, bits=2048):
  return {
    'fingerprint': 'DCBEB0DA3B7D5E32EEB77D50BA4CA5F9A0BFAC9A',
    'publickey': '-----BEGIN PGP PUBLIC KEY BLOCK-----\nVersion: GnuPG v1.4.11 (GNU/Linux)\n\nmI0EUva0lAEEAL3IHje1AwCpM6iE7o+40sPgeOjpx+iMVRdPg67cwzBDqx9pGwMm\nKLT7zSLNe5EuiQlI6L7TGmbFyzn9tDUucsuyKZV0ygpmc9nPlvAeL2aL0VMLrxJc\nEzpIDLRjnFUGPBqJPdhZsDP/LlEzoAKyQERrbBS5C40o6zwwbWTCBG3LABEBAAG0\nKWZvbyAoR2VuZXJhdGVkIGJ5IGdudXBnLnB5KSA8Zm9vQGZvby5jb20+iLgEEwEC\nACIFAlL2tJQCGy8GCwkIBwMCBhUIAgkKCwQWAgMBAh4BAheAAAoJELpMpfmgv6ya\n0EwEAJI7WnBvARb3A9pcCHpuOu0pwNBz0CpVbXtZcZjlYDOl8g4eHGCi7dqgFt3G\noP6M+nJsmAg9DJ99TMGkJa48PLlPa2bPdU0xA58mIggsl5Dsa6a4eY/rnBbn0aFy\nYBc6nlsT8vueDey6Q1fE5MWrUBRXqLS1LVzlsuyf6MMsk9Fv\n=WtFv\n-----END PGP PUBLIC KEY BLOCK-----\n',
    'privatekey': '-----BEGIN PGP PRIVATE KEY BLOCK-----\nVersion: GnuPG v1.4.11 (GNU/Linux)\n\nlQHYBFL2tJQBBAC9yB43tQMAqTOohO6PuNLD4Hjo6cfojFUXT4Ou3MMwQ6sfaRsD\nJii0+80izXuRLokJSOi+0xpmxcs5/bQ1LnLLsimVdMoKZnPZz5bwHi9mi9FTC68S\nXBM6SAy0Y5xVBjwaiT3YWbAz/y5RM6ACskBEa2wUuQuNKOs8MG1kwgRtywARAQAB\nAAP5ASK47Oa+5AVJ2K4kSqTgUf6+X8/CUVBsU+2MYVf9169CpLdOy5KHYindkjc+\nOuIB55XRmrli/47FxrePbqqz/M8UBvPW0WR7Vkhq+V5nF50Jl5RsCWOGRUr1W2Yx\nV+GVAhrbNd7JPtg6eK3REc4aMldyX6M216J+wtBaNZlRsRECAM9J9nWI+JecHCYG\neWVVsJ4LMQajdQ4o48UfcSaoNonnMcqeEVLmD7eeeKluURGKAOGiYC+2crzX01Oh\nJMb2jfECAOpg9gNt9d53728Uyq9pGE5AdAsruXFjVLrcDow3okm0T6WA8t/DvwGd\n1RZ9On3JcuFWiusngcbhfM6jl29i63sB/25YBOqKPWs5U/shGLHy9PgKeVFi0O4A\noobSZNky68/hVc5DRzqQzyXJcO85Egr2DJdTY+EQ2A/mhaatTZ4p3yqlYbQpZm9v\nIChHZW5lcmF0ZWQgYnkgZ251cGcucHkpIDxmb29AZm9vLmNvbT6IuAQTAQIAIgUC\nUva0lAIbLwYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AACgkQukyl+aC/rJrQTAQA\nkjtacG8BFvcD2lwIem467SnA0HPQKlVte1lxmOVgM6XyDh4cYKLt2qAW3cag/oz6\ncmyYCD0Mn31MwaQlrjw8uU9rZs91TTEDnyYiCCyXkOxrprh5j+ucFufRoXJgFzqe\nWxPy+54N7LpDV8TkxatQFFeotLUtXOWy7J/owyyT0W8=\n=615M\n-----END PGP PRIVATE KEY BLOCK-----\n',
  }
# todo: use `stub` package for this?...
config.ConfigManager._real_generateKey = config.ConfigManager.generateKey
config.ConfigManager.generateKey = stubbed_generateKey

#------------------------------------------------------------------------------
class IOR():
  def __init__(self, *items):
    if not items:
      raise ValueError('some %r items expected' % (self.__class__.__name__,))
    self.items = list(items)
  def __repr__(self):
    return self.__class__.__name__ + ': ' \
      + '\n   '.join(repr(item) for item in self.items)
  def clone(self):
    return self.__class__(*self.items)
class I(IOR): pass
class O(IOR): pass
class R(IOR):
  def __init__(self, req, res=None):
    if morph.isstr(req) and res is not None:
      item = aadict()
      item.method, item.url = req.split(':', 1)
      item.method = item.method.lower()
      item.status, item.body = res.split(':', 1)
      item.status = int(item.status)
    else:
      item = req
    self.items = [item]

#------------------------------------------------------------------------------
class TestConfig(unittest.TestCase):

  maxDiff = None

  gettexts = {
    'Add new profile': 'add-profile',
    'Are you sure you want to create an *UNENCRYPTED* storage': 'q-sure-unencrypt',
    'Client name': 'client-name',
    'Continue in verbose mode ("yes" or "no"; default is "yes")': 'q-continue-verbose',
    'Exit': 'exit',
    'High (e.g. mobile device)': 'high-risk',
    '  {index: >{width}}. {label}': '{index}-{label}',
    ' *{index: >{width}}. {label}': '*{index}-{label}',
    'Low (e.g. secure home server)': 'low-risk',
    'Medium (e.g. laptop, shared desktop)': 'medium-risk',
    'My Laptop Computer': 'my-laptop-computer',
    'Networked via the SecPass Broker Protocol': 'spbp',
    'New profile name': 'q-profile-name',
    'Path to CSV file': 'q-path',
    'Path to CSV+PGP file': 'q-pgp-path',
    # 'Personal': '',
    'PGP-encrypted local CSV file': 'pgpfile',
    'Please choose among the following {subject} options': '{subject}-options',
    'Profile "{profile}" created.': 'profile-{profile}-created',
    # '{prompt}:': '',
    # '{prompt} [{default}]:': '',
    '{prompt} (number or enter for default)': '{prompt}-(#*)',
    '{prompt} (number, "?", or enter for default)': '{prompt}-(#?*)',
    # '{prompt} (y/N)': '',
    # '{prompt} (Y/n)': '',
    'Save changes': 'save-config',
    'SecPass configuration action options': 'secpass-menu-options',
    'Secure (e.g. detached moon vault)': 'no-risk',
    'Show configured profiles': 'show-profiles',
    '{title} (default marked with "*"):': '{title}-default-*',
    'Unencrypted local CSV file': 'file',
    'Your {subject} choice': 'choose-{subject}',
    'Create a new account (on Opiyum.net)': 'new-opiyum-account',
    'Use an existing SPBP-enabled account': 'existing-spbp-account',
    'New account email address': 'new-account-email',
    'New account password': 'new-account-password',
    'Repeat password': 'new-account-password-repeat',
    'Message from Opiyum.net:': 'message-from-opiyum',
    'Press enter to continue': 'press-enter',
    'New vault name': 'new-vault-name',
    'Configuration was not saved -- save before exiting': 'q-new-config-not-saved-save-now',
    'Configuration changes were not saved -- save before exiting': 'q-config-not-saved-save-now',
  }

  #----------------------------------------------------------------------------
  def setUp(self):
    self.fso      = fso.push()
    self.iostack  = []
    self.uucnt    = 0

    # todo: use `stub` to stub these out...
    self.real_raw_input = __builtin__.raw_input
    __builtin__.raw_input = self.raw_input
    self.real_getpass = getpass.getpass
    getpass.getpass = self.raw_input
    self.real_uuid4 = uuid.uuid4
    uuid.uuid4 = self.uuid4
    self.real_gettext = gettext.gettext
    gettext.gettext = self.gettext
    self.real_out = base._out
    base._out = self.output
    self.real_request = requests.request
    requests.request = self.request

  #----------------------------------------------------------------------------
  def tearDown(self):
    fso.pop()
    __builtin__.raw_input = self.real_raw_input
    getpass.getpass = self.real_getpass
    uuid.uuid4 = self.real_uuid4
    gettext.gettext = self.real_gettext
    base._out = self.real_out
    requests.request = self.real_request

  #----------------------------------------------------------------------------
  def gettext(self, sid):
    if sid in self.gettexts:
      return '<<' + self.gettexts[sid] + '>>'
    #return '<??<' + sid + '>??>'
    return sid

  #----------------------------------------------------------------------------
  def uuid4(self):
    self.uucnt += 1
    return 'FAKE-UUID-' + str(self.uucnt)

  #----------------------------------------------------------------------------
  def raw_input(self, prompt=None):
    if prompt:
      self.output(prompt)
    return self.pop_input()

  #----------------------------------------------------------------------------
  def pop_input(self):
    self.ioexpect(I, 'not expecting input request')
    return self.pop_iostack()

  #----------------------------------------------------------------------------
  def pop_output(self, output):
    output = output.strip()
    if not output:
      return output
    self.ioexpect(O, msg='not expecting output %r' % (output,))
    ret = self.pop_iostack().strip()
    if output == ret:
      self.assertEqual(output, ret)
      return ret
    if output.startswith(ret):
      return self.pop_output(output[len(ret):])
    if ret.startswith(output):
      put = ret[len(output):]
      self.iostack.insert(0, O(ret[len(output):]))
      return output
    self.assertEqual(output, ret)

  #----------------------------------------------------------------------------
  def pop_iostack(self):
    self.ioexpect(IOR)
    ret = self.iostack[0].items[0]
    if len(self.iostack[0].items) > 1:
      self.iostack[0].items[:1] = []
      return ret
    self.iostack[:1] = []
    return ret

  #----------------------------------------------------------------------------
  def ioexpect(self, type, msg=None):
    if not self.iostack:
      self.fail(msg or 'no more I/O expected')
    self.assertIsInstance(self.iostack[0], type, msg=msg)

  #----------------------------------------------------------------------------
  def request(self, method, url, **kw):
    self.ioexpect(R, 'not expecting request %r:%r' % (method, url))
    xtn = self.pop_iostack()
    self.assertEqual(method.lower(), xtn.method)
    self.assertEqual(url, xtn.url)
    return aadict(status_code=xtn.status, json=lambda: json.loads(xtn.body))

  #----------------------------------------------------------------------------
  def output(self, msg, newline=True):
    self.pop_output(msg)

  #----------------------------------------------------------------------------
  def canonicalIni(self, ini):
    c = ConfigParser.RawConfigParser()
    c.readfp(six.StringIO(ini))
    buf = six.StringIO()
    c.write(buf)
    return buf.getvalue()

  #----------------------------------------------------------------------------
  def assertIniEqual(self, src, chk):
    self.assertMultiLineEqual(self.canonicalIni(src), self.canonicalIni(chk))

  #----------------------------------------------------------------------------
  def runwith(self, *interactions, **kw):
    confpath = kw.pop('confpath', None)
    interactions = morph.flatten(interactions)
    confpath = confpath or 'secpass.ini'
    options  = aadict(config=confpath)
    self.iostack = [i.clone() for i in interactions]
    config.cmd_config(options)
    self.assertEqual(self.iostack, [])
    with open(confpath, 'rb') as fp:
      return fp.read()

  io_mainMenu = [
    O('<<<<secpass-menu-options>>-default-*>>',
      '<<*1-<<show-profiles>>>>',
      '<<2-<<add-profile>>>>',
      '<<3-<<save-config>>>>',
      '<<4-<<exit>>>>',
      '<<<<choose-action>>-(#*)>>: '),
  ]

  io_defaultClientIntro = [
    O('{{welcome}}', '<<q-continue-verbose>> (Y/n): '),
    I(''),
    O('{{intro}}', '{{client-setup}}', '<<client-name>> [<<my-laptop-computer>>]: '),
    I(''),
    O('{{client-setup-risk}}',
      '<<<<risk level-options>>-default-*>>',
      '<<1-<<high-risk>>>>',
      '<<*2-<<medium-risk>>>>',
      '<<3-<<low-risk>>>>',
      '<<4-<<no-risk>>>>',
      '<<<<choose-risk level>>-(#?*)>>: '),
    I(''),
    O('{{profile-create}}',
      '{{profile-create-type}}',
      '<<<<storage-options>>-default-*>>',
      '<<*1-<<spbp>>>>',
      '<<2-<<pgpfile>>>>',
      '<<3-<<file>>>>',
      '<<<<choose-storage>>-(#?*)>>: '),
  ]

  #----------------------------------------------------------------------------
  def test_init_file(self):
    out = self.runwith(
      self.io_defaultClientIntro,
      I('3'),
      O('<<q-sure-unencrypt>> (y/N): '),
      I('yes'),
      O('{{profile-create-options-file}}', '<<q-path>> []: '),
      I('secpass-data.csv'),
      O('{{profile-create-name}}', '<<q-profile-name>> [Personal]: '),
      I(''),
      O('<<profile-Personal-created>>'),
      self.io_mainMenu,
      I('3'),
      self.io_mainMenu,
      I('4'),
    )
    chk = '''
[DEFAULT]
locale                  = en
client.id               = FAKE-UUID-1
client.name             = <<my-laptop-computer>>
client.risk             = medium-risk
profile.default         = FAKE-UUID-2
[profile.FAKE-UUID-2]
name                    = Personal
driver                  = secpass.driver.file
driver.path             = secpass-data.csv
'''
    self.assertIniEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_init_pgpfile(self):
    out = self.runwith(
      self.io_defaultClientIntro,
      I('2'),
      O('{{profile-create-options-pgpfile}}', '<<q-pgp-path>> []: '),
      I('secpass-data.csv.pgp'),
      O('{{profile-create-encrypt-pgpfile-needkey}}',
        '<<<<encryption identity-options>>-default-*>>',
        '<<*1-stubkey-1-uid-1>>',
        '<<2-stubkey-2-uid-1>>',
        '<<<<choose-encryption identity>>-(#?*)>>:'),
      I(''),
      O('{{profile-create-name}}', '<<q-profile-name>> [Personal]: '),
      I(''),
      O('<<profile-Personal-created>>'),
      self.io_mainMenu,
      I('3'),
      self.io_mainMenu,
      I('4'),
    )
    chk = '''
[DEFAULT]
locale                  = en
client.id               = FAKE-UUID-1
client.name             = <<my-laptop-computer>>
client.risk             = medium-risk
profile.default         = FAKE-UUID-2
[profile.FAKE-UUID-2]
name                    = Personal
driver                  = secpass.driver.pgpfile
driver.agent            = true
driver.identity         = stubkey-1-fp
driver.path             = secpass-data.csv.pgp
'''
    self.assertIniEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_init_spbp_newWithMessage(self):

    out = self.runwith(
      self.io_defaultClientIntro,
      I(''),
      O('{{profile-create-options-spbp}}',
        '<<<<account-options>>-default-*>>',
        '<<*1-<<new-opiyum-account>>>>',
        '<<2-<<existing-spbp-account>>>>',
        '<<<<choose-account>>-(#?*)>>:'),
      I(''),
      O('{{profile-create-options-spbp-new}}',
        '<<new-account-email>>:'),
      I('test@example.com'),
      O('<<new-account-password>>:'),
      I('s3cr3t'),
      O('<<new-account-password-repeat>>:'),
      I('s3cr3t'),
      R('POST:' + config.OPIYUM_URL + 'register',
        '200:{"id": "fake-register-id-1", "message": "fake-message\\nline-2"}'),
      O('<<message-from-opiyum>>',
        '  fake-message',
        '  line-2',
        '<<press-enter>>:'),
      I(''),
      R('POST:' + config.OPIYUM_URL + 'client',
        '200:{"id": "fake-client-id-1"}'),
      O('{{profile-create-options-spbp-new-vault}}',
        '<<new-vault-name>> [Personal]:'),
      I(''),
      R('POST:' + config.OPIYUM_URL + 'vault',
        '200:{"id": "fake-vault-id-1"}'),
      O('{{profile-create-encrypt-spbp-needkey}}',
        '<<<<encryption identity-options>>-default-*>>',
        '<<*1-stubkey-1-uid-1>>',
        '<<2-stubkey-2-uid-1>>',
        '<<<<choose-encryption identity>>-(#?*)>>:'),
      I(''),
      O('{{profile-create-name}}', '<<q-profile-name>> [Personal]: '),
      I(''),
      O('<<profile-Personal-created>>'),
      self.io_mainMenu,
      I('3'),
      self.io_mainMenu,
      I('4'),
    )

    chk = '''
[DEFAULT]
locale                  = en
client.id               = FAKE-UUID-1
client.name             = <<my-laptop-computer>>
client.risk             = medium-risk
profile.default         = FAKE-UUID-2
[profile.FAKE-UUID-2]
name                    = Personal
driver                  = secpass.driver.spbp
driver.password         = FAKE-ENC(stubkey-1-fp,s3cr3t)
driver.privatekey       = FAKE-ENC(stubkey-1-fp,-----BEGIN PGP PRIVATE KEY BLOCK-----
\tVersion: GnuPG v1.4.11 (GNU/Linux)
\t.
\tlQHYBFL2tJQBBAC9yB43tQMAqTOohO6PuNLD4Hjo6cfojFUXT4Ou3MMwQ6sfaRsD
\tJii0+80izXuRLokJSOi+0xpmxcs5/bQ1LnLLsimVdMoKZnPZz5bwHi9mi9FTC68S
\tXBM6SAy0Y5xVBjwaiT3YWbAz/y5RM6ACskBEa2wUuQuNKOs8MG1kwgRtywARAQAB
\tAAP5ASK47Oa+5AVJ2K4kSqTgUf6+X8/CUVBsU+2MYVf9169CpLdOy5KHYindkjc+
\tOuIB55XRmrli/47FxrePbqqz/M8UBvPW0WR7Vkhq+V5nF50Jl5RsCWOGRUr1W2Yx
\tV+GVAhrbNd7JPtg6eK3REc4aMldyX6M216J+wtBaNZlRsRECAM9J9nWI+JecHCYG
\teWVVsJ4LMQajdQ4o48UfcSaoNonnMcqeEVLmD7eeeKluURGKAOGiYC+2crzX01Oh
\tJMb2jfECAOpg9gNt9d53728Uyq9pGE5AdAsruXFjVLrcDow3okm0T6WA8t/DvwGd
\t1RZ9On3JcuFWiusngcbhfM6jl29i63sB/25YBOqKPWs5U/shGLHy9PgKeVFi0O4A
\toobSZNky68/hVc5DRzqQzyXJcO85Egr2DJdTY+EQ2A/mhaatTZ4p3yqlYbQpZm9v
\tIChHZW5lcmF0ZWQgYnkgZ251cGcucHkpIDxmb29AZm9vLmNvbT6IuAQTAQIAIgUC
\tUva0lAIbLwYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AACgkQukyl+aC/rJrQTAQA
\tkjtacG8BFvcD2lwIem467SnA0HPQKlVte1lxmOVgM6XyDh4cYKLt2qAW3cag/oz6
\tcmyYCD0Mn31MwaQlrjw8uU9rZs91TTEDnyYiCCyXkOxrprh5j+ucFufRoXJgFzqe
\tWxPy+54N7LpDV8TkxatQFFeotLUtXOWy7J/owyyT0W8=
\t=615M
\t-----END PGP PRIVATE KEY BLOCK-----
\t)
driver.publickey        = -----BEGIN PGP PUBLIC KEY BLOCK-----
\tVersion: GnuPG v1.4.11 (GNU/Linux)
\t.
\tmI0EUva0lAEEAL3IHje1AwCpM6iE7o+40sPgeOjpx+iMVRdPg67cwzBDqx9pGwMm
\tKLT7zSLNe5EuiQlI6L7TGmbFyzn9tDUucsuyKZV0ygpmc9nPlvAeL2aL0VMLrxJc
\tEzpIDLRjnFUGPBqJPdhZsDP/LlEzoAKyQERrbBS5C40o6zwwbWTCBG3LABEBAAG0
\tKWZvbyAoR2VuZXJhdGVkIGJ5IGdudXBnLnB5KSA8Zm9vQGZvby5jb20+iLgEEwEC
\tACIFAlL2tJQCGy8GCwkIBwMCBhUIAgkKCwQWAgMBAh4BAheAAAoJELpMpfmgv6ya
\t0EwEAJI7WnBvARb3A9pcCHpuOu0pwNBz0CpVbXtZcZjlYDOl8g4eHGCi7dqgFt3G
\toP6M+nJsmAg9DJ99TMGkJa48PLlPa2bPdU0xA58mIggsl5Dsa6a4eY/rnBbn0aFy
\tYBc6nlsT8vueDey6Q1fE5MWrUBRXqLS1LVzlsuyf6MMsk9Fv
\t=WtFv
\t-----END PGP PUBLIC KEY BLOCK-----
\t.
driver.url              = ''' + config.OPIYUM_URL + '''
driver.username         = test@example.com
'''
    self.assertIniEqual(out, chk)


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
