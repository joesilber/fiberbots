# fiberbots
code for operating and testing fiber positioner robots

# repo contents

## `bin`
These are the high-level scripts that you run day-to-day.

### `bin/analysis`
Scripts for analyzing measured data. These should all be operable "offline", without any need for hardware, such that anyone with this GitHub repo can simply run the code.

### `bin/control`
Scripts for controlling the motors and camera to do physical tests.

As of 2021-09-21, the resulting data should be automatically saved in the "data" folder. See comments below.

## `data`
As of 2021-09-21, all test data should be archived to GitHub in this folder.

In general, store all data as simple .csv files. First row is column headers, then data in the subsequent rows. Use `astropy` module in general to produce these. All physical distances shall be in millimeters. All camera pixel distances are just pixels.

Document your formatting conventions clearly in `data/readme.md`.

Do *not* save .FITS image files. They are much too large and are not needed. Only save higher level data tables.

If and when we generate a significant amount of data, we may move it to a separate server or database. For now, please label all data files like:

`<timestamp> <some descriptive filename>.<extension>`

where the timestamp would be like:

`20210921T172324-0700` for automated timestamps (most cases)

or

`2021-09-21` for files you manually labeled (rarer)

Hint: Use function "timestamp()" in the globals module to guarantee consistency.

## `modules`
Common modules, including camera and motor drivers, as well as general purpose globals and loggers, etc.

### `modules/globals.py`
A few common constants and helper functions, such as directories for saving files, and a single standard function for timestamping. We generally limit our usage of global variables, but this is useful for more "constant" common items.

### `modules/simple_logger.py`
Common module for logging events in scripts etc.

### `modules/camera`
#### `modules/camera/fvchandler.py`
High-level interface to camera. Sends commands to the camera and interprets the resulting image by centroiding. 

As of 2021-09-21 at LBNL, we are only using an SBIG STF-8300M camera. However `fvchandler.py` is intended to be flexible for using a different camera. In such cases, you would add new commands for the new driver in this module. Meanwhile, the pixel interpretation etc would be taken care of generically.

#### `modules/camera/SBIG`
Low-level drivers for SBIG camera.

See file `readme` in this directory for instructions on SBIG driver installation and some environmental variables that need to be set.

As of 2021-09-21, low-level centroiding code is also in this folder (c.f. `sbig_grab_cen.py` etcetera). This is not ideal modularization. A more flexible architecture would be to make the centroiding more abstracted from the picture-taking. It's not essential right now, but would be useful in the future. In such a case, we would put the new, generic, centroiding module up one directory, next to `fvchandler.py`.

### `modules/motors`
Low-level control of the motors that drive the robots.

As of 2021-09-21, the code is for electronics received from EPFL in 2020.

When using the Lawicel CAN-USB dongle on Linux, we need the user to be in the group `dialout`. To do so:
~~~
sudo adduser <username> dialout
~~~
Then reboot. It is only necessary to do this setting one time for a given user.

## `manuals`
Store existing or external procedures, manuals, and other reference files etcetera here. However, new code documentation should be written in the `.md` format and version-controlled in GitHub (like this file). 
## `unused`
Stuff that isn't currently in use, for example old code that we may want to use parts of. Items here may be nonfunctional, and for information only.

# github tips
At LBNL test stand we may run as a common user `ldrd`. Therefore to commit code as yourself on github:
~~~
git -c user.name="<your github user name>" -c user.email=<your email address> commit -a -m "descriptive comment saying what you changed"
~~~
Then paste in your Personal Access Token at the prompt `Username for 'https://github.com': `, and at the following password prompt just hit enter.

To completely clean the git folder (i.e. make it look exactly like what is in the repo), you would do like:
~~~
mv ~/github/fiberbots
git checkout main
git pull
git clean -dxf
~~~
So this would delete everything local you've done, including any log files in `temp` or new files in `data`. Obviously, you wouldn't do this on a whim, but good to know how to get to an "original" state.
