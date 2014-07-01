import nengo
import numpy as np

D = 5
transform = np.random.randn(D,D)

model = nengo.Network()
with model:
    input = nengo.Node([0]*D, label='input')
    a = nengo.networks.EnsembleArray(64, D)
    b = nengo.networks.EnsembleArray(64, D)
    
    
    data = []
    output = nengo.Node(lambda t, x: data.append(list(x)), size_in=D, label='output')

    nengo.Connection(input, a.input)
    nengo.Connection(a.output, b.input, transform=transform)
    nengo.Connection(b.output, output)




# extract netlist

objs = model.all_ensembles + model.all_nodes
conns = model.all_connections
objs, conns = nengo.utils.builder.remove_passthrough_nodes(objs, conns)

for obj in objs:
    if isinstance(obj, nengo.Ensemble):
        print 'ens', id(obj), obj.label, obj.n_neurons, obj.dimensions
    else:
        print 'node', id(obj), obj.label, obj.size_in, obj.size_out
for conn in conns:
    print 'conn', id(conn.pre), id(conn.post), conn.function, nengo.utils.builder.full_transform(conn, allow_scalars=False)


import nengo_gui
gui = nengo_gui.Config()
gui[model].scale = 0.5779372197309416
gui[model].offset = 18.461883408071856,150.51569506726457
gui[input].pos = 50.000, 250.000
gui[input].scale = 1.000
gui[output].pos = 1125.000, 250.000
gui[output].scale = 1.000
gui[a].pos = 350.000, 250.000
gui[a].scale = 1.000
gui[a].size = 330.000, 380.000
gui[model.all_ensembles[0]].pos = 350.000, 100.000
gui[model.all_ensembles[0]].scale = 1.000
gui[model.all_ensembles[1]].pos = 350.000, 175.000
gui[model.all_ensembles[1]].scale = 1.000
gui[model.all_ensembles[2]].pos = 350.000, 250.000
gui[model.all_ensembles[2]].scale = 1.000
gui[model.all_ensembles[3]].pos = 350.000, 325.000
gui[model.all_ensembles[3]].scale = 1.000
gui[model.all_ensembles[4]].pos = 350.000, 400.000
gui[model.all_ensembles[4]].scale = 1.000
gui[a.input].pos = 225.000, 250.000
gui[a.input].scale = 1.000
gui[a.output].pos = 475.000, 250.000
gui[a.output].scale = 1.000
gui[b].pos = 825.000, 285.664
gui[b].scale = 1.000
gui[b].size = 330.000, 451.329
gui[model.all_ensembles[5]].pos = 825.000, 100.000
gui[model.all_ensembles[5]].scale = 1.000
gui[model.all_ensembles[6]].pos = 825.000, 175.000
gui[model.all_ensembles[6]].scale = 1.000
gui[model.all_ensembles[7]].pos = 825.000, 250.000
gui[model.all_ensembles[7]].scale = 1.000
gui[model.all_ensembles[8]].pos = 825.000, 325.000
gui[model.all_ensembles[8]].scale = 1.000
gui[model.all_ensembles[9]].pos = 726.445, 471.329
gui[model.all_ensembles[9]].scale = 1.000
gui[b.input].pos = 700.000, 250.000
gui[b.input].scale = 1.000
gui[b.output].pos = 950.000, 250.000
gui[b.output].scale = 1.000
