import nengo
import nengo_pushbot
import numpy as np

import tag

motor_speed_factor = -0.2 * tag.get_dir()
sheep_motor_speed_factor=0.4
# how fast can the bot go as a maximum in each direction
input_factor=0.9


model = nengo.Network(label='pushbot')
with model:
    l1 = nengo.Ensemble(100, dimensions=1, label='l1')
    r1 = nengo.Ensemble(100, dimensions=1, label='r1')
# speed cannot go faster than one - want it to be forward and right and it goes double the speed.
    combo1 = nengo.Ensemble(200, dimensions=2, label='combo1', radius = 1.4)
    control = nengo.Ensemble(200, dimensions=2, label='control', radius = 1.4)

#connect to populations that control the motors
    l2 = nengo.Ensemble(100, dimensions=1, label='l2')
    r2 = nengo.Ensemble(100, dimensions=1, label='r2')
# replica of what is sent to the motor so that we can see the behavior and allows plotting - this is also what we are probing
    bot1 = nengo_pushbot.PushBotNetwork(tag.get_addr())
    bot1.laser(tag.get_self_freq())
    bot1.led(tag.get_self_freq())

    #bot1.laser(0)
    #bot1.track_freqs([200, 300])
    bot1.track_freqs([tag.get_good_freq()])


    half_size = 64.0

    y_limit = list()
    y_limit.append(0.0)
    y_limit.append(35.0)
    y_limit.append(40.0)
    y_limit.append(115.0)
    y_limit.append(127.0)

    x_limit=list()
    x_limit.append(0.0)
    x_limit.append(18.0)
    x_limit.append(36.0)
    x_limit.append(54.0)
    x_limit.append(73.0)
    x_limit.append(91.0)
    x_limit.append(109.0)
    x_limit.append(127.0)

# 3 dimensions are x y and a confidence level for how sure there is something there.
    pos0 = nengo.Ensemble(100, 3, label='pos0')
# only want 2 of the dimensions - removing the 3rd component for tracking.
    nengo.Connection(bot1.tracker_0[:2], pos0[:2])

    def normalize_coord(x):
        return (x-half_size)/half_size

# divides the vision field into 9 positions - says that if the interest area is not in the middle then look up or down and turn either left / right to put the stimuli in the middle. This also allows distance to be maintained.
    def orient(x):
        if x[0] < normalize_coord(y_limit[1]): #forward/backward
            y_ret = 1
        elif x[0] >= normalize_coord(y_limit[1]) and x[0] < normalize_coord(y_limit[2]):
            y_ret = 0
        else:
            y_ret = -1

        if x[1] < normalize_coord(x_limit[3]): #rotate left/right
            x_ret = 0.1
        elif x[1] >= normalize_coord(x_limit[3]) and x[1] <= normalize_coord(x_limit[4]):
            x_ret = 0
        else:
            x_ret = -0.1

        return [y_ret, x_ret]

    #pos1 = nengo.Ensemble(100, 2, label='pos1')
    #nengo.Connection(bot1.tracker_1, pos1)

# this is what controls the robot - from control to position through the function orient - transform is just a one to one mapping of a 2D matrix.
    nengo.Connection(pos0, control, function=orient, transform=[[1,0],[0,1]], synapse=0.002)

# duplication so that both robots are controlled - one with the keyboard and the other with the stimuli.
    nengo.Connection(control, l1, transform=[[input_factor, 0]])
    nengo.Connection(control, r1, transform=[[input_factor, 0]])
    nengo.Connection(control, l1, transform=[[0, input_factor]])
    nengo.Connection(control, r1, transform=[[0, -input_factor]])
    nengo.Connection(l1, bot1.motor, synapse=0.002, transform=[[sheep_motor_speed_factor], [0]])
    nengo.Connection(r1, bot1.motor, synapse=0.002, transform=[[0], [sheep_motor_speed_factor]])
    nengo.Connection(l1, combo1, synapse=0.002, transform=[[sheep_motor_speed_factor], [0]])
    nengo.Connection(r1, combo1, synapse=0.002, transform=[[0], [sheep_motor_speed_factor]])


if __name__ == '__main__':
    sim = nengo.Simulator(model)
    while True:
        sim.run(5000)
