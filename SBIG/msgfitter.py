"""
gaussian fitter
M. Schubnell, University of Michigan
"""
import numpy as np
from numpy import sqrt, exp, ravel, arange
from scipy import optimize
from pylab import indices

def gauss(x, *p):
	A, mu, sigma = p
	return A*exp(-(x-mu)**2/(2.*sigma**2))

def gaussian(bias,height, center_x, center_y, width_x, width_y):
	"""Returns a gaussian function with the given parameters"""
	width_x = float(width_x)
	width_y = float(width_y)
	return lambda x,y: bias+height*exp(-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)

def moments(data):
	"""Returns (height, x, y, width_x, width_y)
		the gaussian parameters of a 2D distribution by calculating its
		moments
	"""
	#total = data.sum()
	#bias=data.mean()
	bias=np.min(data) # revised by Kai to make faint object detection easier
	data_this=data-bias
	total=data_this.sum()
	X, Y = indices(data.shape)
	x = (X*data_this).sum()/total
	y = (Y*data_this).sum()/total
	col = data_this[:, int(y)]
	width_x = sqrt(abs((arange(col.size)-y)**2*col).sum()/col.sum())
	row = data_this[int(x), :]
	width_y = sqrt(abs((arange(row.size)-x)**2*row).sum()/row.sum())
	height = data_this.max()
	return bias, height, x, y, width_x, width_y

def fitgaussian(data):
	"""Returns (height, x, y, width_x, width_y)
	the gaussian parameters of a 2D distribution found by a fit"""
	params = moments(data)
	errorfunction = lambda p: ravel(gaussian(*p)(*indices(data.shape)) -data)
	p, success = optimize.leastsq(errorfunction, params)
	return p
