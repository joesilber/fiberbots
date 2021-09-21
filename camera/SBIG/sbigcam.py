'''
sbigcam.py 
March 2016

Author: Kevin Fanning (kfanning@umich.edu) referencing sbigudrv.h

Requires: ctypes*, platform*, numpy, pyfits, time*
*Refers to packages in Python's Standard Library

1.  you need to install the SBIG driver (libsbigudrv.so) to /usr/local/lib. 
    Drivers for ARM, 32-bit and 64 bit Intel processors are in the 
    svn (focalplane/test_stand_control/trunk/camera_code/SBIG_dev).
2.  copy 51-sbig-debian.rules into /etc/udev/rules.d 
    (the rules file is also in the SBIG_Dev directory)
3.  point LD_LIBRARY_PATH to /usr/local/lib

Function:   When run as main, takes image from SBIG camera and 
            saves it as FITS file.

As module:  imports a class with many memeber functions allowing for 
            the control of an SBIG camera.
            First, import this by typing import SBIG, then create
            a camera object using object = SBIG.CAMERA().
            From here you have several member functions that are called
            using object.function(args), where object is your object's name,
            funtion is the funtion namem and args are any arguments
            the function might take.

There are several changable settings for an object:
 
The image resolution is set to 3352x2532 pixels by default as that is
the resolution STF-8300M. This can be changed by calling
set_resolution(width, height), where width and height are integer arguments.

The image is an exposure by default but can be set to a dark image by
calling object.SetDark(x) where ideally x is 0 (exposure) or 1 (dark image), 
but the function casts x as a bool to be safe.

The exposure time is 90ms by default, the shortest time that can be used. 
This can be changed by calling set_exposure(time) command where time is 
the exposure time in milliseconds. The longest exposure time avalible
is 3600000ms (1 hour). 

NOTE: Please use the setter functions rather than manually changing 
the object's elements, since the  setter functions cast the values 
into ctype values that are required for many of the camera commands.

The typical sequence for taking an exposure is as follows:
    import sbigcam
    cam = sbigcam.SBIGCam()
    cam.open_camera()
    cam.select_camera('ST8300')
    cam.set_exposure_time(100)
    cam.set_dark(False)
    image=cam.start_exposure()
    cam.write_fits(image,'Image.FITS')
    cam.close_camera()

Changelog:

160317-MS:  converted to python3 (print statements, raw_input)

160325-MS   renamed to sbigcam.py
            renamed methods to comply with Python convention
            added error checking, added method to write FITS file 
            
160424-MS   fixed exposure time error. The exposureTime item is in
            1/100 seconds (and not in msec)
            implemented fast readout mode (set_fast_mode)
            implemented window mode (set_window_mode)

160506-MS   added 'verbose=False' to constructor
            allowed exposure times of less than 90 ms (needed for bias frames)
            set default exposure time to 0
            Note: this will still be overwritten by the camera's FW for
            non-dark frames.

160721-dyt  added EndReadoutParams for reducing readout noice by freezing TEC.
            fixed bug when open_camera and close_camera are called repeatedly
            and return false.
            adding temperature regulation and query.
            it's best to enable auto_freeze, regulation mode 5.

160722-dyt  added self.CameraName to differentiate STF-8300M and ST-i cameras
            for customising features.
            added self.keepShutterOpen boolean flag for tests that require
            open shutter.
            added shutter open and close and other methods
            
161107-KF  Added initialize_shutter to allow one to "click" the shutter without
           needing to power cycle the camera. Added error handling using this
           function to start_exposure to avoid shutter errors.
           
170508-KF  Added barebones support for STXL-6303E cameras. Might need more
           wrestling to actually get it functioning but none are on hand.
           Added function headers to comply with DESI standards.

'''

from ctypes import CDLL, byref, Structure, c_bool, c_ushort, c_ulong, c_double, c_int, c_char, POINTER
from platform import system
import numpy as np
from astropy.io import fits
import time
import sys
import math
import pprint

CAMERA_TYPE = {4 : 'ST7',
               5 : 'ST8',
               6 : 'ST5C',
               7 : 'TCE_CONTROLLER',
               8 : 'ST237',
               9 : 'STK',
               10: 'ST9',
               11: 'STV',
               12: 'ST10',
               13: 'ST1K',
               14: 'ST2K',
               15: 'STL',
               16: 'ST402',
               17: 'STX',
               18: 'ST4K',
               19: 'STT',
               20: 'STI',
               21: 'STF',
               22: 'NEXT',
               0xFFFF : 'NO_CAMERA'}

class GetCCDInfoParams(Structure):
    _fields_ = [('request',                     c_ushort)]
        
# pixelWidth and Height are BCD encoded (n.mm)
# For example, for the STXL6303 the value returned is 2304 corresponding to 0x900 for the 0.0 micron pixels
class ReadoutInfo(Structure):
    _fields_ = [('mode',                            c_ushort),
                ('width',                           c_ushort),
                ('height',                          c_ushort),
                ('pixelWidth',                      c_ulong),
                ('pixelHeight',                     c_ulong)]

ReadoutInfoArray = (ReadoutInfo * 20)
class GetCCDInfoResults01(Structure):
    _fields_ = [('firmwareVersion',                 c_ushort),
                ('cameraType',                      c_ushort),
                ('name',                            c_char * 64),
                ('readoutModes',                    c_ushort),
                ('readoutInfo',                     ReadoutInfoArray)]

class GetCCDInfoResults2(Structure):
    _fields_ = [('badColumns',                 c_ushort),
                ('columns',                    c_ushort * 4),
                ('imagingABG',                 c_ushort),
                ('serialNumber',               c_char * 10)]

class GetCCDInfoResults3(Structure):
    _fields_ = [('adSize',                 c_ushort),
                ('FilterType',             c_ushort)]

class GetCCDInfoResults45(Structure):
    _fields_ = [('capabilitiesBits',      c_ushort),
                ('dumpExtra',             c_ushort)]

class GetCCDInfoResults6(Structure):
    _fields_ = [('cameraBits',                 c_ushort),
                ('ccdBits',                    c_ushort),
                ('extraBits',                  c_ushort)]

class GetErrorStringParams(Structure):
    _fields_ = [('errorNo',                          c_ushort)]

class GetErrorStringResults(Structure):
    _fields_ = [('errorString',                      c_char * 64)]

class USBInfo(Structure):
    _fields_ = [('cameraFound',                     c_bool),
                ('cameraType',                      c_ushort),
                ('name',                            c_char * 64),
                ('serialNumber',                    c_char * 10)]

USBInfoArray = (USBInfo * 4)
class QueryUSBResults(Structure):
    _fields_ = [('camerasFound',                 c_ushort),
                ('usbInfo',                      USBInfoArray)]
    
