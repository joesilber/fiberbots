'''
	M. Schubnell, January 2017
	This function will reset the SBIG usb connection. It relies on the
	C program 'usbreset.c' and the executable 'usbreset' has to be in the same
	location as the python script.
	C code source:  http://marc.info/?l=linux-usb&m=121459435621262&w=2

	Usage:
		import usbreset
		usbreset.resetSBIG()


	Additional information:	

	Edit the c code (usbreset.c) if necessary and recompile:
    $ cc usbreset.c -o usbreset
	$ chmod +x usbreset

    Get the Bus and Device ID of the USB device you want to reset:

    $ lsusb  
    Bus 002 Device 003: ID 0fe9:9010 DVICO  

    Instead of using this python module the usb bus/device can be reset by executing the code from the
    command line (Make necessary substitution for <Bus> and <Device> ids as found by running the lsusb command):

    $ sudo ./usbreset /dev/bus/usb/002/003  

'''

import subprocess
import re

def resetSBIG():
	device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
	df = subprocess.check_output("lsusb")
	df=df.decode('utf-8')
	devices = []
	for i in df.split('\n'):
	    if i:
	        info = device_re.match(i)
	        if info:
	            dinfo = info.groupdict()
	            dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
	            devices.append(dinfo)
	for d in devices:
		if 'Santa Barbara' in d['tag']: device=d['device']
	print(device)	
	subprocess.call(["/home/msdos/dos_products/posfidfvc/SBIG/usbreset",device])

if __name__=="__main__":
	resetSBIG()
