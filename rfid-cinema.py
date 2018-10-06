import os, signal, subprocess, time
from monotonic import monotonic
from PIL import ImageTk, Image
import RPi.GPIO as GPIO
from MFRC522 import MFRC522
from repoze.lru import CacheMaker
from Tkinter import Tk, Label, LEFT, StringVar

cacheMaker = CacheMaker()
devnull = open(os.devnull, 'w')
selfMountPath = '/rfid-cinema'
isSelfMount = os.path.exists(selfMountPath)
baseLocation = selfMountPath if isSelfMount else '/media/usb0'
configName = 'config.txt'
configLocation = os.path.join(baseLocation, configName)

class TagUidReader:
    def __init__(self):
        self.reader = MFRC522()
    def readTagUid(self):
        (status,TagType) = self.reader.MFRC522_Request(MFRC522.PICC_REQALL)
        if status != MFRC522.MI_OK:
            return None
        (status,uid) = self.reader.MFRC522_Anticoll()
        if status != MFRC522.MI_OK:
            return None
        self.reader.MFRC522_Request(MFRC522.PICC_HALT)
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

@cacheMaker.lrucache(maxsize=16)
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
    swidth = gui.root.winfo_screenwidth()
    sheight = gui.root.winfo_screenheight()
    if (image.width != swidth or image.height > sheight) and (image.height != sheight or image.width > swidth):
        hratio = swidth/float(image.width)
        vratio = sheight/float(image.height)
        ratio = min(hratio, vratio)
        image = image.resize((int(round(ratio*image.width)), int(round(ratio*image.height))), Image.LANCZOS)
    return image

class Gui:
    def __init__(self):
        self.root = Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black', cursor='none')
        self.root.bind('<Escape>',lambda e: self.cleanup())
        self.helpTagLabel = None
        self.imageLabel = None
        self.videoFileName = None
        self.videoPlayer = None

    def clear(self):
        self.helpTagLabel = None
        self.imageLabel = None
        self.videoFileName = None
        if self.videoPlayer is not None:
            os.killpg(os.getpgid(self.videoPlayer.pid), signal.SIGTERM)
            self.videoPlayer.wait()
        self.videoPlayer = None
        for widget in self.root.winfo_children():
            widget.destroy()

    def showStartupMessage(self):
        self.clear()
        swidth = self.root.winfo_screenwidth()
        message='Hello there! Configuration successful, starting in a few seconds...\nFor help on setting up this system, {}.'.format('unplug and connect the USB cable to a PC' if isSelfMount else 'pull out the USB stick at any time')
        label = Label(self.root, text=message, fg='green', bg='black', font=('Helvetica', int(round(swidth/48.0))), justify=LEFT)
        label.pack(side='top', fill='both', expand='yes')
        
    def showError(self, message):
        self.clear()
        swidth = self.root.winfo_screenwidth()
        label = Label(self.root, text=message, fg='red', bg='black', font=('Helvetica', int(round(swidth/96.0))), justify=LEFT)
        label.pack(side='top', fill='both', expand='yes')

    def showImage(self, fileName):
        try:
            image = readImage(os.path.join(baseLocation, fileName))
            photoImage = ImageTk.PhotoImage(image)
        except Exception, e:
            self.showError("Error showing image '{}':\n{}".format(fileName, str(e)))
            return
        if not self.imageLabel:
            self.clear()
            self.imageLabel = Label(self.root, bg='black')
            self.imageLabel.pack(side='top', fill='both', expand='yes')
        self.imageLabel.configure(image=photoImage)
        self.imageLabel.image = photoImage

    def showVideo(self, fileName, loop=False):
        args = ['/usr/bin/omxplayer', '-b', '-o', 'both', '--no-osd', '--no-keys']
        if loop:
            args.append('--loop')
        args.append('--')
        args.append(os.path.join(baseLocation, fileName))
        self.clear()
        self.videoFileName = fileName
        self.videoPlayer = subprocess.Popen(args, preexec_fn=os.setsid, stdin=devnull, stdout=devnull, stderr=devnull)

    def updateVideoPollDoneNow(self):
        if self.videoPlayer is None:
            return False
        exitCode = self.videoPlayer.poll()
        if exitCode is None:
            return False
        fileName = self.videoFileName
        self.videoFileName = None
        self.videoPlayer = None
        if exitCode != 0:
            self.showError("Error showing video '{}'".format(fileName))
            return False
        return True
        
    def showFile(self, fileName, loop=False):
        if fileName is None:
            clear()
        elif os.path.splitext(fileName)[1].lower() in ('.bmp', '.gif', '.jpg', '.jpeg', '.png'):
            self.showImage(fileName)
        else:
            self.showVideo(fileName, loop)
        
    def showHelpWithTagUid(self, tagUid):
        if not self.helpTagLabel:
            self.clear()
            helpText = """This is a presentation system showing a video or an image when the associated RFID tag is presented.
This system was originally developed for O Lab Overbeke, Habbekrats Wetteren and faro.be
by Michiel De Wilde <michiel.dewilde@gmail.com>.

{} a file named '{}'.
In that file, each line needs to associate an RFID tag with a video or image file.

Use the following syntax:
    id=<RFID tag ID>:file=<file name>

You can use ISO 14443A 'MIFARE' tags having a 4-byte unique ID.
If you present an RFID tag now, its ID is shown below this message.
Use 'id=none' to configure what to do when idle.
Use 'id=unknown' to configure what to do with an unknown tag.

Supported formats are avi/flv/mov/mpg/mp4/mkv/m4v (videos) and bmp/gif/jpg/png (images).

You can add extra fields 'min', 'lost' and 'max':
    - min: minimal duration
    - lost: duration after tag removal
    - max: maximal duration
Valid values are:
    - a time in seconds (e.g; '1.5')
    - 'end' to wait until the end of the video (default)
    - 'forever' to loop the video

Example:
    id=F354422ACF:min=end:lost=end:max=forever:file=myvideo.mp4

""".format('This device is a USB drive on your PC. Create' if isSelfMount else 'Insert a USB stick with', configName)
            if isSelfMount:
                helpText += 'This message is shown because this device is connected to a PC.\nNormal functionality is resumed after you connect this device to a dumb power supply.'
            else:
                helpText += "This message is shown because the '{}' file (or the entire USB stick) is missing.\nNormal functionality is resumed immediately after inserting a configured stick.\n".format(configName)
            swidth = self.root.winfo_screenwidth()
            label = Label(self.root, text=helpText, fg='white', bg='black', font=('Helvetica', int(round(swidth/120.0))), justify=LEFT)
            label.pack(side='top', fill='both', expand='yes')
            self.helpTagLabel = Label(self.root, text='', bg='black', font=('Helvetica', int(round(swidth/9.6))))
            self.helpTagLabel.pack(side='top', fill='both', expand='no')
        if tagUid:
            self.helpTagLabel.configure(text=tagUid, fg='yellow')
        else:
            self.helpTagLabel.configure(fg='grey')
        
    def cleanup(self):
        self.clear()
        self.root.destroy()

