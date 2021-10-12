import sbigcam

cam=sbigcam.SBIGCam()
cam.verbose = True
cam.select_camera('ST8300')
cam.close_camera() # in case driver was previously left in "open" state
cam.open_camera()      
cam.set_temperature_regulation('on', ccdSetpoint=0) #turning on regulation to 10 degrees celsius
input('Camera is cooling, press enter to free camera for use by other scripts.')
cam.close_camera()
