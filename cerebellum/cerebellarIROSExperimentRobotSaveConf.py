import time
import sys
from OSC import OSCServer, OSCClient, OSCMessage
import numpy as np

import pylab as pl
import json

myOSC_Server = 0
myOSC_Client = 0

[nDoF, nPNs, bBasis, k_NOI, beta, delayTS]  = [0, 0, 0, 0.0, 0.0, 0] # proximities/actions

# SR = 500.0
SR = 120

#normalizeBasis = bool(int(sys.argv[1]))

rangeExcThresholdFactor=[0.0,0.2]
rangeInhThresholdFactor=[0.2,0.8]

rangeExcMax=[0.5,2.0]
rangeInhMax=[0.8,1.2]

rangeR=[0.002,0.1]
rangeD=[0.1,3.0]

[w, wChange] = [0.0, 0.0] 
[excFactR, excFactD, inhFactR, inhFactD] = [0.0, 0.0, 0.0, 0.0]
[excThreshold, inhThreshold, excScaleBasis, inhScaleBasis] = [0.0, 0.0, 0.0, 0.0]
[excFirstInt, excSecInt, inhFirstInt, inhSecInt] = [0.0, 0.0, 0.0, 0.0]
[out, bufferOut] = [0.0, 0.0]

error = 0
actions=0


index = 0
pastActionsBuffer = 0

start_time = time.time()

# flags debug
save_bases = False
save_ws = False

debug_data = {}
cTrial=1
cStep=0

################ TRAJECTORY  ANALISYS
breakCounter=0
# nTrials=2
# breaksxTrial=[np.zeros(nTrials)]
proximity6=0
# leastProximityxTrial=[np.zeros(nTrials)]

pl.ion()
pl.interactive(True)
# fig=pl.figure(figsize=(10,6))
# pl.subplots_adjust(hspace=.7)
# pl.subplot(1,1,1)
# # pl.title("Breaks per Trial")
# line1, = pl.plot(np.arange(0,nTrials),'*')
# pl.xlim([0,nTrials])
# pl.ylim([0,100])
# pl.subplot(2,1,2)
# pl.title("IR izquierdo")
# line2, = pl.plot(np.arange(0,nTrials))


#Saving first CS-US
CS_US_1 = {}

cerebellumConfig = {}



#################################################
def micro_circuit(idof, thisInput, index) :

    global wChange, excFirstInt, excSecInt, inhFirstInt, inhSecInt, out, bufferOut, error
    global debug_data
       
    wChange[idof]-=beta*error[idof]*bufferOut[idof][index,:]

    excFirstInt[idof]=excFactR[idof]*excFirstInt[idof]+(1-excFactR[idof])*thisInput
    excSecInt[idof]=excFactD[idof]*excSecInt[idof]+(1-excFactD[idof])*excFirstInt[idof]

    inhFirstInt[idof]=inhFactR[idof]*inhFirstInt[idof]+(1-inhFactR[idof])*thisInput
    inhSecInt[idof]=inhFactD[idof]*inhSecInt[idof]+(1-inhFactD[idof])*inhFirstInt[idof]

    exc = np.maximum(excSecInt[idof]-excThreshold[idof],0)*excScaleBasis[idof]
    inh = np.maximum(inhSecInt[idof]-inhThreshold[idof],0)*inhScaleBasis[idof]

    out[idof] = np.maximum(exc-inh,0.0)*w[idof]

    bufferOut[idof][index,:] = np.maximum(exc-inh,0.0)

    if save_bases & (cTrial==0) & (idof==0):
        debug_data['basis']['tot'].append(np.maximum(exc-inh,0.0).tolist())
        debug_data['basis']['exc'].append(exc.tolist())
        debug_data['basis']['inh'].append(inh.tolist())



########################################################
def sendOSCMsg( address='/out', data=[] ) :
    m = OSCMessage()
    m.setAddress(address)
    for d in data :
        m.append(d)
    myOSC_Client.send(m)

########################################################
def receiveFreeze(addr, tags, data, source):
    global beta
    beta=0
