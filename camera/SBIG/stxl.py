import time
import warnings
import numpy as np
import sbigcam
import os


def flip_horizontal(img):
	img = np.fliplr(img)
	return img
def flip_vertical(img):
	img = np.flipud(img)
	return img

cam=sbigcam.SBIGCam()
cam.select_camera('STX')
#cam.set_fast_mode(fast_mode=True)
try:
	cam.close_camera() # in case driver was previously left in "open" state
except:
	pass	
cam.verbose=True
cam.open_camera()   
cam.set_exposure_time(200)
cam.set_dark(False)
cam.start_exposure
start = time.time()
L = flip_horizontal(cam.start_exposure())
print('Time for readout:', time.time()-start, 'seconds.')
filename = 'sbig_image.fits'
try:
	os.remove(filename)
except:
	print('couldn''t remove file: ' + filename)
cam.write_fits(L,filename)
print("All done. Wrote file 'sbig_image.fits'")
