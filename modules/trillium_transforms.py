# -*- coding: utf-8 -*-
'''
Originated: Jan 2023, Joe Silber, Lawrence Berkeley National Lab (LBNL)

This module provides coordinate transformation between gearmotor angles and
arm angles for "Trillium" design fiber positioner robots.

COORDINATES:

    a_mot, b_mot    ... Units deg. Angle of alpha and beta motor shafts. Note that
                        in cases where the arms strike mechanical hard limits or
                        neighboring robots, the motor shaft will keep spinning while
                        the output (a_out or b_out) stops. Therefore we track robot
                        position not by *_mot angles but rather by *_arm (see below).
    
    a_box, b_box    ... Units deg. Angle at output of alpha and beta gearboxes. Note
                        that b_box is not externally observable, since there is a
                        transfer gear mechanism between b_box and b_arm (see below).

    a_arm, b_arm    ... Units deg. Angles of alpha and beta axes' kinematic "arms".
                        These are the externally-observable angles to which the robot
                        physically moves the fiber.

PARAMETERS:

    GEARBOX_A,      ... Unitless floats. Ratios of motor shaft to output shaft for alpha
    GEARBOX_B           and beta gearmotors. For example, on DESI this ratio was ~337:1
                        for both the theta and phi motors.
    
    TEETH_0         ... Unitless int. Number of teeth on gear at end of beta gearmotor's
                        output shaft.
    
    TEETH_1         ... Unitless int. Number of teeth on bottom of idler gear.

    TEETH_2         ... Unitless int. Number of teeth on top of idler gear.

    TEETH_3         ... Unitless int. Number of teeth on gear at bottom of beta arm shaft.
    
'''

# For the Trillium2 and Trillium3 designs. Trillium1 had TEETH_1 = 10.
nominal_teeth = [10, 15, 10, 10]  # See comments above. These correspond to [TEETH_0, TEETH_B1, TEETH_B2, TEETH_B3]
nominal_idler = [nominal_teeth[0] / nominal_teeth[1],  # ratio from b_box to bottom rank of idler gear
                 nominal_teeth[2] / nominal_teeth[3]]  # ratio from top rank of idler gear to beta arm shaft


def mot2box(mot, gearbox_ratio):
     '''Converts from motor angle to output shaft angle.'''
     return mot / gearbox_ratio

def box2mot(box, gearbox_ratio):
    '''Converts from output shaft angle to motor angle.'''
    return box * gearbox_ratio

def box2arm(a_box, b_box, idler=nominal_idler):
    '''Converts from alpha and beta gearmotors' output shaft angles to the observable
    angles of their kinematic arms.
    '''
    a_arm = a_box
    b_arm = a_arm*(1 + idler[1])  +  b_box*(idler[0]*idler[1])
    return a_arm, b_arm

def arm2box(a_arm, b_arm, idler=nominal_idler):
    '''Converts from the observable angles of the alpha and beta gearmotors' kinematic
    arms to their output shaft angles.
    '''
    a_box = a_arm
    b_box = (b_arm - a_arm*(1 + idler[1])) / (idler[0]*idler[1])
    return a_box, b_box
