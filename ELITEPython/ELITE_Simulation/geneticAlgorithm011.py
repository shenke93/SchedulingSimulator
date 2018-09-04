'''Version 0.1.1
Features: 1. Add failure profile for each hour (like price)
          2. Choose job sequence of VL0601 as example
'''

import sys
import numpy as np
import csv
import itertools
import time
from datetime import timedelta, datetime

DNA_SIZE = 5    
POP_SIZE = 4   
CROSS_RATE = 0.3
MUTATION_RATE = 0.2
N_GENERATIONS = 30

def ceil_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt

def floor_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt

def get_energy_cost(indiviaual, start_time, job_dict, price_dict):
    ''' Give an individual (a possible schedule in our case), calculate its energy cost '''
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
#         print("\nFor job: %d" % item)
        t_start = t_now
#         print("Time start: " + str(t_now))
        unit = job_dict.get(item, -1)
        if unit == -1:
            raise ValueError("No matching item in the job dict.")
        du = unit[0] # get job duration
        po = unit[1] # get job power profile
        t_end = t_start + timedelta(hours=du)
#         print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start up
        t_ed = floor_dt(t_end, timedelta(hours=1)) #    t_end down
        t_sd = floor_dt(t_now, timedelta(hours=1))
#         print("Ceil time start to the next hour:" + str(t_u))
#         print("Floor time end to the previous hour:" + str(t_d))
        if price_dict.get(t_sd, 0) == 0 or price_dict.get(t_ed, 0) == 0:
            raise ValueError("In boundary conditions, no matching item in the price dict.")
        tmp = price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) +  price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))
#         print("Head price: %f" % price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0))
#         print("Tail price: %f" % price_dict.get(t_d, 0))
#         print("Head and tail cost: %f" % tmp)
        step = timedelta(hours=1)
        while t_su < t_ed:
            if price_dict.get(t_su, 0) == 0:
                raise ValueError("No matching item in the price dict.")
            energy_cost += price_dict.get(t_su, 0) * po
            t_su += step
        
        energy_cost += tmp * po
        t_now = t_end
    
    return energy_cost

def locate_min(a):
    ''' Find the smallest value of a list and all its indexes.
    '''
    smallest = min(a)
    return smallest, [index for index, element in enumerate(a) 
                      if smallest == element]
    
class GA(object):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size):
        self.dna_size = dna_size
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        
        self.pop = np.vstack([np.random.permutation(range(1, dna_size+1)) for _ in range(pop_size)]) # Job index start from 1 instead of 0
        
    def get_fitness(self, pred):
        ''' Calculate the fitness of every individual in a generation.
        Simple strategy: Since we want to find the schedule with minimum cost, find the distance between max value and current value
        Possible alternative: TODO: using exponential function as possibility for selection
        '''
        return np.max(pred) + 1e-3 - pred
    
    def select(self, fitness):
        ''' Nature selection with individuals' fitnesses.
        '''
        idx = np.random.choice(np.arange(self.pop_size), size=self.pop_size, replace=True, p = fitness/fitness.sum())
#         print("idx:", idx)
        return self.pop[idx] 
    
    def crossover(self, parent, pop):
        ''' Crossover uses two individuals to create their child. Avoid repeated jobs in each individual.
        '''
        if np.random.rand() < CROSS_RATE:
            i_ = np.random.randint(0, POP_SIZE,size=1) # select another individual from pop
#             print("i_: ", i_)
            cross_points = np.random.randint(0, 2, DNA_SIZE).astype(np.bool) # choose crossover points
            keep_job = parent[~cross_points]
#             print("keep_city: ", keep_city)
#             print("pop[i_]: ", pop[i_])
#             print("choose: ", np.isin(pop[i_].ravel(), keep_city, invert=True))
            swap_job = pop[i_, np.isin(pop[i_].ravel(), keep_job, invert=True)]
            parent[:] = np.concatenate((keep_job, swap_job))
        return parent
    
    def mutate(self, child):
        ''' Find two different points of DNA, change their order. 
        '''
        for point in range(DNA_SIZE):
            if np.random.rand() < MUTATION_RATE:
                swap_point = np.random.randint(0, DNA_SIZE)
                swap_A, swap_B = child[point], child[swap_point]
                child[point], child[swap_point] = swap_B, swap_A
        return child
    
    def evolve(self, fitness):
        pop = self.select(fitness)
        pop_copy = pop.copy()
        for parent in pop:
            child = self.crossover(parent, pop_copy)
            child = self.mutate(child)
            parent[:] = child
        self.pop = pop
        
