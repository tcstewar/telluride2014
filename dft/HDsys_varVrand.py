import nengo
import numpy as np
import matplotlib.pyplot as plt


np.random.seed(1)

#### prepare tuning curves/encoders
D          = 14
Dvel       = 1
n_sample   = 1000
n_neurons  = 1000
fsp_res    = 100
shift_fac  = 4  # this is multiplied by the current velocity (between 0 and 1), should yields at least 1-5 inidices shift
fsp_res_f  = 5000
theta      = np.linspace(-np.pi,np.pi,fsp_res)
theta_fine = np.linspace(-np.pi,np.pi,fsp_res_f) # use a fine grained estimate for shifting with roll, then subsample
theta_ind  = np.arange(fsp_res)*fsp_res_f/fsp_res
#print theta_ind
tc_base    = np.exp(-np.square(theta_fine)/1.0)
r          = np.arange(n_neurons-1)   # because we will have 500 neurons, one encoder each. 500th is tc_base
tc         = tc_base[theta_ind]

#plt.figure(1)
#plt.plot(theta_fine,tc_base)

for i in r:
    
    ar = 0.8+(1.2-0.8)*np.random.random((1))
    tc_base    = np.exp(-np.square(theta_fine)/ar)
    
    tc_temp1 = np.roll(tc_base,r[i]*fsp_res_f/n_neurons)
    tc_temp2 = tc_temp1[theta_ind]    
    tc = np.vstack((tc,tc_temp2))
#    plt.figure(2)
#    plt.plot(theta,tc_temp2)   
# now tc has dimensionality 500,100, meaning 500 tuning curves/encoders, defined over 100 data pts in theta



#### SVD and Basis fcts

(U,S,Vt) = np.linalg.svd(tc.T, full_matrices=1, compute_uv=1)   # can use transpose of tc, affects choice of U over V and vice verse

#plt.figure(4)
#plt.imshow(U)
#plt.figure(5)
#plt.imshow(Vt)
#plt.figure(6)
#plt.plot(S)

#print U.shape

trunc_U = U[:,0:14].copy()   # truncation after significant singular value
#plt.figure(7)
#plt.imshow(trunc_U)
#print trunc_U.shape
#for i in np.arange(14):
#    plt.figure(8)
#    plt.plot(trunc_U[:,i])    # plot basis fcts
    #print i

# check for orthogonality
#a=empty((100,100),float)
#r2 = np.arange(100)
#for i in r2:
#    for j in r2:
#        a[i,j] = dot(U[:,i],U[:,j])

#plt.figure(9)
#plt.imshow(a)



#### make sample points, wider Gaussians, corresponds to samples of the bump to be represented, not samples of tuning curves 
sa_pts_base = np.exp(-np.square(theta_fine)/2)
sa_pts      = sa_pts_base[theta_ind]
r_s         = np.arange(n_sample-1)    # suggestion by Chris, roughly 100 sample pts for HD system
for i in r_s:
    sa_pts_temp1 = np.roll(sa_pts_base,r[i]*fsp_res_f/fsp_res)
    sa_pts_temp2 = sa_pts_temp1[theta_ind]    
    sa_pts = np.vstack((sa_pts,sa_pts_temp2))
    #plt.figure(3)
    #plt.plot(theta,sa_pts_temp2)

sample_coef = np.dot(sa_pts,trunc_U)
temp        = sample_coef*sample_coef        
temp2       = np.sqrt(temp.sum(axis=1))
rad         = temp2.max()    
    
    
    
#### get coefficients in vector space for fct representation    
enc_coef = np.dot(tc,trunc_U)
basis    = trunc_U 
#print enc_coef.shape
#plt.figure(10)
#plt.imshow(enc_coef)


#### transform encoders and sample pt vector repres. to 15D space with 0 in last dim
# append not zero to encoders, but +/- 1 rndomnly chose

