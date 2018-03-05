import simpy

class School:
    def __init__(self, env):
        self.env = env
        self.class_ends = env.event()
        self.bell_proc = env.process(self.bell())
        
        self.pupil_procs = [env.process(self.pupil()) for i in range(3)]
        # self.pupil_procs = env.process(self.pupil())
        print(self.pupil_procs)
        
    def bell(self):
        for i in range(2):
            print('bell step %d' % i)
            yield self.env.timeout(45)
            print('45 minutes')
            self.class_ends.succeed()
            self.class_ends = self.env.event()
            print()
            
    def pupil(self):
        print('Run process pupil', end='')
        for i in range(2):
            print('pupil step %d' % i, end='')
            print(' \o/', end='')
            print()
            yield self.class_ends
           
    
env = simpy.Environment();    
school = School(env)
env.run()