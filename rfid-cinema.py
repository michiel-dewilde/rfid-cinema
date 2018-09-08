import os, signal, subprocess, time
from PIL import ImageTk, Image
import RPi.GPIO as GPIO
from MFRC522 import MFRC522
from repoze.lru import lru_cache
from Tkinter import Tk, Label

global MIFAREReader
MIFAREReader = MFRC522()
def readTag():
    global MIFAREReader
    MIFAREReader.MFRC522_Init()
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status != MIFAREReader.MI_OK:
        return None
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    if status != MIFAREReader.MI_OK:
        return None
    return ''.join([format(i,'02X') for i in uid])

root = Tk()
root.attributes('-fullscreen', True)
root.configure(background='black', cursor='none')

videoPlayer = None

def clear():
    global videoPlayer
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
    label = Label(root, image = photoImage)
    label.image = photoImage
    label.configure(background='black')
    label.pack(side = 'bottom', fill = 'both', expand = 'yes')

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
    
root.bind('i', lambda e: showImage('/media/usb0/IMG_0681.JPG'))
root.bind('v', lambda e: showVideo('/media/usb0/F354422ACF-Around the world in 80 days-skUGK5Qut9M.mp4', True))
root.bind('c', lambda e: clear())
root.bind('<Escape>',lambda e: cleanup())

root.mainloop()
GPIO.cleanup()
