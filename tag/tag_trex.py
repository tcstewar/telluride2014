import nengo
import nengo_pushbot
import numpy as np

import tag
flip = tag.get_dir()

model = nengo.Network(label='pushbot')
with model:
    def inv(x):
        return -x

    bot = nengo_pushbot.PushBotNetwork(tag.get_addr())
    #bot.bot.show_image(decay=0.5)

    # keyboard input
    #kb_input = nengo.Node([0, 0, 0, 0], label='keyboard')
    #sum_left = nengo.Ensemble(100, dimensions=1, label='sum_left')
    #sum_right = nengo.Ensemble(100, dimensions=1, label='sum_right')
    #invert_pop = nengo.Ensemble(100, dimensions=1, label='invert')
    #left_drive = nengo.Ensemble(100, dimensions=1, label='left_drive')
    #right_drive = nengo.Ensemble(100, dimensions=1, label='right_drive')

    #track laser to control forward and backward movement
    bot.track_freqs([tag.get_bad_freq(), tag.get_good_freq()])
    #bot.laser(tag.get_self_freq())
    bot.led(tag.get_self_freq())
    laser_pos = nengo.Ensemble(500, 3, label='laser_pos', radius=1.7)
    food_pos = nengo.Ensemble(500, 3, label='food_pos', radius=1.7)
    nengo.Connection(bot.tracker_0, laser_pos)
    nengo.Connection(bot.tracker_1, food_pos)

    # signs of the return [1 , 1] debending on B or F robot version
    def avoid_move(x):
        if x[2] < 0.3:
            return [0.15, 0.25]

        if x[1] > -0.5 and x[1]<0.5:
            return [1, 1]
        elif x[1] >= 0.5:
            return [-1, 1]
        elif x[1] <= -0.5:
            return [1, -1]
        return [0.15, 0.25]

    def hunt_move(x):
        if x[2] < 0.3:
            return [0.15, 0.25]

        if x[1] > -0.5 and x[1]<0.5:
            return [1, 1]
        elif x[1] >= 0.5:
            return [1, -1]
        elif x[1] <= -0.5:
            return [-1, 1]
        return [0.15, 0.25]


    # Attach desires
    #nengo.Connection(laser_pos, bot.motor, function=avoid_move, transform=0.3*flip)
    nengo.Connection(food_pos, bot.motor, function=hunt_move, transform=0.8*flip)

    # Get turn component
    #nengo.Connection(kb_input[2], invert_pop, function=inv)

    # Get forward component
    #nengo.Connection(kb_input[3], sum_left)
    #nengo.Connection(kb_input[2],  sum_left, transform=0.5)
    #nengo.Connection(kb_input[3],  sum_right)
    #nengo.Connection(invert_pop,  sum_right, transform=0.5)

    # Bind sums to output
    #nengo.Connection(sum_left, left_drive)
    #nengo.Connection(sum_right, right_drive)

    #nengo.Connection(left_drive, bot.motor[0], synapse=0.01, transform=-0.5)
    #nengo.Connection(right_drive, bot.motor[1], synapse=0.01, transform=-0.5)


if __name__ == '__main__':
    #import nengo_gui.javaviz
    #jv = nengo_gui.javaviz.View(model)

    sim = nengo.Simulator(model)
    #jv.update_model(sim_normal)
    #jv.view()

    sim.run(5000)
