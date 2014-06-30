import nengo
import numpy as np

model = nengo.Network()
with model:
    input = nengo.Node(np.cos, label='input')
    a = nengo.Ensemble(100, 1, neuron_type=nengo.LIFRate(), label='a')

    data = []
    output = nengo.Node(lambda t, x: data.append(list(x)), size_in=1, label='output')

    nengo.Connection(input, a, transform=0.1)
    nengo.Connection(a, a, synapse=0.1)
    nengo.Connection(a, output)

sim = nengo.Simulator(model)

for c in model.connections:
    print 'connection from', c.pre.label, 'to', c.post.label
    if isinstance(c.pre, nengo.Ensemble):
        print '  decoders', sim.model.params[c].decoders
    print '  transform', nengo.utils.builder.full_transform(c, allow_scalars=False)
    if isinstance(c.post, nengo.Ensemble):
        print '  encoders', sim.model.params[c.post].encoders


sim.run(10)

import pylab
pylab.plot(data)
pylab.plot([input.output(t) for t in sim.trange()])
pylab.show()



