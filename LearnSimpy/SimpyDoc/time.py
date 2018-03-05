import time
import simpy

def example(env):
    start = time.perf_counter()
    yield env.timeout(1)
    # end = time.perf_counter()
    end = env.now
    print('Duration of one simulation time unit: %.2fs' % (end - start))

env = simpy.rt.RealtimeEnvironment(factor=0.1)
proc = env.process(example(env))
env.run(until=proc)