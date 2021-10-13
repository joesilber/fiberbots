# -*- coding: utf-8 -*-
'''Constants, environment variables, and convenience methods.'''
import os
import math
import numpy as np
from datetime import datetime

# Directory locations
this_file_dir = os.path.realpath(os.path.dirname(__file__))
root_dir = os.path.realpath(os.path.join(this_file_dir, '../'))
dirs = {'root': root_dir,
        'temp': os.path.realpath(os.path.join(root_dir, 'temp/')),
        'data': os.path.realpath(os.path.join(root_dir, 'data/')),
       }
for write_dir in ['temp', 'data']:
    if not os.path.isdir(dirs[write_dir]):
        os.mkdir(dirs['temp'])

# Motor constants
gear_ratio = {}
gear_ratio['namiki'] = (46.0/14.0+1)**4  # namiki    "337:1", output rotation/motor input
gear_ratio['maxon'] = 4100625.0/14641.0  # maxon     "280:1", output rotation/motor input
gear_ratio['faulhaber'] = 256.0  		 # faulhaber "256:1", output rotation/motor input

# Camera default parameters
fvc_defaults = {'camera': 'SBIG',
                'exptime': 0.2,  # exposure time in sec
                'fitbox': 15,  # ccd windowing for centroiding in pixels
                'sim_errmax': 0.01,  # simulated measurement noise in mm
                'sim_badmatchfreq': 0.05,  # simulated frequency of bad spot matches
                'x0_px': 0.0,  # x translational offset in pixels
                'y0_px': 0.0,  # y translational offset in pixels
                'angle_deg': 0.0,  # camera mounting angle in deg
                'mm_per_px': 1.0,  # plate scale, i.e. (mm at fibers) / (pixels at ccd)
                }

# Standard timestamps
timestamp_fmt = '%Y%m%dT%H%M%S%z'
def timestamp():
    '''Returns a timestamp string in a standardized format.'''
    return datetime.now().astimezone().strftime(timestamp_fmt)

def stamp_to_time(timestamp):
    '''Returns a datetime object for a given timestamp string.'''
    return datetime.strptime(timestamp, timestamp_fmt) 

# Nice type-checking and casting methods
def is_integer(x):
    return isinstance(x, (int, np.integer))

def is_float(x):
    return isinstance(x, (float, np.floating))

def is_string(x):
    return isinstance(x, (str, np.str))

def is_boolean(x):
    return x in [True, False, 0, 1] or str(x).lower() in ['true', 'false', '0', '1']

def is_none(x):
    return x in [None, 'None', 'none', 'NONE']

def is_collection(x):
    if isinstance(x, (dict, list, tuple, set)):
        return True
    if is_integer(x) or is_float(x) or is_string(x) or is_boolean(x):
        return False
    return '__len__' in dir(x)

def boolean(x):
    '''Cast input to boolean.'''
    if x in [True, False]:
        return x
    if x == None or is_integer(x) or is_float(x):
        return bool(x)
    if is_string(x):
        return x.lower() not in {'false', '0', 'none', 'null', 'no', 'n'}
    if is_collection(x):
        return len(x) > 0
    assert False, f'posconstants.boolean(): undefined interpretation for {x}'

def sign(x):
    '''Return the sign of the value x as +1, -1, or 0.'''
    if x > 0.:
        return 1
    elif x < 0.:
        return -1
    else:
        return 0

# Common unit strings and conversions
deg = '\u00b0'
mm = 'mm'
um_per_mm = 1000
deg_per_rad = 180./math.pi
rad_per_deg = math.pi/180.

# Common, convenient string operations
def join_notes(*args):
    '''Concatenate items into a "note" string with standard format. A list or
    tuple arg is treated as a single "item". So for example if you want the
    subelements of a list "joined", then argue it expanded, like *mylist.
    '''
    separator = '; '
    if len(args) == 0:
        return ''
    elif len(args) == 1:
        return str(args[0])
    strings = (str(x) for x in args if x != '')
    return separator.join(strings)

def ordinal_str(number):
    '''Returns a string of the number plus 'st', 'nd', 'rd', 'th' as appropriate.'''
    numstr = str(number)
    last_digit = numstr[-1]
    second_to_last = numstr[-2]
    if last_digit == '1' and second_to_last != '1':
        return numstr + 'st'
    if last_digit == '2' and second_to_last != '1':
        return numstr + 'nd'
    if last_digit == '3' and second_to_last != '1':
        return numstr + 'rd'
    return numstr + 'th'

