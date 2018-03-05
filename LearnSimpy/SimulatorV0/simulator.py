import random
import simpy

RANDOM_SEED = 42

# Parameters of production time
PT_MEAN = 10.0         # Avg. processing time in minutes
PT_SIGMA = 2.0         # Sigma of processing time

# Parameters of machine breakdown
MTTF = 300.0           # Mean time to failure in minutes
BREAK_MEAN = 1 / MTTF  # Param. for expovariate distribution

# Parameters of operator
JOB_DURATION = 30.0 # Duration of an operator's other jobs

# Parameters of environment
WEEKS = 4              # Simulation time in weeks
SIM_TIME = WEEKS * 7 * 24 * 60  # Simulation time in minutes

def time_repair():
    """Return repairment time for a machine breakdown."""
    return 30.0

def time_per_product():
    """Return actual processing time for a job."""
    return random.normalvariate(PT_MEAN, PT_SIGMA)

def time_to_failure():
    """Return time until next failure for a machine."""
    return random.expovariate(BREAK_MEAN)

class Machine(object):
    """A machine produces parts and may get broken _EveryNode
    now and then. 
    Maintenance order or repairment can be added in the future.
    """
    
    def __init__(self, env, name, operator):
        self.env = env
        self.name = name
        self. products_done= 0
        self.broken = False
        
        # Start "working" and "breaking" processes for this machine
        self.process = env.process(self.working(operator))
        env.process(self.breaking())

    def working(self, operator):
        """ Produce products as long as simulation runs.
        While producing a product, the machine may break multiple times.
        """
        
        while True:
            # Start making a new product
            done_in = time_per_product()
            while done_in:
                try:
                    # working on the product
                    start = self.env.now
                    yield self.env.timeout(done_in)
                    done_in = 0 # Set to 0 to exit while loop
                    
                except simpy.Interrupt:
                    self.broken = True
                    done_in = self.env.now - start # Time left to produce a product
                    
                    # Request an operator.
                    with operator.request(priority = 1) as req:
                        yield req
                        yield self.env.timeout(time_repair())
                    
                    self.broken = False
            
            # Product is produced    
            self.products_done += 1
    
    def breaking(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(time_to_failure())
            if not self.broken:
                # Break the machine if it is currently working
                self.process.interrupt()
                
def other_jobs(env, operator):
    """The operator's other (unimportant) jobs."""
    while True:
        # Start a new job
        done_in = JOB_DURATION
        while done_in:
            # Retry the job until it is done
            # Its priority is lower than that of machine repairs
            with operator.request(priority=2) as req:
                yield req
                try:
                    start = env.now
                    yield env.timeout(done_in)
                    done_in = 0
                except simpy.Interrupt:
                    done_in = env.now - start
                    
# Setup and start the simulation
print('Mahcine shop')
random.seed(RANDOM_SEED)

# Create an environment and start the setup process
env = simpy.Environment()
operator = simpy.PreemptiveResource(env, capacity=1)
machines = [Machine(env, 'PL0063', operator), Machine(env, 'VL0601', operator)]
env.process(other_jobs(env, operator))

# Execute!
env.run(until=SIM_TIME)

# Analyis/results
print('Machine shop results after %s weeks' % WEEKS)
for machine in machines:
    print('%s made %d parts.' % (machine.name, machine.products_done))