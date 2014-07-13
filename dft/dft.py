import numpy as np

N = 2000


v = np.linspace(-1, 1, 1000)
dv = 2.0/len(v)
def make_gaussian(centre, sigma):
    return np.exp(-(v-centre)**2/(2*sigma**2))

encoders = [make_gaussian(centre=np.random.uniform(-1, 1),
                          sigma=np.random.uniform(0.03, 0.07)) for i in range(N)]
encoders = np.array(encoders)

U, S, V = np.linalg.svd(encoders.T)
basis = U/(np.sqrt(dv))

bases = 40
basis = U[:,:bases]/(np.sqrt(dv))

def func_to_vector(f):
    return np.dot(f, basis)*dv
def vector_to_func(v):
    return np.dot(basis, v.T)

e_vector = func_to_vector(encoders)
for i in range(N):
    norm = np.linalg.norm(e_vector[i])
    e_vector[i]/=norm

x = [make_gaussian(centre=np.random.uniform(-1, 1),
                         sigma=np.random.uniform(0.1, 0.15)) for i in range(1000)]
x = np.array(x)
x_vector = func_to_vector(x)


def pulse_in(t):
    if t < 0.1:
        return func_to_vector(make_gaussian(centre=0, sigma=0.1))
    elif 0.2 < t < 0.3:
        return func_to_vector(make_gaussian(centre=0.25, sigma=0.1))

    else:
        return [0]*bases


import nengo
model = nengo.Network()
with model:
    input = nengo.Node(pulse_in)#func_to_vector(make_gaussian(centre=0, sigma=0.1)))
    a = nengo.Ensemble(N, bases, encoders=e_vector, eval_points=x_vector)
    nengo.Connection(input, a)
    nengo.Connection(a, a, synapse=0.1)
    probe = nengo.Probe(a, synapse=0.1)

sim = nengo.Simulator(model)

sim.run(0.8)

data = vector_to_func(sim.data[probe])

import pylab
pylab.imshow(data, aspect='auto')
#pylab.plot(v, data[:,-1])
pylab.show()


