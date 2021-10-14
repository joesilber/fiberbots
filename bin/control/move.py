#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 15:28:27 2021

@author: ldrd
"""

import time
import os, sys
this_file_dir = os.path.realpath(os.path.dirname(__file__))
os.chdir(this_file_dir)
sys.path.append('../../modules')
sys.path.append('../../modules/motors')
import globals as gl
from tendo import Positioners

# connect to positioners
pos = Positioners()
pos.connect()

# make sure firmware is as we expect for the LBNL setup
fw_needed = 262416
for p in pos.available_positioners():
    fw = pos[p].get_firmware()[0].firmware
    assert fw == fw_needed, f'unexpected firmware version {fw}, does not match required {fw_needed}'

# set gear reduction ratios
# note how if we put mixed motor types on the test stand, the handling of motor_name etc will need to be more specific to each particular pos_id
all_gear_ratios = gl.gear_ratio.copy() 
motor_name = 'namiki'
gear_ratio = all_gear_ratios[motor_name]
approx_gear_ratio = round(gear_ratio)  # as of 2021-10-13, firmware only supports integers
for p in pos.available_positioners():
    pos[p].set_alpha_reduction_ratio(approx_gear_ratio)
    pos[p].set_beta_reduction_ratio(approx_gear_ratio)
print(f'Pausing {gl.reboot_delay} sec for reboot.'}
time.sleep(gl.reboot_delay)

# notes per Ricardo 2021-10-05
# - upon reboot, LEDs blink
# - reboot takes approx 10 sec
# - this 10 sec wait is the bootloader mode
# - numerous settings have to be done in the bootloader mode
# - gear ratio (currently) must be an integer
# - gear ratio can only be read or written while in bootloader mode
# - Ricardo might send us a new firmware version
