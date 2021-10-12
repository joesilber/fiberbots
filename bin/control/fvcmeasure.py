#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Standalone script for taking FVC measurements at the command line. 
(Alternately, import FVCHandler module directly into your own scripts
for programmatic control.)
'''
import os
import sys
import argparse
import time
import math 
this_file_dir = os.path.realpath(os.path.dirname(__file__))
os.chdir(this_file_dir)
sys.path.append('../../modules')
sys.path.append('../../modules/camera')
import globals as gl
import fvchandler

# Measurement default parameters
defaults = gl.fvc_defaults.copy()

# Command line args for standalone mode, and defaults
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--camera', type=str, default=defaults['camera'], help=f'fiber view camera to use, valid options are {fvchandler.cameras.keys()}') 
parser.add_argument('-n', '--num_dots', type=int, default=1, help=f'number of dots to centroid')
parser.add_argument('-r', '--num_repeats', type=int, default=1, help=f'number of times to repeat the measurement')
parser.add_argument('-p', '--plot', action='store_true', help='plot measured centroids')
parser.add_argument('-e', '--exptime', type=float, default=defaults['exptime'], help='camera exposure time in seconds')
parser.add_argument('-b', '--fitbox', type=int, default=defaults['fitbox'], help='window size for centroiding in pixels')
parser.add_argument('-d', '--take_darks', action='store_true', help='take dark images (shutter closed). typically not needed, since we keep the test stand in a dark enough enclosure')
parser.add_argument('-im', '--save_images', action='store_true', help='save image files to disk')
parser.add_argument('-bs', '--save_biases', action='store_true', help='save bias image files to disk')
parser.add_argument('-se', '--sim_errmax', type=float, default=defaults['sim_errmax'], help='measurement error max for simulator')
parser.add_argument('-sb', '--sim_badmatchfreq', type=float, default=defaults['sim_badmatchfreq'], help='how often the simulator returns [0,0], indicating a bad match')
inputs = parser.parse_args()

if __name__ == '__main__':
    start_stamp = gl.timestamp()
    import simple_logger
    if not os.path.isdir(gl.dirs['temp']):
        os.mkdir(gl.dirs['temp'])
    path_prefix = os.path.join(gl.dirs['temp'], f'fvchandler_{start_stamp}')
    log_path = f'{path_prefix}.log'
    logger, _, _ = simple_logger.start_logger(log_path)
    logger.info(f'Beginning fvchandler stand-alone measurement run')
    logger.info(f'Inputs: {inputs}')
    params = defaults.copy()
    for key in ['camera', 'exptime', 'fitbox', 'sim_errmax', 'sim_badmatchfreq']:
        params[key] = getattr(inputs, key)
    logger.info(f'Initializing fvchandler with parameters: {params}')
    f = fvchandler.FVCHandler(params=params,
                              take_darks=inputs.take_darks,
                              save_images=inputs.save_images,
                              save_biases=inputs.save_biases,
                              printfunc=logger.info,
                             ) 
    f.min_energy = -math.inf  # suppress checks on dot quality here, since standalone mode often for setup
    xy = []
    peaks = []
    start_time = time.time()
    for i in range(inputs.num_repeats):
        meas_name = f'measurement {i+1} of {inputs.num_repeats}'
        logger.info(f'Beginning {meas_name}')
        these_xy, these_peaks, these_fwhms, imgfiles = f.measure(inputs.num_dots)
        if imgfiles:
            logger.info('Images for {meas_name} stored at {imgfiles}')
        xy.append(these_xy)
        energies = [these_peaks[i]*these_fwhms[i] for i in range(len(these_peaks))]
        statline = lambda name, value: f'\n{name:<26}... ' + (f'{value:.4f}' if gl.is_float(value) else f'{value}')
        stats = f'Measurement {i + 1} of {inputs.num_repeats}...'
        stats += statline('number of dots', len(these_xy))
        stats += statline('xy positions', these_xy)
        stats += statline('peak brightnesses', these_peaks)
        stats += statline('dimmest', min(these_peaks))
        stats += statline('brightest', max(these_peaks))
        stats += statline('full-width half-maxes', these_fwhms)
        stats += statline('narrowest', min(these_fwhms))
        stats += statline('widest', max(these_fwhms))
        stats += statline('energies = peaks * fwhms', energies)
        stats += statline('lowest', min(energies))
        stats += statline('highest', max(energies))
        logger.info(stats)
    if inputs.plot:
        import matplotlib.pyplot as plt
        plt.ioff()
        fig = plt.figure(figsize=(8.0, 6.0), dpi=150) 
        cm = plt.cm.get_cmap('RdYlBu')
        colors = these_peaks
        x = [this[0] for this in xy]
        y = [this[1] for this in xy]
        sc = plt.scatter(x, y, c=colors, alpha=0.7, vmin=min(colors), vmax=max(colors), s=35, cmap=cm)
        plt.colorbar(sc)
        plt.legend(loc='upper left')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title(f'fvc measurements {start_stamp}')
        fig.tight_layout()
        plot_path = f'{path_prefix}.png'
        plt.savefig(plot_path)
        plt.close(fig)
        logger.info(f'Plot saved to {plot_path}')
    total_time = time.time() - start_time
    logger.info(f'Run completed in {total_time:.1f} sec ({total_time/inputs.num_repeats}) per image)')

