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
    
    LIMIT_A0,       ... Units deg. Angular positions of alpha and beta travel limits. Limit
    LIMIT_A1,           "A0" is toward decreasing alpha, limit "A1" is toward increasing alpha,
    LIMIT_B0,           and simillarly for beta. Limit values are given in (a_arm, b_arm)
    LIMIT_B1            coordinates, so that they are local to a given robot. (I.e. mounting
                        the robot at some other angle on the focal plane only changes OFFSET_A,
                        allowing the stop positions to be measured and recorded on a separate
                        test stand, prior to installation, with no further modification needed
                        to them.) In practice we may distinguish between physical limits and
                        software limits, which are typically set a few deg inward of the actual
                        hard stops, to allow some margin for error.
'''

# For the Trillium2 and Trillium3 designs. Trillium1 had TEETH_1 = 10.
nom_teeth = [10, 15, 10, 10]  # See comments above. These correspond to [TEETH_0, TEETH_1, TEETH_2, TEETH_3]
nom_idler = [nom_teeth[0] / nom_teeth[1],  # ratio from b_box to bottom rank of idler gear
             nom_teeth[2] / nom_teeth[3]]  # ratio from top rank of idler gear to beta arm shaft

# Nominal travel limit positions.
nom_limits_a = [-179.999, 180.]  # See comments above. These correspond to [LIMIT_A0, LIMIT_A1], and apply to a_arm coordinates.
nom_limits_b = [0., 180.]  # See comments above. These correspond to [LIMIT_B0, LIMIT_B1], and apply to b_arm coordinates.


def mot2box(mot, gearbox_ratio):
     '''Converts from motor angle to output shaft angle.'''
     return mot / gearbox_ratio

def box2mot(box, gearbox_ratio):
    '''Converts from output shaft angle to motor angle.'''
    return box * gearbox_ratio

def box2arm(a_box, b_box, limits_a=nom_limits_a, limits_b=nom_limits_b, idler=nom_idler):
    '''Converts from alpha and beta gearmotors' output shaft angles to the observable
    angles of their kinematic arms. Limit-checking can be skipped with an argument
    like None, empty container, or False. The return tuple has:
        a_arm, b_arm, contacts
    where contacts is a dictionary describing what if any hardstop contacts may have occurred.
    '''
    a_arm = a_box
    a_arm_limited = _apply_limits(a_arm, limits_a)  # ensure alpha limit will affect beta calculation 
    b_arm = a_arm_limited*idler[1] + b_box*(idler[0]*idler[1])
    b_arm_limited = _apply_limits(b_arm, limits_b)
    a_arm_limited_by_beta = (b_arm_limited - b_box*(idler[0]*idler[1])) / idler[1]
    contacts = {
        'alpha hardstop contact': a_arm_limited != a_arm,
        'beta hardstop contact': b_arm_limited != b_arm,
        'alpha limited by beta contact': a_arm_limited_by_beta != a_arm_limited,
    }
    return a_arm_limited_by_beta, b_arm_limited, contacts

def arm2box(a_arm, b_arm, idler=nom_idler):
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

def _apply_limits(value, limits):
    '''Returns the argued value, bounded by the min and max of container limits.
    Application of limits may be skipped (always returning value unmodified) by
    arguing None, empty container, or False, etc.
    '''
    if limits:
        value = min(value, max(limits))
        value = max(value, min(limits))
    return value

if __name__ == '__main__':

   # demonstrate converting desired arm angles to necessary gearbox angles,
   # then inverting the transformation back to arm angles
    print('\n---------\n')
    a_arm = [-179, -179, -179, -90, -90, -90, 0, 0, 0, 90, 90, 90, 179, 179, 179]
    b_arm = [0, 90, 180]*5
    for i in range(len(a_arm)):
        a_box, b_box = arm2box(a_arm[i], b_arm[i])
        txt = f'desired (a_arm, b_arm) = ({a_arm[i]:4.0f}, {b_arm[i]:4.0f})'
        txt += f' -->  required (a_box, b_box) = ({a_box:6.1f}, {b_box:6.1f})'
        a_arm2, b_arm2, contacts = box2arm(a_box, b_box)
        tol = 1e-6
        inversion_succeeded = abs(a_arm2 - a_arm[i]) < tol and abs(b_arm2 - b_arm[i]) < tol 
        inversion_text = 'SUCCESS' if inversion_succeeded else 'FAILED'
        txt += f' ... inverse transform --> (a_arm\', b_arm\') = ({a_arm2:6.1f}, {b_arm2:6.1f}) [{inversion_text}]'
        print(txt)