#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Module for high-level interfacing with Fiber View Camera (FVC). Commands
camera to take images, detects dots, and returns centroids. May be used
either as a module called by other code, or standalone for single measurements
at the command line.
'''
import os
import sys
import argparse
sys.path.append(os.path.abspath('../'))
import globals as gl

# Supported cameras
cameras = {
    'SBIG': {
        'driver_path': '../SBIG/',
        'max_adu_counts': 2**16 - 1,
        }, 
    'simulator': {
        'driver_path': None,
        'max_adu_counts': None,
        },
    }  

# Measurement default parameters
defaults = {'camera': 'SBIG',
            'exptime': 0.2,  # exposure time in sec
            'fitbox': 5,  # ccd windowing for centroiding in pixels
            'x0_px': 0.0,  # x translational offset in pixels
            'y0_px': 0.0,  # y translational offset in pixels
            'angle_deg': 0.0,  # camera mounting angle in deg
            'mm_per_px': 1.0,  # plate scale, i.e. (mm at fibers) / (pixels at ccd)
            }

# Command line args for standalone mode, and defaults
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--camera', type=str, default=default_camera,
                    help=f'fiber view camera to use, valid options are {cameras.keys()}') 
parser.add_argument('-e', '--exptime', type=float, default=default_exposure_time, help='camera exposure time in seconds')
parser.add_argument('-b', '--fitbox', type=int, default=default_fitbox, help='window size for centroiding in pixels')
parser.add_argument('-d', '--take_darks', action='store_true', help='take dark images (shutter closed). typically not needed, since we keep the test stand in a dark enough enclosure')
parser.add_argument('-i', '--save_images', action='store_true', help='save image files to disk')
parser.add_argument('-b', '--save_biases', action='store_true', help='save bias image files to disk')
parser.add_argument('-se', '--sim_error2D', type=float, default=0.01, help='2D measurement error max for simulator')
parser.add_argument('-sb', '--sim_badmatchfreq', type=float, default=0.05, help='how often the simulator returns [0,0], indicating a bad match')
inputs = parser.parse_args()

import numpy as np
import math
import time
import collections

class FVCHandler(object):
    f'''Provides a generic interface to the Fiber View Camera. Can support different
    particular FVC implementations, providing a common set of functions to call
    from positioner control scripts.
 
    The order of operations for transforming from CCD pixel coordinates to the
    physical object plane (i.e. mm at the fiber tips) is:
        1. translation
        1. rotation
        3. scale

    INPUTS:
        camera ... string, identifying the camera hardware
        take_darks ... boolean, whether to take dark exposures (shutter closed)
        save_images ... boolean, whether to save FITS files etc to disk
        save_biases ... boolean, whether to save bias files to disk 
        printfunc ... function handle, to specify alternate to print (i.e. your logger)
    ''' 
    def __init__(self,
                 camera=inputs.camera,
                 take_darks=inputs.take_darks,
                 save_images=inputs.save_images,
                 save_biases=inputs.save_biases,
                 printfunc=print,
                 ):
        assert camera in cameras, f'unknown camera identifier {camera} (valid options are {cameras.keys()}'
        self.camera = camera
        self.printfunc = printfunc 
        self.min_energy = 0.  # 0.1 * .5 # this is the minimum allowed value for the product peak*fwhm for any given dot
        self.max_attempts = 5  # max number of times to retry an image measurement (if poor dot quality) before quitting hard
        self.exptime = inputs.exptime 
        self.fitbox = inputs.fitbox
        driver_path = cameras[self.camera]['driver_path']
        sys.path.append(os.path.abspath(driver_path))
        if self.camera == 'SBIG':
            import sbig_grab_cen
            self.sbig = sbig_grab_cen.SBIG_Grab_Cen(save_dir=gl.dirs['temp'], write_bias=save_biases)
            self.sbig.take_darks = take_darks 
            self.sbig.write_fits = save_images
            self.max_counts = cameras[self.camera]['max_adu_counts']
         elif self.fvc_type == 'simulator':
            self.sim_err_max = inputs.sim_error
            self.sim_badmatch_frquency = inputs.sim_badmatchfreq 
            self.printfunc(f'FVCHandler is in simulator mode with max 2D errors of size {self.sim_err_max} and bad match frequency of {self.sim_badmatch_frquency}.')
        self.x0_px = defaults['x0_px']  # x translation of origin within the image plane
        self.y0_px = defaults['y0_px']  # y translation of origin within the image plane
        self.angle_deg = defaults['angle_deg']  # [deg] rotation angle from image plane to object plane
        self.mm_per_px = defaults['mm_per_px']  # scale factor from image plane to object plane

    def measure_fvc_pixels(self, num_objects, attempt=1):
        """Gets a measurement from the fiber view camera of the centroid positions
        of all the dots of light landing on the CCD.
        
        INPUTS:  num_objects  ... integer, number of dots FVC should look for
        
        OUTPUT:  xy           ... list of measured dot positions in FVC pixel coordinates, of the form [[x1,y1],[x2,y2],...]
                 peaks        ... list of the peak brightness values for each dot, in the same order
                 fwhms        ... list of the fwhm for each dot, in the same order
                 imgfiles     ... list of image filenames that were produced
        """
        xy = []
        peaks = []
        fwhms = []
        imgfiles = []
        if self.camera == 'SBIG':
            self.sbig.exposure_time = self.exptime * 1000  # sbig_grab_cen thinks in milliseconds
            xy, peaks, fwhms, elapsed_time, imgfiles = self.sbig.grab(num_objects)
            peaks = [x/self.max_counts for x in peaks]
        elif self.camera == 'simulator':
            xy = np.random.uniform(low=0, high=1000, size=(num_objects,2)).tolist()
            peaks = np.random.uniform(low=0.25, high=1.0, size=num_objects).tolist()
            fwhms = np.random.uniform(low=1.0, high=2.0, size=num_objects).tolist()
            imgfiles = ['fake1.FITS', 'fake2.FITS']
        energies = [peaks[i] * fwhms[i] for i in range(len(peaks))]
        if any([e < self.min_energy for e in energies]):
            self.printfunc(f'Poor dot quality found on image attempt {attempt} of {self.max_attempts}. Gaussian fit peak * energy was {min(energies))} which is less than the minimum threshold {self.min_energy}')
            if attempt < self.max_attempts:
                return self.measure_fvc_pixels(num_objects, attempt + 1)
            else:
                self.printfunc(f'Max attempts {self.max_attempts} reached and still poor dot quality.')
                sys.exit(0)
        return xy, peaks, fwhms, imgfiles

    def measure_and_identify(self,expected_pos,expected_ref={}, pos_flags = {}):
        """Calls for an FVC measurement, and returns a list of measured centroids.
        The centroids are in order according to their closeness to the list of
        expected xy values.

        If the expected xy are unknown, then use the measure method instead.

        INPUT:  expected_pos ... dict of dicts giving expected positioner fiber locations
                expected_ref ... dict of dicts giving expected fiducial dot positions, not needed when using fvcproxy
                pos_flags    ... (optional) dict keyed by positioner indicating which flag as indicated below that a
                                 positioner should receive going to the FLI camera with fvcproxy
                
                The expected_pos and expected ref dot dicts should have primary keys
                be the posid or sub-fidid (of each dot), and the sub-keys should include
                'obsXY'. So that this function can access the expected positions with
                calls like:
                    expected_pos['M00001']['obsXY']
                    expected_ref['F001.0']['obsXY']

                flags    2 : pinhole center 
                         4 : fiber center 
                         8 : fiducial center 
                        32 : bad fiber or fiducial 

        OUTPUT: measured_pos ... list of measured positioner fiber locations
                measured_ref ... list of measured fiducial dot positions
                imgfiles     ... list of image file names (if any) that were given back by fvc
                
                The measured_pos and measured_ref returned are similarly shaped
                dicts of dicts. They are ordered dicts, so that they will preserve
                any ordering of the expected_pos and expected_ref, if applicable.
                
                They include the sub-keys:
                    'obsXY' ... measured [x,y] in the observer coordinate system (mm at the focal plane)
                    'peak'  ... peak brightness of the measured dot
                    'fwhm'  ... fwhm of the measured dot
        
        The argument 'expected_ref' is currently (as of May 26, 2017) ignored when
        operating in FLI mode. This is because the platemaker / FVC implementations
        do not currently support providing this information. The return value for
        measured_ref in this mode is an empty dict.
        """
        measured_pos = collections.OrderedDict.fromkeys(expected_pos.keys())
        measured_ref = collections.OrderedDict.fromkeys(expected_ref.keys())
        posids = list(measured_pos.keys())
        refids = list(measured_ref.keys())
        imgfiles = []
        expected_pos_xy = [expected_pos[posid]['obsXY'] for posid in posids]
        expected_ref_xy = [expected_ref[refid]['obsXY'] for refid in refids]
        if self.fvc_type == 'simulator':
            sim_error_magnitudes = np.random.uniform(-self.sim_err_max,self.sim_err_max,len(expected_pos_xy))
            sim_error_angles = np.random.uniform(-np.pi,np.pi,len(expected_pos_xy))
            sim_errors = sim_error_magnitudes * np.array([np.cos(sim_error_angles),np.sin(sim_error_angles)])
            measured_pos_xy = (expected_pos_xy + np.transpose(sim_errors)).tolist()
            for posid in posids:
                if np.random.uniform() < self.sim_badmatch_frquency:
                    obsXY = [0,0]
                else:
                    obsXY = measured_pos_xy[posids.index(posid)]
                measured_pos[posid] = {'obsXY':obsXY}
            for refid in refids:
                measured_ref[refid] = {'obsXY':expected_ref[refid]['obsXY']} # just copy the old vals
            for item in [measured_pos,measured_ref]:
                for key in item.keys():
                    item[key]['peak'] = np.random.uniform(0,1)  
                    item[key]['fwhm'] = np.random.uniform(0,1)
        else:
            expected_xy = expected_pos_xy + expected_ref_xy
            num_objects = len(expected_xy)
            unsorted_xy,unsorted_peaks,unsorted_fwhms,imgfiles = self.measure(num_objects)
            measured_xy,sorted_idxs = self.sort_by_closeness(unsorted_xy, expected_xy)
            sorted_posids_range = range(0,len(expected_pos_xy))
            sorted_refids_range = range(len(expected_pos_xy),len(sorted_idxs))
            measured_pos_xy = [measured_xy[i] for i in sorted_posids_range]
            measured_ref_xy = [measured_xy[i] for i in sorted_refids_range]
            measured_pos_xy = self.correct_using_ref(measured_pos_xy, measured_ref_xy, expected_ref_xy)
            measured_xy[:sorted_posids_range.stop] = measured_pos_xy
            sorted_peaks = np.array(unsorted_peaks)[sorted_idxs].tolist()
            sorted_fwhms = np.array(unsorted_fwhms)[sorted_idxs].tolist()
            for i in range(len(posids)):
                measured_pos[posids[i]] = {'obsXY':measured_xy[i], 'peak':sorted_peaks[i], 'fwhm':sorted_fwhms[i]}
            for i in range(len(refids)):
                j = i + sorted_posids_range.stop
                measured_ref[refids[i]] = {'obsXY':measured_xy[j], 'peak':sorted_peaks[j], 'fwhm':sorted_fwhms[j]}
        return measured_pos, measured_ref, imgfiles

    def correct_using_ref(self, measured_pos_xy, measured_ref_xy, expected_ref_xy):
        """Evaluates the correction that transforms measured_ref_xy into expected_ref_xy,
        and then applies this to the measured_xy values.
        """
        if len(measured_ref_xy) > 0:
            xy_diff = np.array(measured_ref_xy) - np.array(expected_ref_xy)
            xy_shift = np.median(xy_diff,axis=0)
            measured_pos_xy -= xy_shift
            measured_pos_xy = measured_pos_xy.tolist()
            # if two or more ref dots that are widely enough spaced, consider applying rotation and scale corrections here
        return measured_pos_xy

    def sort_by_closeness(self, unknown_xy, expected_xy):
        """Sorts the list unknown_xy so that each point is at the same index
        as its closest-distance match in the list expected_xy.
        """
        if len(unknown_xy) != len(expected_xy):
            self.printfunc('warning: unknown_xy length = ' + str(len(unknown_xy)) + ' but expected_xy length = ' + str(len(expected_xy)))
        xy = [None]*len(expected_xy)
        sorted_idxs = [None]*len(expected_xy)
        dist = []
        for e in expected_xy:
            delta = np.array(unknown_xy) - np.array(e)
            dist.append(np.sqrt(np.sum(delta**2,axis=1)).tolist())
        dist = np.array(dist)
        for i in range(len(unknown_xy)):
            min_idx_1D = np.argmin(dist)
            unknown_min_idx = np.mod(min_idx_1D,len(unknown_xy))
            expected_min_idx = np.int(np.floor(min_idx_1D/len(expected_xy)))
            xy[expected_min_idx] = unknown_xy[unknown_min_idx]
            sorted_idxs[expected_min_idx] = unknown_min_idx
            dist[expected_min_idx,:] = np.inf # disable used up "expected" row
            dist[:,unknown_min_idx] = np.inf # disable used up "unknown" column
        return xy, sorted_idxs

    def measure(self, num_objects=1):
        """Calls for an FVC image capture, applies simple transformations to get the
        centroids into the units and orientation of the object plane, and returns
        the centroids.
        
        This method short-circuits platemaker, operating directly on dots from the fiber
        view camera in a more simplistic manner. The general idea is that this is not a
        replacement for the accuracy performance of platemaker. Rather it is used for
        bootstrapping our knowledge of a new setup to a good-enough point where we can
        start to use platemaker.
            num_objects     ... number of dots to look for in the captured image
        """
        fvcXY,peaks,fwhms,imgfiles = self.measure_fvc_pixels(num_objects)
        obsXY = self.fvcXY_to_obsXY(fvcXY)
        return obsXY,peaks,fwhms,imgfiles

    def fvcXY_to_obsXY(self,xy):
        """Convert a list of xy values in fvc pixel space to obsXY coordinates.
          INPUT:  [[x1,y1],[x2,y2],...]  fvcXY (pixels on the CCD)
          OUTPUT: [[x1,y1],[x2,y2],...]  obsXY (mm at the focal plane)
        """
        if xy != []:
            xy = pc.listify2d(xy)
            xy_np = np.transpose(xy)
            translation_x = self.translation[0] * np.ones(np.shape(xy_np)[1])
            translation_y = self.translation[1] * np.ones(np.shape(xy_np)[1])
            xy_np += [translation_x,translation_y]
            xy_np *= self.scale
            rot = FVCHandler.rotmat2D_deg(self.rotation)
            xy_np = np.dot(rot, xy_np)
            xy = np.transpose(xy_np).tolist() 
        return xy
    
    def obsXY_to_fvcXY(self,xy):
        """Convert a list of xy values in obsXY coordinates to fvc pixel space.
        If there is no platemaker available, then it uses a simple rotation, scale,
        translate sequence instead.
          INPUT:  [[x1,y1],[x2,y2],...]  obsXY (mm at the focal plane)
          OUTPUT: [[x1,y1],[x2,y2],...]  fvcXY (pixels on the CCD)
        """
        if xy != []:
            xy = pc.listify2d(xy)
            xy_np = np.transpose(xy)
            rot = FVCHandler.rotmat2D_deg(-self.rotation)
            xy_np = np.dot(rot, xy_np)
            xy_np /= self.scale
            translation_x = self.translation[0] * np.ones(np.shape(xy_np)[1])
            translation_y = self.translation[1] * np.ones(np.shape(xy_np)[1])
            xy_np -= [translation_x,translation_y]
            xy = np.transpose(xy_np).tolist()
        return xy
    
    @staticmethod
    def rotmat2D_deg(angle):
        """Return the 2d rotation matrix for an angle given in degrees."""
        angle *= pc.rad_per_deg
        return np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])

if __name__ == '__main__':
    #f = FVCHandler(fvc_type='FLI',platemaker_instrument='petal1',fvc_role='FVC2')
    f = FVCHandler(fvc_type='SBIG')
    n_objects =1 #74 
    n_repeats = 1
    f.min_energy = -np.Inf
    xy = []
    peaks = []
    fwhms = []
    energies = []
    print('start taking ' + str(n_repeats) + ' images')
    start_time = time.time()
    for i in range(n_repeats):
        these_xy,these_peaks,these_fwhms,imgfiles = f.measure(n_objects)
        xy.append(these_xy)
        peaks.append(these_peaks)
        fwhms.append(these_fwhms)
        energies.append([these_peaks[i]*these_fwhms[i] for i in range(len(these_peaks))])
        x=[these_xy[i][0] for i in range(len(these_xy))]
        y=[these_xy[i][1] for i in range(len(these_xy))]
        import tkinter.messagebox
        plot = tkinter.messagebox.askyesno(title='Plot the measurements?',message='Plot the measurements?')
        metro = tkinter.messagebox.askyesno(title='Plot the metology data?',message='Plot the metrology data?')

        if plot:
            import matplotlib.pyplot as plt
            import tkinter
            import tkinter.filedialog
            import tkinter.simpledialog
            from tkinter import *
            from astropy.table import Table

            cm = plt.cm.get_cmap('RdYlBu')
            colors=these_peaks
            sc=plt.scatter(x, y, c=colors, alpha=0.7,vmin=min(colors), vmax=max(colors), s=35, cmap=cm)
            plt.colorbar(sc)
            #plt.plot(x,y,'bx',label="Measurements")

            if metro:
                file_metro=tkinter.filedialog.askopenfilename(initialdir=pc.dirs['hwsetups'], filetypes=(("CSV file","*.csv"),("All Files","*")), title='Select Metrology Data')
                fiducials= Table.read(file_metro,format='ascii.csv',header_start=0,data_start=1)
                metro_X_file_arr,metro_Y_file_arr=[],[]
                for row in fiducials:
                    metro_X_file_arr.append(row['X'])
                    metro_Y_file_arr.append(row['Y'])
                plt.plot(metro_X_file_arr,metro_Y_file_arr,'rd',label="Fiducials")
            plt.legend(loc='upper left')
            plt.xlabel('X')
            plt.ylabel('Y')
            plt.show()

        print('ndots: ' + str(len(xy[i])))
        print('')
        print('measured xy positions:')
        print(xy[i])
        print('')
        print('measured peak brightnesses:')
        print(peaks[i])
        print('dimmest (scale 0 to 1): ' + str(min(peaks[i])))
        print('brightest (scale 0 to 1): ' + str(max(peaks[i])))
        print('')
        print('measured full width half maxes:')
        print(fwhms[i])
        print('dimmest (scale 0 to 1): ' + str(min(fwhms[i])))
        print('brightest (scale 0 to 1): ' + str(max(fwhms[i])))
        print('')
        print('measured energies = peaks * fwhms:')
        print(energies[i])
        print('dimmest (scale 0 to 1): ' + str(min(energies[i])))
        print('brightest (scale 0 to 1): ' + str(max(energies[i])))
        print('')
    total_time = time.time() - start_time
    print('total time = ' + str(total_time) + ' (' + str(total_time/n_repeats) + ' per image)')
