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
import time
import socket

class TankUDP(nengo.Node):
    def __init__(self, address, port, size_in, size_out, period=0.01):
        self.target = (address, port)
        self.period = period
        self.data = [0,0,0,0]
        self.last_time = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.01)

        super(TankUDP, self).__init__(output=self.send, size_in=size_in,
                                                          size_out=size_out)
    def send(self, t, x):
        now = time.time()
        if self.last_time is None or now > self.last_time + self.period:

            dead_zone = 0.05

            if -dead_zone < x[0] < dead_zone:
                left = 0
            elif x[0] >= 0:
                left = int(x[0]*120)
            else:
                left = int((-x[0])*120)+136

            if -dead_zone < x[1] < dead_zone:
                right = 0
            elif x[1] >= 0:
                right = int(x[1]*128)
            else:
                right = int((-x[1])*120)+136

            grip = 'close' if x[2] > 0.5 else 'open'

            msg = "%d,%d,%s" % (left, right, grip)
            #print 'send', msg
            self.socket.sendto(msg, self.target)
            try:
                data = self.socket.recv(2048)

                data = data.strip().split(',')

                max_sensor = 25.0
                if len(data) == 5:
                    p_r, p_c, p_l = float(data[1]), float(data[2]), float(data[3])
                    p_r = (max_sensor - min(max(p_r, 0), max_sensor))/max_sensor
                    p_c = (max_sensor - min(max(p_c, 0), max_sensor))/max_sensor
                    p_l = (max_sensor - min(max(p_l, 0), max_sensor))/max_sensor
                    grip = 1 if data[4]=='catch' else 0
                    self.data = [p_r, p_c, p_l, grip]
            except socket.error:
                print 'missed packet'

            self.last_time = now
        return self.data

