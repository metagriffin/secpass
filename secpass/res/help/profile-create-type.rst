The first step in creating a new profile is to decide where to store
the information. SecPass comes with the following built-in options,
ordered from *MOST* secure to *LEAST* secure:

* Networked via the SecPass Broker Protocol: using the SPBP is really
  the right way to do it. Passwords and notes are never stored
  locally, are backed-up and vaulted on a secure cloud system, can be
  shared with others, can be configured with different security
  thresholds on a per-device basis, etc. -- i.e. The Whole Enchilada.
  (Note: currently requires that you have a running gpg-agent.)

* PGP-Encrypted local CSV file: stores all data in a PGP-encrypted CSV
  spreadsheet file on your local hard drive. Although it is difficult
  to extract your passwords from the file, it is not impossible. And
  once compromised, *all* of your passwords are exposed. It also does
  not benefit from being backed-up, vaulted, or shareable. This option
  is "good but not great"...
  (Note: currently requires that you have a running gpg-agent.)

* Unencrypted local CSV file: similar to the PGP-encrypted option,
  except the file is not encrypted. Definitely do not use this option
  for real passwords -- i.e. use it only if you are experimenting with
  SecPass. One of the interesting things with this method is that you
  can open up the file with any spreadsheet program, like LibreOffice
  or Excel. The *enormous* downside is that if anyone gets access to
  your files, they have access to all of your passwords... doh!
