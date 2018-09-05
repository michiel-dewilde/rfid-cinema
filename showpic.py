from Tkinter import *
from PIL import ImageTk, Image
import os, subprocess, signal
devnull = open(os.devnull, 'w')

root = Tk()
root.attributes('-fullscreen', True)
root.configure(background='black', cursor="none")

videoPlayer = None
photoImage = None

def clear():
    global videoPlayer, photoImage
    if videoPlayer is not None:
        os.killpg(os.getpgid(videoPlayer.pid), signal.SIGTERM)
        videoPlayer = None
    for widget in root.winfo_children():
        widget.destroy()
    photoImage = None

def showImg():
    global photoImage
    clear()
    img = Image.open("/media/usb0/761AB7C318-RFID-RC522-raspberry-pi-3-1024x513.png")
    hratio = root.winfo_screenwidth()/float(img.width)
    vratio = root.winfo_screenheight()/float(img.height)
    ratio = min(hratio, vratio)
    img = img.resize((int(round(ratio*img.width)), int(round(ratio*img.height))), Image.LANCZOS)
    photoImage = ImageTk.PhotoImage(img)
    label = Label(root, image = photoImage)
    label.configure(background='black')
    label.pack(side = "bottom", fill = "both", expand = "yes")

def showVideo():
    global devnull, videoPlayer
    clear()
    vidpath = "/media/usb0/F354422ACF-Around the world in 80 days-skUGK5Qut9M.mp4"
    videoPlayer = subprocess.Popen(['/usr/bin/omxplayer', '--no-osd', '--no-keys', '-o', 'hdmi', '--', vidpath], preexec_fn=os.setsid, stdin=devnull, stdout=devnull, stderr=devnull)

def cleanup():
    global root
    clear()
    root.destroy()
    
root.bind('i', lambda e: showImg())
root.bind('v', lambda e: showVideo())
root.bind('c', lambda e: clear())
root.bind('<Escape>',lambda e: cleanup())

root.mainloop()
