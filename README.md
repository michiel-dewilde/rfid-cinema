## rfid-cinema
Documentation as embedded in the installed software:
```
This is a presentation system showing a video or an image when the associated RFID tag is presented.
This system was originally developed for O Lab Overbeke, Habbekrats Wetteren and faro.be
by Michiel De Wilde <michiel.dewilde@gmail.com>.

Insert a USB stick with a file named '{}'.
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

This message is shown because the '{}' file (or the entire USB stick) is missing.
Normal functionality is resumed immediately after inserting a configured stick.
```
## Installation
- Download Raspbian image from https://www.raspberrypi.org/downloads/raspbian/
  (Our image was 2018-06-27-raspbian-stretch.zip)
- Download Etcher from https://etcher.io/
- Use Etcher to flash Raspbian to the Micro SD card
- Install the SD card
- Connect screen, keyboard, mouse, ethernet
- Boot
- "Welcome to Raspberry Pi"
  - Localization
    - Country: Belgium
    - Language: Flemish
    - Timezone: Brussels
  - Password `raspberry`
  - Skip Select WiFi network
  - Check for Updates
  - `sudo reboot` (open a terminal to enter commands marked like this)
- Configure keyboard (as needed)
  - `sudo dpkg-reconfigure keyboard-configuration`
    - English (US)
    - Enable CTRL-ALT-backspace
  - `sudo reboot`
- Configure raspberry pi
  - `sudo raspi-config`
    - Boot Options > Wait for Network at Boot > No
    - Boot Options > Splash Screen > Yes
    - Interfacing Options > SSH > Yes
    - Interfacing Options > VNC > Yes
    - Interfacing Options > SPI > Yes
    - Advanced Options > Overscan > No
    - Advanced Options > Audio > Force HDMI
    - Advanced Options > Resolution > CEA Mode 16 1920x1080 60Hz 16:9
    - Finish (reboot)
- (Optionally, connect now over VNC, then you can copy-paste)
- Open File Browser, Edit > Preferences > Uncheck automount options
- Install packages
  - `sudo apt-get update`
  - `sudo apt-get dist-upgrade`
  - `sudo apt-get install emacs exfat-fuse exfat-utils git ntfs-3g omxplayer python python-dev python-pil python-pil.imagetk python-repoze.lru python-monotonic usbmount`
  - `sudo reboot`
  - `sudo rpi-update`
  - `sudo reboot`
- Configure usbmount
  - `sudo nano /etc/usbmount/usbmount.conf`
    - Add "`ro,`" to the beginning of the comma separated list of `MOUNTOPTIONS`
  - `sudo nano /lib/systemd/system/systemd-udevd.service`
    - Change `MountFlags=slave` to `MountFlags=shared`
- `sudo nano /boot/config.txt`
  - Uncomment (remove '`#`') `hdmi_drive=2`
  - Disable wifi and bluetooth
    - Add to the end:
      ```
      # Disable wifi and bluetooth
      dtoverlay=pi3-disable-wifi
      dtoverlay=pi3-disable-bt
      ```
- Install SPI-Py
  - `cd`
  - `git clone https://github.com/lthiery/SPI-Py.git`
  - `cd SPI-Py`
  - `sudo python setup.py install`
- Install rfid-cinema
  - `cd`
  - `git clone https://github.com/michiel-dewilde/rfid-cinema.git`
  - `cd rfid-cinema`
  - `./register-autostart.sh`
- Install pishrink
  - `cd`
  - `git clone https://github.com/Drewsif/PiShrink.git`
- Set audio volume to 100%
- Make read only (https://gitlab.com/larsfp/rpi-readonly)
  - `cd`
  - `git clone https://gitlab.com/larsfp/rpi-readonly.git`
  - `cd rpi-readonly`
  - `sudo ./setup.sh.jessie`
  - `sudo apt-get autoremove`
  - `sudo systemctl enable watchdog`
  - `sudo systemctl disable dhcpcd`
  - `ln -fs /tmp/.Xauthority /home/pi/.Xauthority`
  - `sudo reboot`
- Backup memory card to USB stick
  - Insert exFAT formatted usb stick (bigger than the Micro SD card)
  - `sudo mount -t exfat /dev/sda /media/usb0`
  - `sudo dd if=/dev/mmcblk0 of=/media/usb0/rfid-cinema.img bs=524288`
  - `sudo mount -o remount,rw /`
  - `cd ~/PiShrink`
  - `sudo ./pishrink.sh -s /media/usb0/rfid-cinema.img`
  - `sudo umount /media/usb0`
  - Remove the USB stick and zip rfid-cinema.img to rfid-cinema.zip. With Etcher you can rewrite the Micro SD card from this zipfile as needed.