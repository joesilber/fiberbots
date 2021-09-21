import time
import multicens
import numpy as np
import gc
import sbigcam
import os
from astropy.io import fits

class SBIG_Grab_Cen(object):
	"""Module for grabbing images and calculating centroids using the SBIG camera.
	"""
	def __init__(self, save_dir='', size_fitbox=4, write_bias=False):  
		self.__exposure_time = 200 # milliseconds, 90 ms is the minimum
		self._cam_init()
		self.min_brightness = 200
		self.max_brightness = 60000
		self.min_num_nonzero_pixels = 100
		self.verbose = False
		self.write_fits = True
		self.take_darks = False #True # whether to measure a dark image and subtract it out
		self.write_bias = write_bias
		self.subtract_bias = True #True # wheather to subtract bias image
		self.flip_horizontal = True # whether to reflect image across y axis
		self.flip_vertical = False # whether to reflect image across x axis
		self.save_dir = save_dir
		self.size_fitbox = size_fitbox # gaussian fitter box dimensions are 2*size_fitbox X 2*size_fitbox

	def _cam_init(self, temperature=10):
		self.cam=sbigcam.SBIGCam()
		self.cam.select_camera('ST8300')
		self.close_camera() # in case driver was previously left in "open" state
		self.open_camera()      
		self.cam.set_exposure_time(self.exposure_time)
		self.cam.set_temperature_regulation('on', ccdSetpoint=temperature) #turning on regulation to 10 degrees celsius

	@property
	def exposure_time(self):
		return self.__exposure_time

	@exposure_time.setter
	def exposure_time(self, exposure_time):
		self.__exposure_time = int(exposure_time)
		self.cam.set_exposure_time(self.exposure_time)

	def grab(self, nWin=1, n_retries=3):
		"""Calls function to grab light and dark images from SBIG camera, then centroids spots.
		
		INPUTS:
			nWin       ... integer, number of centroid windows. For the measure_camera_scale script, nwin should be equal 1
			n_retries  ... integer, max number of recursive retries in certain cases of getting an error
	
		RETURNS
			xy         ... list of centroid coordinates for each spot
			peaks      ... list of values of peak brightness for each spot
			fwhms      ... list of values of fwhm for each spot
			time       ... elapsed time in seconds
			imgfiles   ... filenames of images produced
		 """
		imgfiles = []
		tic = time.time()
		if self.take_darks:
			if self.verbose:
				print("Taking dark image...")
			self.cam.set_dark(True)
			D = self.start_exposure()
			D = self.flip(D)
			if self.write_fits:
				filename = self.save_dir + 'SBIG_dark_image.FITS'
				try:
					os.remove(filename)
				except:
					print('couldn''t remove file: ' + filename)
				self.cam.write_fits(D,filename)
				imgfiles.append(filename)                
		else:
			D = None             

		if self.verbose:
			print("Taking light image...")
		self.cam.set_dark(False)
		L = self.start_exposure()
		L = self.flip(L)


		if self.subtract_bias:
			if self.verbose:
				print("Subtracting Bias Image...")
			filename = self.save_dir + 'SBIG_bias_image.FITS'
			try:
				hdul = fits.open(filename)
				B = hdul[0].data 
			except:
				B = np.zeros(np.shape(L), dtype=np.int32)
				print('No Bias file: ' + filename)
		else:
			B = np.zeros(np.shape(L), dtype=np.int32) 

		if self.write_fits:
			filename = self.save_dir + 'SBIG_light_image.FITS'
			try:
				os.remove(filename)
			except:
				if self.verbose:
					print('couldn''t remove file: ' + filename)
			self.cam.write_fits(L,filename)
			imgfiles.append(filename)
		if self.write_bias:
			a=input('Warning! Do you really want to save a bias frame?')
			if a == 'N' or a == 'n' or a=='no' or a=='No' or a=='NO':
				print('Please change self.write_bias in sbig_grab_cen.py to False')
				import sys; sys.exit()
			filename_bias=self.save_dir + 'SBIG_bias_image.FITS'
			try:
				os.remove(filename_bias)
			except:
				pass
			self.cam.write_fits(L,filename_bias)
			print('Save Bias successfully. Please change self.write_bias in sbig_grab_cen.py to False')
			import sys; sys.exit()
		
		if not(self.take_darks):
			D = np.zeros(np.shape(L), dtype=np.int32)
		LD = np.array(L,dtype = np.int32) - np.array(D,dtype = np.int32)  - np.array(B,dtype = np.int32)
		if self.write_fits and (self.take_darks or self.subtract_bias):
			filename = self.save_dir + 'SBIG_diff_image.FITS'
			try:
				os.remove(filename)
			except:
				pass
			self.cam.write_fits(LD,filename)
			imgfiles.append(filename)
		del L
		gc.collect()
		
		brightness = np.amax(LD)
		if self.verbose:
			print('Brightness: ' + str(brightness))
		if brightness < self.min_brightness:
			print('Warning: the brightest spot in the image is undersaturated. Value = ' + str(brightness))
		elif brightness > self.max_brightness:
			print('Warning: the brightest spot in the image is oversaturated. Value = ' + str(brightness))
		del D
		gc.collect()

		# call routine to determine multiple gaussian-fitted centroids
		centroiding_tic = time.time()
		xcen, ycen, peaks, fwhms, binfile = multicens.multiCens(LD, nWin, self.verbose, self.write_fits, save_dir=self.save_dir, size_fitbox=self.size_fitbox)
		minimum = min(peaks)        
		if minimum < self.min_brightness and n_retries > 0:
			print('Retrying image grab (' + str(n_retries) + ' attempts remaining) after got back a very low peak brightness value = ' + str(minimum) + ' at (' + str(xcen[peaks.index(minimum)]) +', ' + str(ycen[peaks.index(minimum)]) + ')')
			return self.grab(nWin, n_retries-1)
			
		if binfile:
			imgfiles.append(binfile)
		xy = [[xcen[i],ycen[i]] for i in range(len(xcen))]
		centroiding_toc = time.time()
		if self.verbose:
			print('centroiding time: ' + str(centroiding_toc - centroiding_tic))
		
		toc = time.time()
		if self.verbose:
			print("Time used: "+str(toc-tic)+"\n")
		
		return xy,peaks,fwhms,tic-toc,imgfiles
		
	def open_camera(self):
		self.cam.open_camera()
		self.cam.initialize_shutter()
		
	def close_camera(self):
		self.cam.close_camera()
		
	def start_exposure(self):
		'''Wraps the usual start_exposure function with some mild error handling.
		'''
		def expose():
			img = self.cam.start_exposure()
			no_img = not(isinstance(img,np.ndarray))
			num_nonzero_pixels = np.count_nonzero(img)
			all_black = num_nonzero_pixels == 0
			nearly_all_black = num_nonzero_pixels < self.min_num_nonzero_pixels
			return img,no_img,all_black,nearly_all_black,num_nonzero_pixels
		img,no_img,all_black,nearly_all_black,num_nonzero_pixels=expose()
		if no_img or all_black or nearly_all_black:
			if no_img:
				desc = 'no image'
			elif all_black:
				desc = 'a completely black image'
			else:
				desc = 'an image with only ' + str(num_nonzero_pixels) + ' non-black pixels'
			print('The camera returned ' + desc + ', indicating a possible readout failure. Will attempt to re-initialize the camera and keep going.')
			self._cam_init()
			img,no_img,all_black,nearly_all_black,num_nonzero_pixels=expose()
			if no_img or all_black or nearly_all_black:
				raise ValueError('Image not good, try restarting the camera.')
		return img

	def flip(self, img):
		if self.flip_horizontal:
			img = np.fliplr(img)
		if self.flip_vertical:
			img = np.flipud(img)
		return img
	