# Structures defined in sbigudrv.h
class OpenDeviceParams(Structure):
    _fields_ = [('deviceType',                      c_ushort),
                ('lptBaseAddress',                  c_ushort),
                ('ipAddress',                       c_ulong)]
                
class EstablishLinkResults(Structure):
    _fields_ = [('cameraType',                      c_ushort)]
    
class EstablishLinkParams(Structure):
    _fields_ = [('sbigUseOnly',                     c_ushort)]
                
class StartExposureParams2(Structure):
    _fields_ = [('ccd',                             c_ushort),
                ('exposureTime',                    c_ulong),
                ('abgState',                        c_ushort),
                ('openShutter',                     c_ushort),
                ('readoutMode',                     c_ushort),
                ('top',                             c_ushort),
                ('left',                            c_ushort),
                ('height',                          c_ushort),
                ('width',                           c_ushort)]
                
class EndExposureParams(Structure):
    _fields_ = [('ccd',                             c_ushort)]
    
class StartReadoutParams(Structure):
    _fields_ = [('ccd',                             c_ushort),
                ('readoutMode',                     c_ushort),
                ('top',                             c_ushort),
                ('left',                            c_ushort),
                ('height',                          c_ushort),
                ('width',                           c_ushort)]
                
class ReadoutLinesParams(Structure):
    _fields_ = [('ccd',                             c_ushort),
                ('readoutMode',                     c_ushort),
                ('pixelStart',                      c_ushort),
                ('pixelLength',                     c_ushort)]

class EndReadoutParams(Structure):
    _fields_ = [('ccd',                             c_ushort)]

class QueryCommandStatusParams(Structure):
    _fields_ = [('command',                         c_ushort)]

class QueryCommandStatusResults(Structure):
    _fields_ = [('status',                          c_ushort)]
    
#Color Wheel Command Structures
class CFWParams(Structure):
    _fields_ = [('cfwModel', c_ushort),
                ('cfwCommand', c_ushort),
                ('cwfParam1', c_ulong), #CHECK THIS, Typo present in docs, maybe not in code
                ('cfwParam2', c_ulong),
                ('*outPtr', c_char),
                ('inLength', c_ushort),
                ('*inPtr', c_char)]

class CFWResults(Structure):
    _fields_ = [('cfwModel', c_ushort),
                ('cfwPosition', c_ushort),
                ('cfwStatus', c_ushort),
                ('cfwError', c_ushort),
                ('cfwResult1', c_ulong),
                ('cfwResult2', c_ulong)]
  
# Temperature Regulation Commands
# regulation - 0=regulation off, 1=regulation on, 2=regulation override,
#              3=freeze TE cooler, 4=unfreeze TE cooler,
#              5=enable auto-freeze, 6=disable auto-freeze
# ccdSetpoint - CCD temperature setpoint in degrees Celsius.


class SetTemperatureRegulationParams2(Structure):
    _fields_ = [('regulation',                      c_int),
                ('ccdSetpoint',                     c_double)]

class QueryTemperatureStatusParams(Structure):
    _fields_ = [('request',                         c_int)]

class QueryTemperatureStatusResults(Structure):
    _fields_ = [('enabled',                  c_ushort),
                ('ccdSetpoint',              c_ushort),
                ('power',                    c_ushort),
                ('ccdThermistor',            c_ushort),
                ('ambientThermistor',        c_ushort)]

class QueryTemperatureStatusResults2(Structure):
    _fields_ = [('coolingEnabled',                  c_bool),
                ('fanEnabled',                      c_ushort),
                ('ccdSetpoint',                     c_double),
                ('imagingCCDTemperature',           c_double),
                ('trackingCCDTemperature',          c_double),
                ('externalTrackingCCDTemperature',  c_double),
                ('ambientTemperature',              c_double),
                ('imagingCCDPower',                 c_double),
                ('trackingCCDPower',                c_double),
                ('externalTrackingCCDPower',        c_double),
                ('heatsinkTemperature',             c_double),
                ('fanPower',                        c_double),
                ('fanSpeed',                        c_double),
                ('trackingCCDSetpoint',             c_double)]
					
class QueryTemperatureStatusResults1(Structure):
    _fields_ = [('coolingEnabled',                  c_bool),
                ('fanEnabled',                      c_ushort),
                ('ccdSetpoint',                     c_double),
                ('imagingCCDTemperature',           c_double),
                ('trackingCCDTemperature',          c_double),
                ('externalTrackingCCDTemperature',  c_double),
                ('ambientTemperature',              c_double),
                ('imagingCCDPower',                 c_double),
                ('trackingCCDPower',                c_double),
                ('externalTrackingCCDPower',        c_double),
                ('heatsinkTemperature',             c_double),
                ('fanPower',                        c_double)]

# struct MiscellaneousControlParams
#
#    fanEnable - set TRUE to turn on the Fan
#                On the STX/STT setting the fanEnable field to 0 turns off the fan. Setting fanEnable to 1 (or
#                greater than 100) sets the fan to Auto-Speed Control where the fan speed is determined by the
#                STX/STT firmware. Setting fanEnable to 2 through 100 sets the fan to manual control at 2 to
#                100% speed. Note that effective manual speed control is achieved with values between 20 and
#                100 as the fan doesn’t really start spinning at manual speeds below 20.
#    shutterCommand – 0=leave shutter alone, 1=open shutter, 2=close shutter, 3=reinitialize shutter, 4=open STL
#                     (STX) external shutter, 5=close ST-L (STX) external shutter
#    ledState – 0=LED off, 1=LED on, 2=LED blink at low rate, 3=LED blink at high rate
class MiscellaneousControlParams(Structure):
    _fields_ = [('fanEnable',                       c_bool),
                ('shutterCommand',                  c_ushort),
                ('ledState',                        c_ushort)]

