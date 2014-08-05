import nengo.spa as spa
import nengo
import numpy as np

D = 16

model = spa.SPA(label='rl')
with model:
    model.state = spa.Buffer(D)
    model.motor = spa.Buffer(D)

    # the basic actions, starting with 0 utility
    model.bg = spa.BasalGanglia(spa.Actions(
        '0 --> motor=A',
        '0 --> motor=B',
        '0 --> motor=C',
        '0 --> motor=D',
        ))
    model.thal = spa.Thalamus(model.bg)

    def in_state(t):
        return 'ABCD'[int(t / 0.2) % 4]
    model.input = spa.Input(state=in_state)

    pThal = nengo.Probe(model.thal.actions.output, synapse=0.01)
    pUtil = nengo.Probe(model.bg.input, synapse=0.01)


# build the learning connections and the learning signal
#  (this should eventually become some sort of helper function inside spa)
with model:
    # compute the error signal
    def error_func(t, x):
        util = x[:4]  # the current utility of each action
        act = x[4:]   # the information as to what the thalamus is selecting

        index = int(t / 0.2) % 4  # the correct answer
        chosen_index = list(act).index(max(act))
        if chosen_index == index:
            # if you got it right, drive the utility of the chosen action
            # towards 1, and the others towards 0
            error = np.eye(4)[chosen_index] - util
        else:
            # if you got it wrong, drive the utility of the chosen action
            # towards 0, and the others towards 1
            error = (1-np.eye(4)[chosen_index]) - util

        if t % 0.2 > 0.1:
            # print some debugging info
            print t,
            print ','.join(['%1.2f' % x for x in util]),
            print ','.join(['%1.2f' % x for x in error])
            return error
        return [0, 0, 0, 0]
    error = nengo.Node(error_func, size_in=8, size_out=4)
    nengo.Connection(model.bg.input, error[:4])
    nengo.Connection(model.thal.actions.output, error[4:])

    # now make connections from state to bg.input that initially just have
    # a fixed utility of 0.5, but get a learning signal from the error Node
    # that should make it learn the correct answer
    for j, e in enumerate(model.state.state.ensembles):
        c = nengo.Connection(e, model.bg.input, function=lambda x: [0.5, 0.5, 0.5, 0.5])
        error_conn = nengo.Connection(error, model.bg.input,
                                          modulatory=True)
        c.learning_rule = nengo.PES(error_conn, learning_rate=0.2)

if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run(20)

    import pylab
    pylab.subplot(2,1,1)
    pylab.plot(sim.data[pUtil])
    pylab.subplot(2,1,2)
    pylab.plot(sim.data[pThal])
    pylab.show()