########################################################
def receiveSaveConf(addr, tags, data, source):

    global excFactR, excFactD, excThreshold, excScaleBasis, inhFactR, inhFactD, inhThreshold, inhScaleBasis
    # global nDoF, nPNs, bBasis, k_NOI, beta, delayTS

    cerebellumConfig['ws'] = [w[i].tolist() for i in range(nDoF)]
    
    cerebellumConfig['config'].append({}) 
    cerebellumConfig['config'][0]['nDoF'] = nDoF;
    cerebellumConfig['config'][0]['nPNs'] = nPNs;
    cerebellumConfig['config'][0]['bBasis'] = bBasis;
    cerebellumConfig['config'][0]['k_NOI'] = k_NOI;
    cerebellumConfig['config'][0]['beta'] = beta;
    cerebellumConfig['config'][0]['delayTS'] = delayTS;
    
    cerebellumConfig['constants'].append({})
    # cerebellumConfig['constants'][0]['excTauR'] = excTauR.tolist(); 
    # cerebellumConfig['constants'][0]['excTauD'] = excTauD.tolist();
    # cerebellumConfig['constants'][0]['inhTauR'] = inhTauR.tolist();
    # cerebellumConfig['constants'][0]['inhTauD'] = inhTauD.tolist();
    cerebellumConfig['constants'][0]['excFactR'] = [excFactR[i].tolist() for i in range(nDoF)]
    cerebellumConfig['constants'][0]['excFactD'] = [excFactD[i].tolist() for i in range(nDoF)]
    cerebellumConfig['constants'][0]['inhFactR'] = [inhFactR[i].tolist() for i in range(nDoF)]
    cerebellumConfig['constants'][0]['inhFactD'] = [inhFactD[i].tolist() for i in range(nDoF)]

    cerebellumConfig['constants'][0]['excThreshold'] = [excThreshold[i].tolist() for i in range(nDoF)]
    cerebellumConfig['constants'][0]['inhThreshold'] = [inhThreshold[i].tolist() for i in range(nDoF)]
    cerebellumConfig['constants'][0]['excScaleBases'] = [excThreshold[i].tolist() for i in range(nDoF)]
    cerebellumConfig['constants'][0]['excThreshold'] = [excThreshold[i].tolist() for i in range(nDoF)]

   
    filename = '/Users/Santi/Documents/UPF/CSIM/Tesis/IROS/SavedConfig.json'
    input_file = open(filename,'w')
    json.dump(cerebellumConfig, input_file)
    input_file.close()



 
########################################################
def receiveConfig(addr, tags, data, source):
    global nDoF, nBasis, nPNs, k_NOI, beta, delayTS, nTrials

    nPNs = data[0]
    nDoF = data[1]
    nBasis = data[2]

    k_NOI = data[3]
    beta  = data[4]
    delayTS = int(data[5]*SR)
    nTrials = data[6]

    # print(nPNs)
    # print(nDoF)
    print 'beta: ', beta
    print'k_NOI: ', k_NOI
    print 'delay(s): ', data[5]


    global debug_data, cTrial
    global excFirstInt,excSecInt,inhFirstInt,inhSecInt, pastActionsBuffer, w, wChange, out, bufferOut, actions

    cTrial=1

    excFirstInt = [np.zeros(nBasis*nPNs) for x in range(nDoF)]
    excSecInt = [np.zeros(nBasis*nPNs) for x in range(nDoF)]
    inhFirstInt = [np.zeros(nBasis*nPNs) for x in range(nDoF)]
    inhSecInt = [np.zeros(nBasis*nPNs) for x in range(nDoF)]

    w = [np.zeros(nBasis*nPNs) for x in range(nDoF)]
    wChange = [np.zeros(nBasis*nPNs) for x in range(nDoF)]

    out = [np.zeros([nBasis*nPNs]) for x in range(nDoF)]
    bufferOut =  [np.zeros([delayTS,nBasis*nPNs]) for x in range(nDoF)]
    
    index = 0

    actions=np.zeros(nDoF)

    initializeBasis()

    global line1, line2, fig
    global breaksxTrial, leastProximityxTrial
    breaksxTrial=[np.zeros(nTrials)]
    leastProximityxTrial=[np.zeros(nTrials)]
    # pl.ion()
    # pl.interactive(True)
    fig=pl.figure(figsize=(10,6))
    pl.subplots_adjust(hspace=.7)
    pl.subplot(2,1,1)
    # pl.title("Breaks per Trial")
    line1, = pl.plot(np.arange(0,nTrials),'*')
    pl.xlim([0,nTrials])
    pl.ylim([0,200])
    pl.subplot(2,1,2)
    pl.title("Valor IR izquierdo (inverso a proximidad)")
    line2, = pl.plot(np.arange(0,nTrials),'*')
    pl.xlim([0,nTrials])
    pl.ylim([0,1])

    print 'configured'


