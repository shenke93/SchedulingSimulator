import simpy
def example(env):
    value = yield env.timeout(1, value=42)
    print('now=%d, value=%d' % (env.now, value))
    
env = simpy.Environment()
p = env.process(example(env))
env.run()
