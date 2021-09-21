import matplotlib.pyplot as plt
import numpy as np

# Functions for plotting calibration arcs of the fiber positioner.

def plot_arc(path, posid, data):
    """See _calculate_and_set_arms_and_offsets() method in posmovemeasure.py for data format.
    """
    plt.ioff() # interactive plotting off
    fig = plt.figure(figsize=(14, 8))
    state = data[posid]['posmodel'].state

    for ax in ['T','P']:
        name = 'theta' if ax == 'T' else 'phi'
        other_ax = 'P' if ax == 'T' else 'T'
        other_name = 'phi' if ax == 'T' else 'theta'
        plot_num_base = 0 if ax == 'T' else 3
        target_angles = np.array(data[posid]['targ_pos' + ax + '_during_' + ax + '_sweep'])
        measured_angles = np.array(data[posid]['meas_pos' + ax + '_during_' + ax + '_sweep'])
        other_axis_angle = data[posid]['targ_pos' + other_ax + '_during_' + ax + '_sweep']
        radius = data[posid]['radius_' + ax]
        center = data[posid]['xy_ctr_' + ax]
        measured_xy = np.array(data[posid]['measured_obsXY_' + ax])

        plt.subplot(2,3,plot_num_base+1)
        arc_start = np.arctan2(measured_xy[0,1]-center[1],measured_xy[0,0]-center[0]) * 180/np.pi
        arc_finish = arc_start + np.sum(np.diff(measured_angles))
        if arc_start > arc_finish:
            arc_finish += 360
        ref_arc_angles = np.arange(arc_start,arc_finish,5)*np.pi/180
        if ref_arc_angles[-1] != arc_finish:
            ref_arc_angles = np.append(ref_arc_angles,arc_finish*np.pi/180)
        arc_x = radius * np.cos(ref_arc_angles) + center[0]
        arc_y = radius * np.sin(ref_arc_angles) + center[1]
        axis_zero_angle = arc_start - target_angles[0] # where global observer would nominally see the axis's local zero point in this plot
        axis_zero_line_x = [center[0], radius * np.cos(axis_zero_angle*np.pi/180) + center[0]]
        axis_zero_line_y = [center[1], radius * np.sin(axis_zero_angle*np.pi/180) + center[1]]
        plt.plot(arc_x,arc_y,'b-')
        plt.plot(measured_xy[:,0], measured_xy[:,1], 'ko')
        plt.plot(measured_xy[0,0], measured_xy[0,1], 'ro')
        plt.plot(center[0],center[1],'k+')
        plt.plot(axis_zero_line_x,axis_zero_line_y,'k--')
        zero_text_angle = np.mod(axis_zero_angle+360, 360)
        zero_text_angle = zero_text_angle-180 if zero_text_angle > 90 and zero_text_angle < 270 else zero_text_angle
        zero_text = name + '=0\n(' + other_name + '=' + format(other_axis_angle,'.1f') + ')'
        plt.text(np.mean(axis_zero_line_x),np.mean(axis_zero_line_y),zero_text,rotation=zero_text_angle,horizontalalignment='center',verticalalignment='top')
        for i in range(len(measured_xy)):
            this_angle = np.arctan2(measured_xy[i,1]-center[1],measured_xy[i,0]-center[0])
            text_x = center[0] + radius*1.1*np.cos(this_angle)
            text_y = center[1] + radius*1.1*np.sin(this_angle)
            plt.text(text_x,text_y,str(i),verticalalignment='center',horizontalalignment='center')
        if ax == 'T':
            calib_vals_txt = ''
            for key in ['LENGTH_R1','LENGTH_R2','OFFSET_T','OFFSET_P','GEAR_CALIB_T','GEAR_CALIB_P','OFFSET_X','OFFSET_Y']:
                calib_vals_txt += format(key,'12s') + ' = ' + format(state._val[key],'.3f') + '\n'
            plt.text(min(plt.xlim())+0.2,max(plt.ylim())-0.2,calib_vals_txt,fontsize=6,color='gray',family='monospace',horizontalalignment='left',verticalalignment='top')
        plt.xlabel('x (mm)')
        plt.ylabel('y (mm)')
        plt.title(posid + ' ' + name + ' calibration points')
        plt.grid(True)
        plt.margins(0.05, 0.05)
        plt.axis('equal')

        plt.subplot(2,3,plot_num_base+2)
        err_angles = measured_angles - target_angles
        plt.plot(target_angles, err_angles, 'ko-')
        plt.plot(target_angles[0], err_angles[0], 'ro')
        for i in range(len(target_angles)):
            plt.text(target_angles[i],err_angles[i],'\n\n'+str(i),verticalalignment='center',horizontalalignment='center')
        plt.xlabel('target ' + name + ' angle (deg)')
        plt.ylabel('measured ' + name + ' - target ' + name + ' (deg)')
        plt.title('measured angle variation')
        plt.grid(True)
        plt.margins(0.1, 0.1)

        plt.subplot(2,3,plot_num_base+3)
        measured_radii = np.sqrt(np.sum((measured_xy - center)**2,axis=1)) * 1000 # um
        best_fit_radius = radius * 1000 # um
        err_radii = measured_radii - best_fit_radius
        plt.plot(target_angles, err_radii, 'ko-')
        plt.plot(target_angles[0], err_radii[0], 'ro')
        for i in range(len(target_angles)):
            plt.text(target_angles[i],err_radii[i],'\n\n'+str(i),verticalalignment='center',horizontalalignment='center')
        plt.xlabel('target ' + name + ' angle (deg)')
        plt.ylabel('measured radius - best fit radius (um)')
        plt.title('measured radius variation')
        plt.grid(True)
        plt.margins(0.1, 0.1)

    plt.tight_layout(pad=2.0)
    plt.savefig(path,dpi=150)
    plt.close(fig)

