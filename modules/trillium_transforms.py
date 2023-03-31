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
                        physically moves the fiber. The zero point of b_arm starts at
                        the angular position of a_arm.
                        
                        E.g., if (a_arm, b_arm) = (30, 15) and if their lengths are
                        respectively 1.0, 1.1, then one would measure the fiber at
                        position:  x = 1.0 cos(30) + 1.1 cos(30 + 15)
                                   y = 1.0 sin(30) + 1.1 sin(30 + 15)

    a_gbl, b_gbl    ... Units deg. Angles of alpha and beta axes' kinematic "arms" in
                        a global coordinate system. Thus a_gbl may have some calibrated
                        offset with respect to a_arm, and b_gbl will be relative to the
                        global system, not relative to a_arm.

PARAMETERS:

    GEARBOX_A,      ... Unitless floats. Ratios of motor shaft to output shaft for alpha
    GEARBOX_B           and beta gearmotors. For example, on DESI this ratio was ~337:1
                        for both the theta and phi motors.
    
    TEETH_0         ... Unitless int. Number of teeth on gear at end of beta gearmotor's
                        output shaft.
    
    TEETH_1         ... Unitless int. Number of teeth on bottom of idler gear.

    TEETH_2         ... Unitless int. Number of teeth on top of idler gear.

    TEETH_3         ... Unitless int. Number of teeth on gear at bottom of beta arm shaft.

    OFFSET_A        ... Units deg. Angular zero-point of alpha axis within global coordinate
                        system. By convention, we define: a_gbl = a_arm + OFFSET_A
    
    STOP_A0,        ... Units deg. Angular positions of alpha and beta physical hard stops.
    STOP_A1,            These are given in the (a_arm, b_arm) coordinates, so that they are
    STOP_B0,            local to a given robot. (I.e. mounting the robot at some other angle
    STOP_B1             on the focal plane only changes OFFSET_A, allowing the stop positions
                        to be measured and recorded on a separate test stand, prior to
                        installation, with no further modification needed to them.)
'''

# For the Trillium2 and Trillium3 designs. Trillium1 had TEETH_1 = 10.
nominal_teeth = [10, 15, 10, 10]  # See comments above. These correspond to [TEETH_0, TEETH_1, TEETH_2, TEETH_3]
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
    b_arm = a_arm*idler[1] + b_box*(idler[0]*idler[1])
    return a_arm, b_arm

def arm2box(a_arm, b_arm, idler=nominal_idler):
    '''Converts from the observable angles of the alpha and beta gearmotors' kinematic
    arms to their output shaft angles.
    '''
    a_box = a_arm
    b_box = (b_arm - a_arm*idler[1]) / (idler[0]*idler[1])
    return a_box, b_box

def arm2gbl(a_arm, b_arm, offset_a):
    '''Converts from alpha and beta arm angles to angles in a global coordinate system.
    '''
    a_gbl = a_arm + offset_a
    b_gbl = b_arm + a_gbl 
    return a_gbl, b_gbl

def gbl2arm(a_gbl, b_gbl, offset_a):
    '''Converts from global angular coordinates to arm angles.
    '''
    a_arm = a_gbl - offset_a
    b_arm = b_gbl - a_gbl
    return a_arm, b_arm

if __name__ == '__main__':
    quit_strs = ['q', 'quit', 'exit']
    import trillium_transforms as tt
    while True:
        arg = input('type a function command for this module >> ')
        if arg.lower() in quit_strs:
            break
        try:
            print(eval(f'tt.{arg}'))
        except:
            print(f'didn\'t recognize argument "{arg}"')
