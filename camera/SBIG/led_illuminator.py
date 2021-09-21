import serial, struct
import time

class LedIlluminator(object):
	def __init__(self):
		self.arduino = serial.Serial('/dev/serial/by-id/usb-Adafruit_Adafruit_Metro_328_ADAQKbKpR-if00-port0', 9600, timeout=1)
		time.sleep(2)
		self.fiber={el:(0,0) for el in range(0,39)}
		# yes, i know, this can be done with 'range'
		n=0
		for row in [0,2,4,6,8]:
			for column in [1,3,5,7,9,11,13,15]:
				self.fiber[n]=(column,row)
				n=n+1
		#print(self.arduino)
	def set_single_pix(self,x,y,bright):
		try:
			x=int(x)
			y=int(y)
		except:
			return 'FAIL'	
		try:
			ibright=int(bright)
			if ibright>=0 and ibright <256:
				r=self.arduino.write(struct.pack('>BBB',x,y,ibright))
				status='SUCCESS'
		except:
			status='FAIL'
		return status
	def set_halo(self,x,y,d,bright):
		''' set all pixel surrounding (x,y) to brightness bright
			d is the distance from the center pixel'''
		try:
			x=int(x)
			y=int(y)
			d=int(d)
		except:
			return 'FAIL'	
		try:
			ibright=int(bright)
			if ibright>=0 and ibright <256:
				xx=[x-d,x,x+d,x-d,x+d,x-d,x,x+d]
				yy=[y+d,y+d,y+d,y,y,y-d,y-d,y-d]
				ib=[ibright,ibright,ibright,ibright,ibright,ibright,ibright,ibright]
				self.set_multi_pix(xx,yy,ib)
				status='SUCCESS'
		except:
			status='FAIL'
		return status
	def set_far_halo(self,x,y,bright):
		''' set all pixel surrounding (x,y) to brightness bright'''
		try:
			x=int(x)
			y=int(y)
		except:
			return 'FAIL'	
		try:
			ibright=int(bright)
			if ibright>=0 and ibright <256:
				xx=[x-2,x,x+2,x-2,x+2,x-2,x,x+2]
				yy=[y+2,y+2,y+2,y,y,y-2,y-2,y-2]
				ib=[ibright,ibright,ibright,ibright,ibright,ibright,ibright,ibright]
				self.set_multi_pix(xx,yy,ib)
				status='SUCCESS'
		except:
			status='FAIL'
		return status


	def set_multi_pix(self,x,y,bright):
		try:
			x=[int(e) for e in x]
			y=[int(e) for e in y]
		except:
			return 'FAIL'	
		try:
			bright=[int(b) for b in bright]
#			if ibright>=0 and ibright <256:
			for ix,iy,ibright in zip(x,y,bright):
				r=self.arduino.write(struct.pack('>BBB',ix,iy,ibright))
			status='SUCCESS'
		except:
			status='FAIL'
		return status	
	def set_array(self,bright):
		try:
			ibright=int(bright)
			if ibright>=0 and ibright <256:
				for x in range (0,16):
					for y in range (0,9):
						r=self.arduino.write(struct.pack('>BBB',x,y,ibright))
				status='SUCCESS'
		except:
			status='FAIL'
		return status
	def _set_fiber(self,fiberpos,bright):
		# convinience function
		# fiberpos is a list of positions in the fibner block that have fibers [0 to 39]
		# bright is the corresponding brightness
		# let's create a dictionary with the position as the key and the x,y as values
		x,y=self.fiber[fiberpos]
		self.set_single_pix(x,y,bright)




