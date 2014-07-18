# Terry Stewart, Steve Deiss, Brandon Kelly.... so far 7/15/14
# Detect blinking light at 3 frequencies.
# Orient towards the one at 250Hz (good),
# and away from 50Hz (bad).  Approach 250.
# Retreat from 50 and reorient to look for 250.
# Height of laser (400Hz) in camera FOV provides range.
# Reactor also forwards information from here and there
# to here and there as a middle-man.

import nengo
import nengo_pushbot
import numpy as np

import tag

model = nengo.Network()
with model:

    laser_freq=tag.get_self_freq()  #blue  (image dot color)
    good_freq=tag.get_good_freq()   #green
    bad_freq=tag.get_bad_freq()     #red

    #GOOD_bot = nengo_pushbot.PushBotNetwork('10.162.177.43')
    #GOOD_bot.led(good_freq)

    #BAD_bot = nengo_pushbot.PushBotNetwork('10.162.177.47')
    #BAD_bot.led(bad_freq)

    TANK_bot = nengo_pushbot.PushBotNetwork(tag.get_addr())
    #TANK_bot.laser(laser_freq)
    TANK_bot.led(laser_freq)
    TANK_bot.track_freqs([good_freq, bad_freq, laser_freq], certainty_scale=10000.0) #good-green, bad-red, laser-blue
    #TANK_bot.show_image()  # <----

    # Perhaps the Y coordinate would work better for nearby than the laser which is low and offset?
    TARGETS = nengo.Ensemble(3000, 6, label='TARGETS', radius=2.5)#,neuron_type=nengo.Direct()) # <----
    nengo.Connection(TANK_bot.tracker_0[1],TARGETS[0])  # GOOD X
    nengo.Connection(TANK_bot.tracker_1[1],TARGETS[1])  # BAD X
    nengo.Connection(TANK_bot.tracker_2[0],TARGETS[2])  # Laser Y
    nengo.Connection(TANK_bot.tracker_0[2],TARGETS[3], synapse=0.1)# GOOD certainty
    nengo.Connection(TANK_bot.tracker_1[2],TARGETS[4])  # BAD certainty
    nengo.Connection(TANK_bot.tracker_2[2],TARGETS[5])  # Laser certainty

    def victory(x):  # Supposed to buzz when it gets close to GOOD
        nearby=0.6
        if (x[3]>0.7) and (-0.1<x[0]<0.1):
            if x[2]>nearby:
                return [500]
        return [0]

    nengo.Connection(TARGETS, TANK_bot.beep, synapse=0.2, function=victory)

    def next_step(x):
        advance=1
        goforit=2
        retreat=3
        scram=2
        dance=10
        detect=0.7
        nearby=0.7
        dist=0.5  # may be using this incorrectly - test!
        marg=0.2
        #print 'good_c', x[3]
        if (x[3]<detect) and (x[4]>=detect) and (x[1]<0):
            #print 'no good present, bad on left'
        # no good present, and bad on left
            if x[2]>=-dist: return [2-retreat,-retreat]  # hurry away to the right, close
            elif x[2]<-dist: return [2-scram,-scram] # scram to the right , too close
            # turn right and go away
        elif (x[3]<detect) and (x[4]>=detect) and (x[1]>0):
            #print 'no good, bad on right'
        # no good, and bad right
            if x[2]>=-dist: return [4-retreat,-retreat]  # hurry away to the right, close
            elif x[2]<-dist: return [4-scram,-scram] # scram to the right, too close
            # turn left and go away
        elif (x[3]>=detect) and (x[0]<-marg) and ((x[4]<detect) or ((x[4]>=detect) and (x[1]>=marg))):
            #print 'good left, no bad or bad on right'
        # good left, and no bad or bad right
            if x[2]<-dist: return [-0.8+goforit,1+goforit]
            elif x[2]>=-dist: return [-0.4+advance,0.5+advance]
            # turn left and go forward
        elif (x[3]>=detect) and (x[0]>marg) and ((x[4]<detect) or ((x[4]>=detect) and (x[1]<-marg))):
            #print 'good right, no bad or bad on left'
        # good right, and no bad or bad left
            if x[2]>=-dist: return [1+goforit,-0.8+goforit]
            elif x[2]<-dist: return [0.5+advance,-0.4+advance]
            # turn right and go forward
        elif (x[3]>detect) and (-marg<x[0]<marg): # directly ahead
            #print 'charge ~directly ahead', x[2]
            #if x[2]>nearby: # and really close
                #return [dance,dance]
            return [5,5]
        elif (x[3]>=detect) and (x[4]>detect) and (x[0]<x[1]):
            #print 'good left, bad right'
        # good left, bad right
            if x[2]>=-dist: return [-2,0]
            elif x[2]<-dist: return [-1,0]
            #turn left and inch forward
        elif (x[3]>=detect) and (x[4]>detect) and (x[0]>x[1]):
            #print 'good right, bad left'
        # good right, bad left
            if x[2]>=-dist: return [2,0]
            elif x[2]<-dist: return [1,0]
            # turn right and inch forward
        elif (x[3]<detect) and (x[4]<detect):
            #print 'no good and no bad'
        # no good and no bad, check for and avoid obstacles
            if x[2]>=0: return [1+advance,-advance] # spiral forward and right
            elif x[2]>-dist: return [1,-1] # turn in place to avoid near object
            elif x[2]<dist: return [0.5,-0.5] # turn in place to avoid very near object
            # spiral out and right
        elif x[3]>detect and x[2]<dist: return [-3,-3]
        # Too close to something, backup
        #print 'nothing to do'
        return [1,-1]
            # fell through above ifs, so turn and look more

    # F.M.I.
    # a[start:end] # items start through end-1  <----------Less confusing (sort of)
    # a[start:]    # items start through the rest of the array
    # a[:end]      # items from the beginning through end-1
    # a[:]         # a copy of the whole array

    nengo.Connection(TARGETS, TANK_bot.motor, function=next_step, transform=0.05*tag.get_dir(),synapse=0.002)

if __name__ == '__main__':
    sim = nengo.Simulator(model)

    while True:
        sim.run(1000)
