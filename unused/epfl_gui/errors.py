#cython: language_level=3
class Error(Exception):
	"""Base class for custom errors"""
	
class OutOfRangeError(Error):
	"""Error raised when a parameter is out of range"""

class CANError(Error):
	"""Error raised when the CAN communication encountered an error"""
