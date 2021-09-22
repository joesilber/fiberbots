# fiberbots
code for operating and testing fiber positioner robots

## bin
These are the high-level scripts that you run day-to-day.

### analysis
Scripts for analyzing measured data. These should all be operable "offline", without any need for hardware, such that anyone with this GitHub repo can simply run the code.

### control
Scripts for controlling the motors and camera to do physical tests.

As of 2021-09-21, the resulting data should be automatically saved in the "data" folder. See comments below.

## camera
### fvchandler.py
High-level interface to camera. Sends commands to the camera and interprets the resulting image by centroiding. 

As of 2021-09-21 at LBNL, we are only using an SBIG STF-8300M camera. However `fvchandler.py` is intended to be flexible for using a different camera. In such cases, you would add new commands for the new driver in this module. Meanwhile, the pixel interpretation etc would be taken care of generically.

### `SBIG`
Low-level drivers for SBIG camera.

See file `readme` in this directory for instructions on SBIG driver installation and some environmental variables that need to be set.

As of 2021-09-21, low-level centroiding code is also in this folder (c.f. `sbig_grab_cen.py` etcetera). This is not ideal modularization. A more flexible architecture would be to make the centroiding more abstracted from the picture-taking. It's not essential right now, but would be useful in the future. In such a case, we would put the new, generic, centroiding module up one directory, next to `fvchandler.py`.

## data
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

Hint: You can generate the first timestamp automatically with a command like:
```
from datetime import datetime, timezone
prefix = datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')
```

## manuals
Store existing or external procedures, manuals, and other reference files etcetera here. However, new code documentation should be written in the `.md` format and version-controlled in GitHub (like this file). 

## motors
Low-level control of the motors that drive the robots.

As of 2021-09-21, the code is for electronics received from EPFL in 2020.

## other
Stuff that isn't currently in use, for example old code that we may want to use parts of. Items here may be nonfunctional, and for information only.


