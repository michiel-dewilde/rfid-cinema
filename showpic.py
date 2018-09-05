from Tkinter import *
from PIL import ImageTk, Image
import os

root = Tk()
root.attributes('-fullscreen', True)
root.configure(background='black')
root.configure(cursor="none")
root.bind('<Escape>',lambda e: root.destroy())
img = Image.open("/media/usb0/761AB7C318-RFID-RC522-raspberry-pi-3-1024x513.png")
hratio = root.winfo_screenwidth()/float(img.width)
vratio = root.winfo_screenheight()/float(img.height)
ratio = min(hratio, vratio)
img = img.resize((int(round(ratio*img.width)), int(round(ratio*img.height))), Image.LANCZOS)
pimg = ImageTk.PhotoImage(img)
panel = Label(root, image = pimg)
panel.configure(background='black')
panel.pack(side = "bottom", fill = "both", expand = "yes")
root.mainloop()
