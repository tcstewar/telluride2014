import cerebellum
import numpy as np

crb = cerebellum.Cerebellum()
crb.config('basis_visual_sim.cfg')
crb.plug(nDoF=1,
         nBasis=300,
         nPNs=1,
         k_NOI=0.5,
         beta=40,
         delay=0.1,
         SR=60)

t = np.arange(500)
CS = np.where(t<200, 1, 0)
UR = np.where(t<200, np.where(t>150,1,0), 0)


CR_all = []


for trial in range(500):
    print trial
    crb.initTrial()
    CRs = []

    for x in range(len(CS)):
        CR = crb.input([CS[x],UR[x]])
        CRs.append(CR[0])


    CR_all.append(CRs)
    crb.endTrial()

import pylab
pylab.figure()
pylab.imshow(CR_all, aspect='auto')
pylab.figure()
pylab.plot(CS, label='CS')
pylab.plot(UR, label='UR')
pylab.plot(CR_all[-1], label='CR')
pylab.show()
