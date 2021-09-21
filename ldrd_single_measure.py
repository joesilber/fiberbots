import time
import numpy as np
import time
import pandas as pd

from fvchandler import FVCHandler
#import matplotlib.pyplot

f = FVCHandler(fvc_type='SBIG')
n_objects =1 
f.min_energy = -np.Inf
xy = []
peaks = []
fwhms = []
energies = []
print('start taking images')
start_time = time.time()
count = 0
n_step = 20
n_round =1 
sleep_time = 7-2
manual = True
while count<n_step*n_round*2:
    print('Count:'+str(count))
    count+=1
    #temp = input()
    #if temp.lower() == 'q':
    #    break
    these_xy,these_peaks,these_fwhms,imgfiles = f.measure(n_objects)
    xy.append(these_xy)
    peaks.append(these_peaks)
    fwhms.append(these_fwhms)
    energies.append([these_peaks[i]*these_fwhms[i] for i in range(len(these_peaks))])
    x=[these_xy[i][0] for i in range(len(these_xy))]
    y=[these_xy[i][1] for i in range(len(these_xy))]
    if manual:
        a=input()
        if a=='q':
            break
    else:
        time.sleep(sleep_time)

x = [xy[i][0][0] for i in range(len(xy))]
y = [xy[i][0][1] for i in range(len(xy))]

xy =[item[0] for item in xy]
df = pd.DataFrame(xy,columns = ['x','y'])
df.to_csv('test_'+str(int(time.time()))+'.csv',index = False)
import matplotlib.pyplot as plt
plt.plot(x,y,'bx',label="Measurements")
plt.xlabel('X')
plt.ylabel('Y')
plt.show()

