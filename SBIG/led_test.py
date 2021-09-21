import numpy as np
import sbigcam
import os
import multicens
import sys
#import matplotlib as plt
import serial, struct

def flip_horizontal(img):
	img = np.fliplr(img)
	return img
def flip_vertical(img):
	img = np.flipud(img)
	return img


class LedIlluminator(object):
	def __init__(self):
		self.arduino = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
		#print(self.arduino)
	def set_intensity(self,bright):
		try:
			ibright=int(bright)
			if ibright>=0 and ibright <256:
				r=self.arduino.write(struct.pack('>BBB',8,8,ibright))
				status='SUCCESS'
		except:
			status='FAIL'
		return status


class STF(object):

	def __init__(self):
		VERBOSE=False
		self.cam=sbigcam.SBIGCam()
		self.cam.select_camera('ST8300')
		self.cam.set_fast_mode(fast_mode=True)
		#cam.set_window_mode(top=400, left=450)
		#cam.set_image_size(2200,1400)
		try:
			self.cam.close_camera() # in case driver was previously left in "open" state
		except:
			pass
		self.cam.verbose=VERBOSE
		self.cam.open_camera()
		self.cam.set_exposure_time(200)
		self.cam.set_dark(False)
		self.nspots=1
		self.size_fitbox=7
	def expose_and_centroid(self):
		img = flip_horizontal(self.cam.start_exposure())
		#print(L[0:10])
		#img = np.array(L,dtype = np.int32)
		xCenSub, yCenSub, peaks, FWHMSub, filename =multicens.multiCens(img, n_centroids_to_keep=1, verbose=True, write_fits=False,size_fitbox=self.size_fitbox)
		#energy=[FWHMSub[i]*(peaks[i]/max_counts) for i in range(len(peaks))]
		#print(" Spot  x y FWHM Peak LD  ",xCenSub, yCenSub, peaks, FWHMSub)
		return xCenSub, yCenSub, peaks, FWHMSub


if __name__ == '__main__':
	import time
	stf=STF()
	led=LedIlluminator()
	time.sleep(2)
#	led.set_intensity(100)
	for brightness in range(255,0,-5):
		led.set_intensity(brightness)
		try:
			xCenSub, yCenSub, peaks, FWHMSub=stf.expose_and_centroid()
			print(" brightness x y FWHM Peak LD  ",brightness,xCenSub, yCenSub, peaks, FWHMSub)
		except:
			print("ouch")
			pass	