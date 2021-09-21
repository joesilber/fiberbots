import os
import sys
if "TEST_LOCATION" in os.environ and os.environ['TEST_LOCATION']=='Michigan':
    basepath=os.environ['TEST_BASE_PATH']+'plate_control/'+os.environ['TEST_TAG']
    sys.path.append(os.path.abspath(basepath+'/petal/'))

else:
    sys.path.append(os.path.abspath('../petal/'))

import postransforms
import numpy as np
import fitcircle
import posconstants as pc
import poscalibplot
import scipy.optimize
import collections
from astropy.table import Table

class PosMoveMeasure(object):
    """Coordinates moving fiber positioners with fiber view camera measurements.
    """
    def __init__(self, petals, fvc, printfunc=print):
        self.printfunc = printfunc # allows you to specify an alternate to print (useful for logging the output)
        if not isinstance(petals,list):
            petals = [petals]
        self.petals = petals # list of petal objects
        self._petals_map = {} # maps which petals hold which posids
        for petal in self.petals:
            for posid in petal.posids:
                self._petals_map[posid] = petal
            for fidid in petal.fidids:
                self._petals_map[fidid] = petal
                for dotid in fid_dotids(fidid, petal):
                    self._petals_map[dotid] = petal
        self.fvc = fvc # fvchandler object
        self.wide_spotmatch_radius = 80.0 #20.0 #1000.0 # [pixels on FLI FVC CCD] wide search radius used during rough calibration when theta and phi offsets are unknown
        self.ref_dist_tol = 3.0   # [pixels on FVC CCD] used for identifying fiducial dots
        self.ref_dist_thres =100.0  # [pixels on FVC CCD] if distance to all dots are greater than this, probably a misidentification 
        self.nudge_dist   = 10.0  # [deg] used for identifying fiducial dots
        self.extradots_fvcXY = [] # stores [x,y] pixel locations of any "extra" fiducial dots in the field (used for fixed ref fibers in laboratory test stands)
        self.extradots_id = 'EXTRA' # identifier to use in extra dots id string
        self.n_extradots_expected = 0 # number of extra dots to look for in the field of view
        self.n_points_calib_T = 7 # number of points in a theta calibration arc
        self.n_points_calib_P = 7 # number of points in a phi calibration arc
        self.should_set_gear_ratios = False # whether to adjust gear ratios after calibration
        self.phi_Eo_margin = 3.0 # [deg] margin on staying within Eo envelope
        self.phi_close_angle = 135.0 # [deg] phi angle where fiber is quite close to the center, within the spot-matching radius tolerance of the fiber view camera. Consider at a later date moving this parameter out into a settings file such as the collider .conf file.
        self.calib_arc_margin = 3.0 # [deg] margin on calibration arc range
        self.use_current_theta_during_phi_range_meas = False # useful for when theta axis is not installed on certain sample positioners
        self.general_trans = postransforms.PosTransforms() # general transformation object (not specific to calibration of any one positioner), useful for things like obsXY to QS or QS to obsXY coordinate transforms
        self.grid_calib_param_keys = ['LENGTH_R1','LENGTH_R2','OFFSET_T','OFFSET_P','OFFSET_X','OFFSET_Y']
        self.err_level_to_save_move0_img = np.inf # value at which to preserve move 0 fvc images (for debugging if a measurement is off by a lot)
        self.err_level_to_save_moven_img = np.inf # value at which to preserve last corr move fvc images (for debugging if a measurement is off by a lot)
        self.tp_updates_mode = 'posTP' # options are None, 'posTP', 'offsetsTP'. see comments in move_measure() function for explanation
        self.tp_updates_tol = 0.065 # [mm] tolerance on error between requested and measured positions, above which to update the POS_T,POS_P or OFFSET_T,OFFSET_P parameters
        self.tp_updates_fraction = 0.8 # fraction of error distance by which to adjust POS_T,POS_P or OFFSET_T,OFFSET_P parameters after measuring an excessive error with FVC
        self.make_plots_during_calib = True # whether to automatically generate and save plots of the calibration data
        self.enabled_posids = []
        self.disabled_posids = []
        self.posid_not_identified=self.all_posids
        
    def measure(self, pos_flags = None):
        """Measure positioner locations with the FVC and return the values.

        INPUT:  pos_flags ... (optional) dict keyed by positioner indicating which flag as indicated below that a
                              positioner should receive going to the FLI camera with fvcproxy
                flags    2 : pinhole center 
                         4 : fiber center 
                         8 : fiducial center 
                        32 : bad fiber or fiducial 

        Return data is a dictionary with:   keys ... posid
                                          values ... [measured_obs_x, measured_obs_y]
        """
        if not(pos_flags):
            pos_flags = {}
            for ptl in self.petals:
                pos_flags.update(ptl.get_pos_flags())        
        data = {}
        expected_pos = collections.OrderedDict()
        for posid in self.all_posids:
            ptl = self.petal(posid)
            expected_pos[posid] = {'obsXY':ptl.expected_current_position(posid,'obsXY')}
        expected_ref = {} if self.fvc.fvcproxy else self.ref_dots_XY
        measured_pos,measured_ref,imgfiles = self.fvc.measure_and_identify(expected_pos,expected_ref, pos_flags=pos_flags)            
        for posid in self.all_posids:
            ptl = self.petal(posid)            
            ptl.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_pos[posid]['obsXY'][0])
            ptl.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_pos[posid]['obsXY'][1])
            ptl.set_posfid_val(posid,'LAST_MEAS_PEAK',measured_pos[posid]['peak'])
            ptl.set_posfid_val(posid,'LAST_MEAS_FWHM',measured_pos[posid]['fwhm'])
            data[posid] = measured_pos[posid]['obsXY']
        fid_data = {}
        for refid in measured_ref.keys():
            if self.extradots_id not in refid:
                ptl = self.petal(refid)
                fidid = self.extract_fidid(refid)
                if fidid not in fid_data.keys():
                    fid_data[fidid] = {key:[] for key in ['obsX','obsY','peaks','fwhms']}
                fid_data[fidid]['obsX'].append(measured_ref[refid]['obsXY'][0])
                fid_data[fidid]['obsY'].append(measured_ref[refid]['obsXY'][1])
                fid_data[fidid]['peaks'].append(measured_ref[refid]['peak'])
                fid_data[fidid]['fwhms'].append(measured_ref[refid]['fwhm'])
        for fidid in fid_data.keys():
            ptl = self.petal(fidid)
            ptl.set_posfid_val(fidid,'LAST_MEAS_OBS_X',fid_data[fidid]['obsX'])
            ptl.set_posfid_val(fidid,'LAST_MEAS_OBS_Y',fid_data[fidid]['obsY'])
            ptl.set_posfid_val(fidid,'LAST_MEAS_PEAKS',fid_data[fidid]['peaks'])
            ptl.set_posfid_val(fidid,'LAST_MEAS_FWHMS',fid_data[fidid]['fwhms'])
        return data,imgfiles

    def move(self, requests, anticollision='default'):
        """Move positioners. See request_targets method in petal.py for description
        of format of the 'requests' dictionary.
        
        Return is another requests dictionary, but now containing only the requests
        that were accepted as valid.
        """
        posids_by_petal = self.posids_by_petal(requests)
        accepted_requests= {}
        for petal,posids in posids_by_petal.items():
            these_requests = {}
            for posid in posids:
                these_requests[posid] = requests[posid]
            these_accepted_requests = petal.request_targets(these_requests)
            petal.schedule_send_and_execute_moves(anticollision=anticollision)
            accepted_requests.update(these_accepted_requests)
        print('<posmovemeasure.move> accepted_requests',accepted_requests) #from B141 PAF 5/28/19
        print('<posmovemeasure.move> these_requests',these_requests) #from B141 PAF 5/28/19
        return accepted_requests

    def move_measure(self, requests, tp_updates=None, anticollision='default'):
        """Move positioners and measure output with FVC.
        See comments on inputs from move method.
        See comments on outputs from measure method.
        tp_updates  ... This optional setting allows one to turn on a mode where the measured fiber positions
                        will be compared against the expected positions, and then if the error exceeds some
                        tolerance value, we will update internal parameters to mitigate the error on future moves.
                        
                            tp_updates='posTP'     ... updates will be made to the internally-tracked shaft positions, POS_T and POS_P
                            tp_updates='offsetsTP' ... updates will be made to the calibration values OFFSET_T and OFFSET_P
                            tp_updates='offsetsTP_close' ... updates will be made to the calibration values OFFSET_T and OFFSET_P. The difference with 'offsetTP' is that the phi is opend to phi_close_angle instead of the E0 angle specified in poscollider. 
                            tp_updates=None        ... no updating (this is the default)
                        
                        The intention of the 'posTP' option is that if the physical motor shaft hangs up slightly and loses
                        sync with the rotating magnetic field in the motors, then we slightly lose count of where we are. So
                        updating 'posTP' adjusts our internal count of shaft angle to try to mitigate.
                        
                        The usage of the 'offsetsTP' option is expected to be far less common than 'posTP', because
                        we anticipate that the calibration offsets should be quite stable, reflecting the unchanging
                        physical geometry of the fiber positioner as-installed. The purpose of using 'offsetsTP' would be more
                        limited to scenarios of initial calibration, if for some reason we find that the usual calibrations are
                        failing.
        """
        accepted_requests = self.move(requests,anticollision)
        data,imgfiles = self.measure()

        if tp_updates == 'posTP' or tp_updates =='offsetsTP' or tp_updates == 'offsetsTP_close':
            self._test_and_update_TP(data, tp_updates)
        return data,imgfiles,accepted_requests

    def move_and_correct(self, requests, num_corr_max=2, force_anticoll_on=False):
        """Move positioners to requested target coordinates, then make a series of correction
        moves in coordination with the fiber view camera, to converge.

        INPUTS:     
            requests      ... dictionary of dictionaries
                                ... formatted the same as any other move request
                                ... see request_targets method in petal.py for description of format
                                ... however, only 'obsXY' or 'QS' commands are allowed here
            num_corr_max  ... maximum number of correction moves to perform on any positioner
            force_anticoll_on   ... boolean value to force usage of anticollision (overrides any petal default)

        OUTPUT:
            The measured data gets stored into into a new dictionary, which is a shallow copy of
            'requests', but with new fields added to each positioner's subdictionary:

                KEYS        VALUES
                ----        ------
                targ_obsXY  [x,y]                       ... target coordinates in obsXY system
                meas_obsXY  [[x0,y0],[x1,y1],...]       ... measured xy coordinates for each submove
                errXY       [[ex0,ey0],[ex1,ey1],...]   ... error in x and y for each submove
                err2D       [e0,e1,...]                 ... error distance (errx^2 + erry^2)^0.5 for each submove
                posTP       [[t0,p0],[t1,p1],...]       ... ierr_level_to_save_movei_imgnternally-tracked expected angular positions of the (theta,phi) shafts at the outputs of their gearboxes
        """
        data = requests.copy()
        for posid in data.keys():
            m = data[posid] # for terseness below
            if m['command'] == 'obsXY':
                m['targ_obsXY'] = m['target']
            elif m['command'] == 'QS':
                m['targ_obsXY'] = self.general_trans.QS_to_obsXY(m['target'])
            else:
                self.printfunc('coordinates \'' + m['command'] + '\' not valid or not allowed')
                return
            m['log_note'] = 'blind move'
            self.printfunc(str(posid) + ': blind move to (obsX,obsY)=(' + self.fmt(m['targ_obsXY'][0]) + ',' + self.fmt(m['targ_obsXY'][1]) + ')')
        anticoll = 'adjust' if force_anticoll_on else 'default'
        
        # make the blind move
        this_meas,imgfiles,accepted_requests = self.move_measure(data, tp_updates=self.tp_updates_mode, anticollision=anticoll)
        save_img = False
        for posid in this_meas.keys():
            m = data[posid] # again, for terseness
            m['meas_obsXY'] = [this_meas[posid]]
            if m['meas_obsXY'][-1] == [0,0]:
                self.petal(posid).set_posfid_val(posid, 'CTRL_ENABLED', False)
                self.petal(posid).pos_flags[posid] |= self.petal(posid).ctrl_disabled_bit
                self.petal(posid).pos_flags[posid] |= self.petal(posid).bad_fiber_fvc_bit
                self.printfunc(str(posid) + ': disabled due to not being matched to a centroid.')
            m['errXY'] = [[m['meas_obsXY'][-1][0] - m['targ_obsXY'][0],
                           m['meas_obsXY'][-1][1] - m['targ_obsXY'][1]]]
            m['err2D'] = [(m['errXY'][-1][0]**2 + m['errXY'][-1][1]**2)**0.5]
            m['posTP'] = self.petal(posid).expected_current_position(posid,'posTP')
            if m['err2D'][-1] > self.err_level_to_save_move0_img:
                save_img = True
        if save_img:
            timestamp_str = pc.filename_timestamp_str()
            for file in imgfiles:
                os.rename(file, pc.dirs['xytest_plots'] + timestamp_str + '_move0' + file)
                
        # record which positioners that had their blind move accepted vs denied
        accepted_blindmove_posids = accepted_requests.keys()         
        
        # make the correction moves
        for i in range(1,num_corr_max+1):
            correction = {}
            save_img = False
            for posid in data.keys():
                correction[posid] = {}
                if posid in accepted_blindmove_posids:
                    dxdy = [-data[posid]['errXY'][-1][0],-data[posid]['errXY'][-1][1]]
                    correction[posid]['log_note'] = 'correction move ' + str(i)
                    self.printfunc(str(posid) + ': correction move ' + str(i) + ' of ' + str(num_corr_max) + ' by (dx,dy)=(' + self.fmt(dxdy[0]) + ',' + self.fmt(dxdy[1]) + '), \u221A(dx\u00B2+dy\u00B2)=' + self.fmt(data[posid]['err2D'][-1]))
                else:
                    dxdy = [0.0,0.0]
                    correction[posid]['log_note'] = 'zero distance correction move ' + str(i) + ' after a denied blind move'
                    self.printfunc(str(posid) + ': zero distance correction move after a denied blind move')
                correction[posid]['command'] = 'dXdY'
                correction[posid]['target'] = dxdy
            anticoll = 'freeze' if force_anticoll_on else None
            this_meas,imgfiles,accepted_requests = self.move_measure(correction, tp_updates=self.tp_updates_mode, anticollision=anticoll)
            for posid in this_meas.keys():
                m = data[posid] # again, for terseness
                m['meas_obsXY'].append(this_meas[posid])
                if m['meas_obsXY'][-1] == [0,0] and self.fvc.fvcproxy:
                    self.petal(posid).set_posfid_val(posid, 'CTRL_ENABLED', False)
                    self.petal(posid).pos_flags[posid] |= self.petal(posid).ctrl_disabled_bit
                    self.petal(posid).pos_flags[posid] |= self.petal(posid).bad_fiber_fvc_bit
                    self.printfunc(str(posid) + ': disabled due to not being matched to a centroid.')
                m['errXY'].append([m['meas_obsXY'][-1][0] - m['targ_obsXY'][0],
                                   m['meas_obsXY'][-1][1] - m['targ_obsXY'][1]])
                m['err2D'].append((m['errXY'][-1][0]**2 + m['errXY'][-1][1]**2)**0.5)
                m['posTP'].append(self.petal(posid).expected_current_position(posid,'posTP'))
                if m['err2D'][-1] > self.err_level_to_save_moven_img and i == num_corr_max:
                    save_img = True
            if save_img:
                timestamp_str = pc.filename_timestamp_str()
                for file in imgfiles:
                    os.rename(file, pc.dirs['xytest_plots'] + timestamp_str + '_move' + str(i) + file)                
        for posid in data.keys():
            self.printfunc(str(posid) + ': final error distance=' + self.fmt(data[posid]['err2D'][-1]))
            print('<posmovemeasure.move_and_correct> anticollision: ',anticoll) #from B141 PAF 5/28/19
        return data

    def retract_phi(self,posids='all'):
        """Get all phi arms within their clear rotation envelopes for positioners
        identified by posids.
        """
        posids_by_petal = self.posids_by_petal(posids)
        requests = {}
        obsP = self.phi_clear_angle # uniform value in all cases
        for these_posids in posids_by_petal.values():
            for posid in these_posids:
                obsT = self.posmodel(posid).expected_current_obsTP[0]
                requests[posid] = {'command':'obsTP', 'target':[obsT,obsP], 'log_note':'retracting phi'}
        self.move(requests)
    
    def park(self,posids='all'):
        """Fully retract phi arms inward, and put thetas at their neutral theta = 0 position.
        """
        posids_by_petal = self.posids_by_petal(posids)
        requests = {}
        posT = 0.0 # uniform value in all cases
        for these_posids in posids_by_petal.values():
            for posid in these_posids:
                posP = max(self.posmodel(posid).targetable_range_P)
                requests[posid] = {'command':'posTP', 'target':[posT,posP], 'log_note':'parking'}
        self.move(requests)
        
    def one_point_calibration(self, posids='all', mode='posTP', wide_spotmatch=False):
        """Goes to a single point, makes measurement with FVC, and re-calibrates the internally-
        tracked angles for the current theta and phi shaft positions.
        
        This method is attractive after steps like rehoming to hardstops, because it is very
        quick to do, and should be fairly accurate in most cases. But will never be as statistically
        robust as a regular calibration routine, which does arcs of multiple points and then takes
        the best fit circle.
        
          mode ... 'posTP'              --> [common usage] moves positioner to (posT=0,obsP=self.phi_clear_angle),
                                                  and then updates our internal counter on where we currently
                                                  expect the theta and phi shafts to be
                                                 
               ... 'offsetsTP'          --> [expert usage] moves to (posT=0,obsP=self.phi_clear_angle),
                                                  and then updates setting for theta and phi physical offsets
                                                 
               ... 'offsetsTP_close'    --> [expert usage] moves to (posT=0,obsP=self.phi_close_angle),
                                                  and then updates setting for theta and phi physical offsets
                                                  
               ... 'offsetsXY'          --> [expert usage] moves positioner to (posT=0,obsP=180),
                                                  and then updates setting for x and y physical offsets
               
        Prior to calling a mode of 'offsetTP' or 'offsetXY', it is recommended to re-home the positioner
        if there is any uncertainty as to its current location. This is generally not necessary
        in the default case, using 'posTP'.
        
        The wide_spotmatch argument allows forcing use of self.wide_spotmatch_radius when in fvcproxy mode.
        """
        self.printfunc('Running one-point calibration of ' + mode)
        if self.fvc.fvcproxy and wide_spotmatch:
            old_spotmatch_radius = self.fvc.fvcproxy.get('match_radius')
            self.fvc.fvcproxy.set(match_radius = self.wide_spotmatch_radius)
            self.printfunc('Spotmatch radius temporarily changed from ' + str(old_spotmatch_radius) + ' to ' + str(self.wide_spotmatch_radius) + '.')
        posT = 0.0 # uniform value in all cases
        dummy_obsT = 0.0 # value doesn't matter -- only used for conformance to transforms interface below
        if mode in {'posTP','offsetsTP'}:
            obsP = self.phi_clear_angle
        elif mode == 'offsetsTP_close':
            obsP = self.phi_close_angle
        else:
            obsP = 180.0
        posids_by_petal = self.posids_by_petal(posids)
        requests = {}
        for these_posids in posids_by_petal.values():
            for posid in these_posids:
                posP = self.trans(posid).obsTP_to_posTP([dummy_obsT,obsP])[1]
                requests[posid] = {'command':'posTP', 'target':[posT,posP], 'log_note':'one point calibration of ' + mode}
        if mode == 'posTP' or mode == 'offsetsTP' or mode == 'offsetsTP_close':
            old_tp_updates_tol = self.tp_updates_tol
            old_tp_updates_fraction = self.tp_updates_fraction
            self.tp_updates_tol = 0.001
            self.tp_updates_fraction = 1.0
            data,imgfiles,accepted_requests = self.move_measure(requests,tp_updates=mode)
            self.tp_updates_tol = old_tp_updates_tol
            self.tp_updates_fraction = old_tp_updates_fraction
        else:
            data,imgfiles,accepted_requests = self.move_measure(requests, tp_updates=None)
            for petal,these_posids in posids_by_petal.items():
                for posid in these_posids:
                    xy = data[posid]
                    if petal.posmodels[posid].is_enabled:
                        petal.set_posfid_val(posid,'OFFSET_X',xy[0])
                        petal.set_posfid_val(posid,'OFFSET_Y',xy[1])
                        self.printfunc(posid + ': Set OFFSET_X to ' + self.fmt(xy[0]))
                        self.printfunc(posid + ': Set OFFSET_Y to ' + self.fmt(xy[1]))
                        petal.altered_calib_states.add(petal.posmodels[posid].state)
        self.commit() # log note is already handled above
        self.commit_calib()
        if self.fvc.fvcproxy and wide_spotmatch:
            self.fvc.fvcproxy.set(match_radius = old_spotmatch_radius)
            self.printfunc('Spotmatch radius restored to ' + str(old_spotmatch_radius) + '.')
        if 'offsets' in mode:
            for petal in self.petals:
                petal.collider.update_positioner_offsets_and_arm_lengths()
            

    def rehome(self,posids='all'):
        """Find hardstops and reset current known positions.
        INPUTS:     posids ... 'all' or a list of specific posids
        """
        posids_by_petal = self.posids_by_petal(posids)
        self.printfunc('rehoming', str({'petal ' + str(ptl.petal_id):posids_by_petal[ptl] for ptl in posids_by_petal}))
        for petal,these_posids in posids_by_petal.items():
            petal.request_homing(these_posids)
            petal.schedule_send_and_execute_moves() # in future, do this in a different thread for each petal

    def measure_range(self,posids='all',axis='theta'):
        """Expert usage. Sweep several points about axis ('theta' or 'phi') on
        positioners identified by posids, striking the hard limits on either end.
        Calculate the total available travel range. Note that for axis='phi', the
        positioners must enter the collisionable zone, so the range seeking may
        occur in several successive stages.
        """
        if axis == 'phi':
            axisid = pc.P
            parameter_name = 'PHYSICAL_RANGE_P'
            batches = posids # implement later some selection of smaller batches of positioners guaranteed not to collide
        else:
            axisid = pc.T
            parameter_name = 'PHYSICAL_RANGE_T'
            batches = posids
        data = {}
        batches = {batches} if isinstance(batches,str) else set(batches)
        for batch in batches:
            batch_data = self._measure_range_arc(batch,axis)
            data.update(batch_data)

        # unwrapping code here
        for posid in data.keys():
            delta = data[posid]['target_dtdp'][axisid]
            obsXY = data[posid]['measured_obsXY']
            center = data[posid]['xy_center']
            xy_ctrd = np.array(obsXY) - np.array(center)
            angles_measured = np.arctan2(xy_ctrd[:,1], xy_ctrd[:,0]) * 180/np.pi
            total_angle = 0
            direction = pc.sign(delta)
            for i in range(len(angles_measured) - 1):
                step_measured = angles_measured[i+1] - angles_measured[i]
                if pc.sign(step_measured) != direction:
                    step_measured += direction * 360
                total_angle += step_measured
            total_angle = abs(total_angle)
            if data[posid]['petal'].posmodels[posid].is_enabled:
                data[posid]['petal'].set_posfid_val(posid,parameter_name,total_angle)
                data[posid]['petal'].altered_calib_states.add(data[posid]['petal'].posmodels[posid].state)
        self.commit(log_note='range measurement complete')
        self.commit_calib()
        self.rehome(posids)
        self.one_point_calibration(posids, mode='posTP')

    def calibrate(self,posids='all',mode='arc',save_file_dir='./',save_file_timestamp='sometime',keep_phi_within_Eo=True):
        """Do a series of test points to measure and calculate positioner center
        locations, R1 and R2 arm lengths, theta and phi offsets, and then set all these
        calibration values for each positioner.

        INPUTS:  posids   ... list of posids or 'all'
        
                 mode     ... 'rough' -- very rough calibration using two measured points only, always should be followed by an arc or grid calibration
                              'arc'   -- best-fit circle to arcs of points on the theta and phi axes
                              'grid'  -- error minimizer on grid of points to find best fit calibration parameters
        
                 keep_phi_within_Eo ... boolean, states whether to never let phi outside the free rotation envelope

        Typically one does NOT call keep_phi_within_Eo = False unless the theta offsets are already
        reasonably well known. That can be achieved by first doing a 'rough' calibration.
        
        OUTPUTS:  files  ... set of plot file paths generated by the function
                             (this is an empty set if the parameter make_plots_during_calib == False)
        """
        if mode not in {'rough','grid','arc'}:
            return
        files = set()
        if mode == 'arc' or mode == 'grid':
            if self.make_plots_during_calib:
                def save_file(posid):
                    return save_file_dir + posid + '_' + save_file_timestamp + '_calib_' + mode + '.png'
            remove_outliers = True if (self.fvc.fvcproxy or self.fvc.fvc_type == 'simulator') else False
        if mode == 'rough':
            self.rehome(posids)
            self.one_point_calibration(posids, mode='offsetsXY', wide_spotmatch=True)
            posids_by_petal = self.posids_by_petal(posids)
            for petal,these_posids in posids_by_petal.items():
                keys_to_reset = ['LENGTH_R1','LENGTH_R2','OFFSET_T','OFFSET_P','GEAR_CALIB_T','GEAR_CALIB_P']
                for key in keys_to_reset:
                    for posid in these_posids:
                        if petal.posmodels[posid].is_enabled:
                            petal.set_posfid_val(posid, key, pc.nominals[key]['value'])
            self.one_point_calibration(posids, mode='offsetsTP_close', wide_spotmatch=True)
            self.one_point_calibration(posids, mode='offsetsTP', wide_spotmatch=False)
        elif mode == 'grid':
            if self.grid_calib_num_DOF >= self.grid_calib_num_constraints: # the '=' in >= comparison is due to some places in the code where I am requiring at least one extra point more than exact constraint 
                new_mode = 'arc'    
                self.printfunc('Not enough points requested to constrain grid calibration. Defaulting to ' + new_mode + ' calibration method.')
                return self.calibrate(posids,new_mode,save_file_dir,save_file_timestamp,keep_phi_within_Eo)
            grid_data = self._measure_calibration_grid(posids, keep_phi_within_Eo, remove_outliers)
            grid_data = self._calculate_and_set_arms_and_offsets_from_grid_data(grid_data, set_gear_ratios=self.should_set_gear_ratios)
            if self.make_plots_during_calib:
                for posid in grid_data.keys():
                    file = save_file(posid)
                    poscalibplot.plot_grid(file,posid, grid_data)
                    files.add(file)
        elif mode == 'arc':
            T = self._measure_calibration_arc(posids,'theta', keep_phi_within_Eo, remove_outliers)
            P = self._measure_calibration_arc(posids,'phi', keep_phi_within_Eo, remove_outliers)
            self.printfunc("Finished measuring calibration arcs.")
            unwrapped_data = self._calculate_and_set_arms_and_offsets_from_arc_data(T,P,set_gear_ratios=self.should_set_gear_ratios)
            if self.make_plots_during_calib:
                for posid in T.keys():
                    file = save_file(posid)
                    poscalibplot.plot_arc(file, posid, unwrapped_data)
                    files.add(file)
        self.one_point_calibration(posids, mode='posTP', wide_spotmatch=False) # important to lastly update the internally-tracked theta and phi shaft angles
        self.commit(log_note = str(mode) + ' calibration complete')
        for petal in self.petals:
            petal.commit_calib_DB()
            if mode == 'arc' or mode == 'grid':
                petal.collider.update_positioner_offsets_and_arm_lengths()
        return files

    def identify_fiducials(self):
        """Turn fidicuals on and off to determine which centroid dots are fiducials.
        """
        self.printfunc('Turning fiducials on and off to identify reference dots.')
        requests = {}
        for posid in self.all_posids:
            requests[posid] = {'command':'posTP', 'target':[0,180], 'log_note':'identify fiducials starting point'}
        self.move(requests) # go to starting point
        self._identify(None)
        self.commit()
        self.commit_calib()

    def identify_many_enabled_positioners(self,posids):
        """ Identify a list of positioners one-by-one. All positioners are nudged first, then move back to homing positions one-by-one. 
            The identification of the first positioner takes two images, while all consecutive positioner only need one image. 
            If a positioner is enabled, it will be added to the enabled_posids list, and if no dots are moving after nudging a positioner, 
            it is added to disabled_posids list. 
            Input: posids, a list of positioners. like ['M00322','M01511']. 
            Output: the obsXY of each enabled positioner will be stored in the conf file.  
        """
        
        self.set_fiducials(setting='off')
        n_posids = len(posids)
        n_dots = len(self.all_posids)# + self.n_ref_dots
        nudges = [-self.nudge_dist, self.nudge_dist]
        xy_init = []
        pseudo_xy_ref = []
        self.rehome(posids='all')

        for i in range(n_posids):
            posid=posids[i]
            print('Identifying location of positioner '+posid+' ('+str(i+1)+' of '+str(n_posids)+')')
            this_petal = self.petal(posid)
            if i ==0:
                request={}
                log_note='Nudge all positioners first' 
                for j in range(n_posids):
                    request[posids[j]] = {'target':[0,nudges[0]], 'log_note':log_note} 
                this_petal.request_direct_dtdp(request)
                this_petal.schedule_send_and_execute_moves()
                xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_dots)            
                xy_init=xy_meas
            dtdp = [0,nudges[1]]
            log_note = 'nudge back to identify positioner location '
            request = {posid:{'target':dtdp, 'log_note':log_note}}
            enabled=this_petal.get_posfid_val(posid,'CTRL_ENABLED')
            if enabled:
                this_petal.request_direct_dtdp(request)
                this_petal.schedule_send_and_execute_moves()
            xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_dots)
            if len(xy_init) != len(xy_meas) or len(xy_init) != n_dots:
                print('Expect '+str(n_dots))
                print('Found '+str(len(xy_init))+' dots initially, but '+str(len(xy_meas))+ ' dots now.')
            if self.fvc.fvc_type == 'simulator':
                xy_meas = self._simulate_measured_pixel_locations(pseudo_xy_ref)
                pseudo_xy_ref = xy_meas[n_posids:]
            xy_test = xy_meas
            xy_ref = []

            for this_xy in xy_test:
                test_delta = np.array(this_xy) - np.array(xy_init)
                test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
                if any(test_dist < self.ref_dist_tol) or all(test_dist > self.ref_dist_thres):
                    xy_ref.append(this_xy)
            xy_pos = [xy for xy in xy_test if xy not in xy_ref]  # Moving dots xy^M



            if len(xy_pos) > 1:
                self.printfunc('warning: more than one moving dots (' + str(len(xy_pos)) + ') detected when trying to identify positioner ' + posid)
                print(xy_pos)
            elif len(xy_pos) < 1:
                self.printfunc('warning: no moving dots detected when trying to identify positioner ' + posid)
                self.disabled_posids.append(posid)
            else:
                self.enabled_posids.append(posid)
                expected_obsXY = this_petal.expected_current_position(posid,'obsXY')
                measured_obsXY = self.fvc.fvcXY_to_obsXY(xy_pos)[0]
                err_x = measured_obsXY[0] - expected_obsXY[0]
                err_y = measured_obsXY[1] - expected_obsXY[1]
                prev_offset_x = this_petal.get_posfid_val(posid,'OFFSET_X')
                prev_offset_y = this_petal.get_posfid_val(posid,'OFFSET_Y')
                this_petal.set_posfid_val(posid,'OFFSET_X', prev_offset_x + err_x) # this works, assuming we have already have reasonable knowledge of theta and phi (having re-homed or rough-calibrated)^M
                this_petal.set_posfid_val(posid,'OFFSET_Y', prev_offset_y + err_y) # this works, assuming we have already have reasonable knowledge of theta and phi (having re-homed or rough-calibrated)^M
                this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_obsXY[0])
                this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_obsXY[1])
                this_petal.altered_calib_states.add(this_petal.posmodels[posid].state)
            xy_init=xy_meas
        self.commit()
        self.commit_calib()
        self.rehome(posids='all')


    def identify_enabled_positioners(self):
        """Nudge positioners (one at a time) forward/back to determine which positioners are where on the FVC.
        """
        self.printfunc('Nudging positioners to identify their starting locations.')
        requests = {}
        all_posids = self.all_posids # no need to retreive dynamic property multiple times below
        for posid in all_posids:
            requests[posid] = {'command':'posTP', 'target':[0,180], 'log_note':'identify positioners starting point'}
        self.move(requests) # go to starting point
        total = len(all_posids)
        n = 0
        for posid in all_posids:
            n += 1
            self.printfunc('Identifying location of positioner ' + posid + ' (' + str(n) + ' of ' + str(total) + ')')
            self._identify(posid)
        self.commit()
        self.commit_calib()

    def identify_disabled_positioners(self):
        """Using a single image with everything lit up, associate all the remaining unknown dots to appropriate disabled positioners. For each dot:
             1. Decide which nominal hole xy position is closest.
             2. Save nominal xy to be that positioner’s X_OFFSET, Y_OFFSET.
             3. Using that positioner’s postranform instance, do fvcXY_to_obsXY(measured dot pixels), then obsXY_to_posTP(measured dot xy mm).
             4. Save posTP to that positioner’s POS_T, POS_P.
             If two disabled positioner dots are both within a single overlap of patrol regions, then cause an error and tell user to manually identify which one is which.
        """
        self.printfunc('Assigning dots not moving to disabled positioners.')
        requests = {}
        for posid in self.all_posids:
            requests[posid] = {'command':'posTP', 'target':[0,180], 'log_note':'identify fiducials starting point'}
        self.move(requests) # go to starting point
        n_posids = len(self.all_posids)
        self.set_fiducials(setting='off') 
        xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_posids)
        self.set_fiducials(setting='on')
        if self.fvc.fvc_type == 'simulator':
            xy_meas = self._simulate_measured_pixel_locations([])
            pseudo_xy_ref = xy_meas[n_posids:]
            xy_meas = xy_meas[0:n_posids] 
        ###########################################
        # Match dots to enabled positioners list
        ###########################################
        fvcX_enabled_arr,fvcY_enabled_arr=[],[]
        x_meas=[xy_meas[i][0] for i in range(len(xy_meas))]
        y_meas=[xy_meas[i][1] for i in range(len(xy_meas))]
        obsX_arr=[]
        obsY_arr=[]
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        pp = PdfPages('identification_check.pdf')
        plt.figure(1,figsize=(8,15))
        plt.subplot(211)
        plt.plot(x_meas,y_meas,'ko')


        for posid in self.enabled_posids:
            ptl=self.petal(posid)
            obsXY_this=ptl.expected_current_position(posid,'obsXY') 
            obsX_arr.append(obsXY_this[0])
            obsY_arr.append(obsXY_this[1])
            this_xy=self.fvc.obsXY_to_fvcXY(obsXY_this)[0]
            plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5)
            fvcX_enabled_arr.append(this_xy[0])
            fvcY_enabled_arr.append(this_xy[1])
            test_delta = np.array(this_xy) - np.array(xy_meas)
            test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
            matches = [dist < 20 for dist in test_dist] # 20 pixels matching radius. Hard coded for now. 
            if not any(matches):
                self.printfunc(posid+' was identified earlier but now disappear.')
                self.printfunc('obsXY:',obsXY_this,'\n','fvcXY:',this_xy)
                self.printfunc('Minimum dist:',np.min(test_dist))
            else:
                self.printfunc(posid,' matched with ','obsXY:',obsXY_this,' fvcXY:',this_xy)
                index=np.where(test_dist == min(test_dist))[0][0]
                xy_meas.remove(xy_meas[index])
        
        plt.plot(fvcX_enabled_arr,fvcY_enabled_arr,'b+')
        plt.xlabel('fvcX')
        plt.ylabel('fvcY')

        ############################################
        ##  Load metrology data and DEVICE_LOC #####
        ############################################

        if not self.enabled_posids:
            self.printfunc('No positioners are enabled, I can not move on. Exit. ')
            raise SystemExit
        if ptl.shape == 'petal':
            self.file_metro=pc.positioner_locations_file
        elif ptl.shape == 'small_array':
            self.file_metro=pc.small_array_locations_file
        else:
            self.file_metro=None # might be a bug


        # read the Metrology data first, then match positioners to DEVICE_LOC 
        positioners = Table.read(self.file_metro,format='ascii.csv',header_start=0,data_start=1)
        device_loc_file_arr,metro_X_file_arr,metro_Y_file_arr=[],[],[]
        for row in positioners:
            device_loc_file_arr.append(row['device_loc'])
            metro_X_file_arr.append(row['X'])
            metro_Y_file_arr.append(row['Y'])

         
         ############################################################
         # Enabled positioners should be matched to their dots now
         # Match disabled positioners
         ############################################################

        if ptl.shape == 'petal' or ptl.shape == 'small_array':
            for posid in self.disabled_posids:
                this_petal=self.petal(posid)
                device_loc_this=this_petal.get_posfid_val(posid,'DEVICE_LOC') # Use populate_pos_conf.py under pos_utility to populate pos setting files before usage. 
                index2=device_loc_file_arr.index(device_loc_this)
                metroX_this=metro_X_file_arr[index2]
                metroY_this=metro_Y_file_arr[index2]
                obsXY_this=[metroX_this,metroY_this]
                obsX_arr.append(obsXY_this[0])
                obsY_arr.append(obsXY_this[1])
                this_xy=self.fvc.obsXY_to_fvcXY(obsXY_this)[0]
                plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5,color='red')
                #self.printfunc(posid,' is located at:\n obsXY:',obsXY_this,'fvcXY:',this_xy)
                test_delta = np.array(this_xy) - np.array(xy_meas)
                test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
                #print('minimum distance:',np.min(test_dist))
                mm2pix=1./self.fvc.scale  
                matches = [dist < 6*mm2pix for dist in test_dist]
                min_dist=min(test_dist)
                index=np.where(test_dist <6*mm2pix)
                if not any(matches):
                    self.printfunc(posid+' has no dot in its patrol area. It probably has a broken fiber.')
                else:
                    if len(index) == 1:
                        index=np.where(test_dist == min(test_dist))[0][0]
                        measured_obsXY = self.fvc.fvcXY_to_obsXY(xy_meas[index])[0]
                        self.printfunc(posid+' matched with obsXY:',measured_obsXY,' fvcXY:',xy_meas[index])
                        posTP=this_petal.posmodels[posid].trans.obsXY_to_posTP(measured_obsXY)[0]
                        this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_obsXY[0])
                        this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_obsXY[1])
                        this_petal.set_posfid_val(posid,'POS_T',posTP[0])
                        this_petal.set_posfid_val(posid,'POS_P',posTP[1])
                        this_petal.set_posfid_val(posid,'CTRL_ENABLED',False)
                        self.posid_not_identified.remove(posid)
                    else:
                        self.printfunc(posid+' has '+str(len(index))+' dots in its patrol area, select the nearest one')
                        index=np.where(test_dist == min(test_dist))[0][0]
                        self.printfunc(posid+' matched with ',xy_meas[index])
                        measured_obsXY = self.fvc.fvcXY_to_obsXY(xy_meas[index])[0]
                        posTP=this_petal.posmodels[posid].trans.obsXY_to_posTP(measured_obsXY)[0]
                        this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_obsXY[0])
                        this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_obsXY[1])
                        this_petal.set_posfid_val(posid,'POS_T',posTP[0])
                        this_petal.set_posfid_val(posid,'POS_P',posTP[1])
                        this_petal.set_posfid_val(posid,'CTRL_ENABLED',False)
                        self.posid_not_identified.remove(posid)

        else:  # No metrology data, just match arbitraryly
            for posid in self.disabled_posids:
                this_petal=self.petal(posid)
                if xy_meas:
                    xy_fvc = xy_meas.pop()  # fvcXY
                    self.printfunc(posid+' is matched to ',xy_fvc)
                    xy_this = self.fvc.fvcXY_to_obsXY(xy_fvc)[0]  # obsXY
                    this_petal.set_posfid_val(posid,'OFFSET_X',xy_this[0]+0.01) # add a little error to make it reachable
                    this_petal.set_posfid_val(posid,'OFFSET_Y',xy_this[1])
                    posTP=this_petal.posmodels[posid].trans.obsXY_to_posTP(xy_this)[0]
                    this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',xy_this[0])
                    this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',xy_this[1])
                    this_petal.set_posfid_val(posid,'POS_T',posTP[0])
                    this_petal.set_posfid_val(posid,'POS_P',posTP[1])
                    this_petal.set_posfid_val(posid,'CTRL_ENABLED',False)
                    self.posid_not_identified.remove(posid)
                else:
                    self.printfunc(posid+'has no more dots to match')
        plt.legend(loc=2)

        plt.subplot(212)
        plt.plot(obsX_arr,obsY_arr,'ko')
        plt.legend(loc=2)
        pp.savefig()

        plt.close()
        pp.close()
        self.commit()
     

    def identify_positioners_2images(self):
        """ Turn off fiducials, and use two images to identify moving and non-moving dots. Assign all dots to positioners according to metrology data. 
            Must be a petal or small_array with correct metrology data to work. 
            
        """ 
        posids=list(self.all_posids)
        n_posids = len(self.all_posids)
        self.set_fiducials(setting='off')
        xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_posids)

        nudges = [-self.nudge_dist, self.nudge_dist]
        xy_init = []
        pseudo_xy_ref = []
        self.rehome(posids='all')

        request={}
        log_note='Nudge all positioners first'
        this_petal = self.petal(posids[0]) 
        for j in range(n_posids):
            request[posids[j]] = {'target':[0,nudges[0]], 'log_note':log_note}
        this_petal.request_direct_dtdp(request)
        this_petal.schedule_send_and_execute_moves()
        xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_posids)
        xy_init=xy_meas

        request={}
        log_note='Nudge all positioners back to home position'
        for j in range(n_posids):
            request[posids[j]] = {'target':[0,nudges[1]], 'log_note':log_note}
        this_petal.request_direct_dtdp(request)
        this_petal.schedule_send_and_execute_moves()
        xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_posids)

        move_arr=[]
        for this_xy in xy_meas:
            test_delta = np.array(this_xy) - np.array(xy_init)
            test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
            min_dist=min(test_dist) 
            if min_dist<self.ref_dist_tol:
                move_arr.append(False)
            else:
                move_arr.append(True)

        if this_petal.shape == 'petal':
            self.file_metro=pc.positioner_locations_file
        elif this_petal.shape == 'small_array':
            self.file_metro=pc.small_array_locations_file
        else:
            self.printfunc('Must be a petal or a small_array to proceed. Exit')
            raise SystemExit
        

        # read the Metrology data first, then match positioners to DEVICE_LOC 
        positioners = Table.read(self.file_metro,format='ascii.csv',header_start=0,data_start=1)
        device_loc_file_arr,metro_X_file_arr,metro_Y_file_arr=[],[],[]
        for row in positioners:
            device_loc_file_arr.append(row['device_loc'])
            metro_X_file_arr.append(row['X'])
            metro_Y_file_arr.append(row['Y'])

        x_meas=[xy_meas[i][0] for i in range(len(xy_meas))]
        y_meas=[xy_meas[i][1] for i in range(len(xy_meas))]
        obsX_arr,obsY_arr=[],[]
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        pp = PdfPages('identification_check_2image.pdf')
        plt.figure(1,figsize=(8,15))
        plt.subplot(211)
        plt.plot(x_meas,y_meas,'ko')
        plt.xlabel('fvcX')
        plt.ylabel('fvcY')


        print('Found '+str(len(x_meas))+' spots, match with '+str(n_posids)+' positioners')
        for i in range(n_posids):
            posid=posids[i]
            self.printfunc('Identifying location of positioner '+posid+' ('+str(i+1)+' of '+str(n_posids)+')')
            this_petal=self.petal(posid)
            device_loc_this=this_petal.get_posfid_val(posid,'DEVICE_LOC') # Use populate_pos_conf.py under pos_utility to populate pos setting files before usage. 
            index2=device_loc_file_arr.index(device_loc_this)
            metroX_this=metro_X_file_arr[index2]
            metroY_this=metro_Y_file_arr[index2]
            obsXY_this=[metroX_this,metroY_this]
            obsX_arr.append(obsXY_this[0])
            obsY_arr.append(obsXY_this[1])
            this_xy=self.fvc.obsXY_to_fvcXY(obsXY_this)[0]
            test_delta = np.array(this_xy) - np.array(xy_meas)
            test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
            if self.fvc.fvc_type == 'FLI':
                mm2pix=1./(13.308*0.006) 
            else:
                1./self.fvc.scale
            matches = [dist < 6*mm2pix for dist in test_dist]
            min_dist=min(test_dist)
            index=np.where(test_dist <6*mm2pix)
            if not any(matches):
                self.printfunc(posid+' has no dot in its patrol area. It probably has a broken fiber.')
                plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5,color='green')
            else:
                if len(index) == 1:
                    index=np.where(test_dist == min(test_dist))[0][0]
                    measured_obsXY = self.fvc.fvcXY_to_obsXY(xy_meas[index])[0]
                    #self.printfunc(posid+' matched with obsXY:',measured_obsXY,' fvcXY:',xy_meas[index])
                    posTP=this_petal.posmodels[posid].trans.obsXY_to_posTP(measured_obsXY)[0]
                    this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_obsXY[0])
                    this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_obsXY[1])
                    this_petal.set_posfid_val(posid,'OFFSET_X',metroX_this) #measured_obsXY[0])
                    this_petal.set_posfid_val(posid,'OFFSET_Y',metroY_this) #measured_obsXY[1])
                    posTP=this_petal.posmodels[posid].trans.obsXY_to_posTP(measured_obsXY)[0]
                    this_petal.set_posfid_val(posid,'POS_T',posTP[0])
                    this_petal.set_posfid_val(posid,'POS_P',posTP[1])
                    if move_arr[index]:
                        this_petal.set_posfid_val(posid,'CTRL_ENABLED',True)
                        plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5,color='blue')
                    else:
                        this_petal.set_posfid_val(posid,'CTRL_ENABLED',False)
                        plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5,color='red')
                else:
                    self.printfunc(posid+' has '+str(len(index))+' dots in its patrol area, select the nearest one')
                    index=np.where(test_dist == min(test_dist))[0][0]
                    #self.printfunc(posid+' matched with ',xy_meas[index])
                    measured_obsXY = self.fvc.fvcXY_to_obsXY(xy_meas[index])[0]
                    this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_obsXY[0])
                    this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_obsXY[1])
                    this_petal.set_posfid_val(posid,'OFFSET_X',metroX_this) #measured_obsXY[0])
                    this_petal.set_posfid_val(posid,'OFFSET_Y',metroY_this) #measured_obsXY[1])
                    posTP=this_petal.posmodels[posid].trans.obsXY_to_posTP(measured_obsXY)[0]
                    this_petal.set_posfid_val(posid,'POS_T',posTP[0])
                    this_petal.set_posfid_val(posid,'POS_P',posTP[1])
                    this_petal.altered_calib_states.add(this_petal.posmodels[posid].state)
                    if move_arr[index]:
                        this_petal.set_posfid_val(posid,'CTRL_ENABLED',True)
                        plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5,color='blue')
                    else:
                        this_petal.set_posfid_val(posid,'CTRL_ENABLED',False)
                        plt.text(this_xy[0],this_xy[1],posid,fontsize=2.5,color='red')
        self.commit()
        self.commit_calib()
        plt.legend(loc=2)

        plt.subplot(212)
        plt.plot(obsX_arr,obsY_arr,'ko')
        for i in range(len(posids)):
            posid=posids[i] 
            plt.text(obsX_arr[i],obsY_arr[i],posid,fontsize=2.5,color='blue')
        plt.legend(loc=2)
        plt.xlabel('obsX')
        plt.ylabel('obsY')

        pp.savefig()

        plt.close()
        pp.close()
        self.set_fiducials(setting='on')

    def posids_by_petal(self, posids='all'):
        """Returns a dict that organizes the argued posids by the petals they are
        associated with. Keys = petal objects, values = sets of posids on each petal.
        Arguing 'all' returns all petals, and all posids on those petals.
        """
        if posids == 'all':
            return {petal:petal.posids for petal in self.petals}
        posids = {posids} if isinstance(posids,str) else set(posids)
        ptl_map = {posid:self._petals_map[posid] for posid in posids}
        posids_by_petal = {petal:{p for p in ptl_map if ptl_map[p] == petal} for petal in set(ptl_map.values())}
        return posids_by_petal
    
    @property
    def all_posids(self):
        """Returns a set of all the posids on all the petals.
        """
        all_posids = set()
        for ptl in self.petals:
            all_posids = all_posids.union(ptl.posids)
        return all_posids
    
    @property
    def all_fidids(self):
        """Returns a set of all the fidids on all the petals.
        """
        all_fidids = set()
        for ptl in self.petals:
            all_fidids = all_fidids.union(ptl.fidids)
        return all_fidids

    def petal(self, posid_or_fidid_or_dotid):
        """Returns the petal object associated with a single id key.
        """
        return self._petals_map[posid_or_fidid_or_dotid]
    
    def posmodel(self, posid):
        """Returns the posmodel object associated with a single posid.
        """
        return self.petal(posid).posmodels[posid]

    def state(self, posid):
        """Returns the posstate object associated with a single posid.
        """
        return self.posmodel(posid).state
    
    def trans(self, posid):
        """Returns the postransforms object associated with a single posid.
        """
        return self.posmodel(posid).trans
    
    def commit(self,log_note=''):
        """Commit state data controlled by all petals to storage.
        See commit function in petal.py for explanation of optional additional log note.
        """
        for ptl in self.petals:
            ptl.commit(log_note=log_note)

    def commit_calib(self,log_note=''):
        """Commit state data controlled by all petals to storage.
        See commit function in petal.py for explanation of optional additional log note.
        """
        for ptl in self.petals:
            ptl.commit_calib_DB()
    
    def set_fiducials(self, setting='on'):
        """Apply uniform settings to all fiducials on all petals simultaneously.
        See set_fiducials() comments in petal for further details on argument and
        return formats. The typical usage is:
            set_fiducials('on')
            set_fiducials('off')
        """
        all_settings_done = {}
        for petal in self.petals:
            settings_done = petal.set_fiducials(setting=setting)
            all_settings_done.update(settings_done)
        return all_settings_done
            
    @property
    def ref_dots_XY(self):
        """Ordered dict of ordered dicts of nominal locations of all fixed reference dots in the FOV.
        Primary keys are the dot id strings. Sub-keys are:
            'fvcXY' --> [x,y] values in the FVC coordinate system (pixels)
            'obsXY' --> [x,y] values in the observer coordinate system (millimeters)
        """
        data = collections.OrderedDict()
        for ptl in self.petals:
            more_data = self.fiducial_dots_fvcXY(ptl)
            for dotid in more_data.keys():
                more_data[dotid]['obsXY'] = self.fvc.fvcXY_to_obsXY([more_data[dotid]['fvcXY']])[0]
            data.update(more_data)
        if not self.fvc.fvcproxy:
            for i in range(len(self.extradots_fvcXY)):            
                dotid = self.dotid_str(self.extradots_id,i) # any petal instance is fine here (static method)
                data[dotid] = collections.OrderedDict()
                data[dotid]['obsXY'] = self.fvc.fvcXY_to_obsXY([self.extradots_fvcXY[i]])[0]
        return data

    def set_motor_parameters(self):
        '''Tells each petal to send all the latest motor settings out to positioners.
        '''
        for petal in self.petals:
            petal.set_motor_parameters()

    def _measure_calibration_grid(self, posids='all', keep_phi_within_Eo=True, remove_outliers=False):
        """Expert usage. Send positioner(s) to a series of commanded (theta,phi) positions. Measure
        the (x,y) positions of these points with the FVC.

        INPUTS:   posids              ... list of posids or 'all'
                  keep_phi_within_Eo  ... True, to guarantee no anticollision needed
                                          False, to cover the full range of phi with the grid

        OUTPUTS:  data ... see comments below

        Returns a dictionary of dictionaries containing the data. The primary
        keys for the dict are the posid. Then for each posid, each subdictionary
        contains the keys:
            'target_posTP'    ... the posTP targets which were attempted
            'measured_obsXY'  ... the resulting measured xy positions
            'petal'           ... the petal this posid is on
            'trans'           ... the postransform object associated with this particular positioner
        """
        posids_by_petal = self.posids_by_petal(posids)
        data = {}
        dummy_obsT = 0.0
        for petal,these_posids in posids_by_petal.items():
            for posid in these_posids:
                data[posid] = {}
                posmodel = self.posmodel(posid)
                range_posT = posmodel.targetable_range_T
                range_posP = posmodel.targetable_range_P
                if keep_phi_within_Eo:
                    min_obsP = self.phi_clear_angle
                    min_posP = posmodel.trans.obsTP_to_posTP([dummy_obsT,min_obsP])[1]
                    range_posP[0] = min_posP
                t_cmd = np.linspace(min(range_posT),max(range_posT),self.n_points_calib_T + 1) # the +1 is temporary, remove that extra point in next line
                t_cmd = t_cmd[:-1] # since theta covers +/-180, it is kind of redundant to hit essentially the same points again
                p_cmd = np.linspace(min(range_posP),max(range_posP),self.n_points_calib_P + 1) # the +1 is temporary, remove that extra point in next line
                p_cmd = p_cmd[:-1] # since there is very little useful data right near the center
                data[posid]['target_posTP'] = [[t,p] for t in t_cmd for p in p_cmd]
                data[posid]['trans'] = posmodel.trans
                data[posid]['petal'] = petal
                data[posid]['measured_obsXY'] = []
                n_pts = len(data[posid]['target_posTP'])
        
        # make the measurements
        for i in range(n_pts):
            requests = {}
            for posid in data:
                requests[posid] = {'command':'posTP', 'target':data[posid]['target_posTP'][i], 'log_note':'calib grid point ' + str(i+1)}
            self.printfunc('calibration grid point ' + str(i+1) + ' of ' + str(n_pts))
            this_meas_data,imgfiles,accepted_requests = self.move_measure(requests, tp_updates=None)
            for p in this_meas_data.keys():
                data[p]['measured_obsXY'] = pc.concat_lists_of_lists(data[p]['measured_obsXY'],this_meas_data[p])

        # optionally remove outliers
        if remove_outliers:
            data = self._remove_outlier_calibration_points(data, 'grid')
            
        return data 

    def _measure_calibration_arc(self, posids='all', axis='theta', keep_phi_within_Eo=True, remove_outliers=False):
        """Expert usage. Sweep an arc of points about axis ('theta' or 'phi')
        on positioners identified by posids. Measure these points with the FVC
        and do a best fit of them.

        INPUTS:   posids  ... list of posids or 'all'
                  axis    ... 'theta' or 'phi'

        keep_phi_within_Eo == True  --> phi never exceeds Eo envelope
        keep_phi_within_Eo == False --> phi can cover the full range (including collidable territory) during calibration
        remove_outliers == True --> any definitely bad points (e.g. unmatched centroids) are removed from the set of calibration points

        OUTPUTS:  data ... see comments below

        Returns a dictionary of dictionaries containing the data. The primary
        keys for the dict are the posid. Then for each posid, each subdictionary
        contains the keys:
            'target_posTP'    ... the posTP targets which were attempted
            'measured_obsXY'  ... the resulting measured xy positions
            'xy_center'       ... the best fit arc's xy center
            'radius'          ... the best fit arc's radius
            'petal'           ... the petal this posid is on
            'trans'           ... the postransform object associated with this particular positioner
        """
        posids_by_petal = self.posids_by_petal(posids)
        dummy_obsT = 0.0
        dummy_obsP = 0.0
        data = {}
        for petal,these_posids in posids_by_petal.items():
            these_posmodels = {posid:self.posmodel(posid) for posid in these_posids}
            start_posTP = {}
            final_posTP = {}
            if axis == 'theta':
                n_pts = self.n_points_calib_T
                for posid,posmodel in these_posmodels.items():
                    targetable_range_T = posmodel.targetable_range_T
                    posP = posmodel.trans.obsTP_to_posTP([dummy_obsT,self.phi_clear_angle])[1]
                    start_posTP[posid] = [min(targetable_range_T) + self.calib_arc_margin, posP]
                    final_posTP[posid] = [max(targetable_range_T) - self.calib_arc_margin, posP]
            else:
                n_pts = self.n_points_calib_P
                for posid,posmodel in these_posmodels.items():
                    posT = posmodel.trans.obsTP_to_posTP([0.0,dummy_obsP])[0] # When doing phi axis, nice to have obsT all uniform (simplifies anti-collision). this line working correctly depends on already knowing theta offset reasonably well
                    if keep_phi_within_Eo:
                        min_posP = posmodel.trans.obsTP_to_posTP([dummy_obsT,self.phi_clear_angle])[1]
                    else:
                        min_posP = min(posmodel.targetable_range_P)
                    start_posTP[posid] = [posT, min_posP + self.calib_arc_margin]
                    final_posTP[posid] = [posT, max(posmodel.targetable_range_P) - self.calib_arc_margin]
            for posid,posmodel in these_posmodels.items():
                posT = np.linspace(start_posTP[posid][0], final_posTP[posid][0], n_pts)
                posP = np.linspace(start_posTP[posid][1], final_posTP[posid][1], n_pts)
                data[posid] = {'target_posTP':[[posT[j],posP[j]] for j in range(n_pts)], 'measured_obsXY':[], 'petal':petal, 'trans':posmodel.trans}

        # make the measurements
        for i in range(n_pts):
            requests = {}
            for posid in data:
                this_petal = self.petal(posid)
                enabled=this_petal.get_posfid_val(posid,'CTRL_ENABLED')
                posT_this=this_petal.get_posfid_val(posid,'POS_T')
                posP_this=this_petal.get_posfid_val(posid,'POS_P')
                if enabled:
                    requests[posid] = {'command':'posTP', 'target':data[posid]['target_posTP'][i], 'log_note':'calib arc on ' + axis + ' point ' + str(i+1)}
                else:
                    requests[posid] = {'command':'posTP', 'target':[posT_this,posP_this], 'log_note':'calib arc on ' + axis + ' point ' + str(i+1)}
            self.printfunc('calibration arc on ' + axis + ' axis: point ' + str(i+1) + ' of ' + str(n_pts))
            this_meas_data,imgfiles,accepted_requests = self.move_measure(requests, tp_updates=None)
            for p in this_meas_data.keys():
                data[p]['measured_obsXY'] = pc.concat_lists_of_lists(data[p]['measured_obsXY'],this_meas_data[p])
        
        # optionally remove outliers
        if remove_outliers:
            data = self._remove_outlier_calibration_points(data, 'arc')
        
        # circle fits
        for posid in data:
            (xy_ctr,radius) = fitcircle.FitCircle().fit(data[posid]['measured_obsXY'])
            data[posid]['xy_center'] = xy_ctr
            data[posid]['radius'] = radius
        return data

    def _measure_range_arc(self,posids='all',axis='theta'):
        """Expert usage. Measure physical range of an axis by sweep a brief arc of points
        on positioners identified bye unwrapped  posids. Measure these points with the FVC
        and do a best fit of them.

        INPUTS:   posids  ... list of posids or 'all'
                  axis    ... 'theta' or 'phi'

        Returns a dictionary of dictionaries containing the data. The primary
        keys for the dict are the posid. Then for each posid, each subdictionary
        contains the keys:
            'initial_posTP'   ... starting theta,phi position
            'target_dtdp'     ... delta moves which were attempted
            'measured_obsXY'  ... resulting measured xy positions
            'xy_center'       ... best fit arc's xy center
            'radius'          ... best fit arc's raTruedius
            'petal'           ... petal this posid is on
            'trans'           ... postransform object associated with this particular positioner
        """
        posids_by_petal = self.posids_by_petal(posids)
        dummy_obsT = 0.0
        dummy_obsP = 0.0
        n_intermediate_pts = 2
        initial_tp_requests = {}
        initial_posP = {}
        prefix = 'range measurement on ' + axis + ' axis'
        for petal,these_posids in posids_by_petal.items():
            for posid in these_posids:
                initial_posP[posid] = self.trans(posid).obsTP_to_posTP([dummy_obsT,self.phi_clear_angle])[1]
            if axis == 'theta':
                delta = 360/(n_intermediate_pts + 1)
                dtdp = [delta,0]
                axisid = pc.T
                for posid in these_posids:
                    initial_posTP = [-150, initial_posP[posid]]
                    initial_tp_requests[posid] = {'command':'posTP', 'target':initial_posTP, 'log_note':'range arc ' + axis + ' initial point'}
            else:
                delta = -180/(n_intermediate_pts + 1)
                dtdp = [0,delta]
                axisid = pc.P
                for posid in these_posids:
                    if self.use_current_theta_during_phi_range_meas:
                        initial_posT = self.posmodel(posid).expected_current_posTP[0]
                    else:
                        initial_posT = self.trans(posid).obsTP_to_posTP([0.0,dummy_obsP])[0]
                    initial_posTP = [initial_posT,initial_posP[posid]]
                    initial_tp_requests[posid] = {'command':'posTP', 'target':initial_posTP,  'log_note':'range arc ' + axis + ' initial point'}
            data = {posid:{'target_dtdp':dtdp, 'measured_obsXY':[], 'petal':petal} for posid in these_posids}

        # go to initial point
        self.printfunc(prefix + ': initial point')
        self.move(initial_tp_requests)

        # seek first limit
        self.printfunc(prefix + ': seeking first limit')
        for petal,these_posids in posids_by_petal.items():
            petal.request_limit_seek(these_posids, axisid, -pc.sign(delta), log_note='seeking first ' + axis + ' limit')
            petal.schedule_send_and_execute_moves() # in future, do this in a different thread for each petal
        meas_data,imgfiles = self.measure()
        for p in meas_data.keys():
            data[p]['measured_obsXY'] = pc.concat_lists_of_lists(data[p]['measured_obsXY'],meas_data[p])

        # intermediate points
        for i in range(n_intermediate_pts):
            self.printfunc(prefix + ': intermediate point ' + str(i+1) + ' of ' + str(n_intermediate_pts))
            # Note that anticollision is NOT done here. The reason is that phi location is not perfectly
            # well-known at this point (having just struck a hard limit). So externally need to have made
            # sure there was a clear path for the phi arm ahead of time.
            for petal,these_posids in posids_by_petal.items():
                requests = {}
                for posid in these_posids:
                    requests[posid] = {'target':dtdp, 'log_note':'intermediate ' + axis + ' point ' + str(i)}
                petal.request_direct_dtdp(requests)
                petal.schedule_send_and_execute_moves() # in future, do this in a different thread for each petal
            meas_data,imgfiles = self.measure()
            for p in meas_data.keys():
                data[p]['measured_obsXY'] = pc.concat_lists_of_lists(data[p]['measured_obsXY'],meas_data[p])

        # seek second limit
        self.printfunc(prefix + ': seeking second limit')
        for petal,these_posids in posids_by_petal.items():
            petal.request_limit_seek(these_posids, axisid, pc.sign(delta), log_note='seeking second ' + axis + ' limit')
            petal.schedule_send_and_execute_moves()
        meas_data,imgfiles = self.measure()
        for p in meas_data.keys():
            data[p]['measured_obsXY'] = pc.concat_lists_of_lists(data[p]['measured_obsXY'],meas_data[p])

        # circle fits
        for posid in data:
            (xy_ctr,radius) = fitcircle.FitCircle().fit(data[posid]['measured_obsXY'])
            data[posid]['xy_center'] = xy_ctr

        # get phi axis well back in clear envelope, as a best practice housekeeping thing to do
        if axis == 'phi' and pc.sign(delta) == -1:
            for petal,these_posids in posids_by_petal.items():
                petal.request_limit_seek(these_posids, axisid, -pc.sign(delta), log_note='housekeeping extra ' + axis + ' limit seek')
                petal.schedule_send_and_execute_moves()

        return data

    def _calculate_and_set_arms_and_offsets_from_grid_data(self, data, set_gear_ratios=False):
        """Helper function for grid method of calibration. See the _measure_calibration_grid method for
        more information on format of the dictionary 'data'. This method adds the fields 'ERR_NORM' and
        'final_expected_obsXY' to the data dictionary for each positioner.
        """
        param_keys = self.grid_calib_param_keys
        for posid in data.keys():
            trans = data[posid]['trans']   
            trans.alt_override = True
            for key in param_keys:
                data[posid][key] = []
            data[posid]['ERR_NORM'] = []
            data[posid]['point_numbers'] = []
            initial_params_dict = postransforms.PosTransforms().alt
            params0 = [initial_params_dict[key] for key in param_keys]
            point0 = self.grid_calib_num_DOF - 1
            for pt in range(point0,len(data[posid]['measured_obsXY'])):
                meas_xy = np.array([data[posid]['measured_obsXY'][j] for j in range(pt+1)]).transpose()
                targ_tp = [data[posid]['target_posTP'][j] for j in range(pt+1)]
                def expected_xy(params):
                    for j in range(len(param_keys)):
                        trans.alt[param_keys[j]] = params[j]
                    obsxy = [trans.posTP_to_obsXY([targ_tp[i][0],targ_tp[i][1]]) for i in range(len(targ_tp))]
                    return np.transpose(obsxy)
                def err_norm(params):
                    expected = np.array(expected_xy(params))
                    all_err = expected - meas_xy
                    return np.linalg.norm(all_err,ord='fro')/np.sqrt(np.size(all_err,axis=1))
                bounds = ((2.5,3.5),(2.5,3.5),(-180,180),(-50,50),(None,None),(None,None)) #Ranges which values should be in
                params_optimized = scipy.optimize.minimize(fun=err_norm, x0=params0, bounds=bounds)
                params0 = params_optimized.x
                if pt > point0: # don't bother logging first point, which is always junk and just getting the (x,y) offset in the ballpark
                    data[posid]['ERR_NORM'].append(err_norm(params_optimized.x))
                    data[posid]['point_numbers'].append(pt+1)
                    debug_str = 'Grid calib on ' + str(posid) + ' point ' + str(data[posid]['point_numbers'][-1]) + ':'
                    debug_str += ' ERR_NORM=' + format(data[posid]['ERR_NORM'][-1],'.3f')
                    for j in range(len(param_keys)):
                        if param_keys[j] == 'OFFSET_T' or param_keys[j] == 'OFFSET_P':
                            params_optimized.x[j] = self._centralize_angular_offset(params_optimized.x[j])
                        data[posid][param_keys[j]].append(params_optimized.x[j])
                        debug_str += '  ' + param_keys[j] +': ' + format(data[posid][param_keys[j]][-1],'.3f')
                    # print(debug_str)
            trans.alt_override = False
            petal = data[posid]['petal']
            for key in param_keys:
                if petal.posmodels[posid].is_enabled:
                    petal.set_posfid_val(posid, key, data[posid][key][-1])
            petal.altered_calib_states.add(petal.posmodels[posid].state)
            self.printfunc('Grid calib on ' + str(posid) + ': ' + key + ' set to ' + format(data[posid][key][-1],'.3f'))
            data[posid]['final_expected_obsXY'] = np.array(expected_xy(params_optimized.x)).transpose().tolist()
        return data

    def _calculate_and_set_arms_and_offsets_from_arc_data(self, T, P, set_gear_ratios=False):
        """Helper function for arc method of calibration. T and P are data dictionaries taken on the
        theta and phi axes. See the _measure_calibration_arc method for more information.
        """
        data = {}
        for posid in T.keys():
            # gather targets data
            t_targ_posT = [posTP[pc.T] for posTP in T[posid]['target_posTP']]
            t_targ_posP = [posTP[pc.P] for posTP in T[posid]['target_posTP']]
            p_targ_posP = [posTP[pc.P] for posTP in P[posid]['target_posTP']]
            p_targ_posT = [posTP[pc.T] for posTP in P[posid]['target_posTP']]        
            t_meas_obsXY = T[posid]['measured_obsXY']
            p_meas_obsXY = P[posid]['measured_obsXY']
            
            # arms and offsets
            ptl = T[posid]['petal']
            t_ctr = np.array(T[posid]['xy_center'])
            p_ctr = np.array(P[posid]['xy_center'])
            length_r1 = np.sqrt(np.sum((t_ctr - p_ctr)**2))
            length_r2 = P[posid]['radius']
            
			# BEGIN - probably should remove this -- JHS
			# It is not in a good place to bury these automatic actions
            if self._outside_of_tolerance_from_nominals(posid, length_r1, length_r2):
                self.rehome(posid)
                self.petal(posid).set_posfid_val(posid, 'CTRL_ENABLED', False)
                self.petal(posid).pos_flags[posid] |= self.petal(posid).ctrl_disabled_bit
                self.petal(posid).pos_flags[posid] |= self.petal(posid).bad_fiber_fvc_bit
                self.printfunc(str(posid) + ': disabled due to poor arc calibration.')
			# END - probably should remove this
			# (and may also want to remove the if statement right below)
				
            if ptl.posmodels[posid].is_enabled:
                ptl.set_posfid_val(posid,'LENGTH_R1',length_r1)
                ptl.set_posfid_val(posid,'LENGTH_R2',length_r2)
                ptl.set_posfid_val(posid,'OFFSET_X',t_ctr[0])
                ptl.set_posfid_val(posid,'OFFSET_Y',t_ctr[1])
            p_meas_obsT = np.arctan2(p_ctr[1]-t_ctr[1], p_ctr[0]-t_ctr[0]) * 180/np.pi
            offset_t = p_meas_obsT - p_targ_posT[0] # just using the first target theta angle in the phi sweep
            offset_t = self._centralize_angular_offset(offset_t)
            if ptl.posmodels[posid].is_enabled:
                ptl.set_posfid_val(posid,'OFFSET_T',offset_t)
            xy = np.array(p_meas_obsXY)
            angles = np.arctan2(xy[:,1]-p_ctr[1], xy[:,0]-p_ctr[0]) * 180/np.pi
            p_meas_obsP = angles - p_meas_obsT
            p_meas_obsP[p_meas_obsP < 0] += 360
            expected_direction = pc.sign(p_targ_posP[1] - p_targ_posP[0])
            p_meas_obsP_wrapped = self._wrap_consecutive_angles(p_meas_obsP.tolist(), expected_direction)
            offset_p = np.median(np.array(p_meas_obsP_wrapped) - np.array(p_targ_posP))
            offset_p = self._centralize_angular_offset(offset_p)
            if ptl.posmodels[posid].is_enabled:
                ptl.set_posfid_val(posid,'OFFSET_P',offset_p)
            p_meas_posP_wrapped = (np.array(p_meas_obsP_wrapped) - offset_p).tolist()
            
            # unwrap thetas
            t_meas_posTP = [T[posid]['trans'].obsXY_to_posTP(this_xy,range_limits='full')[0] for this_xy in t_meas_obsXY]
            t_meas_posT = [this_tp[pc.T] for this_tp in t_meas_posTP]
            expected_direction = pc.sign(t_targ_posT[1] - t_targ_posT[0])
            t_meas_posT_wrapped = self._wrap_consecutive_angles(t_meas_posT, expected_direction)
            
            # gather data to return in an organized fashion (used especially for plotting)
            data[posid] = {}
            data[posid]['xy_ctr_T'] = t_ctr
            data[posid]['xy_ctr_P'] = p_ctr
            data[posid]['radius_T'] = T[posid]['radius']
            data[posid]['radius_P'] = P[posid]['radius']
            data[posid]['measured_obsXY_T'] = t_meas_obsXY
            data[posid]['measured_obsXY_P'] = p_meas_obsXY
            data[posid]['targ_posT_during_T_sweep'] = t_targ_posT
            data[posid]['targ_posP_during_P_sweep'] = p_targ_posP
            data[posid]['meas_posT_during_T_sweep'] = t_meas_posT_wrapped
            data[posid]['meas_posP_during_P_sweep'] = p_meas_posP_wrapped
            data[posid]['targ_posP_during_T_sweep'] = t_targ_posP[0]
            data[posid]['targ_posT_during_P_sweep'] = p_targ_posT[0]
            data[posid]['posmodel'] = self.posmodel(posid)
            
            # gear ratios
            ratios_T = np.divide(np.diff(t_meas_posT_wrapped),np.diff(t_targ_posT))
            ratios_P = np.divide(np.diff(p_meas_posP_wrapped),np.diff(p_targ_posP))
            ratio_T = np.median(ratios_T)
            ratio_P = np.median(ratios_P)
            data[posid]['gear_ratio_T'] = ratio_T
            data[posid]['gear_ratio_P'] = ratio_P            
            if set_gear_ratios and ptl.posmodels[posid].is_enabled:
                ptl.set_posfid_val(posid,'GEAR_CALIB_T',ratio_T)
                ptl.set_posfid_val(posid,'GEAR_CALIB_P',ratio_P)
            else:
                self.printfunc(posid + ': measurement proposed GEAR_CALIB_T = ' + format(ratio_T,'.6f'))
                self.printfunc(posid + ': measurement proposed GEAR_CALIB_P = ' + format(ratio_P,'.6f'))
            ptl.altered_calib_states.add(ptl.posmodels[posid].state)
        return data

    def _remove_outlier_calibration_points(self, data, mode):
        """Removes bad points from calibration data set.
            data ... dict from _measure_calibration_grid() or _measure_calibration_arc() function
            mode ... "arc" or "grid"
        """
        for posid in data:
            matched_index=[]
            n_pts = len(data[posid]['measured_obsXY'])
            for i in range(n_pts):
                if data[posid]['measured_obsXY'][i] != [0,0]: # unmatched spot case
                    matched_index.append(i)
                else:
                    self.printfunc(str(posid) + ': Removed ' + str(mode) + ' calibration point ' + str(i) + ' of ' + str(n_pts) + ', due to no matched spot.')
            if len(matched_index)>2: # if the remaining dots >=3 fine for good fit
                data[posid]['measured_obsXY']=np.array(data[posid]['measured_obsXY'])[matched_index].tolist()
                data[posid]['target_posTP']=np.array(data[posid]['target_posTP'])[matched_index].tolist()
            else:
                self.printfunc(str(posid)+' does not have enough good measurement for '+mode+' fit')

        #for i in unmatched_index:	
        #    del data[posid]['measured_obsXY'][i]
        #    del data[posid]['target_posTP'][i]
        #    self.printfunc(str(posid) + ': Removed ' + str(mode) + ' calibration point ' + str(i) + ' of ' + str(n_pts) + ', due to no matched spot.')
            # elif ... any other cases to check?
        return data

    def _identify(self, posid=None):
        """Generic function for identifying either all fiducials or a single positioner's location.
        """
        n_posids = len(self.all_posids)
        n_dots = n_posids + self.n_ref_dots
        nudges = [-self.nudge_dist, self.nudge_dist]
        xy_init = []
        pseudo_xy_ref = []
        
        if posid == None:
            identify_fiducials = True
            xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_dots)
            if self.fvc.fvc_type == 'simulator':
                xy_meas = self._simulate_measured_pixel_locations(pseudo_xy_ref)
                pseudo_xy_ref = xy_meas[n_posids:]
            xy_init = xy_meas
            xy_test = xy_meas
        else:
            for i in range(len(nudges)):
                dtdp = [0,nudges[i]]
                identify_fiducials = False
                log_note = 'nudge to identify positioner location '
                request = {posid:{'target':dtdp, 'log_note':log_note}}
                this_petal = self.petal(posid)
                enabled=this_petal.get_posfid_val(posid,'CTRL_ENABLED')
                if enabled:
                    this_petal.request_direct_dtdp(request)
                    this_petal.schedule_send_and_execute_moves()
                xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_dots)
                if self.fvc.fvc_type == 'simulator':
                    xy_meas = self._simulate_measured_pixel_locations(pseudo_xy_ref)
                    pseudo_xy_ref = xy_meas[n_posids:]
                if i == 0:
                    xy_init = xy_meas
                else:
                    xy_test = xy_meas
        xy_ref = []
        for this_xy in xy_test:
            test_delta = np.array(this_xy) - np.array(xy_init)
            test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
            if any(test_dist < self.ref_dist_tol) or all(test_dist > self.ref_dist_thres):
                xy_ref.append(this_xy)
        xy_pos = [xy for xy in xy_test if xy not in xy_ref]  # Moving dots xy
        if identify_fiducials:
            #if len(xy_ref) != self.n_ref_dots:
            #    self.printfunc('warning: number of ref dots detected (' + str(len(xy_ref)) + ') is not equal to expected number of fiducial dots (' + str(self.n_ref_dots) + ')')
            all_xyref_detected = []
            for fidid in self.all_fidids:
                ptl = self.petal(fidid)
                num_expected = ptl.get_posfid_val(fidid,'N_DOTS')
                if num_expected > 0:
                    self.printfunc('Temporarily turning off fiducial ' + fidid + ' to determine which dots belonged to it.')
                    ptl.set_fiducials(fidid,'off')
                    xy_meas,peaks,fwhms,imgfiles = self.fvc.measure_fvc_pixels(n_dots - num_expected)
                    if self.fvc.fvc_type == 'simulator':
                        xy_meas = self._simulate_measured_pixel_locations(pseudo_xy_ref)
                        for j in range(num_expected):
                            for k in range(n_posids,len(xy_meas)):
                                if xy_meas[k] not in all_xyref_detected:
                                    del xy_meas[k] # this is faking turning off that dot
                                    break
                    these_xyref = []
                    for this_xy in xy_ref:
                        test_delta = np.array(this_xy) - np.array(xy_meas)
                        test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
                        matches = [dist < self.ref_dist_tol for dist in test_dist]
                        if not any(matches):
                            these_xyref.append(this_xy)
                            self.printfunc('Ref dot ' + str(len(these_xyref)-1) + ' identified for fiducial ' + fidid + ' at fvc coordinates ' + str(this_xy))
                    num_detected = len(these_xyref)
                    if num_detected != num_expected:
                        self.printfunc('warning: expected ' + str(num_expected) + ' dots for fiducial ' + fidid + ', but detected ' + str(num_detected))
                    ptl.set_posfid_val(fidid,'DOTS_FVC_X',[these_xyref[i][0] for i in range(num_detected)])
                    ptl.set_posfid_val(fidid,'DOTS_FVC_Y',[these_xyref[i][1] for i in range(num_detected)])
                    ptl.set_posfid_val(fidid,'LAST_MEAS_OBS_X',[these_xyref[i][0] for i in range(num_detected)])
                    ptl.set_posfid_val(fidid,'LAST_MEAS_OBS_Y',[these_xyref[i][1] for i in range(num_detected)])
                    all_xyref_detected += these_xyref
                    ptl.set_fiducials(fidid,'on')
            #self.extradots_fvcXY = [xy for xy in xy_ref if xy not in all_xyref_detected] # The extra dots are not identified here
            #if self.extradots_fvcXY:
            #    self.printfunc(str(len(self.extradots_fvcXY)) + ' extra reference dots detected at FVC pixel coordinates: ' + str(self.extradots_fvcXY))
        else:  # Identify positioner
            if len(xy_pos) > 1:
                self.printfunc('warning: more than one moving dots (' + str(len(xy_pos)) + ') detected when trying to identify positioner ' + posid)
                print(xy_pos)
            elif len(xy_pos) < 1:
                self.printfunc('warning: no moving dots detected when trying to identify positioner ' + posid)
                self.disabled_posids.append(posid)
            else:
                self.enabled_posids.append(posid)
                expected_obsXY = this_petal.expected_current_position(posid,'obsXY')
                measured_obsXY = self.fvc.fvcXY_to_obsXY(xy_pos)[0]
                err_x = measured_obsXY[0] - expected_obsXY[0]
                err_y = measured_obsXY[1] - expected_obsXY[1]
                prev_offset_x = this_petal.get_posfid_val(posid,'OFFSET_X')
                prev_offset_y = this_petal.get_posfid_val(posid,'OFFSET_Y')
                this_petal.set_posfid_val(posid,'OFFSET_X', prev_offset_x + err_x) # this works, assuming we have already have reasonable knowledge of theta and phi (having re-homed or rough-calibrated)
                this_petal.set_posfid_val(posid,'OFFSET_Y', prev_offset_y + err_y) # this works, assuming we have already have reasonable knowledge of theta and phi (having re-homed or rough-calibrated)
                this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_X',measured_obsXY[0])
                this_petal.set_posfid_val(posid,'LAST_MEAS_OBS_Y',measured_obsXY[1])
                this_petal.altered_calib_states.add(this_petal.posmodels[posid].state)

    def _simulate_measured_pixel_locations(self,xy_ref=[]):
        """Generates simulated locations in fvcXY space.
        Positioner locations are generated by simply looking up current expected positions.
        The optional argument xy_ref allows you to specify a list of [x,y] locations of
        reference points to repeat.
        """
        xy_meas = []
        posids_by_petal = self.posids_by_petal('all')
        for petal,these_posids in posids_by_petal.items():
            positioners_current = [petal.expected_current_position(posid,'obsXY') for posid in these_posids]
            positioners_current = self.fvc.obsXY_to_fvcXY(positioners_current)
            if len(positioners_current) > 1:
                i = 0
                while i < len(positioners_current):
                    this_xy = positioners_current[i]
                    other_xys = positioners_current.copy()
                    other_xys.remove(this_xy)
                    test_delta = np.array(this_xy) - np.array(other_xys)
                    test_dist = np.sqrt(np.sum(test_delta**2,axis=1))
                    matches = [dist < self.ref_dist_tol for dist in test_dist]
                    if any(matches):
                        this_xy[0] += self.ref_dist_tol*10*(i+1)
                        this_xy[1] += self.ref_dist_tol*10*(i+1)
                        positioners_current[i] = this_xy
                    i += 1
            xy_meas = pc.concat_lists_of_lists(xy_meas,positioners_current)
        if not xy_ref:
            for i in range(self.n_ref_dots):
                faraway = 2*np.max(np.abs(xy_meas))
                new_xy = np.random.uniform(low=faraway,high=2*faraway,size=2).tolist()
                xy_meas.append(new_xy)
        else:
            xy_meas.extend(xy_ref)
        return xy_meas

    def _test_and_update_TP(self,measured_data,tp_updates='posTP'):
        """Check if errors between measured positions and expected positions exceeds a tolerance
        value, and if so, then adjust parameters in the direction of the measured error.
        
        By default, this function will only changed the internally-tracked shaft position, POS_T
        and POS_P. The assumption is that we have fairly stable theta and phi offset values, based
        on the mechanical reality of the robot. However there is an option (perhaps useful in limited cases,
        such as when a calibration angle unwrap appears to have gone awry on a new test stand setup) where
        one would indeed want to change the calibration parameters, OFFSET_T and OFFSET_P. Activate
        this by arguing tp_updates='offsetsTP'.
        
        The overall idea here is to be able to deal gracefully with cases where the shaft has slipped
        just a little, and we have slightly lost count of shaft positions, or where the initial
        calibration was just a little off.
        
        The input value 'measured_data' is the same format as produced by the 'measure()' function.
        
        Any updating of parameters that occurs will be written to the move log. Check the notes field for
        a note like 'updated POS_T and POS_P after positioning error of 0.214 mm', to figure out when
        this has occurred.
        
        The return is a dictionary with:
            keys   ... posids 
            values ... 1x2 [delta_theta,delta_phi]
        """
        delta_TP = {}
        for posid in measured_data.keys():
            delta_TP[posid] = [0,0]
            if measured_data[posid] == [0,0] and self.fvc.fvcproxy:
                #Do not update TP for positioner that did not get matched to a centroid
                continue
            ptl = self.petal(posid)
            measured_obsXY = measured_data[posid]
            expected_obsXY = ptl.expected_current_position(posid,'obsXY')
            err_xy = ((measured_obsXY[0]-expected_obsXY[0])**2 + (measured_obsXY[1]-expected_obsXY[1])**2)**0.5
            if err_xy > self.tp_updates_tol:
                posmodel = self.posmodel(posid)
                if posmodel.is_enabled:
                    expected_posTP = ptl.expected_current_position(posid,'posTP')
                    measured_posTP = posmodel.trans.obsXY_to_posTP(measured_data[posid],range_limits='full')[0]
                    T_options = measured_posTP[0] + np.array([0,360,-360])
                    T_diff = np.abs(T_options - expected_posTP[0])
                    T_best = T_options[np.argmin(T_diff)]
                    measured_posTP[0] = T_best
                    delta_T = (measured_posTP[0] - expected_posTP[0]) * self.tp_updates_fraction
                    delta_P = (measured_posTP[1] - expected_posTP[1]) * self.tp_updates_fraction
                    if tp_updates == 'offsetsTP' or tp_updates == 'offsetsTP_close':
                        param = 'OFFSET'
                    else:
                        param = 'POS'
                    old_T = ptl.get_posfid_val(posid,param + '_T')
                    old_P = ptl.get_posfid_val(posid,param + '_P')              
                    new_T = old_T + delta_T
                    new_P = old_P + delta_P
                    if tp_updates == 'offsetsTP' or tp_updates == 'offsetsTP_close' :
                        ptl.set_posfid_val(posid,'OFFSET_T',new_T)
                        ptl.set_posfid_val(posid,'OFFSET_P',new_P)
                        self.printfunc(posid + ': Set OFFSET_T to ' + self.fmt(new_T))
                        self.printfunc(posid + ': Set OFFSET_P to ' + self.fmt(new_P)) 
                        ptl.collider.update_positioner_offsets_and_arm_lengths()
                    else:
                        posmodel.axis[pc.T].pos = new_T
                        posmodel.axis[pc.P].pos = new_P
                        self.printfunc(posid + ': xy err = ' + self.fmt(err_xy) + ', changed ' + param + '_T from ' + self.fmt(old_T) + ' to ' + self.fmt(new_T))
                        self.printfunc(posid + ': xy err = ' + self.fmt(err_xy) + ', changed ' + param + '_P from ' + self.fmt(old_P) + ' to ' + self.fmt(new_P))
                    delta_TP[posid] = [delta_T,delta_P]
                    posmodel.state.next_log_notes.append('updated ' + param + '_T and ' + param + '_P after positioning error of ' + self.fmt(err_xy) + ' mm')
                    if param == 'OFFSET':
                        ptl.altered_calib_states.add(ptl.posmodels[posid].state)
        return delta_TP
    
    def _outside_of_tolerance_from_nominals(self, posid, r1, r2):
        """Check to see if R1 or R2 are outside of a certain tolerance
        from nominal values.  Return True if either of these values are out of bounds, else False.
        Add offset x,y check to this.
        """         
        tol = pc.nominals['LENGTH_R1']['tol']
        nom_val = pc.nominals['LENGTH_R1']['value']
        if not(nom_val - tol <= r1 <= nom_val + tol):
            return True
        tol = pc.nominals['LENGTH_R2']['tol']
        nom_val = pc.nominals['LENGTH_R2']['value']
        if not(nom_val - tol <= r2 <= nom_val + tol):
            return True

    def fiducial_dots_fvcXY(self, ptl):
        """Returns an ordered dict of ordered dicts of all [x,y] positions of all
        fiducial dots this petal contributes in the field of view.
        
        Primary keys are the fiducial dot ids, formatted like:
            'F001.0', 'F001.1', etc...
        
        Returned values are accessed with the sub-key 'fvcXY'. So that:
            data['F001.1']['fvcXY'] --> [x,y] floats giving location of dot #1 in fiducial #F001
            
        The coordinates are all given in fiber view camera pixel space.
        
        In some laboratory setups, we have a "extra" fixed reference fibers. These
        are not provided here (instead they are handled in posmovemeasure.py).
        """
        data = collections.OrderedDict()
        for fidid in self.fidids:
            dotids = self.fid_dotids(fidid)
            for i in range(len(dotids)):
                data[dotids[i]] = collections.OrderedDict()
                x = ptl.get_posfid_val(fidid,'DOTS_FVC_X')[i]
                y = ptl.get_posfid_val(fidid,'DOTS_FVC_Y')[i]
                data[dotids[i]]['fvcXY'] = [x,y]
        return data

    def fid_dotids(self, fidid, ptl):
        """Returns a list (in a standard order) of the dot id strings
        for a particular fiducial.
        """
        return [self.dotid_str(fidid, i) for i in
                range(int(ptl.get_posfid_val(fidid, 'N_DOTS')))]

    @property
    def phi_clear_angle(self):
        """Returns the phi angle in degrees for which two positioners cannot collide
        if they both have phi at this angle or greater.
        """
        phi_Eo_angle = self.petals[0].collider.Eo_phi
        phi_clear = phi_Eo_angle + self.phi_Eo_margin
        return phi_clear
        
    @property
    def grid_calib_num_DOF(self):
        return len(self.grid_calib_param_keys) # need at least this many points to exactly constrain the TP --> XY transformation function
    
    @property
    def grid_calib_num_constraints(self):
        return self.n_points_calib_T * self.n_points_calib_P

    @property
    def n_ref_dots(self):
        """Number of reference dots to expect in the field of view.
        """
        n_dots = 0
        for petal in self.petals:
            n_dots_ptl = petal.n_fiducial_dots
            n_dots += n_dots_ptl
        n_dots += self.n_extradots_expected
        return n_dots
    
    @property
    def n_moving_dots(self):
        """Returns the total number of mobile dots (on functioning positioners) to expect in an fvc image.
        """
        self.printfunc('n_moving_dots() method not yet implemented')
        pass
    
    @property
    def n_fixed_dots(self):
        """Returns the total number of immobile light dots (fiducials or non-functioning positioners) to expect in an fvc image.
        """
        self.printfunc('n_fixed_dots() method not yet implemented')
        pass

    @staticmethod
    def dotid_str(fidid,dotnumber):
        return fidid + '.' + str(dotnumber)

    @staticmethod
    def extract_fidid(dotid):
        return dotid.split('.')[0]
            
    def _wrap_consecutive_angles(self, angles, expected_direction):
        """Wrap angles in one expected direction. It is expected that the physical deltas
        we are trying to wrap all increase or all decrease sequentially. In other words, that
        the sequence of angles is only going one way around the circle.
        """
        wrapped = [angles[0]]
        for i in range(1,len(angles)):
            delta = angles[i] - wrapped[i-1]
            while pc.sign(delta) != expected_direction and pc.sign(delta) != 0:
                delta += expected_direction * 360
            wrapped.append(wrapped[-1] + delta)
        return wrapped
    
    def _centralize_angular_offset(self,offset_angle):
        """A special unwrapping check for OFFSET_T and OFFSET_P angles, for which we are always
        going to want to default to the option closer to 0 deg. Hence if our calibration routine
        calculates a best fit value for example of OFFSET_T or OFFSET_P = 351 deg, then the real
        setting we want to apply should clearly instead be -9.
        """
        try_plus = offset_angle % 360
        try_minus = offset_angle % -360
        if abs(try_plus) <= abs(try_minus):
            return try_plus
        else:
            return try_minus

    def fmt(self,number):
        """for consistently printing floats in terminal output
        """
        return format(number,'.3f')