model = nengo.Network()
with model:

    tank = TankUDP(address='10.128.0.18', port=8889,
                  size_in=3, size_out=4, period=0.1)


    laser_freq=400  #blue  (image dot color)
    good_freq=250   #green
    bad_freq=50     #red

    #GOOD_bot = nengo_pushbot.PushBotNetwork('10.162.177.43')
    #GOOD_bot.led(good_freq)

    #BAD_bot = nengo_pushbot.PushBotNetwork('10.162.177.47')
    #BAD_bot.led(bad_freq)

    TANK_bot = nengo_pushbot.PushBotNetwork('10.162.177.43')
    TANK_bot.laser(laser_freq)
    TANK_bot.track_freqs([good_freq, bad_freq, laser_freq], certainty_scale=10000.0) #good-green, bad-red, laser-blue
    #TANK_bot.show_image()  # <----

    GOOD = nengo.Ensemble(100, 3, label='GOOD')
    nengo.Connection(TANK_bot.tracker_0, GOOD)

    BAD = nengo.Ensemble(100, 3, label='BAD')
    nengo.Connection(TANK_bot.tracker_1, BAD)

    TANK = nengo.Ensemble(100, 3, label='TANK')
    nengo.Connection(TANK_bot.tracker_2, TANK)

    # Perhaps the Y coordinate would work better for nearby than the laser which is low and offset?
    TARGETS = nengo.Ensemble(2000, 6, label='TARGETS',neuron_type=nengo.Direct()) # <----
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
        advance=0.5
        goforit=1
        retreat=2
        scram=3
        dance=10
        detect=0.7
        nearby=0.75
        #print 'good_c', x[3]
        if (x[3]<detect) and (x[4]>=detect) and (x[1]<0):
            #print 'no good present, bad on left'
        # no good present, and bad on left
            if x[2]>=-0.5: step = [-1-retreat,-0.5-retreat]  # hurry away to the right, close
            elif x[2]<-0.5: step = [-1-scram,-0.5-scram] # scram to the right , too close
            # turn right and go away
        elif (x[3]<detect) and (x[4]>=detect) and (x[1]>0):
            #print 'no good, bad on right'
        # no good, and bad right
            if x[2]>=-0.5: step = [-0.5-retreat,-1-retreat]  # hurry away to the left, close
            elif x[2]<-0.5: step = [-0.5-scram,-1-scram] # scram to the left, too close
            # turn left and go away
        elif ((x[3]>=detect) and (x[0]<-0)) and ((x[4]<detect) or ((x[4]>=detect) and (x[1]>=0))):
            #print 'good left, no bad or bad on right'
        # good left, and no bad or bad right
            if x[2]<-0.5: step = [-0.75+goforit,1+goforit]
            elif x[2]>=-0.5: step = [-0.4+advance,0.5+advance]
            # turn left and go forward
        elif ((x[3]>=detect) and (x[0]>5)) and ((x[4]<detect) or ((x[4]>=detect) and (x[1]<0))):
            #print 'good right, no bad or bad on left'
        # good right, and no bad or bad left
            if x[2]>=-0.5: step = [1+goforit,-0.75+goforit]
            elif x[2]<-0.5: step = [0.5+advance,-0.4+advance]
            # turn right and go forward
        elif (x[3]>detect) and (-0.2<x[0]<0.2): # directly ahead
            #print 'charge directly ahead', x[2]
            if x[2]>nearby: # and really close
                step = [-dance,dance]
            step = [3,3]
        elif (x[3]>=detect) and (x[4]>detect) and (x[0]<x[1]):
            #print 'good left, bad right'
        # good left, bad right
            if x[2]>=-0.5: step = [-0.75,0]
            elif x[2]<-0.5: step = [-0.25,0]
            #turn left and inch forward
        elif (x[3]>=detect) and (x[4]>detect) and (x[0]>x[1]):
            #print 'good right, bad left'
        # good right, bad left
            if x[2]>=-0.5: step = [0.75,0]
            elif x[2]<-0.5: step = [0.25,0]
            # turn right and inch forward
        elif (x[3]<detect) and (x[4]<detect):
            #print 'no good and no bad'
        # no good and no bad, check for and avoid obstacles
            if x[2]<=0: step = [0.5+advance,-advance] # spiral forward and right
            elif x[2]<0.5: step = [0.5,-0.5] # turn in place to avoid near object
            elif x[2]>=0.5: step = [0.25,-0.25] # turn in place to avoid very near object
            # spiral out and right
        elif x[2]>.7: step = [-3,-3]
        # Too close to something, backup
        #print 'nothing to do'
        else: step = [0.25,-0.25]
            # fell through above ifs
        return step

    # F.M.I.
    # a[start:end] # items start through end-1  <----------Less confusing (sort of)
    # a[start:]    # items start through the rest of the array
    # a[:end]      # items from the beginning through end-1
    # a[:]         # a copy of the whole array

    #
    #  To drive the pushbot use the 'TANK' code, to drive the real tank use the 'tank' code
    #

    udpread_Cerebellum = nengo_pushbot.UDPReceiver(9001, size_out=2) # Cereb. motor command
    #cerebellum_motor = nengo.Node([0,0])
    udpread_Planner = nengo_pushbot.UDPReceiver(9006, size_out=2) # get the Cereb. motor command
    #planner_motor = nengo.Node([0,0])
    nengo.Connection(TARGETS, tank[0:2], function=next_step, transform=0.05,synapse=0.002)
    nengo.Connection(udpread_Cerebellum[:2], tank[0:2])
    nengo.Connection(udpread_Planner[:2], tank[0:2])
    #nengo.Connection(TARGETS, TANK_bot.motor, function=next_step, transform=0.05,synapse=0.002)
    #nengo.Connection(cerebellum_motor, TANK_bot.motor[0:2])
    #nengo.Connection(planner_motor, TANK_bot.motor[0:2])

    # Send movement command (averaged) and compass to Hippocampus
    udpsend_hippocampus = nengo_pushbot.UDPSender('10.162.177.248', 9003, size_in=3)
    nengo.Connection(TARGETS, udpsend_hippocampus[0], function=next_step, transform=[[0.5, 0.5]],synapse=0.002) # motor avg
    nengo.Connection(TANK_bot.compass[0:2],udpsend_hippocampus[0:2]) # compass (x,y only)

    # Read the Vision system recognized objects
    udpread_vision = nengo_pushbot.UDPReceiver(9005, size_out=3)

    # Send motor command, proximity, tracker, and vision recognition to the Cerebellum
    udpsend_cerebellum = nengo_pushbot.UDPSender('10.162.177.248', 9001, size_in=17)
    nengo.Connection(TARGETS, udpsend_cerebellum[:2], function=next_step, synapse=0.002) # motor drive to Cerebellum
    nengo.Connection(tank[0:3],udpsend_cerebellum[2:5]) # 3 proximity sensor values
    nengo.Connection(TANK_bot.tracker_0[0:3], udpsend_cerebellum[5:8])
    nengo.Connection(TANK_bot.tracker_1[0:3], udpsend_cerebellum[8:11])
    nengo.Connection(TANK_bot.tracker_2[0:3], udpsend_cerebellum[11:14])
    nengo.Connection(udpread_vision[0:3], udpsend_cerebellum[14:17])

    # Retrieve and forward energy level to the Planner
    def battery(t):
        bat=TANK_bot.bot.sensor['bat']
        return bat
    bat_level=nengo.Node(battery)
    udpsend_battery = nengo_pushbot.UDPSender('10.162.177.248', 9004, size_in=1) # send battery level to Planner
    nengo.Connection(bat_level, udpsend_battery[0])

    #nengo.Probe(GOOD)
    #nengo.Probe(BAD)
    #nengo.Probe(TANK)

if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run(1000)
