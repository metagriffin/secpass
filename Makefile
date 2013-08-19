test:
	nosetests --verbose

images:
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=128 \
	  asset/secpass-logo-lettered.svg --export-png=secpass/gui/res/logo-let-128x128.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=64 \
	  asset/secpass-logo-lettered.svg --export-png=secpass/gui/res/logo-let-64x64.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=16 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-16x16.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=24 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-24x24.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=32 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-32x32.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=64 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-64x64.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=128 \
	  asset/secpass-logo.svg --export-png=secpass/gui/res/logo-128x128.png
	xsltproc asset/select-icon-hide.xslt asset/icons-toolbar.svg > asset/icons-toolbar.gen-hide.svg
	xsltproc asset/select-icon-show.xslt asset/icons-toolbar.svg > asset/icons-toolbar.gen-show.svg
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=24 \
	  asset/icons-toolbar.gen-hide.svg --export-png=secpass/gui/res/icon-hide-24x24.png
	inkscape --without-gui --export-area=0:0:1000:1000 --export-width=24 \
	  asset/icons-toolbar.gen-show.svg --export-png=secpass/gui/res/icon-show-24x24.png
	rm -f asset/icons-toolbar.gen-*.svg

download:
	cat setup.py | tr -d ' ' | tr '>' '=' | egrep "^[\"']\S+==\S+[\"'],$$" \
	  | sed -re "s/^[\"'](\S+)[>=]=(\S+)[\"'],$$/\1==\2/" \
	  | grep -v wxPython \
	  | xargs pip install --download-dir=lib

upload:
	python setup.py sdist upload

# TODO: extract version from setup.py...
pot:
	find secpass -iname '*.py' \
	  | xargs xgettext \
            --language Python \
            --copyright-holder 'UberDev' \
            --package-name secpass \
            --package-version 0.1.0 \
            --msgid-bugs-address metagriffin@uberdev.org \
            --output -
