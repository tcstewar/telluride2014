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




# extract netlist

for ens in model.all_ensembles:
    print 'ens', id(ens), ens.label, ens.n_neurons, ens.dimensions
for node in model.all_nodes:
    print 'node', id(node), node.label, node.size_in, node.size_out
for conn in model.all_connections:
    print 'conn', id(conn.pre), id(conn.post), conn.function, nengo.utils.builder.full_transform(conn, allow_scalars=False)
