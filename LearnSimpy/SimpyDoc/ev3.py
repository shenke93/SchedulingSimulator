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
            print('Estimated driving time: %d' % p)
            yield env.timeout(p)
            
            # Park for 1 hour
            print('Start parking at', env.now)
            charging = env.process(self.bat_ctrl(env))
            print('Estimated parking time: 60')
            parking = env.timeout(60)
            yield charging | parking
            if not charging.triggered:
                # Interrupt chaging if not already done
                charging.interrupt('Need to go!')
            print('Stop parking at', env.now)
            
    def bat_ctrl(self, env):
        print('Bat. ctrl. started at', env.now)
        try:
            p = randint(60, 90)
            print('Estimated charging time:', p)
            yield env.timeout(p)
            print('Bat. ctrl. done at', env.now)
        except simpy.Interrupt as i:
            # Got interrupted before the charging was done
            print('Bat. ctrl. interrupted at', env.now, 'msg:', i.cause)
    

env = simpy.Environment()
ev = EV(env)
env.run(until=100)
            
            
            