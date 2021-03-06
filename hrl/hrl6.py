import nengo.spa as spa
import nengo
import numpy as np
import random

stims = []

def get_stim(index):
    while index >= len(stims):
        color = random.choice(['RED', 'BLUE', 'GREEN', 'GREEN'])
        shape = random.choice(['CIRCLE', 'SQUARE'])
        if color in ['RED', 'BLUE']:
            answer = dict(CIRCLE=0, SQUARE=1)[shape]
        else:
            answer = dict(CIRCLE=2, SQUARE=3)[shape]
        stims.append(('%s + %s' % (color, shape), answer, color, shape))
    return stims[index]

def get_input(index):
    return get_stim(index)[0]
def get_color(index):
    return get_stim(index)[2]
def get_shape(index):
    return get_stim(index)[3]
def get_answer(index):
    return get_stim(index)[1]


D = 16

model = spa.SPA(label='hrl')
with model:
    model.vision = spa.Buffer(D)
    model.state = spa.Buffer(D)
    model.color = spa.Buffer(D)
    model.task = spa.Buffer(D)
    model.motor = spa.Buffer(D)

    model.cortical = spa.Cortical(spa.Actions(
        'state=task',
        ))

    model.bg3 = spa.BasalGanglia(spa.Actions(
        '0.8 --> color = vision*~COLOR, state=vision*~SHAPE',
        '0.2 --> color = vision*~SHAPE, state=vision*~COLOR',
        ))
    model.thal3 = spa.Thalamus(model.bg3)


    model.bg = spa.BasalGanglia(spa.Actions(
        '0 --> motor=A',
        '0 --> motor=B',
        '0 --> motor=C',
        '0 --> motor=D',
        ))
    model.thal = spa.Thalamus(model.bg)

    model.bg2 = spa.BasalGanglia(spa.Actions(
        '0 --> task=W',
        '0 --> task=X',
        '0 --> task=Y',
        '0 --> task=Z',
        ))
    model.thal2 = spa.Thalamus(model.bg2)

    def in_color(t):
        index = int(t/0.2)
        return get_color(index)
    def in_state(t):
        index = int(t/0.2)
        return get_shape(index)

    def in_vision(t):
        index = int(t/0.2)
        return '%s*COLOR + %s*SHAPE' % (get_color(index), get_shape(index))


    #model.input = spa.Input(color=in_color, state=in_state)
    model.input = spa.Input(vision=in_vision)

    pThal = nengo.Probe(model.thal.actions.output, synapse=0.01)
    pUtil = nengo.Probe(model.bg.input, synapse=0.01)
    pThal2 = nengo.Probe(model.thal2.actions.output, synapse=0.01)
    pUtil2 = nengo.Probe(model.bg2.input, synapse=0.01)


with model:
    def error_func(t, x):
        util = x[:4]
        act = x[4:8]
        motor_act=x[8:]

        index = get_answer(int(t / 0.2))
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

    for j, e in enumerate(model.color.state.ensembles):
        c = nengo.Connection(e, model.bg2.input, function=lambda x: [0, 0, 0, 0])
        error_conn = nengo.Connection(error2, model.bg2.input,
                                          modulatory=True)
        c.learning_rule = nengo.PES(error_conn, learning_rate=0.2)


if __name__ == '__main__':

    sim = nengo.Simulator(model)
    sim.run(60)

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


