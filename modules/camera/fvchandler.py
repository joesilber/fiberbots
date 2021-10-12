#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Module for high-level interfacing with Fiber View Camera (FVC). Commands
camera to take images, detects dots, and returns centroids.
'''
import os
import sys
import math
import numpy as np
this_file_dir = os.path.realpath(os.path.dirname(__file__))
os.chdir(this_file_dir)
sys.path.append('../../modules')
import globals as gl

# Supported cameras
cameras = {
    'SBIG': {
        'driver_path': './SBIG/',
        'max_adu_counts': 2**16 - 1,
        }, 
    'sim': {
        'driver_path': None,
        'max_adu_counts': None,
        },
    }  

# Measurement default parameters
defaults = gl.fvc_defaults.copy()

class FVCHandler():
    '''Provides a generic interface to the Fiber View Camera. Can support different
    particular FVC implementations, providing a common set of functions to call
    from positioner control scripts.
 
    The order of operations for transforming from CCD pixel coordinates to the
    physical object plane (i.e. mm at the fiber tips) is:
        1. translation
        1. rotation
        3. scale

    INPUTS:
        params ... dict, shaped like the 'defaults' dictionary above 
        take_darks ... boolean, whether to take dark exposures (shutter closed)
        save_images ... boolean, whether to save FITS files etc to disk
        save_biases ... boolean, whether to save bias files to disk 
        printfunc ... function handle, to specify alternate to print (i.e. your logger)
    ''' 
    def __init__(self, params=defaults, take_darks=False, save_images=False,
                 save_biases=False, printfunc=print):
        self.camera = params['camera']
        assert self.camera in cameras, f'unknown camera identifier {self.camera} (valid options are {cameras.keys()}'
        self.printfunc = printfunc 
        self.min_energy = 0.05  # this is the minimum allowed value for the product peak*fwhm for any given dot
        self.max_attempts = 3  # max number of times to retry an image measurement (if poor dot quality) before quitting hard
        self.exptime = params['exptime']
        self.fitbox = params['fitbox']
        driver_path = cameras[self.camera]['driver_path']
        sys.path.append(driver_path)
        if self.camera == 'SBIG':
            import sbig_grab_cen
            self.sbig = sbig_grab_cen.SBIG_Grab_Cen(save_dir=gl.dirs['temp'], write_bias=save_biases)
            self.sbig.take_darks = take_darks 
            self.sbig.write_fits = save_images
            self.max_counts = cameras[self.camera]['max_adu_counts']
        elif self.camera == 'sim':
            self.sim_errmax = params['sim_errmax']
            self.sim_badmatchfreq = params['sim_badmatchfreq']
            self.printfunc(f'FVCHandler is in simulator mode with max 2D errors of size {self.sim_errmax} and bad match frequency of {self.sim_badmatchfreq}.')
        self.x0_px = params['x0_px']  # x translation of origin within the image plane
        self.y0_px = params['y0_px']  # y translation of origin within the image plane
        self.angle_deg = params['angle_deg']  # [deg] rotation angle from image plane to object plane
        self.mm_per_px = params['mm_per_px']  # scale factor from image plane to object plane

    def measure_and_identify(self, expected, ref_keys=None):
        '''Calls for an FVC measurement, and returns a list of measured centroids.

        The centroids are identified according to their closeness to the argued 
        'expected' xy values.

        All coordinates are at the object plane (not the CCD).

        If expected positions are not yet known, then you can first use the measure()
        method alone and make your initial identifications of dots expected.

        INPUT:  expected ... dict with keys = unique identifiers for each dot to be
                             expected in the image, and values = (x,y) pairs, giving
                             location where dot is expected (in object plane coords,
                             i.e. physical mm at the fiber tips).

                ref_keys ... set of identifier keys, saying which if any of the
                             expected positions are reference fiducial dots
                
        OUTPUT: measured ... dict of (x,y) measured dot locations
                peaks    ... dict of peak brightnesses of measured dots
                fwhms    ... dict of full-width half-maxes of measured dots
                imgfiles ... list of image file names (if any) returned by camera 

        Output dicts will be keyed by same identifiers as the input dict 'expected'.
        '''
        ref_keys = set() if not ref_keys else set(ref_keys)
        posids = set(expected) - ref_keys 
        imgfiles = []
        ordered_keys = list(expected.keys())
        expected_xy = [expected[key] for key in ordered_keys]
        num_objects = len(expected_xy)
        unsorted_xy, unsorted_peaks, unsorted_fwhms, imgfiles = self.measure(num_objects)
        if self.camera == 'sim': # redo simulated measurements to be near the expected_xy
            jumbled_xy = expected_xy.copy()
            random.shuffle(jumbled_xy)
            for i, xy in enumerate(jumbled_xy):
                if random.uniform() < self.sim_badmatchfreq:
                    unsorted_xy[i] = [0, 0]
                else:
                    unsorted_xy[i] = [xy[j] + random.uniform(-self.sim_errmax, self.sim_errmax) for j in [0,1]] 
        sorted_xyraw, sorted_idxs = self.sort_by_closeness(unsorted_xy, expected_xy)
        sorted_peaks = [unsorted_peaks[i] for i in sorted_idxs]
        sorted_fwhms = [unsorted_fwhms[i] for i in sorted_idxs]
        xyraw = {ordered_keys[i]: sorted_xyraw[i] for i in range(len(sorted_xyraw))}
        peaks = {ordered_keys[i]: sorted_peaks[i] for i in range(len(sorted_peaks))}
        fwhms = {ordered_keys[i]: sorted_fwhms[i] for i in range(len(sorted_fwhms))}
        measured = self.correct_using_ref(xyraw, expected, ref_keys)
        return measured, peaks, fwhms, imgfiles

    def measure(self, num_objects=1):
        '''Calls for an FVC image capture, transforms the centroids from pixels into
        the units and orientation of the object plane.

        INPUTS:  num_objects ... number of dots to look for in the captured image

        Outputs are lists of:
            (x,y) centroids
            peak brightness values
            full-width half-maxes
            paths to any image files 
        '''
        xy_px, peaks, fwhms, imgfiles = self.measure_fvc_pixels(num_objects)
        xy_mm = self.fvc_to_obs(xy_px)
        return xy_mm, peaks, fwhms, imgfiles

    def measure_fvc_pixels(self, num_objects, attempt=1):
        """Gets a measurement from the fiber view camera of the centroid positions
        of all the dots of light landing on the CCD.
        
        INPUTS:  num_objects ... integer, number of dots FVC should look for
        
        OUTPUT:  xy          ... list of measured dot (x,y) positions in FVC pixel coordinates
                 peaks       ... list of the peak brightness values for each dot
                 fwhms       ... list of the fwhm for each dot
                 imgfiles    ... list of image filenames that were produced

        Lists xy, peaks, and fwhms are all in matching order.
        """
        xy = []
        peaks = []
        fwhms = []
        imgfiles = []
        if self.camera == 'SBIG':
            self.sbig.exposure_time = self.exptime * 1000  # sbig_grab_cen thinks in milliseconds
            xy, peaks, fwhms, elapsed_time, imgfiles = self.sbig.grab(num_objects)
            peaks = [x/self.max_counts for x in peaks]
        elif self.camera == 'sim':
            xy = np.random.uniform(low=0, high=1000, size=(num_objects,2)).tolist()
            peaks = np.random.uniform(low=0.25, high=1.0, size=num_objects).tolist()
            fwhms = np.random.uniform(low=1.0, high=2.0, size=num_objects).tolist()
            imgfiles = ['fake1.FITS', 'fake2.FITS']
        energies = [peaks[i] * fwhms[i] for i in range(len(peaks))]
        if any([e < self.min_energy for e in energies]):
            self.printfunc(f'Poor dot quality found on image attempt {attempt} of {self.max_attempts}. Gaussian fit peak * energy was {min(energies)} which is less than the minimum threshold {self.min_energy}')
            if attempt < self.max_attempts:
                return self.measure_fvc_pixels(num_objects, attempt + 1)
            else:
                self.printfunc(f'Max attempts {self.max_attempts} reached and still poor dot quality.')
                sys.exit(0)
        return xy, peaks, fwhms, imgfiles

    def correct_using_ref(self, measured, expected, ref_keys):
        '''Calculates a correction to transform measured reference dots into expected,
        and then applies this to all the measured xy values.

        INPUTS:  measured ... dict with keys = identifiers, values = [x,y] pairs
                 expected ... dict with keys = identifiers, values = [x,y] pairs
                 ref_keys ... set of keys indicating which dots are reference fiducials

        OUTPUT:  dict with keys = identifiers, values = [x,y] pairs
        '''
        assert all([key in measured and key in expected for key in ref_keys]), f'missing ref_key {ref_key}'
        x_shift, y_shift = 0, 0
        if any(ref_keys):
            x_diff = [measured[key][0] - expected[key][0] for key in ref_keys]
            y_diff = [measured[key][1] - expected[key][1] for key in ref_keys]
            x_shift = np.median(x_diff)
            y_shift = np.median(y_diff)
            # If we have two or more ref dots that are widely enough spaced, consider
            # applying rotation and scale corrections here. You'd especially want to
            # check for "widely-enough spaced", to ensure measurement noise isn't
            # significant.
        corrected = [[measured[key][0] + x_shift, measured[key][1] + y_shift] for key in measured]
        return corrected

    def sort_by_closeness(self, unknown_xy, expected_xy):
        """Sorts the list unknown_xy so that each point is at the same index
        as its closest-distance match in the list expected_xy.
        """
        if len(unknown_xy) != len(expected_xy):
            self.printfunc(f'unknown_xy length {len(unknown_xy)} != expected_xy length {len(expected_xy)}')
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

    def fvc_to_obs(self, xy_px):
        '''Convert a list or tuple of xy values in fvc pixel space to physical
        coordinates, as seen by an observer looking at the fiber tips.

        INPUT:  xy ... list or tuple of (x,y) coord in pixels on the CCD
        OUTPUT: list of (x,y) coord in mm at the focal plane
        '''
        x = [xy[0] + self.x0_px for xy in xy_px]
        y = [xy[1] + self.y0_px for xy in xy_px]
        rot = FVCHandler.rotmat2D_deg(self.angle_deg)
        xy_rotated = np.dot(rot, [x,y])
        xy_scaled = xy_rotated * self.mm_per_px
        xy_mm = np.transpose(xy_scaled).tolist()
        return xy_mm
    
    def obs_to_fvc(self, xy_mm):
        '''Convert a list or tuple of xy values in obsXY coordinates to fvc pixel space.

        INPUT:  xy ... list or tuple of (x,y) coord in mm at the focal plane
        OUTPUT: list of (x,y) coord in pixels on the CCD
        '''
        xy_np = np.transpose(xy_mm)
        xy_scaled = xy_np / self.mm_per_px
        rot = FVCHandler.rotmat2D_deg(-self.angle_deg)
        xy_rotated = np.dot(rot, xy_scaled)
        xy_translated = xy_rotated - [self.x0_mm, self.y0_mm]
        xy_px = np.transpose(xy_translated).tolist()
        return xy_px
    
    @staticmethod
    def rotmat2D_deg(angle):
        """Return the 2d rotation matrix for an angle given in degrees."""
        angle *= gl.rad_per_deg
        return np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])