class Rule:
    def __init__(self):
        self.minDuration = 'end'
        self.lostDuration = 'end'
        self.maxDuration = 'end'
        self.fileName = None

startupRule = Rule()
startupRule.maxDuration = 5.0

def readConfig():
    config = {}
    lineNum = 0
    for line in open(configLocation, 'U'):
        lineNum = lineNum + 1
        try:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            tagUids = []
            rule = Rule()
            for field in line.split(':'):
                field = field.strip()
                if not field:
                    continue
                lhsrhs = field.split('=')
                if len(lhsrhs) != 2:
                    raise Exception("expected a single '=' in '{}'".format(field))
                lhs = lhsrhs[0].strip()
                rhs = lhsrhs[1].strip()
                if lhs == 'id':
                    if rhs == 'none' or rhs == 'unknown' or isValidTagUid(rhs):
                        tagUids.append(rhs)
                    else:
                        raise Exception("invalid id: '{}'".format(rhs))
                elif lhs == 'min' or lhs == 'lost' or lhs == 'max':
                    if rhs == 'end' or rhs == 'forever':
                        duration = rhs
                    else:
                        try:
                            duration = float(rhs)
                        except:
                            raise Exception("invalid duration: '{}'".format(field))
                    setattr(rule, lhs + 'Duration', duration)
                elif lhs == 'file':
                    rule.fileName = rhs.replace('\\', '/')
                    if not os.path.isfile(os.path.join(baseLocation, rule.fileName)):
                        raise Exception("missing file: '{}'".format(rhs))
                else:
                    raise Exception("invalid key '{}'".format(lhs))
            for tagUid in tagUids:
                config[tagUid] = rule
        except Exception, e:
            raise Exception('{} line {}: {}'.format(configName, lineNum, str(e)))
    return config

