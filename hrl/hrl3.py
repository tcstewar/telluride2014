import nengo.spa as spa
import nengo
import numpy as np

inputs = ['RED+SQUARE',
          'RED+TRIANGLE',
          'BLUE+SQUARE',
          'BLUE+TRIANGLE'
          ]

D = 16

model = spa.SPA(label='hrl')
with model:
    model.state = spa.Buffer(D)
    model.vision = spa.Buffer(D)
    model.context = spa.Buffer(D)
    model.motor = spa.Buffer(D)

    model.cortical = spa.Cortical(spa.Actions(
        'state=vision*VISION',
        'state=context*CONTEXT',
        ))

    model.bg = spa.BasalGanglia(spa.Actions(
        '0 --> motor=A',
        '0 --> motor=B',
        '0 --> motor=C',
        '0 --> motor=D',
        ))
    model.thal = spa.Thalamus(model.bg)

    model.bg2 = spa.BasalGanglia(spa.Actions(
        '0 --> context=W',
        '0 --> context=X',
        '0 --> context=Y',
        '0 --> context=Z',
        ))
    model.thal2 = spa.Thalamus(model.bg2)

    def in_vision(t):
        return inputs[int(t / 0.2) % 4]
    model.input = spa.Input(state=in_vision)

    pThal = nengo.Probe(model.thal.actions.output, synapse=0.01)
    pUtil = nengo.Probe(model.bg.input, synapse=0.01)
    pThal2 = nengo.Probe(model.thal2.actions.output, synapse=0.01)
    pUtil2 = nengo.Probe(model.bg2.input, synapse=0.01)


with model:
    def error_func(t, x):
        util = x[:4]
        act = x[4:8]
        motor_act=x[8:]

        index = int(t / 0.2) % 4
        motor_index = list(motor_act).index(max(motor_act))
        chosen_index = list(act).index(max(act))
        if motor_index == index:
            error = np.eye(4)[chosen_index] - util
            #error = [0, 0, 0, 0]
            #error[chosen_index] = 1 - util[chosen_index]
        else:
            error = (1-np.eye(4)[chosen_index]) - util

        if t % 0.2 > 0.1:
            print t,
            print ','.join(['%1.2f' % x for x in util]),
            print ','.join(['%1.2f' % x for x in error])
            return error
        return [0, 0, 0, 0]
    error = nengo.Node(error_func, size_in=12, size_out=4)
    nengo.Connection(model.bg.input, error[:4])
    nengo.Connection(model.thal.actions.output, error[4:8])
    nengo.Connection(model.thal.actions.output, error[8:])

    error2 = nengo.Node(error_func, size_in=12, size_out=4)
    nengo.Connection(model.bg2.input, error2[:4])
    nengo.Connection(model.thal2.actions.output, error2[4:8])
    nengo.Connection(model.thal.actions.output, error2[8:])

    for j, e in enumerate(model.state.state.ensembles):
        c = nengo.Connection(e, model.bg.input, function=lambda x: [0, 0, 0, 0])
        error_conn = nengo.Connection(error, model.bg.input,
                                          modulatory=True)
        c.learning_rule = nengo.PES(error_conn, learning_rate=0.2)

    #for j, e in enumerate(model.context.state.ensembles):
    #    c = nengo.Connection(e, model.bg.input, function=lambda x: [0, 0, 0, 0])
    #    error_conn = nengo.Connection(error, model.bg.input,
    #                                      modulatory=True)
    #    c.learning_rule = nengo.PES(error_conn, learning_rate=0.2)

    for j, e in enumerate(model.vision.state.ensembles):
        c = nengo.Connection(e, model.bg2.input, function=lambda x: [0, 0, 0, 0])
        error_conn = nengo.Connection(error2, model.bg2.input,
                                          modulatory=True)
        c.learning_rule = nengo.PES(error_conn, learning_rate=0.2)




sim = nengo.Simulator(model)
sim.run(30)

import pylab
pylab.subplot(2,2,1)
pylab.plot(sim.data[pUtil])
pylab.subplot(2,2,2)
pylab.plot(sim.data[pThal])
pylab.subplot(2,2,3)
pylab.plot(sim.data[pUtil2])
pylab.subplot(2,2,4)
pylab.plot(sim.data[pThal2])
pylab.show()


