#!/usr/bin/env bash

cd ..

path=`pwd`

cat << EOF > $HOME/Desktop/PLSDR.desktop
[Desktop Entry]
Comment=PLSDR software-defined radio
Encoding=UTF-8
Exec=$path/PLSDR.py
GenericName=PLSDR
GenericName[en_US]=PLSDR
Icon=$path/icon/app_icon_32x32.png
MimeType=
Name=PLSDR
Name[en_US]=PLSDR
StartupNotify=false
Terminal=false
Type=Application
EOF
