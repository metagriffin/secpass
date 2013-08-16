test:
	nosetests --verbose

download:
	cat setup.py | tr -d ' ' | egrep "^[\"']\S+[>=]=\S+[\"'],$$" \
	  | sed -re "s/^[\"'](\S+)[>=]=(\S+)[\"'],$$/\1==\2/" \
	  | grep -v wxPython \
	  | xargs pip install --download-dir=lib

upload:
	python setup.py sdist upload
