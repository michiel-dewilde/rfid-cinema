import os, signal, subprocess, time
from monotonic import monotonic
from PIL import ImageTk, Image
import RPi.GPIO as GPIO
from MFRC522 import MFRC522
from repoze.lru import lru_cache
from Tkinter import Tk, Label, LEFT, StringVar

global MIFAREReader
MIFAREReader = MFRC522()
def readTagUid():
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQALL)
    if status != MIFAREReader.MI_OK:
        return None
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    if status != MIFAREReader.MI_OK:
        return None
    MIFAREReader.MFRC522_Request(MIFAREReader.PICC_HALT)
    return ''.join([format(i,'02X') for i in uid])

def isValidTagUid(tagUid):
    if any([c.islower() for c in tagUid]):
        return False
    try:
        uidBytes = [x for x in bytearray(tagUid.decode('hex'))]
    except:
        return False
    if len(uidBytes) != 5:
        return False
    serNumCheck = 0
    for i in xrange(5):
        serNumCheck = serNumCheck ^ uidBytes[i]
    return serNumCheck == 0

root = Tk()
root.attributes('-fullscreen', True)
root.configure(bg='black', cursor='none')

helpTagLabel = None
videoPlayer = None

def clear():
    global helpTagLabel, videoPlayer
    helpTagLabel = None
    if videoPlayer is not None:
        os.killpg(os.getpgid(videoPlayer.pid), signal.SIGTERM)
        videoPlayer = None
    for widget in root.winfo_children():
        widget.destroy()

@lru_cache(maxsize=32)
def readImage(path):
    image = Image.open(path)
    orientation = 1
    try:
        orientation = image._getexif()[0x0112]
    except:
        pass #no EXIF
    if orientation == 1:
        pass
    elif orientation == 3:
        image = image.rotate(180, expand=True)
    elif orientation == 6:
        image = image.rotate(270, expand=True)
    elif orientation == 8:
        image = image.rotate(90, expand=True)
    swidth = root.winfo_screenwidth()
    sheight = root.winfo_screenheight()
    if (image.width != swidth or image.height > sheight) and (image.height != sheight or image.width > swidth):
        hratio = swidth/float(image.width)
        vratio = sheight/float(image.height)
        ratio = min(hratio, vratio)
        image = image.resize((int(round(ratio*image.width)), int(round(ratio*image.height))), Image.LANCZOS)
    return image

def showImage(path):
    clear()
    image = readImage(path)
    photoImage = ImageTk.PhotoImage(image)
    label = Label(root, image=photoImage, bg='black')
    label.image = photoImage
    label.pack(fill='both', expand='yes')

def showHelpWithTag(tagUid='', tagPresent=False):
    global helpTagLabel
    if not helpTagLabel:
        clear()
        label = Label(root, text='help message', fg='white', bg='black', font=('Helvetica', 20), justify=LEFT)
        label.pack(side='top', fill='both', expand='yes')
        helpTagLabel = Label(root, text='', bg='black', font=('Helvetica', 200))
        helpTagLabel.pack(side='top', fill='both', expand='no')
    helpTagLabel.configure(text=tagUid, fg=('yellow' if tagPresent else 'grey'))
        
devnull = open(os.devnull, 'w')
def showVideo(path, loop=False):
    global videoPlayer
    clear()
    args = ['/usr/bin/omxplayer', '-o', 'both', '--no-osd', '--no-keys']
    if loop:
        args.append('--loop')
    args.append('--')
    args.append(path)
    videoPlayer = subprocess.Popen(args, preexec_fn=os.setsid, stdin=devnull, stdout=devnull, stderr=devnull)

def cleanup():
    clear()
    root.destroy()

class Rule:
    minDuration = 'end'
    lostDuration = 'end'
    maxDuration = 'end'
    location = None
config = None

baseLocation = '/media/usb0'
configLocation = os.path.join(baseLocation, 'config.txt')
def readConfig():
    global config
    newConfig = {}
    lineNum = 0
    for line in open(configLocation, 'U'):
        lineNum = lineNum + 1
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        id = None
        rule = Rule()
        for field in line.split(':'):
            field = field.strip()
            if not field:
                continue
            lhsrhs = field.split('=')
            if len(lhsrhs) != 2:
                raise Exception('config.txt line {}: expected a single \'=\' in \'{}\''.format(lineNum, field))
            lhs = lhsrhs[0].strip()
            rhs = lhsrhs[1].strip()
            if lhs == 'id':
                if rhs == 'none' or rhs == 'unknown' or isValidTagUid(rhs):
                    id = rhs
                else:
                    raise Exception('config.txt line {}: invalid id: \'{}\''.format(lineNum, rhs))
            elif lhs == 'min' or lhs == 'lost' or lhs == 'max':
                if rhs == 'end' or rhs == 'forever':
                    duration = rhs
                else:
                    try:
                        duration = float(rhs)
                    except:
                        raise Exception('config.txt line {}: invalid duration: \'{}\''.format(lineNum, field))
                setattr(rule, lhs + 'Duration', duration)
            elif lhs == 'file':
                location = os.path.join(baseLocation, rhs)
                if not os.path.isfile(location):
                    raise Exception('config.txt line {}: missing file: \'{}\''.format(lineNum, rhs))
                rule.location = location
            else:
                raise Exception('config.txt line {}: invalid key \'{}\''.format(lineNum, lhs))
        if id is None:
            raise Exception('config.txt line {}: missing id'.format(lineNum))
        if file is None:
            raise Exception('config.txt line {}: missing file'.format(lineNum))
        newConfig[id] = rule
    config = newConfig

helpTagText = ''
def handleTagChange(tagUid):
    global helpTagText
    if tagUid:
        helpTagText = tagUid
    showHelpWithTag(helpTagText, bool(tagUid));    
    
activeTagUid = None
readFailCount = None
readSuccessTime = None
def pollTag():
    global readFailCount
    global readSuccessTime
    global activeTagUid
    tagUid = readTagUid()
    if tagUid:
        print isValidTagUid(tagUid)
        readFailCount = 0
        readSuccessTime = monotonic()
        if tagUid != activeTagUid:
            activeTagUid = tagUid
            handleTagChange(tagUid)
    elif activeTagUid:
        failCountExceeded = readFailCount == 4
        if not failCountExceeded:
            readFailCount = readFailCount + 1
        failDurationExceeded = monotonic() - readSuccessTime > 0.5
        if failCountExceeded and failDurationExceeded:
            activeTagUid = None
            readFailCount = None
            readSuccessTime = None
            handleTagChange(None)

def poll():
    global config
    root.after(50, poll)
    if os.path.isfile(configLocation):
        if config is not None:
            readConfig()
    else:
        config = None
    pollTag()
    root.update_idletasks()

root.bind('i', lambda e: showImage('/media/usb0/IMG_0681.JPG'))
root.bind('v', lambda e: showVideo('/media/usb0/F354422ACF-Around the world in 80 days-skUGK5Qut9M.mp4', True))
root.bind('c', lambda e: clear())
root.bind('<Escape>',lambda e: cleanup())

handleTagChange(None)
poll()
root.mainloop()
GPIO.cleanup()
