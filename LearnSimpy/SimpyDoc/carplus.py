class Car(object):
    def __init__(self, env):
        self.env = env
        # Start and run the process everytime an instance is created
        self.action = env.process(self.run())
        
    def run(self):
        while True:
            print('Start parking and charging at %d' % self.env.now)
            charge_duration = 5
            yield self.env.process(self.charge(charge_duration))
            
            print('Start driving at %d' % self.env.now)
            trip_duration = 2
            yield self.env.timeout(trip_duration)
            
    def charge(self, duration):
        # print('Charging start now!')
        yield self.env.timeout(duration)
        # print('Charging for %d hours, end!' % duration)
        
import simpy
env = simpy.Environment()
car = Car(env)
env.run(until=15)