import os, signal, subprocess, time
from monotonic import monotonic
from PIL import ImageTk, Image
import RPi.GPIO as GPIO
from MFRC522 import MFRC522
from repoze.lru import lru_cache
from Tkinter import Tk, Label, LEFT, StringVar

global MIFAREReader
MIFAREReader = MFRC522()
def readTag():
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQALL)
    if status != MIFAREReader.MI_OK:
        return None
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    if status != MIFAREReader.MI_OK:
        return None
    MIFAREReader.MFRC522_Request(MIFAREReader.PICC_HALT)
    return ''.join([format(i,'02X') for i in uid])

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
    label = Label(root, image = photoImage, bg = 'black')
    label.image = photoImage
    label.pack(fill = 'both', expand = 'yes')

def showHelpWithTag(tagId = '', tagPresent = False):
    global helpTagLabel
    if not helpTagLabel:
        clear()
        label = Label(root, text = 'help message', fg = 'white', bg = 'black', font=('Helvetica', 20), justify=LEFT)
        label.pack(side = 'top', fill = 'both', expand = 'yes')
        helpTagLabel = Label(root, text = '', bg='black', font=("Helvetica", 200))
        helpTagLabel.pack(side = 'top', fill = 'both', expand = 'no')
    helpTagLabel.configure(text=tagId, fg=('green' if tagPresent else 'red'))
        
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

helpTagText = ''
def handleTagChange(tagId):
    global helpTagText
    if tagId:
        helpTagText = tagId
    showHelpWithTag(helpTagText, bool(tagId));    
    
activeTagId = None
readFailCount = None
readSuccessTime = None
def pollTag():
    global readFailCount
    global readSuccessTime
    global activeTagId
    tagId = readTag()
    if tagId:
        readFailCount = 0
        readSuccessTime = monotonic()
        if tagId != activeTagId:
            activeTagId = tagId
            handleTagChange(tagId)
    elif activeTagId:
        failCountExceeded = readFailCount == 4
        if not failCountExceeded:
            readFailCount = readFailCount + 1
        failDurationExceeded = monotonic() - readSuccessTime > 0.5
        if failCountExceeded and failDurationExceeded:
            activeTagId = None
            readFailCount = None
            readSuccessTime = None
            handleTagChange(None)

def poll():
    root.after(50, poll)
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