# Enumerated codes taken from sbigudrv.h
# general use camera commands
CC_END_EXPOSURE                 = 2
CC_READOUT_LINE                 = 3
CC_QUERY_TEMPERATURE_STATUS     = 6
CC_ESTABLISH_LINK               = 9
CC_GET_CCD_INFO                 = 11
CC_QUERY_COMMAND_STATUS         = 12
CC_MISCELLANEOUS_CONTROL        = 13
CC_OPEN_DRIVER                  = 17
CC_CLOSE_DRIVER                 = 18
CC_END_READOUT                  = 25
CC_OPEN_DEVICE                  = 27
CC_CLOSE_DEVICE                 = 28
CC_START_READOUT                = 35
CC_GET_ERROR_STRING             = 36
CC_QUERY_USB                    = 40
CC_CFW                          = 43
CC_START_EXPOSURE2              = 50
CC_SET_TEMPERATURE_REGULATION2  = 51
# camera error base
CE_NO_ERROR                     = 0
CE_DEVICE_NOT_CLOSED            = 29
# CCD request
CCD_IMAGING                     = 0
# shutter command
SC_LEAVE_SHUTTER                = 0
SC_OPEN_SHUTTER                 = 1
SC_CLOSE_SHUTTER                = 2
SC_INITIALIZE_SHUTTER           = 3
# readout binning mode
RM_1X1                          = 0
# ABG_STATE7 - Passed to Start Exposure Command
ABG_LOW7                        = 0
# activate the fast readout mode of the STF-8300, etc.
EXP_FAST_READOUT                = 0x08000000
# LED State
LED_OFF                         = 0
LED_ON                          = 1
LED_BLINK_LOW                   = 2
LED_BLINK_HIGH                  = 3
# temperature regulation codes
REGULATION_OFF                  = 0
REGULATION_ON                   = 1
REGULATION_OVERRIDE             = 2
REGULATION_FREEZE               = 3
REGULATION_UNFREEZE             = 4
REGULATION_ENABLE_AUTOFREEZE    = 5
REGULATION_DISABLE_AUTOFREEZE   = 6
REGULATION_ENABLE_MASK          = 0x0001
REGULATION_FROZEN_MASK          = 0x8000

class SBIGCam(object):

   
    # prebuild dictionaries to avoid rebuilding upon each regulation call
    tempRegulationDict = {'off':                REGULATION_OFF,
                          'on':                 REGULATION_ON,
                          'override':           REGULATION_OVERRIDE,
                          'freeze':             REGULATION_FREEZE,
                          'unfreeze':           REGULATION_UNFREEZE,
                          'enable_autofreeze':  REGULATION_ENABLE_AUTOFREEZE,
                          'disable_autofreeze': REGULATION_DISABLE_AUTOFREEZE}
    # inverse mapping for displaying messages
    # regulationDictInv = {regulationDict[k]: k for k in regulationDict.keys()}
    
    def __init__(self, verbose=False):
        self.cameraName = 'No Camera Selected'
        self.DARK = 0 # Defaults to 0
        self.exposure = 0 # units 1/100 second (minimum exposure is 0.09 seconds)
        self.TOP = c_ushort(0)
        self.LEFT = c_ushort(0)
        self.FAST = 0
        # self.cam_model=cam_model
        self.WIDTH = 0
        self.HEIGHT = 0
        # Include sbigudrv.so
        if system() == 'Linux':
            self.SBIG = CDLL("/usr/local/lib/libsbigudrv.so")
        elif system() == 'Windows': # Note: Requires 32bit python to access 32bit DLL
            self.SBIG = CDLL('C:\\Windows\system\sbigudrv.dll')
        else: # Assume Linux
            self.SBIG = CDLL("/usr/local/lib/libsbigudrv.so")
        self.verbose = verbose
        self.keepShutterOpen = False
        self.setpoint = 0.0
        self.usb_info = {}   # cache USB info (can only be called when device is closed)
        self.cfw = None
        self.cfw_errors = ['No Error', 'CFW Busy', 'Bad Command', 'Calibration Error', 'Motor Timeout', 'Bad Model']

    ### SETTERS ###

    def keep_shutter_open(self, keepShutterOpen = False):
        """
        Set self.keepShutterOpen
        Input:
            Bool
        Returns:
            self.keepShutterOpen
        """
        if isinstance(keepShutterOpen, bool):
            self.keepShutterOpen = keepShutterOpen
        else:
            if self.verbose:
                print ('Invalid shutter option. Boolean required.')
        return self.keepShutterOpen

    def set_shutter(self, shutterState):
        """
        opens or closes shutter
        Input:
            'open' or 'closed'
        Returns:
            True if success
            False if failed
        """
        shutterState = str(shutterState)
        if shutterState in ['open', 'closed']:
            if shutterState == 'open':
                mcp = MiscellaneousControlParams(
                        shutterCommand = SC_OPEN_SHUTTER,
                        ledState = c_ushort(1))
            elif shutterState == 'closed':
                mcp = MiscellaneousControlParams(
                        shutterCommand = SC_CLOSE_SHUTTER,
                        ledState = c_ushort(1))
            Error = self.SBIG.SBIGUnivDrvCommand(
                       CC_MISCELLANEOUS_CONTROL, byref(mcp), None)
            if Error != CE_NO_ERROR:
                print("Setting shutter returned error:", Error)
                return False
            elif self.verbose:
                print("Shutter is now:", shutterState)
            return True
        else:
            print('Invalid shutter state, open and closed only.')
            return False

    def set_image_size(self, width, height):
        """
        sets the CCD chip size in pixels
        Input
            width: Integer, width of CCD
            height: Integer, height of CCD
        Returns:
            True if success
            False if failed
        """
        try:
            self.WIDTH = c_ushort(width)
            self.HEIGHT = c_ushort(height)
            return True
        except:
            return False

    def set_window_mode(self, top=0, left=0):
        try:
            self.TOP=c_ushort(top)
            self.LEFT=c_ushort(left)
            return True
        except:
            return False
            
    def select_camera(self, name='STF-8300M'):
        """
        sets the CCD chip size in pixels according to
        the camera model selected
        Input
            name: string, camera model (must be 'ST8300' or 'STi')
        Returns:
            True if success
            False if failed
        Default CCD size is for the SBIG STF-8300M
        """

        if name in ['ST8300', 'STi', 'STX']:   #L6303E']:
            try:
                if name == 'ST8300': 
                    self.cameraName = 'ST8300'
                    self.set_image_size(3352,2532)
                if name == 'STi':
                    self.cameraName = 'STi'
                    self.set_image_size(648,484)
                if name in 'STXL6303E':
                    self.cameraName = 'STX'  #L6303E'
                    self.set_image_size(3072,2048)
                    self.set_window_mode(3,16) #Prevents readout of the buffer
                return True
            except:
                print('could not select camera: ' + name)
                return False    
        else:
            print('Not a valid camera name (use "ST8300" or "STi" or "STX") ')
            return False
            
    def select_CFW(self, cfw):
        """
        Input cfw - string indicating name of cfw accessory
        Sets the correct int in self.cfw see page 22 of SBIGUDrv.pdf
        only about half of color wheels checked for, operating under
        assumption cameras are relatively new/ stxl or sft
        """
        if cfw.lower() == 'cfw-10':
            self.cfw = c_ushort(8)
        elif cfw.lower() == 'fw8-8300':
            self.cfw = c_ushort(16)
        elif 'fw8' in cfw.lower():
            self.cfw = c_ushort(18)
        elif cfw.lower() == 'fw5-8300':
            self.cfw = c_ushort(15)
        elif cfw.lower() == 'fw5-stx':
            self.cfw = c_ushort(14)
        elif cfw.lower() == 'fw7-stx':
            self.cfw = c_ushort(17)
        elif cfw == None:
            self.cfw = None
        else:
            self.cfw = c_ushort(8) #assume cfw-10 controls, seems like most will operate fine in this case

    def set_resolution(self, width,height):
        """
        wrapper for legacy method
        Input:
            int, int
        Returns:
            None
        """
        self.set_image_size(width,height)
        return

    def set_fast_mode(self, fast_mode=False):
        """
        Enables fast mode (only for STF-8300!)
        Input:
            Bool
        Return:
            None
        """
        if fast_mode:
            self.FAST=EXP_FAST_READOUT
        return

    def set_exposure_time(self, exp_time=90):
        """
        sets the exposure time in ms
        Input
            time: Integer, exposure time in ms (min: 90, max: 3600)
        Returns:
            True if success
            False if failed
        """
