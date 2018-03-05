
def car(env):
    while True:
        print('Start parking at %d' % env.now)
        parking_duration = 5
        yield env.timeout(parking_duration)
        
        print('Start driving at %d' % env.now)
        trip_duration = 2
        yield env.timeout(trip_duration)

import simpy
env = simpy.Environment()
env.process(car(env))
until = 15
while env.peek() < until:
    input("Press Enter to continue...")
    env.step()