class TagPoller:
    def __init__(self):
        self.isFirstPoll = True
        self.activeTagUid = None
        self.readFailCount = None
        self.readSuccessTime = None
        self.tagUidReader = TagUidReader()        
    def pollTagUidAndHasChanged(self):
        tagUid = self.tagUidReader.readTagUid()
        hasChanged = self.isFirstPoll
        self.isFirstPoll = False
        if tagUid:
            self.readFailCount = 0
            self.readSuccessTime = monotonic()
            if tagUid != self.activeTagUid:
                self.activeTagUid = tagUid
                hasChanged = True
        elif self.activeTagUid:
            failCountExceeded = self.readFailCount == 4
            if not failCountExceeded:
                self.readFailCount = self.readFailCount + 1
            failDurationExceeded = monotonic() - self.readSuccessTime > 0.5
            if failCountExceeded and failDurationExceeded:
                self.activeTagUid = None
                self.readFailCount = None
                self.readSuccessTime = None
                hasChanged = True
        return self.activeTagUid, hasChanged

class Main:
    def __init__(self):
        self.config = None
        self.isFirstPoll = True
        self.tagPoller = TagPoller()
        self.initRule()
        self.poll()
        gui.root.mainloop()
        GPIO.cleanup()

    def initRule(self):
        self.currentRule = None
        self.ruleRunningSince = 0.0
        self.minDurationReached = True
        self.maxDurationReached = True
        self.tagLostSince = None

    def updateTagLostSince(self, tagUid, now):
        if tagUid is None:
            if self.tagLostSince is None:
                self.tagLostSince = now
        else:
            self.tagLostSince = None

    def processCurrentRule(self, tagUid, now, videoDoneNow):
        if self.currentRule is None:
            return
        if not self.maxDurationReached:
            if not self.minDurationReached:
                if self.currentRule.minDuration == 'forever':
                    pass
                elif self.currentRule.minDuration == 'end':
                    if videoDoneNow:
                        self.minDurationReached = True
                else:
                    if now - self.ruleRunningSince >= self.currentRule.minDuration:
                        self.minDurationReached = True
            if tagUid is None and self.minDurationReached:
                if self.currentRule.lostDuration == 'forever':
                    pass
                elif self.currentRule.lostDuration == 'end':
                    if videoDoneNow:
                        self.maxDurationReached = True
                else:
                    if now - self.tagLostSince >= self.currentRule.lostDuration:
                        self.maxDurationReached = True
                        gui.clear()
        if not self.maxDurationReached:
            if self.currentRule.maxDuration == 'forever':
                if videoDoneNow:
                    gui.showFile(self.currentRule.fileName, loop=False)
            elif self.currentRule.maxDuration == 'end':
                if videoDoneNow:
                    self.maxDurationReached = True
            else:
                if now - self.ruleRunningSince >= self.currentRule.maxDuration:
                    self.maxDurationReached = True
                    gui.clear()

    def processNewRule(self, tagUid, now):
        rule = None
        if tagUid is None:
            if self.maxDurationReached:
                rule = self.config.get('none', None)
                if rule is None:
                    self.initRule()
        else:
            rule = self.config.get(tagUid, None)
            if rule is None:
                rule = self.config.get('unknown', None)
                
        if rule is not None and rule is not self.currentRule:
            self.currentRule = rule
            self.ruleRunningSince = now
            self.minDurationReached = False
            self.maxDurationReached = False
            loop = (tagUid is None or (rule.minDuration != 'end' and rule.lostDuration != 'end')) \
                and rule.maxDuration == 'forever'
            gui.showFile(rule.fileName, loop=loop)
        
    def runConfig(self, tagUid, now, videoDoneNow):
        self.updateTagLostSince(tagUid, now)
        self.processCurrentRule(tagUid, now, videoDoneNow)
        self.processNewRule(tagUid, now)
        
    def poll(self):
        global config
        gui.root.after(50, self.poll)

        configHasChanged = self.isFirstPoll
        self.isFirstPoll = False

        if os.path.isfile(configLocation):
            if self.config is None:
                configHasChanged = True
                try:
                    self.config = readConfig()
                except Exception, e:
                    gui.showError("Error reading configuration:\n{}".format(str(e)))
                    self.config = 'bad'
        else:
            if self.config is not None:
                configHasChanged = True
                self.config = None

        tagUid, tagHasChanged = self.tagPoller.pollTagUidAndHasChanged()
        videoDoneNow = gui.updateVideoPollDoneNow()

        if configHasChanged:
            self.initRule()
            cacheMaker.clear()
                
        if self.config is None:
            if configHasChanged or tagHasChanged:
                gui.showHelpWithTagUid(tagUid)
        elif self.config != 'bad':
            now = monotonic()
            if configHasChanged:
                self.currentRule = startupRule
                self.ruleRunningSince = now
                self.minDurationReached = False
                self.maxDurationReached = False
                gui.showStartupMessage()
            self.runConfig(tagUid, now, videoDoneNow)
        
        gui.root.update_idletasks()

gui = Gui()
main = Main()
