#!/bin/sh
exec aplay -t raw -r 48000 -c 2 -f S16_LE /dev/zero </dev/null >/dev/null 2>&1
