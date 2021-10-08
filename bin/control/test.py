#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 15:28:27 2021

@author: ldrd
"""

import sys
sys.path.append('motors')
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
gear_ratios = {}
gear_ratios['namiki'] = (46.0/14.0+1)**4  # namiki    "337:1", output rotation/motor input
gear_ratios['maxon'] = 4100625.0/14641.0  # maxon     "280:1", output rotation/motor input
gear_ratios['faulhaber'] = 125.0          # faulhaber "125:1", output rotation/motor input
motor_name = 'namiki'
for p in pos.available_positioners():
    pos[p].set_alpha_reduction_ratio(gear_ratios[motor_name])
    pos[p].set_beta_reduction_ratio(gear_ratios[motor_name])