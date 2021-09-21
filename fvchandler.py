import os
import sys
if "TEST_LOCATION" in os.environ and os.environ['TEST_LOCATION']=='Michigan':
    basepath=os.environ['TEST_BASE_PATH']+'plate_control/'+os.environ['TEST_TAG']
    sys.path.append(os.path.abspath(basepath+'/petal/'))
    sys.path.append(os.path.abspath(basepath+'/posfidfvc/SBIG'))
else:
    sys.path.append(os.path.abspath('../petal/'))
    sys.path.append(os.path.abspath('../posfidfvc/SBIG'))
import numpy as np
import math
import time
import postransforms
import posconstants as pc
import collections

class FVCHandler(object):
    """Provides a generic interface to the Fiber View Camera. Can support different
    particular FVC implementations, providing a common set of functions to call
    from positioner control scripts.
    
    The order of operations for transforming from CCD coordinates to output is:
        1. rotation
        2. scale
        3. translation
    """
    def __init__(self, fvc_type='FLI', platemaker_instrument='petal2',fvc_role='FVC', printfunc=print, save_sbig_fits=True, write_bias=False):
        self.printfunc = printfunc # allows you to specify an alternate to print (useful for logging the output)
        self.fvc_type = fvc_type # 'SBIG' or 'SBIG_Yale' or 'FLI' or 'simulator'
        self.fvcproxy = None # may be auto-initialized later by the platemaker instrument setter
        self.min_energy = 0. #0.1 * .5 # this is the minimum allowed value for the product peak*fwhm for any given dot
        self.max_attempts = 5 # max number of times to retry an image measurement (if poor dot quality) before quitting hard
        self.fvc_role=fvc_role
        if self.fvc_type == 'SBIG':
            import sbig_grab_cen
            self.sbig = sbig_grab_cen.SBIG_Grab_Cen(save_dir=pc.dirs['temp_files'],write_bias=write_bias)
            self.sbig.take_darks = False # typically we have the test stand in a dark enough enclosure, so False here saves time
            self.sbig.write_fits = save_sbig_fits
        elif self.fvc_type == 'FLI' or self.fvc_type == 'SBIG_Yale':   
            self.platemaker_instrument = platemaker_instrument # this setter also initializes self.fvcproxy
        elif self.fvc_type == 'simulator':
            self.sim_err_max = 0.01 # 2D err max for simulator
            self.sim_badmatch_frquency = 0.05 # how often the simulator returns [0,0], indicating a bad match
            self.printfunc('FVCHandler is in simulator mode with max 2D errors of size ' + str(self.sim_err_max) + ', and bad match frequency of ' + str(self.sim_badmatch_frquency) + '.')
        if 'SBIG' in self.fvc_type:
            self.exposure_time = 0.20
            self.max_counts = 2**16 - 1 # SBIC camera ADU max
        else:
            self.exposure_time = 2.5
            self.max_counts = 2**16 - 1 # FLI camera ADU max
        self.trans = postransforms.PosTransforms() # general transformer object -- does not look up specific positioner info, but fine for QS <--> global X,Y conversions
        self.rotation = 0        # [deg] rotation angle from image plane to object plane
        self._scale = 1.0        # scale factor from image plane to object plane
        self.translation = [0,0] # translation of origin within the image plane
        self.fitbox_mm = 0.7     # size of gaussian fitbox at the object plane (note minimum fiducial dot distance is 1.0 mm apart)

    @property
    def scale(self):
        '''Return the fiber view camera scale. (scale * image plane --> object plane)
        '''
        return self._scale

    @scale.setter
    def scale(self,scale):
        '''Set the fiber view camera scale. (scale * image plane --> object plane)
        '''
        self._scale = scale
        if 'SBIG' in self.fvc_type:
            self.sbig.size_fitbox = 5 #int(np.ceil(self.fitbox_mm/2.3 / scale))

    @property
    def platemaker_instrument(self):
        """Return name of the platemaker instrument.
        """
        return self.__platemaker_instrument

    @platemaker_instrument.setter
    def platemaker_instrument(self,name):
        """Set the platemaker instrument.
        """
        from DOSlib.proxies import FVC
        self.__platemaker_instrument = name
        self.fvcproxy = FVC(self.platemaker_instrument, fvc_role =self.fvc_role)
        self.printfunc('proxy FVC created for instrument %s' % self.fvcproxy.get('instrument'))

    @property
    def exposure_time(self):
        """Time in seconds to expose.
        """
        return self.__exposure_time

    @exposure_time.setter
    def exposure_time(self,value):
        self.__exposure_time = value
        if self.fvc_type == 'SBIG':
            self.sbig.exposure_time = value*1000 # sbig_grab_cen thinks in milliseconds
        elif self.fvcproxy:
            self.fvcproxy.send_fvc_command('set',exptime=value)
        
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
        if self.fvc_type == 'SBIG':
            xy,peaks,fwhms,elapsed_time,imgfiles = self.sbig.grab(num_objects)
            peaks = [x/self.max_counts for x in peaks]
        elif self.fvc_type == 'simulator':
            xy = np.random.uniform(low=0,high=1000,size=(num_objects,2)).tolist()
            peaks = np.random.uniform(low=0.25,high=1.0,size=num_objects).tolist()
            fwhms = np.random.uniform(low=1.0,high=2.0,size=num_objects).tolist()
            imgfiles = ['fake1.FITS','fake2.FITS']
        else:
            self.fvcproxy.send_fvc_command('make_targets',num_spots=num_objects)
            centroids = self.fvcproxy.locate(send_centroids=True)
            #if len(centroids) < num_objects:
            #    print('number of spots found does not match number of targets, autotune and try again. ')
            #    self.fvcproxy.calibrate_image()      
            #    centroids = self.fvcproxy.locate(send_centroids=True)
            if 'FAILED' in centroids:
                self.printfunc('Failed to locate centroids using FVC.')
            else:
                for params in centroids.values():
                    xy.append([params['x'],params['y']])
                    peaks.append(self.normalize_mag(params['mag']))
                    fwhms.append(params['fwhm'])
        energies = [peaks[i]*fwhms[i] for i in range(len(peaks))]
        if any([e < self.min_energy for e in energies]):
            self.printfunc('Poor dot quality found on image attempt ' + str(attempt) + ' of ' + str(self.max_attempts) + '. Gaussian fit peak * energy was ' + str(min(energies)) + ' which is less than the minimum threshold (' + str(self.min_energy) + ')')
            if attempt < self.max_attempts:
                return self.measure_fvc_pixels(num_objects, attempt + 1)
            else:
                if self.fvc_type == 'FLI':
                    self.printfunc('Max attempts (' + str(self.max_attempts) + ') reached and still poor dot quality.')
                else:
                    sys.exit(0) # on the test stand, we definitely want to hard quit in this case
        return xy,peaks,fwhms,imgfiles

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
        if self.fvcproxy:
            expected_qs = [] # this is what will be provided to platemaker
            fiber_ctr_flag = 4 # this enumeration is specific to Yale/FLI FVC interface
            for posid in posids:
                qs = self.trans.obsXY_to_QS(expected_pos[posid]['obsXY'])
                if posid in pos_flags.keys():
                    expected_qs.append({'id':posid, 'q':qs[0], 's':qs[1], 'flags':pos_flags[posid]})
                else: #Assume it is good, old default behavior
                    expected_qs.append({'id':posid, 'q':qs[0], 's':qs[1], 'flags':fiber_ctr_flag})
            measured_qs = self.fvcproxy.measure(expected_qs)
            if len(measured_qs) < len(expected_qs):
                # for all the expected positioners that weren't included, generate a dummy dict
                measured_posids = {d['id'] for d in measured_qs}
                expected_posids = {d['id'] for d in expected_qs} #PARKER CHANGED set(expected_qs.keys())
                # posids set difference etc
                #dummy_qs_dict = {'q':0.0,'s':0.0, 'dq':0.0,'ds':0.0, 'flags':1, 'peak':0.0, 'mag':0.0, 'fwhm':0.0}
                # make one for each posid and add to the list measured_qs
                for id in expected_posids:
                	if id not in measured_posids:
                		#print(id)
                		dummy_qs_dict = {'id':id,'q':0.0,'s':0.0, 'dq':0.0,'ds':0.0, 'flags':1, 'peak':0.0, 'mag':0.0, 'fwhm':0.0}

                		#dummy_qs_dict.update({'id':id})
                		#print(dummy_qs_dict)
                		measured_qs.append(dummy_qs_dict)
            elif len(measured_qs) > len(expected_qs):
            	# remove dicts from measured_qs until correct number remaining
            	# start with the unmatched ones (those with flag =0)
            	for e in measured_qs:
            		if len(measured_qs) > len(expected_qs) and e['flag']==0:
            			measured_qs.remove(e) # check that this actually works and that the loop is still okay
            	# if we still have too many measured_qs's
            	if len(measured_qs) > len(expected_qs):	
            	# remove the dimmest ones (this may not be the right approch ..)
            	# we have to see from experience how to filter best. It may require to sort 
            	# by variation of fwhm, or fwhm*mag, or something to know which to remove	
            		pass
            for qs_dict in measured_qs:
                match_found = qs_dict['flags'] & 1 # when bit 0 is true, that means a match was found
                if match_found:
                    q = qs_dict['q']
                    s = qs_dict['s'] #CHANGED BY PARKER 2/11/19
                    dq = qs_dict['dq']
                    ds = qs_dict['ds'] #ALSO CHANGED BY PARKER 2/1//19
                else:
                    print(qs_dict)
                    q = [0.0]
                    s = [0.0] # intentionally an impossible-to-reach unique position, so that it's obvious we had a match failure but code continues
                    dq =[0.0]
                    ds = [0.0]
                xy = self.trans.QS_to_obsXY([q,s])
                posid = qs_dict['id']
                measured_pos[posid] = {'obsXY':xy, 'peak':self.normalize_mag(qs_dict['mag']), 'fwhm':qs_dict['fwhm'], 'q':q, 's':s, 'dq':dq, 'ds':ds}
        else:
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

    def normalize_mag(self,value):
        """Convert magnitude values coming from Rabinowitz code to a normalized
        brightness value in the range 0.0 to 1.0.
        25.0 - 2.5*log10(peak signal in ADU)
        """
        newval = 10**((25.0 - value)/2.5)
        newval = newval / self.max_counts
        newval = min(newval,1.0)
        newval = max(newval,0.0)
        return newval

    def fvcXY_to_obsXY(self,xy):
        """Convert a list of xy values in fvc pixel space to obsXY coordinates.
        If there is no platemaker available, then it uses a simple rotation, scale,
        translate sequence instead.
          INPUT:  [[x1,y1],[x2,y2],...]  fvcXY (pixels on the CCD)
          OUTPUT: [[x1,y1],[x2,y2],...]  obsXY (mm at the focal plane)
        """
        if xy != []:
            if self.fvcproxy:
                #Temporary hack, data passed in wrong format
                if isinstance(xy[0],float):
                    xy=[xy]
                else:
                    if isinstance(xy[0][0], list):
                        xy_new = [[xy[0][0][i],xy[0][1][i]] for i in range(len(xy[0][0]))]
                        xy = xy_new
                #End of hack
                spotids = [i for i in range(len(xy))]
                fvcXY_dicts = [{'spotid':spotids[i],'x_pix':xy[i][0],'y_pix':xy[i][1]} for i in range(len(spotids))]
                qs_dicts = self.fvcproxy.fvcxy_to_qs(fvcXY_dicts)
                return_order = [spotids.index(d['spotid']) for d in qs_dicts]
                qs = [[qs_dicts[i]['q'],qs_dicts[i]['s']] for i in return_order]
                xy = [self.trans.QS_to_obsXY(qs[i]) for i in range(len(qs))]
                #xy = np.transpose(xy).tolist()
            else:
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
            if self.fvcproxy:
                #Temporary hack, data passed in wrong format
                #import pdb;pdb.set_trace()
                if isinstance(xy[0], float):
                    xy=[xy]
                else:
                    if isinstance(xy[0][0], list):
                        xy_new = [[xy[0][0][i],xy[0][1][i]] for i in range(len(xy[0][0]))]
                        xy = xy_new
                #End of hack
                spotids = [i for i in range(len(xy))]
                qs = [self.trans.obsXY_to_QS(this_xy) for this_xy in xy]
                qs_dicts = [{'spotid':spotids[i],'q':qs[i][0],'s':qs[i][1]} for i in range(len(spotids))]
                print(qs_dicts)
                fvcXY_dicts = self.fvcproxy.qs_to_fvcxy(qs_dicts) # fiducials are added in this process 
                fvcXY_dicts_this=[]  # Kai: This is a temporary fix, a more efficient fix should be done in the future to save time
                for d in fvcXY_dicts:
                    if d['spotid'] in spotids:
                        fvcXY_dicts_this.append(d)
                return_order = [spotids.index(d['spotid']) for d in fvcXY_dicts_this]
                xy = [[fvcXY_dicts_this[i]['x'],fvcXY_dicts_this[i]['y']] for i in return_order]
            else:
                
                #import pdb; pdb.set_trace()
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