#       if exp_time < 90: exp_time = 90  removed to allow 0s bias frames
        if exp_time > 3600000: exp_time=3600000
        try:
            self.exposure = int(exp_time/10)
            return True
        except:
            return False
        return

    def set_dark(self, x=False):
        """
        Setter function
        Dark Frame:
        if x == True then shutter stays closed during exposure
        Input:
            Bool
        Return:
            None

        """
        self.DARK = bool(x)
        return
        
    def initialize_shutter(self):
        """
        Initializes (clicks) shutter, similar to what happens
        when power cycling. Should clear errors when start exposure
        fails to work.
        Input
            None
        Returns
            True if success, False otherwise
        """    
        mcp = MiscellaneousControlParams(True,SC_INITIALIZE_SHUTTER,LED_ON)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_MISCELLANEOUS_CONTROL,byref(mcp),None)
        if Error != CE_NO_ERROR:
            print ('Attempt to open initialize shutter returned error:', Error)
            return False
        elif self.verbose:
            print ('Shutter initialized.')
        # Wait for shutter to initialize
        qcspar = QueryCommandStatusParams(command = CC_MISCELLANEOUS_CONTROL)
        qcsres = QueryCommandStatusResults(status = 6)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_QUERY_COMMAND_STATUS, byref(qcspar), byref(qcsres))
        while qcsres.status == 2:
            Error = self.SBIG.SBIGUnivDrvCommand(CC_QUERY_COMMAND_STATUS, byref(qcspar), byref(qcsres))
        return True

    ### CAMERA COMMANDS ###

    def open_camera(self, deviceType = 'USB'):
        """
        initializes driver and camera, must be called before any other camera
        command
        Input:
            deviceType (USB (== next available USB camera), USB1, 2, 3, 4 (other types are not supported)
        Return:
            True if success
            False if failed
        """
        devicetypes = {'USB' : 0x7F00, 'USB1' : 0x7F02, 'USB2' : 0x7F03, 'USB3' : 0x7F04, 'USB4' : 0x7F05}
        assert deviceType in devicetypes,'Invalid device type requested'
        dt = devicetypes[deviceType]

        # Open Driver
        Error = self.SBIG.SBIGUnivDrvCommand(CC_OPEN_DRIVER, None, None)
        if Error == 21:
            print ('Code 21: driver already opened.')
        elif Error != CE_NO_ERROR:
            print ('Attempt to open driver returned error:', Error)
            return False
        elif self.verbose:
            print ('Driver successfully opened.')
     
        # Query USB bus
        try:
            info = self.query_usb()
            pprint.pprint(info)
        except Exception as e:            
            raise RuntimeError('Exception calling query_usb: %s' % str(e))

        found_camera = False
        if len(info['usbInfo']) == 0:
            raise RuntimeError('No USB camera found')
        if deviceType == 'USB':
            found_camera = True
        else:
            for i in range(len(info['usbInfo'])):
                if info['usbInfo'][i]['deviceType'] == deviceType:
                    if self.verbose:
                        print('Requested USB camera found')
                    found_camera = True
                    break
        if not found_camera:
            raise RuntimeError('Requsted USB camera not found (%r)' % deviceType)

        # Open Device
        odp = OpenDeviceParams(deviceType = dt)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_OPEN_DEVICE, byref(odp), None)
        if Error == 29:
            print ('Code 29: device already opened.')
        elif Error != CE_NO_ERROR:
            print ('Attempt to open device returned error:', Error)
            return False
        elif self.verbose:
            print ('Device successfully opened.')
        
        # Establish Link
        elp = EstablishLinkParams(sbigUseOnly = 0)
        elr = EstablishLinkResults()
        self.SBIG.SBIGUnivDrvCommand(CC_ESTABLISH_LINK, byref(elp), byref(elr))
        if elr.cameraType == 0xFFFF:
            print ('No camera found.')
            return False
        elif self.verbose:
            print ('Link successfully established. Camera type %r' % elr.cameraType)
        
        # Get CCD Info (tbd - use results to setup camera type, pixel array size etc)
        # info = self.get_camera_info()
        return True
        
    def query_usb(self):
        """
        Query the USB bus to detect up to 4 cameras.
        To Establish a link to a specific camera specify DEV_USB1, DEV_USB2, DEV_USB3 or
        DEV_USB4 in the device field of the Open Device command. DEV_USB1 corresponds to the
        camera described in usbInfo[0], DEV_USB2 corresponds to usbInfo[1], etc. If you specify
        USB_DEV in Open Device it opens the next available device.
        """
        qusbr = QueryUSBResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_QUERY_USB, None, byref(qusbr))
        if Error != CE_NO_ERROR:
            if Error == CE_DEVICE_NOT_CLOSED:
                self.usb_info['updated'] = False
                return self.usb_info     # return cached information
            else:
                raise RuntimeError('Attempt to query USB us returned error: %r' % Error)
        elif self.verbose:
            print ('USB bus information successfully retrieved.')
        info = {'camerasFound' : qusbr.camerasFound, 'usbInfo' : []}
        for i in range(min(4, qusbr.camerasFound)):
            ui = {}
            ui['cameraFound'] = qusbr.usbInfo[i].cameraFound
            ct = qusbr.usbInfo[i].cameraType
            ui['cameraType'] = str(ct) if ct not in CAMERA_TYPE else CAMERA_TYPE[ct]
            ui['deviceType'] = 'USB%d' % (i+1)
            ui['name'] = qusbr.usbInfo[i].name.decode('utf-8')
            ui['serialNumber'] = qusbr.usbInfo[i].serialNumber.decode('utf-8')
            info['usbInfo'].append(ui)
        info['updated'] = True
        self.usb_info = info      # cache information
        return info

    def get_error_string(self, err):
        """
        Returns a string describing driver error "err"
        """
        gesp = GetErrorStringParams(errorNo = err)
        gesr = GetErrorStringResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_GET_ERROR_STRING, byref(gesp), byref(gesr))
        if Error != CE_NO_ERROR:
            raise RuntimeError('Attempt to retrieve Error String (error = %r) returned error: %r' % (err, Error))
        elif self.verbose:
            print ('Driver Error String (error = %r) successfully retrieved.' % err)
        return gesr.errorString.decode('utf-8')

    def get_camera_info(self, request = 0):
        """
        Retrieve information about the camera and the CCD from the driver (and firmware)
        The function returns a dictionary but the key/values depend on what is requested.
        For the default, request = 0, the following is returned:
        {'firmwareVersion' : <integer>,
         'cameraType' : string,
         'name'  : string,
         'readoutInfo' [ modeInfo_0, modeInfo_1...]
        }

        Where modeInfo is a dictionary with these keys:
        mode : index (integer)
        width : number of pixels (width)
        height : number of pixels (height)
        pixelWidth : pixel size (width) in microns
        pixelHeight : pixel size (height) in microns

        The length of the readoutInfo list depends on the camera
        """
        
        # setup control structures
        gcip = GetCCDInfoParams(request = request)
        if request in  [0, 1]:
            gcir = GetCCDInfoResults01()        
        elif request in  [2]:
            gcir = GetCCDInfoResults2()
        elif request in  [3]:
            gcir = GetCCDInfoResults3()
        elif request in  [4, 5]:
            gcir = GetCCDInfoResults45()
        elif request in  [6]:
            gcir = GetCCDInfoResults6()
        else:
            raise RuntimeError('request type %r for get_camera_info command not yet implemented' % request)

        Error = self.SBIG.SBIGUnivDrvCommand(CC_GET_CCD_INFO, byref(gcip), byref(gcir))
        if Error != CE_NO_ERROR:
            raise RuntimeError('Attempt to retrieve CCD INFO (request = %r) returned error: %r' % (request, Error))
        elif self.verbose:
            print ('CCD INFO (request = %r) successfully retrieved.' % request)

        # support for different request modes
        info = {}
        if request in [0, 1]:
            info['firmwareVersion'] = gcir.firmwareVersion
            info['cameraType'] = str(gcir.cameraType) if gcir.cameraType not in CAMERA_TYPE else CAMERA_TYPE[gcir.cameraType]
            info['name'] = gcir.name.decode('utf-8')
            info['readoutInfo'] = []
            def tofloat(bcd):
                h = hex(bcd).lstrip('0x')
                return float(h[:-2]) + int(h[-2:])/100.0

            for i in range(gcir.readoutModes):
                im = {'mode' : gcir.readoutInfo[i].mode,
                      'width' : gcir.readoutInfo[i].width,
                      'height' : gcir.readoutInfo[i].height,
                      'pixelWidth' : tofloat(gcir.readoutInfo[i].pixelWidth),
                      'pixelHeight' : float(hex(gcir.readoutInfo[i].pixelHeight).lstrip('0x').rstrip('00'))}
                info['readoutInfo'].append(im)
            return info
        elif request == 2:
            info['badColumns'] = gcir.badColumns
            info['columns'] = []
            for i in range(min(4, gcir.badColumns)):
                info['columns'].append(gcir.columns[i])
            info['imagingABG'] = gcir.imagingABG
            info['serialNumber'] = gcir.serialNumber
            return info
        elif request == 3:
            adSize = gcir.adSize
            if adSize == 1:
                info['adSize'] = 12
            elif adSize == 2:
                info['adSize'] = 16
            else:
                info['adSize'] = 'unknown'
            info['FilterType'] = gcir.FilterType   # 0 unknown, 1 External, 2 2-position, 3 - 5 position
            return info
        elif request in [4, 5]:
            bits = gcir.capabilitiesBits
            info['FrameTransferDevice'] = True if (bits & 1) else False
            info['HasElectronicShutter'] = True if (bits & 2) else False
            info['HasFrameBuffer'] = True if (bits & 32) else False
            info['dumpExtra'] = gcir.dumpExtra
            return info
        elif request == 6:
            bits = gcir.cameraBits
            info['STX'] = True if not (bits & 1) else False
            info['STXL'] = True if (bits & 1) else False
            info['HasMechanicalShutter'] = True if not (bits & 2) else False
            bits = gcir.ccdBits
            info['ColorCCD'] = True if (bits  & 1) else False
            info['BayerColorMatrix'] = True if not (bits & 2) else False
            return info
        raise RuntimeError('get_camera_info: Invalid request type')

    def start_exposure(self): 
        """
        starts the exposure
        Input
            None
        Returns
            Image if success, False otherwise
        """    
        # Take Image  
        exposure = c_ulong(self.exposure + self.FAST)
        sep2 = StartExposureParams2(
                    ccd = CCD_IMAGING, 
                    exposureTime = exposure, 
                    abgState = ABG_LOW7, 
                    readoutMode = RM_1X1,
                    top = self.TOP, 
                    left = self.LEFT, 
                    height = self.HEIGHT,
                    width = self.WIDTH)
        if self.DARK:
            sep2.openShutter = SC_CLOSE_SHUTTER
        else:
            sep2.openShutter = SC_OPEN_SHUTTER

        Error = self.SBIG.SBIGUnivDrvCommand(CC_START_EXPOSURE2, byref(sep2), None)
        if Error != CE_NO_ERROR:
            print ('Attempt to start exposure returned error:', Error)
            self.initialize_shutter()
            Error = self.SBIG.SBIGUnivDrvCommand(CC_START_EXPOSURE2, byref(sep2), None)
            if Error != CE_NO_ERROR:
                print ('Attempt to start exposure returned error:', Error)
                return False
            elif self.verbose:
                print ('Exposure successfully initiated.')
        elif self.verbose:
            print ('Exposure successfully initiated.')

        # Wait for exposure to end
        qcspar = QueryCommandStatusParams(command = CC_START_EXPOSURE2)
        qcsres = QueryCommandStatusResults(status = 6)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_QUERY_COMMAND_STATUS, byref(qcspar), byref(qcsres))
        while qcsres.status == 2:
            Error = self.SBIG.SBIGUnivDrvCommand(CC_QUERY_COMMAND_STATUS, byref(qcspar), byref(qcsres))
        # End Exposure
        eep = EndExposureParams(ccd = CCD_IMAGING)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_END_EXPOSURE, byref(eep), None)
        if Error != CE_NO_ERROR:
            print ('Attempt to end exposure returned error:', Error)
            return False
        elif self.verbose:
            print ('Exposure successfully ended.')
            
        # close shutter for ST-i camera
        # This section is skipped for 8300 camera and keepShutterOpen=True
        if self.cameraName == 'STi' and self.keepShutterOpen == False:
            try:
                self.set_shutter('closed')
                print('ST-i shutter closed.')
            except: 
                print('Could not close ST-i shutter.')
         
        # Start Readout
        srp = StartReadoutParams(ccd = CCD_IMAGING, readoutMode = RM_1X1,
                                 top = self.TOP, left = self.LEFT, height = self.HEIGHT,
                                 width = self.WIDTH)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_START_READOUT, byref(srp), None)
        if Error != CE_NO_ERROR:
            print ('Attempt to initialise readout returned error:', Error)
            return False
        elif self.verbose:
            print ('Readout initiated.')
          
        # Readout
        rlp = ReadoutLinesParams(ccd = CCD_IMAGING, readoutMode = RM_1X1,
                                 pixelStart = self.LEFT, pixelLength = self.WIDTH)
        cameraData = ((c_ushort*(self.WIDTH.value))*self.HEIGHT.value)()
        for i in range(self.HEIGHT.value):
            Error = self.SBIG.SBIGUnivDrvCommand(CC_READOUT_LINE, byref(rlp), byref(cameraData, i*self.WIDTH.value*2)) # the 2 is essential
            if Error != CE_NO_ERROR:
                print ('Readout failed with error ' + str(Error) + '. Writing readout then closing device and driver.')
                if Error == 8:
                    print('(Error 8 means CE_RX_TIMEOUT, "Receive (Rx) timeout error")')
                break
        image = np.ctypeslib.as_array(cameraData)
        if Error == CE_NO_ERROR and self.verbose:
            print ('Readout successful.')

        # End readout in any case for autofreeze to function proper
        '''
        The End Readout command should be called at least once per readout
        after calls to the Readout Line, Read Subtract Line or Dump Lines 
        command are complete. Several End Readout commands can be issued 
        without generating an error.
        '''
        erp = EndReadoutParams(cd = CCD_IMAGING)
        Error = self.SBIG.SBIGUnivDrvCommand(CC_END_READOUT, byref(erp), None)
        if Error != CE_NO_ERROR:
            print ('End readout failed with error code: ', Error)
        elif self.verbose:
            print ('Readout session was ended.')
        # hdu = fits.PrimaryHDU(image)
        # name = time.strftime("%Y-%m-%d-%H%M%S") + '.fits' # Saves file with timestamp
        # hdu.writeto(name)
        return image
       
    def write_fits(self, image, name):
        """
        Writes out image to a FITS file with name 'name'
        Input:
            image: numpy array
            name: string, filename
        Return:
            True if success (Image is saved to disk as fits)
            False if failed
          """
        # image = np.ctypeslib.as_array(cameraData)
        # retrieve current CCD temperature

        try:
            hdu = fits.PrimaryHDU(image)
        # name = time.strftime("%Y-%m-%d-%H%M%S") + '.fits' # Saves file with timestamp
            hdu.writeto(name)
            return True
        except:
            return False
            
    def close_camera(self):
        """
        Closes camera and driver software. Should always be called when finished
        with the camera (leave it open for several images in squence).
        Input:
            None
        Return:
            None
        """
        return_val = True        
        
         # Close Device
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CLOSE_DEVICE, None, None)
        if Error == 20:
            print ('Code 20: device already closed.')
        elif Error != CE_NO_ERROR:
            print ('Closing device returned error:', Error)
            return_val = False
        elif self.verbose:
            print ('Device successfully closed.')
        
        # Close Driver
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CLOSE_DRIVER, None, None)
        if Error == 20:
            print ('Code 20: driver already closed.')
        elif Error != CE_NO_ERROR:
            print ('Attempt to close driver returned error:', Error)
            return_val = False
        elif self.verbose:
            print ('Driver successfully closed.')
        
        return return_val
        
    ### CFW COMMANDS ###
    
    def open_cfw(self):
        """
        Opens the CFW, only needed for RS232 connection to computer
        """
        cfwp = CFWParams(cfwModel = self.cfw, cfwCommand = 4)
        cfwr = CFWResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        if Error != CE_NO_ERROR:
            print('Opening CFW returned camera error:', Error)
            return False
        elif cfwr.cfwError != 0:
            print('Opening CFW returned CFW error:', cfwr.cfwError, self.cfw_error[cfwr.cfwError])
            return False
        elif self.verbose:
            print('CFW successfully opened.')
        return True
        
    def close_cfw(self):
        """
        Closes the CFW, only needed for RS232 connection to computer
        """
        cfwp = CFWParams(cfwModel = self.cfw, cfwCommand = 5)
        cfwr = CFWResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        if Error != CE_NO_ERROR:
            print('Closing CFW returned camera error:', Error)
            return False
        elif cfwr.cfwError != 0:
            print('Closing CFW returned CFW error:', cfwr.cfwError, self.cfw_error[cfwr.cfwError])
            return False
        elif self.verbose:
            print('CFW successfully closed.')
        return True
        
    def move_cfw(self, position):
        """
        Moves the CFW to desired position.
        Input: Position - int representing which filter to go to, usually a number less than the model
        Returns: the reported position if successful, else False
        """
        if not(isinstance(position, int)):
            if self.verbose:
                print('Invalid position, must be an int usually less than the number of the model (IE FW8 goes from 0-7).')
            return False
        cfwp = CFWParams(cfwModel = self.cfw, cfwCommand = 1, cwfParam1 = c_ulong(position))
        cfwr = CFWResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        if Error != CE_NO_ERROR:
            print('Moving CFW returned camera error:', Error)
            return False
        elif cfwr.cfwError != 0:
            print('Moving CFW returned CFW error:', cfwr.cfwError, self.cfw_error[cfwr.cfwError])
            return False
        cfwp = CFWParams(cfwModel = self.cfw, cfwCommand = 0)
        cfwr = CFWResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        while cfwr.cfwStatus == 2:
            Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        if self.verbose:
            print('CFW successfully moved.')
        return cfwr.cfwPosition
        
    def get_cfw_position(self):
        """
        Gets the CFW's position.
        Returns position as int if successful, else False
        """
        cfwp = CFWParams(cfwModel = self.cfw, cfwCommand = 0)
        cfwr = CFWResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        if Error != CE_NO_ERROR:
            print('Query of CFW returned camera error:', Error)
            return False
        elif cfwr.cfwError != 0:
            print('Query of CFW returned CFW error:', cfwr.cfwError, self.cfw_error[cfwr.cfwError])
            return False
        if self.verbose:
            print('CFW position successfully returned.')
        return cfwr.cfwPosition
        
    def init_cfw(self):
        """
        Initializes CFW, may help resolve any errors.
        Returns: success of command True or False.
        """
        cfwp = CFWParams(cfwModel = self.cfw, cfwCommand = 2)
        cfwr = CFWResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_CFW, byref(cfwp), byref(cfwr))
        if Error != CE_NO_ERROR:
            print('Initialization of CFW returned camera error:', Error)
            return False
        elif cfwr.cfwError != 0:
            print('Initialization of CFW returned CFW error:', cfwr.cfwError, self.cfw_error[cfwr.cfwError])
            return False
        if self.verbose:
            print('CFW successfully Initialized.')
        return True

    ### TEMPERATURE COMMANDS ###

    def set_temperature_regulation(self, regulationInput, ccdSetpoint=None):
        """
        This is actually CC_SET_TEMPERATURE_REGULATION2, in degree celsius,
        not the legacy method in A/D units

        Requires camera to be open (open_camera())
        Command values:
        'off' - regulation off (0)
        'on' - regulation on (1)
        'override' - regulation override (2)
        'freeze' - freeze TE cooler (ST-8/7 cameras) (3)
        'unfreeze' - unfreeze TE cooler (4)
        'enable_autofreeze' - enable auto-freeze (5)
        'disable_autofreeze' - disable auto-freeze (6)
        ccdSetpoint is the CCD temperature in celsius to activate regulation
        
        Input:
            Command value (string)), temperature in celsius
        
        """
        # check input
        if regulationInput in self.tempRegulationDict.keys():
            regulation = self.tempRegulationDict[regulationInput]
        else:
            print('Invalid temperature regulation command.')
            return False
                           
        if ccdSetpoint is None:
            # query current setpoint from driver
            ccdSetpoint = self.query_ccd_setpoint()    
        else:
            # get setpoint in A/D units
            r = 3.0 * math.exp(math.log(2.57)*(25.0 - ccdSetpoint)/25.0)
            self.setpoint = int(4096/(10.0/r + 1.0))
            print('Setpoint: %f (%d)' % (ccdSetpoint, self.setpoint))
        # send driver command
        trp2 = SetTemperatureRegulationParams2(
                    regulation  = regulation,
                    ccdSetpoint = ccdSetpoint)
        Error = self.SBIG.SBIGUnivDrvCommand(
                    CC_SET_TEMPERATURE_REGULATION2, byref(trp2), None)
        if Error != CE_NO_ERROR:
            print('Temperature regulation returned error: ', Error)
            return False
        elif self.verbose:
            print('Temperature regulation set: ', regulationInput, 
                      '. CCD Setpoint: ', ccdSetpoint, 'degree C.')
        return True
    
    def set_ccd_setpoint(self, ccdSetpoint):
        """
        Convenience function to set the temperature set point 
        Sets ccd temperature for TEC cooler
        Input:
            Setpoint temperature
        Return:
            True if success
            False if fail
        """
        regulation = self.query_tec_enabled()
        if regulation:
            regulation = 'on'
        if not regulation:
            regulation = 'off'
        try:
            self.set_temperature_regulation(regulation, ccdSetpoint)
            if self.verbose:
                print('New CCD Setpoint:', ccdSetpoint)
            return True
        except:
            print('Changing CCD Setpoint failed.')
            return False
    
    def set_fan(self, fanState):
        """
        Sets fan on or off
        Input:
            bool
        Return:
            True if success
            False if fail
        """
        # does not seem to be supported by STF-8300
        fanState = str(fanState)
        if fanState in ['on', 'off']:
            
            if fanState == 'on':                
                mcp = MiscellaneousControlParams(
                        fanEnable = c_bool(True),
                        ledState = c_ushort(1))
            elif fanState == 'off':
                mcp = MiscellaneousControlParams(
                        fanEnable = c_bool(False),
                        ledState = c_ushort(1))
                
            Error = self.SBIG.SBIGUnivDrvCommand(
                   CC_MISCELLANEOUS_CONTROL, byref(mcp), None)
            if Error != CE_NO_ERROR:
                print("Setting fan returned error:", Error)
                return False
            elif self.verbose:
                print("Cooling fan is now:", fanState)
            return True
        else:
            print('Invalid fanState state, on or off only.')
            return False
        
    def set_tec(self, tecState):
        """
        Sets TEC on or off
        Input:
            bool
        Return:
            True if success
            False if fail
        """
        # set thermoelectric cooler, status indicated by 'coolingEnabled'
        tecState = str(tecState)
        if tecState in ['on', 'off']:
            try:
                if tecState == 'on':                
                    self.set_temperature_regulation('on')
                elif tecState == 'off':
                    self.set_temperature_regulation('off')
                return True
            except:
                print('Setting TEC failed.')
                return False
        else:
            print('Invalid TEC state, on or off only.')
            return False
            
    def freeze_tec(self):
        """
        Freezes TEC
        Input:
            None
        Return:
            True if success
            False if fail
        """
        trp2 = self.SetTemperatureRegulationParams2(
                    regulation = self.tempRegulationDict['freeze'])
        Error = self.SBIG.SBIGUnivDrvCommand(
                    CC_SET_TEMPERATURE_REGULATION2, byref(trp2), None)
        if Error != CE_NO_ERROR:
            print('Freezing TEC returned error: ', Error)
            return False
        elif self.verbose:
            print('TEC is frozen for readout.')
        return True
        
    def unfreeze_tec(self):
        """
        Unfreezes TEX
        Input:
            None
        Return:
            True if success
            False if fail
        """
        trp2 = SetTemperatureRegulationParams2(
                    regulation = self.tempRegulationDict['unfreeze'])
        Error = self.SBIG.SBIGUnivDrvCommand(
                    CC_SET_TEMPERATURE_REGULATION2, byref(trp2), None)
        if Error != CE_NO_ERROR:
            print('Unfreezing TEC returned error: ', Error)
            return False
        elif self.verbose:
            print('TEC is unfrozen.')
        return True
                    
    def set_autofreeze(self, autofreezeState):
        """
        Sets autofreeze on of off for TEC
        Input:
            bool
        Return:
            True if success
            False if fail
        """
        autofreezeState = str(autofreezeState)
        if autofreezeState in ['on', 'off']:
            try:
                ccdSetpoint = self.query_ccd_setpoint()
                if autofreezeState == 'on':                
                    self.set_temperature_regulation(
                        'enable_autofreeze', ccdSetpoint)
                elif autofreezeState == 'off':
                    self.set_temperature_regulation(
                        'disable_autofreeze', ccdSetpoint)
                return True
            except:
                print('Setting autofreeze function failed.')
                return False
        else:
            print('Invalid autofreeze state, on or off only.')
            return False
    

    def query_temperature_status(self, request = 2):
        
        '''
        Internal function for use in following funtions
        Input:
            None
        Return:
            standard request returns temperature status in A/D units
            advanced request returns degree celsius, recommended, request=2
        '''
        if 'STX' in self.cameraName: 
            request = 0 # 1 and 2 doesn't seem to work for the STX
        qtsp = QueryTemperatureStatusParams(request = request)
        if request == 1:
            qtsr = QueryTemperatureStatusResults1()
        elif request == 2:
            qtsr = QueryTemperatureStatusResults2()
        else:
            qtsr = QueryTemperatureStatusResults()
        Error = self.SBIG.SBIGUnivDrvCommand(CC_QUERY_TEMPERATURE_STATUS, byref(qtsp), byref(qtsr))
            
        if Error != CE_NO_ERROR:
            print ('Temperature status query returned error:', Error)
            return False
        if request == 2:
            tempStatusDict = {
                'cooling_enabled':                  True if qtsr.coolingEnabled != 0 else False,
                'fan_enabled':                      True if qtsr.fanEnabled != 0 else False,
                'ccd_setpoint':                     qtsr.ccdSetpoint,
                'imaging_ccd_temperature':          qtsr.imagingCCDTemperature,
                'tracking_ccd_temperature':         qtsr.trackingCCDTemperature,
                'external_tracking_ccd_temperature':qtsr.externalTrackingCCDTemperature,
                'ambient_temperature':              qtsr.ambientTemperature,
                'imaging_ccd_power':                qtsr.imagingCCDPower,
                'tracking_ccd_power':               qtsr.trackingCCDPower,
                'external_tracking_ccd_power':      qtsr.externalTrackingCCDPower,
                'heatsink_temperature':             qtsr.heatsinkTemperature,
                'fan_power':                        qtsr.fanPower,
                'fan_speed':                        qtsr.fanSpeed}
        elif request == 1:
            tempStatusDict = {
                'cooling_enabled':                  True if qtsr.coolingEnabled != 0 else False,
                'fan_enabled':                      True if qtsr.fanEnabled != 0 else False,
                'ccd_setpoint':                     qtsr.ccdSetpoint,
                'imaging_ccd_temperature':          qtsr.imagingCCDTemperature,
                'tracking_ccd_temperature':         qtsr.trackingCCDTemperature,
                'external_tracking_ccd_temperature':qtsr.externalTrackingCCDTemperature,
                'ambient_temperature':              qtsr.ambientTemperature,
                'imaging_ccd_power':                qtsr.imagingCCDPower,
                'tracking_ccd_power':               qtsr.trackingCCDPower,
                'external_tracking_ccd_power':      qtsr.externalTrackingCCDPower,
                'heatsink_temperature':             qtsr.heatsinkTemperature,
                'fan_power':                        qtsr.fanPower,
                'fan_speed':                        None}
        else:
            r = 10.0/(4096/qtsr.ccdThermistor -1)
            ccdTemperature = 25.0 - 25.0*(math.log(r/3.0)/math.log(2.57))
            r = 3.0/(4096/qtsr.ambientThermistor -1)
            ambientTemperature = 25.0 - 45.0*(math.log(r/3.0)/math.log(7.791))
            r = 10.0/(4096/qtsr.ccdSetpoint -1)
            ccdSetpoint = 25.0 - 25.0*(math.log(r/3.0)/math.log(2.57))
            tempStatusDict = {
                'cooling_enabled':                  True if qtsr.enabled != 0 else False,
                'fan_enabled':                      None,
                'ccd_setpoint':                     round(ccdSetpoint,3),
                'imaging_ccd_temperature':          round(ccdTemperature,3),
                'tracking_ccd_temperature':         None,
                'external_tracking_ccd_temperature':None,
                'ambient_temperature':              round(ambientTemperature,3),
                'imaging_ccd_power':                round(float(qtsr.power/255.0),3),
                'tracking_ccd_power':               None,
                'external_tracking_ccd_power':      None,
                'heatsink_temperature':             None,
                'fan_power':                        None,
                'fan_speed':                        None}

        if self.verbose:
            pprint.pprint(tempStatusDict)
        return tempStatusDict

    def query_tec_enabled(self):
        """
        Finds if TEC (cooling unit) is enabled
        Input:
            None
        Return:
            True if enabled
            False if disabled
        """
        results = self.query_temperature_status()
        return bool(results['cooling_enabled'] & REGULATION_ENABLE_MASK)
        
    def query_tec_frozen(self):
        """
        Finds if TEC (cooling unit) is frozen
        Input:
            None
        Return:
            True if frozen
            False if frozen
        """
        results = self.query_temperature_status()
        return bool(results['cooling_enabled'] & REGULATION_FROZEN_MASK)
        
    def query_fan_enabled(self):
        """
        Finds if fan is enabled
        Input:
            None
        Return:
            True if enabled
            False if disabled
        """
        results = self.query_temperature_status()
        return results['fan_enabled']
    
    def query_ccd_setpoint(self):
        """
        Finds ccd temperature setpoint
        Input:
            None
        Return:
            setpoint temperature for ccd
        """        
        results = self.query_temperature_status()
        return results['ccd_setpoint']
        
    def query_imaging_ccd_temperature(self):
        """
        Finds ccd imaging temperature 
        Input:
            None
        Return:
            Imaging temperature for ccd
        """
        results = self.query_temperature_status()
        return results['imaging_ccd_temperature']
    

