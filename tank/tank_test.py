import nengo
import nengo_pushbot
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



model = nengo.Network(label='tank')
with model:
    keyboard = nengo.Node([0,0,0], label='keyboard')
    udp = TankUDP(address='10.128.0.18', port=8889,
                  size_in=3, size_out=4, period=0.1)

    sensors = nengo.Ensemble(10, 4, neuron_type=nengo.Direct(), label='sensor')


    nengo.Connection(keyboard, udp)
    nengo.Connection(udp, sensors)

    nengo.Probe(sensors)

import nengo_gui
jv = nengo_gui.javaviz.View(model)
sim = nengo.Simulator(model)
jv.view()
while True:
    sim.run(100)

