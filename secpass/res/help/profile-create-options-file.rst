When storing passwords using the local file storage driver, SecPass
needs the path to a filename (relative to the configuration file
location). The data is stored in CSV format. Please note that the
contents of this file is *not* encrypted, so efforts should be taken
to protect the file, such as using access control and encrypted
drives. If left blank, the file will be given the same name as the
profile ID appended with ".data.csv", and will be located in the same
directory as configuration file.
