from random import randint
import simpy

class EV:
    def __init__(self, env):
        self.env = env
        self.drive_proc = env.process(self.drive(env))
        
    def drive(self, env):
        while True:
            # Drive for 20-40 min
            p = randint(20, 40)
            print('Estimated Driving time: %d' % p)
            yield env.timeout(p)
            
            # Park for 1-6 hours
            print('Start parking at', env.now)
            charging = env.process(self.bat_ctrl(env))
            p = randint(60, 360)
            print('Estimated Parking time: %d' % p)
            parking = env.timeout(p)
            yield charging & parking
            print('Stop parking at', env.now)
    
    def bat_ctrl(self, env):
        print('Bat. ctrl. started at', env.now)
        
        # Intellingent charging behavior here
        p = randint(30, 90)
        print('Estimated Charging time: %d' % p)
        yield env.timeout(p)
        print('Bat. ctrl. done at', env.now)
        
env = simpy.Environment()
ev = EV(env)
env.run(until=310)