########################################################
def receiveTrial(addr, tags, data, source):
    
    print "received /trial"

    global debug_data
    global excFirstInt,excSecInt,inhFirstInt,inhSecInt, pastActionsBuffer, w, wChange

    for i in range(nDoF):
        w[i]-=wChange[i]
        excFirstInt[i] *= 0
        excSecInt[i] *= 0
        inhFirstInt[i] *= 0
        inhSecInt[i] *= 0
        wChange[i] *= 0
    
    pastActionsBuffer=np.zeros([delayTS,nDoF])

    # create new data field
    debug_data['trials'].append({})
    debug_data['trials'][-1]['steps']=[]

    if cTrial==0:
        if save_bases:
            debug_data['basis']={}
            debug_data['basis']['tot']=[]
            debug_data['basis']['exc']=[]
            debug_data['basis']['inh']=[]
        debug_data['inputs']=[]

#################################################
def receiveUpdate(addr, tags, data, source):
    
    global debug_data, cTrial
    global w, wChange

    for i in range(nDoF):
        w[i]-=wChange[i]
        wChange[i] *= 0

#################################################
def receiveEndTrial(addr, tags, data, source):
    
    global debug_data, cTrial, nTrials
    global excFirstInt,excSecInt,inhFirstInt,inhSecInt, pastActionsBuffer, w, wChange
    global breakCounter,breaksxTrial, proximity6, leastProximityxTrial
    global fig
    
    breakCounter=data[0];
    proximity6=data[1];

    print 'Trial: ', cTrial
    print 'brakes: ', breakCounter;
    print 'proximity: ', proximity6
    breaksxTrial[0][cTrial-1]=breakCounter
    leastProximityxTrial[0][cTrial-1]=proximity6
    line1.set_ydata(breaksxTrial[0])
    line2.set_ydata(leastProximityxTrial)
    pl.draw()
    

    if cTrial==nTrials :
        print('hola')
        pl.subplot(2,1,1)
        pl.title("Breaks per Trial, "+ "beta: " + str(beta) +', knoi: '+str(k_NOI)+', nBasis: '+str(nBasis)+', delay(s): '+str(delayTS/SR))
        fig.savefig('beta'+str(beta)+'_knoi'+str(k_NOI)+'_nBasis'+str(nBasis)+', delay(s): '+str(delayTS/SR)+'.pdf')
        
    # if cTrial==nTrials:
    #     cTrial=1;      


    if save_ws:
        debug_data['trials'][cTrial]['ws']       = [w[i].tolist() for i in range(nDoF)]
        debug_data['trials'][cTrial]['wChanges'] = [wChange[i].tolist() for i in range(nDoF)]

    cTrial = cTrial + 1

########################################################
def receiveDebug(addr, tags, data, source):

    print "received /debug"
    
    filename = data[0]

    global debug_data
    debug_file = open(filename,'w')

    json.dump(debug_data, debug_file)

    debug_file.close()

    print "debug printed"
    exitServer()


########################################################
def receiveInput(addr, tags, data, source):

    thisInputSimple = np.array(data[0:nPNs])
    target = data[nPNs:(nPNs+nDoF)]
    # print "hasta aca"
    # repmat
    global pastActionsBuffer, index
    global actions, error
    global CS_US_1
    
    error=np.array(target)-k_NOI*pastActionsBuffer[index][:];

    global debug_data

    debug_data['trials'][-1]['steps'].append({})
        
    thisInput=np.tile(thisInputSimple,[nBasis,1]).flatten(2) # here I should use flatten

    for idof in range(nDoF):
        micro_circuit(idof, thisInput, index)
        
