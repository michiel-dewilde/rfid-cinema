#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/rfid-cinema.desktop <<EOF
[Desktop Entry]
Type=Application
Exec=$PWD/autostart.sh
EOF
