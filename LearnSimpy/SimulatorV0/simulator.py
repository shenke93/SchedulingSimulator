import random
import simpy
import csv
import numpy

# RANDOM_SEED = 42

# Parameters of production time
PT_MEAN = 10.0         # Avg. processing time in minutes
PT_SIGMA = 2.0         # Sigma of processing time

# Parameters of machine breakdown
MTTF = 300.0           # Mean time to failure in minutes
BREAK_MEAN = 1 / MTTF  # Param. for expovariate distribution

# Parameters of environment
WEEKS = 4              # Simulation time in weeks
SIM_TIME = WEEKS * 7 * 24 * 60  # Simulation time in minutes

# Parameters of operator
JOB_DURATION = SIM_TIME # Duration of an operator's other jobs


down_prod = []
run_prod = []
down_pack = []
run_pack = []

def read_data(filename):
    """Read data from files"""
    result = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            result.append(int(row[1]))
        
    return result

def environment_setup():
    global down_prod
    down_prod = read_data('VL0601Down.csv')
    global run_prod
    run_prod = read_data('VL0601Run.csv')
    global down_pack
    down_pack = read_data('PL0063Down.csv')
    global run_pack
    run_pack = read_data('PL0063Run.csv')
    
def time_downtime(name):
    """Return down time for a machine breakdown."""
    # return 30.0
    if name == 'PL0063':
        return numpy.random.choice(down_prod)
    elif name == 'VL0601':
        return numpy.random.choice(down_pack)
    else:
        return 30.0

def time_per_product():
    """Return actual processing time for a job."""
    # return random.normalvariate(PT_MEAN, PT_SIGMA)
    return SIM_TIME

def time_to_failure(name):
    """Return time until next failure for a machine."""
    #return random.expovariate(BREAK_MEAN)
    if name == 'PL0063':
        return numpy.random.choice(run_prod)
    elif name == 'VL0601':
        return numpy.random.choice(run_pack)
    else:
        return random.expovariate(BREAK_MEAN)

class Machine(object):
    """A machine produces parts and may get broken _EveryNode
    now and then. 
    Maintenance order or repairment can be added in the future.
    """
    
    def __init__(self, env, name, operator):
        self.env = env
        self.name = name
        self.broken = False
        self.products_done = 0
        self.failure_time = 0
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
                    # self.available_time += done_in
                    done_in = 0 # Set to 0 to exit while loop
                    
                except simpy.Interrupt:
                    self.broken = True
                    done_in -= self.env.now - start # Time left to produce a product
                    
                    # Request an operator.
                    with operator.request(priority = 1) as req:
                        yield req
                        yield self.env.timeout(time_downtime(self.name))
                    
                    self.broken = False
            
            # Product is produced    
            self.products_done += 1
    
    def breaking(self):
        """Break the machine every now and then."""
        while True:
            time_failure = time_to_failure(self.name)
            yield self.env.timeout(time_failure)
            if not self.broken:
                # Break the machine if it is currently working
                self.failure_time += time_failure
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
print('Mahcine Shop Simulation of Soubry Case')
# random.seed(RANDOM_SEED)

# Create an environment and start the setup process

environment_setup()
env = simpy.Environment()
operator = simpy.PreemptiveResource(env, capacity=2)
machines = [Machine(env, 'PL0063', operator), Machine(env, 'VL0601', operator)]
env.process(other_jobs(env, operator))

# Execute!
env.run(until=SIM_TIME)

# Analyis/results
print('Machine shop results after %s weeks:' % WEEKS)
for machine in machines:
    print('%s made %d products, working rate is %.2f %%' % (machine.name, machine.products_done, 100 * (1 - machine.failure_time / SIM_TIME)))