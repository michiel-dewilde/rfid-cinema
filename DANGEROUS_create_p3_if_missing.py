import os, subprocess
devnull = open(os.devnull, 'w')

def createP3IfMissing():
    subprocess.check_call(['/usr/bin/sudo', '/sbin/partprobe', '/dev/mmcblk0'])
    if os.path.exists('/dev/mmcblk0p3'):
        return
    freeText = subprocess.check_output(['/usr/bin/sudo', '/sbin/sfdisk', '-Fq', '/dev/mmcblk0'])
    firstFree, lastFree = [int(s) for s in freeText.splitlines()[1:][-1].split()[0:2]]
    align = 8192
    partBegin = align * ((firstFree + align - 1) // align)
    partSize = lastFree - partBegin + 1
    if partSize <= align:
        raise Exception('insufficient space')
    proc = subprocess.Popen(['/usr/bin/sudo', '/sbin/sfdisk', '-aq', '--no-reread', '--no-tell-kernel', '-W', 'always', '/dev/mmcblk0'], stdin=subprocess.PIPE, stderr=devnull)
    proc.communicate('start=%d,size=%d,type=da\n' % (partBegin, partSize))
    if proc.wait() != 0:
        raise Exception('sfdisk failed')    
    subprocess.check_call(['/usr/bin/sudo', '/sbin/partprobe', '/dev/mmcblk0'])
    subprocess.check_call(['/usr/bin/sudo', '/sbin/losetup', '/dev/loop0', '/dev/mmcblk0p3'])
    subprocess.check_call(['/usr/bin/sudo', '/bin/dd', 'if=/dev/zero', 'of=/dev/loop0', 'bs=512', 'count=1'], stderr=devnull)
    proc = subprocess.Popen(['/usr/bin/sudo', '/sbin/sfdisk', '-q', '--no-reread', '--no-tell-kernel', '-w', 'always', '-W', 'always', '/dev/loop0'], stdin=subprocess.PIPE, stderr=devnull)
    proc.communicate('label:dos\nstart=%d,size=%d,type=c\n' % (align, partSize-align))
    if proc.wait() != 0:
        raise Exception('sfdisk failed')
    subprocess.check_call(['/usr/bin/sudo', '/sbin/partprobe', '/dev/loop0'])
    subprocess.check_call(['/usr/bin/sudo', '/sbin/mkfs.vfat', '/dev/loop0p1'], stdout=devnull)
    subprocess.check_call(['/usr/bin/sudo', '/sbin/losetup', '-d', '/dev/loop0'])    
    
createP3IfMissing()
