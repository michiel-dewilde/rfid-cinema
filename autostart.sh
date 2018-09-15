#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
killall xscreensaver 2>/dev/null
xset s noblank
xset s off
xset s -dpms
./playsilence.sh&
SILENCE=$!
while ! python rfid-cinema.py; do
    :
done
kill $SILENCE
