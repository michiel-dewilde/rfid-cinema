#!/usr/bin/env python

import RPi.GPIO as GPIO
from MFRC522 import MFRC522
import signal, time

GPIO.setwarnings(False)
global MIFAREReader
MIFAREReader = MFRC522()

#print "def", format(MIFAREReader.Read_MFRC522(MFRC522.RFCfgReg), "02X")
#MIFAREReader.Write_MFRC522(MFRC522.RFCfgReg, 0x70)
#print "new", format(MIFAREReader.Read_MFRC522(MFRC522.RFCfgReg), "02X")

def readTag():
    global MIFAREReader
    #MIFAREReader.MFRC522_Init()
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQALL)
    if status != MIFAREReader.MI_OK:
        return None
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    if status != MIFAREReader.MI_OK:
        return None
    MIFAREReader.MFRC522_Request(MIFAREReader.PICC_HALT)
    return ''.join([format(i,'02X') for i in uid])

while True:
    print readTag()
    #time.sleep(0.05)


