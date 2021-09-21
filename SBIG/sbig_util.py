"""
This is a script for focusing the SBIG camera and then finding the camera scale based on fiducial metrology.
If the camera is already focused and just the camera scale is needed, simply click in the window that appears to skip focusing.
A single fiducial (3- or 4-dot) is the only thing that should be lit up when measuring the camera scale.  If just focusing is needed,
fibers can also be lit.  When running the script, enter the number of dots in the setup as an argument.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sbigcam
import multicens
import threading
from math import hypot
from itertools import combinations

cam = sbigcam.SBIGCam()
cam.open_camera()
cam.select_camera('ST8300')
cam.set_exposure_time(90)
cam.set_dark(False)
cam.set_fast_mode(fast_mode=False)

nargs=len(sys.argv)
if nargs < 2:
    print("Usage: puython3 sbig_util.py <nspots_expected>")
    sys.exit()
try:
    n_dots = int(sys.argv[1])
except:
    print("<ndots_expected> has to be an integer")
    sys.exit()
    
margin = 25
ready_for_centroiding = False
run_thread = True

fig = plt.figure("SBIG Utility", facecolor='w', figsize=(15,12))

def dist(p1,p2):
    x1,y1 = p1
    x2,y2 = p2
    return hypot(x2 - x1, y2 - y1)

def onClick(event):
    global ready_for_centroiding
    ready_for_centroiding ^= True
    if ready_for_centroiding:
        find_fid()
        scale, status = calc_scale()
        statustr = 'OK: expected spot configuration' if status else 'WARNING: unexpected spot configuration'
        plt.xlabel('Scale is:%8.2f $\mu$m/pxl,  %s' % (scale, statustr))
        
def get_cens():
    global peaksav, fwhmav
    while run_thread:
        if ready_for_centroiding:
            try:
                xt, yt,peakst,fwhmt,filename = multicens.multiCens(img, n_dots, verbose=True, write_fits=False)
                peaksav=int(np.mean(peakst))
                fwhmav=int(np.mean(fwhmt))
            except:
                peaksav=0
                fwhmav=0
     
def find_fid():
    global x,y,peaks,fwhm
    sample_image = cam.start_exposure()
    x,y,peaks,fwhm,filename = multicens.multiCens(sample_image, n_dots, verbose=True, write_fits=False)

def calc_scale():
    if n_dots == 4:
        ref_dists = np.asarray([ 1000., 1000., 1000., 1200., 1600., 2000.])
    elif n_dots == 3:
        ref_dists = np.asarray([1200., 1600., 2000.])
    else:
        return None, False
    meas_spot_coords = list(zip(x,y))
    meas_dists = np.asarray(sorted([dist(*combo) for combo in combinations(meas_spot_coords,2)]))
    scales = [ref/meas for ref,meas in zip(ref_dists, meas_dists)]
    scale=np.mean(scales)
    return scale, np.std(scales) <= 0.05

def take_exposure():
    global img
    img = cam.start_exposure()
    if ready_for_centroiding:
       return np.log(img[np.min(y)-margin:np.max(y)+margin, np.min(x)-margin:np.max(x)+margin]) 
    else:
       return np.log(img)

def updatefig(*args):
    im.set_array(take_exposure())
    if ready_for_centroiding:
        plt.title('Peak (avg): %d, FWHM (avg): %d, click to go back'% (peaksav,fwhmav))
    else:
        plt.title('Click when ready for centroiding/camera scale...')
        plt.xlabel('course focus mode: adjust focus until fiducial dots are distinct')
    plt.draw()
    return im,

im = plt.imshow(take_exposure(), animated=True)
fig.canvas.mpl_connect('button_press_event', onClick)
ani = animation.FuncAnimation(fig, updatefig, interval=100, blit=True)

fig.colorbar(im)
plt.title('Click when ready for centroiding/camera scale...')
plt.xlabel('course focus mode: adjust focus until fiducial dots are distinct')
t = threading.Thread(target=get_cens)
t.start()
plt.show()
run_thread = False
