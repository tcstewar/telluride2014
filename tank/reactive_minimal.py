import nengo
import nengo_pushbot
import numpy as np

import tankudp

addr_cerebellum = '10.162.177.253'
port_cerebellum = 8889
addr_hippocampus = '10.162.177.253'
port_hippocampus = 5005
addr_planner = '10.162.177.253'
port_planner = 9004
port_vision = 9005


model = nengo.Network()
with model:

    tank = tankudp.TankUDP(address='10.162.177.254')
    TANK_bot = nengo_pushbot.PushBotNetwork('10.162.177.57')

    TANK_bot.track_freqs([100, 200, 300], certainty_scale=10000)


    # my motor outputs
    motor = nengo.Ensemble(100, 2, neuron_type=nengo.Direct(), label='motor')

    #nengo.Connection(motor, TANK_bot.motor, synapse=0.002)


    # external UDP inputs
    udpread_Planner = nengo_pushbot.UDPReceiver(port_planner, size_out=2) # get the Cereb. motor command
    udpread_vision = nengo_pushbot.UDPReceiver(port_vision, size_out=3)


    # send all motor commands to tank
    nengo.Connection(motor, tank[0:2], synapse=0.002)
    nengo.Connection(udpread_Planner[:2], tank[0:2])

    # Send movement command (averaged) and compass to Hippocampus
    udpsend_hippocampus = nengo_pushbot.UDPSender(addr_hippocampus, port_hippocampus, size_in=3)
    nengo.Connection(motor, udpsend_hippocampus[2], transform=[[0.5, 0.5]],synapse=0.002) # motor avg
    nengo.Connection(TANK_bot.compass[1:3],udpsend_hippocampus[0:2]) # compass (x,y only)

    # Send motor command, proximity, tracker, and vision recognition to the Cerebellum
    udpsend_cerebellum = nengo_pushbot.UDPSender(addr_cerebellum, port_cerebellum, size_in=17, size_out=2)
    nengo.Connection(motor, udpsend_cerebellum[:2], synapse=0.002) # motor drive to Cerebellum
    nengo.Connection(tank[0:3],udpsend_cerebellum[2:5]) # 3 proximity sensor values
    nengo.Connection(TANK_bot.tracker_0[0:3], udpsend_cerebellum[5:8])
    nengo.Connection(TANK_bot.tracker_1[0:3], udpsend_cerebellum[8:11])
    nengo.Connection(TANK_bot.tracker_2[0:3], udpsend_cerebellum[11:14])
    nengo.Connection(udpread_vision[0:3], udpsend_cerebellum[14:17])

    nengo.Connection(udpsend_cerebellum[:2], tank[0:2])

    # Retrieve and forward energy level to the Planner
    udpsend_planner = nengo_pushbot.UDPSender(addr_planner, port_planner, size_in=1) # send battery level to Planner
    def battery(t):
        bat=TANK_bot.bot.sensor['bat']
        return bat
    bat_level=nengo.Node(battery)
    nengo.Connection(bat_level, udpsend_planner[0])

if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run(1000)