def plot_grid(path, posid, data):
    """See ___ method in posmovemeasure.py for data format.
    """
    plt.ioff() # interactive plotting off
    fig = plt.figure(figsize=(14, 8))

    target_posTP = np.array(data[posid]['target_posTP'])
    measured_obsXY = np.array(data[posid]['measured_obsXY'])
    expected_obsXY = np.array(data[posid]['final_expected_obsXY'])
    point_nums = np.array(data[posid]['point_numbers'])
    params = {0: {'ERR_NORM':np.array(data[posid]['ERR_NORM'])*1000, 'unit':'um', 'title':'error of calibration'},
              1: {'LENGTH_R1':np.array(data[posid]['LENGTH_R1']), 'unit':'mm', 'title':'kinematic arm length'},
              2: {'LENGTH_R2':np.array(data[posid]['LENGTH_R2']), 'unit':'mm', 'title':'kinematic arm length'},
              3: {'OFFSET_T':np.array(data[posid]['OFFSET_T']), 'unit':'deg', 'title':'theta offset angle'},
    		    4: {'OFFSET_P':np.array(data[posid]['OFFSET_P']), 'unit':'deg', 'title':'phi offset angle'},
		    5: {'OFFSET_X':np.array(data[posid]['OFFSET_X']), 'unit':'mm', 'title':'global x offset'},
		    6: {'OFFSET_Y':np.array(data[posid]['OFFSET_Y']), 'unit':'mm', 'title':'global y offset'}}

    subplot_num = 1
    plt.subplot(2,4,subplot_num)
    plt.plot(measured_obsXY[:,0],measured_obsXY[:,1],'ro',label='(x,y)=meas by FVC',markersize=4,markeredgecolor='r',markerfacecolor='None')
    plt.plot(expected_obsXY[:,0],expected_obsXY[:,1],'k+',label='(x,y)=optim func(t,p)',markersize=6,markeredgewidth='1')
    for i in range(len(target_posTP[:,0])):
        text_x = measured_obsXY[i,0]
        text_y = measured_obsXY[i,1]
        plt.text(text_x,text_y,'\n\n\n(' + format(target_posTP[i,0],'.1f') + ',\n' + format(target_posTP[i,1],'.1f') + ')',
                               verticalalignment='center',horizontalalignment='center',fontsize=6,color='gray')
    plt.xlabel('x (mm)')
    plt.ylabel('y (mm)')
    plt.title(str(posid) + ' grid calibration points',fontsize=8)
    plt.margins(0.1, 0.1)
    txt_x = np.min(plt.xlim()) - np.diff(plt.xlim()) * 0.02
    txt_y = np.max(plt.ylim()) - np.diff(plt.ylim()) * 0.05
    plt.text(txt_x,txt_y,'Point labels are the\n(posT,posP) input\nangles (degrees).',horizontalalignment='left',verticalalignment='top',fontsize=6,color='gray')
    plt.axis('equal')
    plt.legend(loc='upper right',fontsize=6)

    param_keys = list(params.keys())
    param_keys.sort()
    for p in param_keys:
        subplot_num += 1
        plt.subplot(2,4,subplot_num)
        line_format = 'b-'
        param_label = ''
        for q in params[p].keys():
            if q != 'unit' and q != 'title':
                values = params[p][q]
                plt.plot(point_nums,values,line_format,label=q)
                line_format = 'r-'
                param_label = q
        plt.xlabel('number of points measured')
        plt.ylabel(params[p]['title'] + ' (' + params[p]['unit'] + ')')
        plt.legend(loc='upper right',fontsize=8)
        #plt.xticks(point_nums, [format(x,'.0f') for x in point_nums])
        if param_label == 'OFFSET_X' or param_label == 'OFFSET_Y':
            plt.yticks(plt.yticks()[0], [format(x,'.2f') for x in plt.yticks()[0]])
    plt.tight_layout(pad=2.0)
    plt.savefig(path,dpi=150)
    plt.close(fig)

#fakedata = {'somepos':{'target_posTP':[[0,0],[90,0],[180,0],[-90,0]],
#                       'measured_obsXY':[[6.1,0.2],[-0.1,5.9],[-5.7,0.2],[0.1,-6.2]],
#                       'final_expected_obsXY':[[6,0],[0,6],[-6,0],[0,-6]],
#                       'point_numbers':[7,8,9,10],
#                       'ERR_NORM':[.2,.1,.05,.01],
#                       'LENGTH_R1':[3.1,2.9,3.05,2.95],
#                       'LENGTH_R2':[3.2,2.7,2.8,3.05],
#                       'OFFSET_T':[0,10,-20,5],
#                       'OFFSET_P':[7,-3,-12,2],
#                       'OFFSET_X':[1,2,-1,0],
#                       'OFFSET_Y':[-1,0.5,2,0.3]}}
#plot_grid('out.png','somepos',fakedata)