#        actions[idof]=np.mean(out[idof])
        actions[idof]=max(0,np.mean(out[idof]))
        pastActionsBuffer[index][idof]=actions[idof]
    
    sendOSCMsg('/out', actions)

    debug_data['trials'][-1]['steps'][-1]['error']=error.tolist()
    debug_data['trials'][-1]['steps'][-1]['target']=target

    
    #Saving first cs us
    # if cTrial==0:
    #     debug_data['inputs'].append(thisInputSimple.tolist())
        
    #     CS_US_1['inputs'].append({})
    #     CS_US_1['inputs'][-1]['CS']=data[0:nPNs]
    #     CS_US_1['inputs'][-1]['US']=target

    if cTrial==1:
        filename = 'Input'

        input_file = open(filename,'w')

        json.dump(CS_US_1, input_file)

        input_file.close()

        


    index = (index+1) % delayTS

    
    


# this function sends a pulse, waits 3 seconds and then updates the scale basis so that the total response 
# of all basis is equal to one

def runNormalization():

    global index
    global excScaleBasis, inhScaleBasis

    print "normalization"
    global excFirstInt,excSecInt,inhFirstInt,inhSecInt, pastActionsBuffer, w, wChange
    global out, cTrial
    global error

    for i in range(nDoF):
        excFirstInt[i] *= 0
        excSecInt[i] *= 0
        inhFirstInt[i] *= 0
        inhSecInt[i] *= 0
        wChange[i] *= 0

    error = np.zeros(nDoF)

    sim_time = np.arange(0.0,3.0,1.0/SR).tolist()

    thisInput = np.ones(nBasis*nPNs)

    pastActionsBuffer=np.zeros([delayTS,nDoF])
    index = 0

    # temporal, reverted at the end of the call
    w =       [np.ones(nBasis*nPNs) for x in range(nDoF)]
    cTrial = -1

    tmpOuts = [np.zeros(nBasis*nPNs) for x in range(nDoF)]

    for t in sim_time:
        for idof in range(nDoF):
            micro_circuit(idof, thisInput, index)
            tmpOuts[idof]+=out[idof]/SR

        thisInput = np.zeros(nBasis*nPNs)
    
    for idof in range(nDoF):
        tmpOuts[idof][tmpOuts[idof]==0.0]=1.0 # avoid problem with basis yielding a 0 output

        excScaleBasis[idof]*=1.0/tmpOuts[idof]
        inhScaleBasis[idof]*=1.0/tmpOuts[idof]

    # back to initial point
    w = [np.zeros(nBasis*nPNs) for x in range(nDoF)]

    cTrial = 0