if __name__ == '__main__':

    model={'1':     'ST8300',
           '2':     'STi'}
    camtype=input("Select camera type.  (1) for ST8300 or (2) for STi: ")
    if camtype.lower() not in ['1','2']:
        print("Not a valid camera type")
        sys.exit()
    camera = SBIGCam()
    camera.select_camera(model[camtype.lower()])    
    # Time of exposure in between 90ms and 3600000ms
    if not camera.open_camera():
        print ("Can't establish connection to camera")
        sys.exit()
    # set temperature regulation
    regulation = input("Enter temperature regulation mode:")
    if not regulation in camera.tempRegulationDict.keys():
        print("invalid input.")   
        camera.close_camera()
        sys.exit()
    setpoint = input("Enter CCD Setpoint:")
    while (type(setpoint) is str):
        try:
            setpoint = float(setpoint)
        except:
            print("Invalid input.")
            camera.close_camera()
            sys.exit()
    camera.set_temperature_regulation(regulation, setpoint)
    camera.query_temperature_status()
    exptime = input("Exposure time in milliseconds (between 0 and 3600000): ")
    while (type(exptime) is str):
        try:
            exptime = int(exptime)
        except ValueError:
            print("Looks like that's not a valid exposure time ")
            camera.close_camera()
            sys.exit()
    camera.set_exposure_time(exptime)        
    response= input("Will this be a dark image? (Y/N) ")
    # 1 for dark, 0 for exposure
    try:
        if response[0].lower() not in ['y','n']:
            print("Input Error")
        else:
            camera.set_dark(False)
            if response[0].lower() == 'y':
                camera.set_dark(True)
    except:
        print("Input Error")
        
    image=camera.start_exposure()
    filename = 'sbig'+time.strftime("%y%m%d-%H%M%S") + '.fits' 
    camera.write_fits(image, filename)
    camera.close_camera()
