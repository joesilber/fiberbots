# Python version of measure_camera_scale.m
# F.B. and M.S., University of Michigan
#
# Requires:
#   Python 3, tested with Python 3.4
#
# History:
#   2015-11-23: created
#   2016-03-26: (M.S) converted to Python3
# To Do:
#
#
#
#

import datetime
import math
import numpy as np
import matplotlib.pyplot as plt

from sys import path
from configobj import ConfigObj

config=ConfigObj('measure_camera_scale.conf')
verbose=config.get('Preferences').as_bool('verbose')
simflag=config.get('Preferences').as_bool('simflag')
ref_dist_tol = config.get('Settings').as_float('ref_dist_tol')
nmin_measurements = config.get('Settings').as_int('nmin_measurements')
sbig_exposure_time=config.get('Settings').as_int('sbig_exposure_time')


path.insert(0, 'camera_code')
import sbig_grab_cen#import fvc_measure_with_ref as fvc
def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        float(value)
        return False    
         
def distance(p1,p2): # p=[x,y]
    dist=np.linalg.norm(np.array(p1)-np.array(p2))
    return dist

print("\n***********************************************************")
print("* Quick script for measuring camera scale.                *")
print("* Manually move fiber known distances across camera field *")
print("***********************************************************\n")


keep_measuring = True
n = 0
input_pos = []
xy = [] 
measurement=[]  #this is the big container for all the measurements

while keep_measuring:
    user_val = input("Enter current position (CR to end sequence): ")

    if user_val == '':
        keep_measuring = False
    elif isfloat(user_val):
        input_pos.append(float(user_val))
#        xy.append(fvc.fvc_measure_with_ref([])) #no xy_ref output for fvc; Mx2 values
#          don't really need fvc_measure_with_ref here. mMaybe want to resurrect this later.  
        sbig = sbig_grab_cen.SBIG_Grab_Cen()
        xy,peaks,fwhms,t = sbig.grab(2)
        print("centroids measured: ",xy)
        measurement.append(xy)
    else:
        print ("Didn't recognize input.\n")
        
# input_pos is a list of the positions (this is typically in micron, e.g. [0,10,20])
xy=list([x[0],x[1]] for x in measurement) # this is now a list of [xcen,ycen,fwhm] again

if verbose:
    print("*************")
    print("input_pos: ",input_pos)
    print("xy: ",xy)

if simflag:
    # =========== for testing only!!! =======
    xy=[]
    xy.append([[635.512, 2316.378], [1537.857, 1703.025], [4.069, 4.267]])
    xy.append([[645.512, 2316.377], [1547.857, 1703.026], [4.050, 4.447]])
    xy.append([[655.502, 2316.379], [1557.877, 1703.023], [4.080, 4.067]])
    xy.append([[665.542, 2316.379], [1567.827, 1703.021], [4.010, 3.967]])
    input_pos = [10.,15.,20.,25.]
    # ============ end testing


number_of_measurements=len(input_pos)
#ref_dist_tol = 0.2

if number_of_measurements >= nmin_measurements: #so if the while loop ran at least twice

    xy_init = xy[0] #
    xy_test = xy[1] # 

    if verbose:
        print("xy_init, xy_test")
        print(xy_init)
        print(xy_test)
    # first find the reference fiber
        
    xy_ref = []

#    print(" len(xy_test) :"+str(len(xy_test[0]))+"\n")
    
    for i in range(len(xy_test[0])):
        test_dist=distance([xy_init[0][i],xy_init[1][i]],[xy_test[0][i],xy_test[1][i]])
        #print("TEST distance: "+str(test_dist))
        if test_dist < ref_dist_tol:
            xy_ref.append([xy_test[0][i],xy_test[1][i]])
            print ("Reference fiber detected at (x,y) = ({0:.3f},{0:.3f})\n".format(xy_test[0][i], xy_test[1][i])) 
            ind_ref=i

    if verbose:
        print("** i: ",i)
        print("xy_ref:")
        print(xy_ref)                
        print(" ******* now fitting moving fiber ****")    
    # now fit the 'moving' fiber and de-rotate
    
    meas_pos = []

    for i in range(number_of_measurements):
        for j in range(len(xy[0][0])): 
            if j != ind_ref:
                meas_pos.append([xy[i][0][j],xy[i][1][j]])  # x,y from xy list
    print("++++ meas_pos +++")
    print(meas_pos)
    meas_pos = np.asarray(meas_pos)    

    if verbose:             
        print("first polyfit ====")
        print(meas_pos[:,0])     
        print(meas_pos[:,1])         
        print("--------------")

    m = np.polyfit(meas_pos[:,0],meas_pos[:,1],1)

    if verbose:
        print("m: ",m)
       
    a = math.atan(m[0])

    if verbose:
        print("a: ",a)

    
    R = np.matrix([[math.cos(a), math.sin(a)],[-1*math.sin(a), math.cos(a)]])

    if verbose:
        print("meas_pos")
        print(meas_pos)
        print("R")
        print(R)
    
    meas_pos_rot = np.dot(meas_pos,R.T)

    if verbose:
        print("meas_pos_rot")
        print(meas_pos_rot)

        print("second polyfit ====")
        print(meas_pos_rot[:,0])     
        print(input_pos)         
        print("--------------")

    q=np.asarray(meas_pos_rot[:,0]).flatten()
    p = np.polyfit(q,input_pos,1)
    print ("Measured scale is ",abs(p[0]), " input_unit / pixel\n")
   
    # now let's do some plotting
          
    plt.figure()
    plt.plot(q,input_pos,'bo')
    axes = plt.gca()
    xlim=axes.get_xlim()
    plt.plot(xlim,np.polyval(p,xlim),'k--')
    plt.xlabel('pixels')
    plt.ylabel('input unit')
    plot_filename='camera_scale_'+datetime.datetime.now().strftime("%Y%m%d-%I%M")[2:]
    plt.title(plot_filename)
    legend=str( round(abs(p[0]),3))+" input_units / pixel"
    plt.text(0.4, 0.95,legend, ha='center', va='center', transform=axes.transAxes)
    texttable ='INPUT  FVC X [px]   FVC Y [px]  ROTATED [px]'
    #texttable ='10.0   635.512   1537.888   1534.000'
    ypos=0.3    
    plt.text(0.35, ypos,texttable, ha='left', va='center', transform=axes.transAxes)
    sp="     "
    for i,x in enumerate(input_pos):
        ypos=ypos-0.035    
        texttable =str(round(x,2))+sp+str(round(meas_pos[i,0],3))+sp+str( round(meas_pos[i,1],3) )+sp+str( round(q[i],3) )
        plt.text(0.35, ypos,texttable, ha='left', va='center', transform=axes.transAxes)

    plt.xlabel('pixels')
    plt.ylabel('input unit')
    plt.savefig(plot_filename+".pdf")
    plt.show()  
else:
    print ("Not enough data points taken")
  

