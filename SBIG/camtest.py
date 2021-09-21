# basic script to take an image with the STF8300
# MS, University of Michigan 
import time
import warnings
import numpy as np
import sbigcam
import os
import multicens
import usbreset

def flip_horizontal(img):
	img = np.fliplr(img)
	return img
def flip_vertical(img):
	img = np.flipud(img)
	return img

take_darks=False
verbose=True
write_fits=False

#imdata=[]
cam=sbigcam.SBIGCam()
cam.select_camera('ST8300')
cam.verbose=True
try:
	cam.close_camera() # in case driver was previously left in "open" state
except:
	pass	

cam.open_camera()   
cam.set_exposure_time(200)
cam.set_dark(take_darks)
#cam.start_exposure
f=open('camdata2017-01-16b.dat','w')
for i in range (2000):
	try:
		L = flip_horizontal(cam.start_exposure())
	except:
		usbreset.resetSBIG()
		f.write("USB reset \n")
	#if not(take_darks):
	  #  D = np.zeros(np.shape(L), dtype=np.int32)
	LD = np.array(L,dtype = np.int32) #- np.array(D,dtype = np.int32)

	xcen, ycen, fwhm, binfile = multicens.multiCens(LD, 11, verbose, write_fits)
	#print(i, xcen, ycen, fwhm)
	print(i)
	#imdata.append([i, xcen, ycen, fwhm, binfile])
	f.write(str([i, xcen, ycen, fwhm])+"\n")

	#filename = 'sbig_image'+str(i)+'.fits'

	#cam.write_fits(L,filename)

f.close()

