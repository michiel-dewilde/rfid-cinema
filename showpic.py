import os, signal, subprocess
from Tkinter import *
from PIL import ImageTk, Image
from repoze.lru import lru_cache
devnull = open(os.devnull, 'w')

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
    hratio = root.winfo_screenwidth()/float(image.width)
    vratio = root.winfo_screenheight()/float(image.height)
    ratio = min(hratio, vratio)
    image = image.resize((int(round(ratio*image.width)), int(round(ratio*image.height))), Image.LANCZOS)
    return image

def showImage():
    clear()
    image = readImage('/media/usb0/IMG_0681.JPG')
    photoImage = ImageTk.PhotoImage(image)
    label = Label(root, image = photoImage)
    label.image = photoImage
    label.configure(background='black')
    label.pack(side = 'bottom', fill = 'both', expand = 'yes')

def showVideo():
    global videoPlayer
    clear()
    vidpath = '/media/usb0/F354422ACF-Around the world in 80 days-skUGK5Qut9M.mp4'
    videoPlayer = subprocess.Popen(['/usr/bin/omxplayer', '--no-osd', '--no-keys', '-o', 'hdmi', '--', vidpath], preexec_fn=os.setsid, stdin=devnull, stdout=devnull, stderr=devnull)

def cleanup():
    clear()
    root.destroy()
    
root.bind('i', lambda e: showImage())
root.bind('v', lambda e: showVideo())
root.bind('c', lambda e: clear())
root.bind('<Escape>',lambda e: cleanup())

root.mainloop()
