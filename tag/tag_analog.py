import nengo
import nengo_pushbot
import math

import tag

flip = tag.get_dir()

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork(tag.get_addr())
    bot.track_freqs([tag.get_good_freq(), tag.get_bad_freq()],
                    certainty_scale=5000)
    bot.led(tag.get_self_freq())
    bot.laser(tag.get_self_freq())


    scale_good = 1.4
    scale_bad = 1.0

    turn_speed = 0.05


    #charge = nengo.Ensemble(50, 1, encoders=[[1]]*50, intercepts=nengo.objects.Uniform(0.3, 1))
    #nengo.Connection(bot.tracker_0[2], charge)




    bias = nengo.Node([1])
    turn = nengo.Ensemble(50, 1)
    nengo.Connection(bias, turn)

    #nengo.Connection(charge.neurons, turn, transform=[[-1]*50], synapse=0.2)



    #nengo.Connection(bot.tracker_0[2], turn, transform = -0.5)

    nengo.Connection(turn, bot.motor[0], transform=-turn_speed*flip)
    nengo.Connection(turn, bot.motor[1], transform=turn_speed*flip)

    nengo.Connection(bot.tracker_0[2], bot.motor[0], transform=(1 * scale_good + turn_speed)*flip)
    nengo.Connection(bot.tracker_0[2], bot.motor[1], transform=(1 * scale_good - turn_speed)*flip)

    nengo.Connection(bot.tracker_1[2], bot.motor[0], transform=(-1 * scale_bad - turn_speed)*flip)
    nengo.Connection(bot.tracker_1[2], bot.motor[1], transform=(-1 * scale_bad + turn_speed)*flip)




if __name__ == '__main__':
    javaviz = False

    if javaviz:
        import nengo_gui
        jv = nengo_gui.javaviz.View(model)
    sim = nengo.Simulator(model)
    if javaviz:
        jv.update_model(sim)
        jv.view()

    while True:
        sim.run(10)




