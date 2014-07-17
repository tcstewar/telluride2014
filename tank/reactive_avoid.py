import nengo

from reactive_minimal import *

with model:
    prox = nengo.Ensemble(300, 3, label='proximity')

    nengo.Connection(tank[:3], prox)

    def explore(x):

        scale = 2
        speed = max(0.6 - scale*sum(x), 0)
        print 'explore', speed
        return [speed, speed]
    nengo.Connection(prox, motor, function=explore)

    def avoid_left(x):
        scale = 2
        print 'aleft', scale*x[0]
        return [-scale*x[0], scale*x[0]]
    nengo.Connection(prox, motor, function=avoid_left)

    def avoid_right(x):
        scale = 2
        z = x[2] + 0.5* x[1]
        print 'aright', scale*z
        return [scale*z, -scale*z]
    nengo.Connection(prox, motor, function=avoid_right)

    def back_away(x):
        scale = 2
        print 'back', scale*x[1]
        return [-scale*x[1], -scale*x[1]]
    nengo.Connection(prox, motor, function=back_away)


if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run(1000)
