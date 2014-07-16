import nengo
import nengo_pushbot
import math

import tag

flip = tag.get_dir()

model = nengo.Network()
with model:
    #bot = nengo_pushbot.PushBotNetwork('10.162.177.55')
    #bot.led(300)
    #bot = nengo_pushbot.PushBotNetwork('10.162.177.47')
    #bot.led(200)


    bot = nengo_pushbot.PushBotNetwork(tag.get_addr())
    bot.track_freqs([tag.get_good_freq(), tag.get_bad_freq()],
                    certainty_scale=5000)
    bot.led(tag.get_self_freq())
    bot.laser(tag.get_self_freq())
    #bot.show_image()

    osc = nengo.Ensemble(300, 2, label='osc')
    tau = 0.1
    omega = 12
    gain = 1.0
    nengo.Connection(osc, osc, transform=[[gain, -omega*tau], [omega*tau, gain]], synapse=tau)

    osc_start = nengo.Node(lambda t: [1,0] if t<0.1 else [0,0])
    nengo.Connection(osc_start, osc)

    pulse = nengo.Ensemble(100, 1, label='pulse')
    def osc_pulse(x):
        theta = math.atan2(x[0], x[1])
        if -0.1 < theta < 0.1:
            return 1
        return 0

    nengo.Connection(osc, pulse, function=osc_pulse)

    nengo.Connection(pulse, bot.motor, transform=[[1.5*flip], [-1.5*flip]])


    found = nengo.Ensemble(100, 1, label='found')
    nengo.Connection(bot.tracker_0[2], found, transform=2)
    nengo.Connection(nengo.Node([-1]), found)
    nengo.Connection(found, bot.beep, transform=1000, synapse=0.01)

    charge = nengo.Ensemble(100, 1, encoders=[[1]]*100,
                            intercepts=nengo.objects.Uniform(0.2, 1),
                            label='charge')
    nengo.Connection(found, charge)
    nengo.Connection(charge, bot.motor, transform=[[2*flip], [2*flip]])

    nengo.Connection(found, pulse.neurons, function=lambda x: 1 if x>0.5 else 0,
                            transform=[[-5]]*100)



    found_bad = nengo.Ensemble(100, 1, label='found_bad')
    nengo.Connection(bot.tracker_1[2], found_bad, transform=2)
    nengo.Connection(nengo.Node([-1]), found_bad)
    avoid = nengo.Ensemble(100, 1, encoders=[[1]]*100,
                            intercepts=nengo.objects.Uniform(0.2, 1),
                            label='avoid')
    nengo.Connection(found_bad, avoid)
    nengo.Connection(avoid, bot.motor, transform=[[-1*flip], [-0.5*flip]])




    #pO = nengo.Probe(osc, synapse=0.01)
    #pP = nengo.Probe(pulse, synapse=0.01)
    nengo.Probe(found)


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




