When storing passwords using the local PGP file storage driver,
SecPass needs the path to a filename (relative to the configuration
file location). The data is stored in CSV format, then encrypted with
PGP using a configurable identity. If left blank, the file will be
given the same name as the profile ID appended with ".data.csv.pgp",
and will be located in the same directory as configuration file.
