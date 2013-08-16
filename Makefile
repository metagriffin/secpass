test:
	nosetests --verbose

images:
	inkscape --export-area=0:0:1000:1000 --export-width=128 \
	  asset/secpass-logo-lettered.svg --export-png=secpass/gui/res/logo-let-128x128.png
	inkscape --export-area=0:0:1000:1000 --export-width=64 \
	  asset/secpass-logo-lettered.svg --export-png=secpass/gui/res/logo-let-64x64.png
	inkscape --export-area=0:0:1000:1000 --export-width=16 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-16x16.png
	inkscape --export-area=0:0:1000:1000 --export-width=24 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-24x24.png
	inkscape --export-area=0:0:1000:1000 --export-width=32 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-32x32.png
	inkscape --export-area=0:0:1000:1000 --export-width=64 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-64x64.png
	inkscape --export-area=0:0:1000:1000 --export-width=128 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-128x128.png

download:
	cat setup.py | tr -d ' ' | egrep "^[\"']\S+[>=]=\S+[\"'],$$" \
	  | sed -re "s/^[\"'](\S+)[>=]=(\S+)[\"'],$$/\1==\2/" \
	  | grep -v wxPython \
	  | xargs pip install --download-dir=lib

upload:
	python setup.py sdist upload
