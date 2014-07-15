import nengo.spa as spa
import nengo
import numpy as np

D = 16

model = spa.SPA(label='hrl')
with model:
    model.state = spa.Buffer(D)
    model.motor = spa.Buffer(D)

    model.bg = spa.BasalGanglia(spa.Actions(
        '0.5 --> motor=A',
        '0.5 --> motor=B',
        '0.5 --> motor=C',
        '0.5 --> motor=D',
        ))
    model.thal = spa.Thalamus(model.bg)

    def in_state(t):
        return 'ABCD'[int(t / 0.2) % 4]
    model.input = spa.Input(state=in_state)

    pThal = nengo.Probe(model.thal.actions.output, synapse=0.01)
    pUtil = nengo.Probe(model.bg.input, synapse=0.01)


with model:
    def error_func(t, x):
        index = int(t / 0.2) % 4
        if t % 0.2 > 0.1:
            correct = np.eye(4)[index]
            error = correct - x
            print t, error
            return error
        return [0, 0, 0, 0]
    error = nengo.Node(error_func, size_in=4, size_out=4)
    error_pop = nengo.networks.EnsembleArray(100, 4)
    nengo.Connection(error, error_pop.input)
    nengo.Connection(model.bg.input, error)

    vocab = model.get_input_vocab('state')
    for i in range(4):
        t = vocab.parse('NONE%d' % i).v
        for j, e in enumerate(model.state.state.ensembles):
            t0 = t[j*e.dimensions: (j+1)*e.dimensions]
            c = nengo.Connection(e, model.bg.input, function=lambda x: [0, 0, 0, 0])#, transform=[t0])
            error_conn = nengo.Connection(error_pop.ensembles[i], model.bg.input[i],
                                          modulatory=True)
            c.learning_rule = nengo.PES(error_conn, learning_rate=2.0)


sim = nengo.Simulator(model)
sim.run(2.0)

import pylab
pylab.subplot(2,1,1)
pylab.plot(sim.data[pUtil])
pylab.subplot(2,1,2)
pylab.plot(sim.data[pThal])
pylab.show()