if __name__ == '__main__':
    
    start_time = datetime(2016, 11, 7, 1, 0)
    price_dict = {}
    job_dict = {}
    
    ''' Input: Energy price
        Input file: price_ga.csv
        Format: date(date), price(float)
        Output: price_dict: key = Date, value = Price
    '''
    try:
        with open('price.csv', encoding='utf-8') as price_csv:
            reader = csv.DictReader(price_csv)
            for row in reader:
                price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})
    except:
        print("Unexpected error when reading energy price:", sys.exc_info()[0]) 
        exit()

    ''' Input: List of jobs (original schedule)
        Input file: jobInfo_ga.csv
        Format: index(int), duration(float), power(float)
        Output: job_dict: key = JobID, value = [Duration, Power]
    '''
    try:
        with open('jobInfoPack_ga.csv', encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                job_dict.update({int(row['ID']):[float(row['Duration']), float(row['Power'])]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
     
#     print(price_dict)        
#     print(job_dict)        
 
    ''' Input: List of maintenance events: timestamp when maintenance is evaluated
        Output: health_dict: key = Date, value = health
    '''
    # Input maintenance influence
    maintenance_influence = []
    try:
        with open('maintenanceInfluence.csv', encoding='utf-8') as mainInf_csv:
            reader = csv.DictReader(mainInf_csv)
            for row in reader:
                maintenance_influence.append(float(row['Influence']))
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    
#     print(maintenance_influence)
  
    # Maintenance events: 
    health_dict = {}
    for key in price_dict:
        health_dict.update({key:0})
    for key in price_dict:
        if key.weekday() == 5 and key.hour == 0:    #    Find all Saturdays
            for i in range(24):
                health_dict.update({key+timedelta(hours=(i-12)):maintenance_influence[i]})  
    
#     for key in health_dict:
#         if health_dict.get(key) != 0:
#             print(key)

    exit()
    '''Optimization possibility 1: Add maintenance events.
        Rules: 1. 
    '''
    
    '''Optimization possibility 2: From Xu's paper, machine different power states.
        Rules: 
    '''
    
    ''' Optimization possibility 3: Job with different power profile.
    '''
    ts = time.time()
    elite_cost = float('inf')
    elite_schedule = []
    ga = GA(dna_size=DNA_SIZE, cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE)
    for generation in range(N_GENERATIONS):
        cost = [get_energy_cost(i, start_time, job_dict, price_dict) for i in ga.pop]
        fitness = ga.get_fitness(cost)
    
        best_idx = np.argmax(fitness)
        print('Gen:', generation, '| best fit %.2f' % fitness[best_idx])
        print("Most fitted DNA: ", ga.pop[np.argmax(fitness)])
        print("Most fitted cost: ", cost[np.argmax(fitness)])
        
        if cost[np.argmax(fitness)] < elite_cost:
            elite_cost = cost[np.argmax(fitness)]
            elite_schedule = ga.pop[np.argmax(fitness)]
        
        ga.evolve(fitness)
    
    print()
    original_schedule = [1, 2, 3, 4, 5]        
    print("Original schedule: ", original_schedule)
    print("Original cost: ", get_energy_cost(original_schedule, start_time, job_dict, price_dict))
    print("Elite schedule: ", elite_schedule)
    print("Elite cost:", elite_cost)
    te = time.time()
    print("Time consumed: ", te - ts)
    
    ''' Compare with the brute force method
    '''
    print()
    
    ts = time.time()
    print("Brute force method: ")
    space = list(itertools.permutations(range(1, 6)))
    costs = [get_energy_cost(item, start_time, job_dict, price_dict) for item in space]
    print("Minimal cost: ", locate_min(costs)[0])
    best_schedules = locate_min(costs)[1]   # print all possible schedules
    for i in best_schedules:
        print("Best schedule: ", space[i]) 
    te = time.time()
    print("Time consumed: ", te - ts)