def initializeBasis():
    global excFactR, excFactD, excThreshold, excScaleBasis, inhFactR, inhFactD, inhThreshold, inhScaleBasis

    excTauR=rangeR[0]+(rangeR[1]-rangeR[0])*np.random.rand(nDoF,nBasis*nPNs)
    excTauD=rangeD[0]+(rangeD[1]-rangeD[0])*np.random.rand(nDoF,nBasis*nPNs)
    
    excThresholdFactor=rangeExcThresholdFactor[0]+ \
        (rangeExcThresholdFactor[1]-rangeExcThresholdFactor[0])*np.random.rand(nDoF,nBasis*nPNs)
    inhThresholdFactor=rangeInhThresholdFactor[0]+ \
        (rangeInhThresholdFactor[1]-rangeInhThresholdFactor[0])*np.random.rand(nDoF,nBasis*nPNs)
    
    excMax=rangeExcMax[0]+ \
        (rangeExcMax[1]-rangeExcMax[0])*np.random.rand(nDoF,nBasis*nPNs)
    
    inhMax=rangeInhMax[0]+ \
        (rangeInhMax[1]-rangeInhMax[0])*np.random.rand(nDoF,nBasis*nPNs)


    excFactR_ = np.exp(-1.0/(excTauR*SR))
    excFactD_ = np.exp(-1.0/(excTauD*SR))
    
    tmax=(excTauR*excTauD/(excTauD-excTauR))*(np.log(excTauD)-np.log(excTauR))
    maxVal=(np.exp(-tmax/excTauR)-np.exp(-tmax/excTauD))/((excTauR-excTauD)*SR)
    excThreshold_=excThresholdFactor*maxVal
    excScaleBasis_=excMax/(maxVal-excThreshold_)
    
    inhTauR=excTauR*1.5
    inhTauD=excTauD*1.5
    
    inhFactR_ = np.exp(-1.0/(inhTauR*SR))
    inhFactD_ = np.exp(-1.0/(inhTauD*SR))
    
    tmax=(inhTauR*inhTauD/(inhTauD-inhTauR))*(np.log(inhTauD)-np.log(inhTauR))
    maxVal=(np.exp(-tmax/inhTauR)-np.exp(-tmax/inhTauD))/((inhTauR-inhTauD)*SR)

    inhThreshold_=inhThresholdFactor*maxVal
    inhScaleBasis_=inhMax/(maxVal-inhThreshold_)
    
    excFactR = [excFactR_[:][i] for i in range(nDoF)]
    excFactD = [excFactD_[:][i] for i in range(nDoF)]
    inhFactR = [inhFactR_[:][i] for i in range(nDoF)]
    inhFactD = [inhFactD_[:][i] for i in range(nDoF)]
    
    excThreshold = [excThreshold_[:][i] for i in range(nDoF)]
    inhThreshold =  [inhThreshold_[:][i] for i in range(nDoF)]
    excScaleBasis =  [excScaleBasis_[:][i] for i in range(nDoF)]
    inhScaleBasis =  [inhScaleBasis_[:][i] for i in range(nDoF)]

#    if normalizeBasis:
#        runNormalization()


def main():
    global bRun
    global inOSCport, outOSCport
    global myOSC_Server, myOSC_Client

    global cTrial, nTrials, breaksxTrial

    cTrial = 1 

    global debug_data
    global CS_US_1 

    CS_US_1['inputs']=[]

    cerebellumConfig['weights']=[]
    cerebellumConfig['config']=[]
    cerebellumConfig['constants']=[]


    debug_data['trials']=[]
    if save_bases:
        debug_data['basis']=[]
    debug_data['inputs']=[]

    inOSCport = 1234
    outOSCport = 1235
    
    # myOSC_Server = OSCServer( ('' , inOSCport) )
    # myOSC_Client = OSCClient()
    # myOSC_Client.connect( ('10.0.0.116' , outOSCport) )

    myOSC_Server = OSCServer( ('127.0.0.1' , inOSCport) )
    myOSC_Client = OSCClient()
    myOSC_Client.connect( ('127.0.0.1' , outOSCport) )
    
    print "Receiving messages /trial,/input in port", inOSCport
    print "Sending messages to port", outOSCport


    myOSC_Server.addMsgHandler("/config", receiveConfig)
    myOSC_Server.addMsgHandler("/trial", receiveTrial)
    myOSC_Server.addMsgHandler("/endtrial", receiveEndTrial)
    myOSC_Server.addMsgHandler("/input", receiveInput)
    myOSC_Server.addMsgHandler("/debug", receiveDebug)
    myOSC_Server.addMsgHandler("/update", receiveUpdate)
    myOSC_Server.addMsgHandler("/freeze", receiveFreeze)
    myOSC_Server.addMsgHandler("/saveConfig", receiveSaveConf)
    

    

    # if (cTrial==nTrials):
    #     pl.figure(figsize=(10,6))
    #     plot(breaksxTrial)

    
    print "Ready"

    myOSC_Server.serve_forever()

def exitServer():
    bRun = 0
    myOSC_Server.close()
    elapsed_time = time.time() - start_time
    print 'Time:',elapsed_time,'s'
    print "Done."
   

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitServer()
