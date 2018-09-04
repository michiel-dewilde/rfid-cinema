#!/usr/bin/env python

import RPi.GPIO as GPIO
import MFRC522
import signal

GPIO.setwarnings(False)
MIFAREReader = MFRC522.MFRC522()

def readTag():
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status != MIFAREReader.MI_OK:
        return None
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    if status != MIFAREReader.MI_OK:
        return None
    return ''.join([format(i,'02X') for i in uid])

print readTag()