a = -1+(1+1)*np.random.random((n_neurons,1))
#ind1 = np.nonzero(a<0)
#ind2 = np.nonzero(a>0)
#a[ind1] = np.floor(a[ind1])
#a[ind2] = np.ceil(a[ind2])

D2            = D+1   # increase dimensionality
#a             = np.zeros((n_neurons,1))
enc_coef15    = np.append(enc_coef, a, axis=1)

b = -1+(1+1)*np.random.random((n_sample,1))
#ind1 = np.nonzero(b<0)
#ind2 = np.nonzero(b>0)
#b[ind1] = np.floor(b[ind1])
#b[ind2] = np.ceil(b[ind2])
#b             = np.zeros((n_sample,1))
sample_coef15 = np.append(sample_coef, b, axis=1)
# radius should say the same with ahv 0, but see below



# updated radius because of random -,1 entries for ahv in dim 15
temp3       = sample_coef15*sample_coef15        
temp4       = np.sqrt(temp3.sum(axis=1))
rad2        = temp4.max()  




#ahv_mag = 0



#### building the network
model = nengo.Network(label='HDring')
with model:
    
    def initialinput(t):
        if t<0.05: x = enc_coef[1,:]
        else: x = [0]*D
        return x
       
    def readout_fct(t,x):
        reduced = x[0:14]
        y = np.dot(trunc_U,x[:D])
        return y

    def bla(t):
        if t>1:
            x = np.sin(2*t)
        else: x = 0
        return x
       
    def translate(x):
        reduced            = x[0:D]
        fsp_rep            = np.dot(trunc_U,reduced)
        shift              = int(x[-1]*shift_fac)   # x[-1] is between 0 and 1
        fsp_rep = np.roll(fsp_rep, shift)
        x[0:D]             = np.dot(fsp_rep,trunc_U)
        return x

    # inputs    
    #ahv     = nengo.Node(bla,label="AHVinput")
    ahv     = nengo.Node([0],label="AHVinput")
    input   = nengo.Node(initialinput, label="initial stim")
    
    HDpop = nengo.Ensemble(n_neurons, dimensions=D2,encoders=enc_coef15,
    eval_points=sample_coef15,radius=rad2,label="HDring")

    # reconstruct function representation
    #readout = nengo.Node(output=None, size_in=fsp_res, label="readout")
    #readout = nengo.Node(output=readout_fct, size_in=fsp_res, label="readout")
    readout = nengo.Node(output=readout_fct, size_in=D, size_out=fsp_res, label="readout")
    # note that in the file 
    # /Users/ijon/Desktop/Nengo/nengo-3b0c9bc/python/timeview/components/vector_grid.py
    # we changed         if self.rows is None:^M
    #                       rows = int(sqrt(len(data)))^M
    # to                    rows = 1

    # Connect the population to itself
    nengo.Connection(HDpop,HDpop,function=translate,synapse=0.01) 
    # slower synaptic decay scales translation speed
    
    # input signals
    nengo.Connection(ahv,HDpop[14])
    nengo.Connection(input,HDpop[0:14])  # in matlab corresponds to 1:14, last one not included in python

    # recompute a 100D repres. to be displayed as a grid in the visualizer    
    #nengo.Connection(HDpop,readout,function=readout_fct)
    #nengo.Connection(HDpop[:14],readout[:14])
    nengo.Connection(HDpop[:14],readout)

    # Add probes
    nengo.Probe(input)
    nengo.Probe(readout)
    nengo.Probe(HDpop)
    nengo.Probe(HDpop,'spikes')

import nengo_gui
gui = nengo_gui.Config()
gui[model].scale = 0.8887731075597414
gui[model].offset = 1.9989679875754973,181.80283051951318
gui[HDpop].pos = 175.000, 87.500
gui[HDpop].scale = 1.000
gui[ahv].pos = 50.000, 50.000
gui[ahv].scale = 1.000
gui[input].pos = 50.000, 125.000
gui[input].scale = 1.000
gui[readout].pos = 300.000, 87.500
gui[readout].scale = 1.000
