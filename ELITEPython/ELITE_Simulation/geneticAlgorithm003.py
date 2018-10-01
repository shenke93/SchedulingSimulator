''' Version 0.0.3
Features: 1. Idea: make sure the next generation has better performance, keep the elitism
          2. In function evolve(), we find the loser and winner from each selection:
          crossover part of winner into loser (try to make loser better?), also mutate loser
'''

import sys
import numpy as np
import csv
import time
from datetime import timedelta, datetime


# DNA_SIZE = 5    
POP_SIZE = 8   
CROSS_RATE = 0.5
MUTATION_RATE = 0.8
N_GENERATIONS = 20

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
            raise ValueError("No matching item in the job dict for %d" % item)
        du = unit[0] # get job duration
        po = unit[3] # get job power profile
        t_end = t_start + timedelta(hours=du)
#         print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start up
        t_ed = floor_dt(t_end, timedelta(hours=1)) #    t_end down
        t_sd = floor_dt(t_now, timedelta(hours=1))
#         print("Ceil time start to the next hour:" + str(t_u))
#         print("Floor time end to the previous hour:" + str(t_d))
        if price_dict.get(t_sd, 0) == 0 or price_dict.get(t_ed, 0) == 0:
            raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
        tmp = price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) +  price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))
#         print("Head price: %f" % price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0))
#         print("Tail price: %f" % price_dict.get(t_d, 0))
#         print("Head and tail cost: %f" % tmp)
        step = timedelta(hours=1)
        while t_su < t_ed:
            if price_dict.get(t_su, 0) == 0:
                raise ValueError("For item %d: No matching item in the price dict for %s" % (item, t_su))
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

def select_jobs(daterange1, daterange2, job_dict):
    ''' Select jobs between daterange1 and daterange2 from original job_dict and
    return a new dict.
    '''
    dict = {}
    for key, value in job_dict.items():
        if value[1] >= daterange1 and value[2] <= daterange2:
            dict.update({key:value})
    return dict
        
        
def select_prices(daterange1, daterange2, price_dict):
    ''' Select prices between deterange1 and daterange2 form original price_dict and
    return a new dict.
    '''
    dict = {}
    for key, value in price_dict.items():
        if key >= daterange1 and key <= daterange2:
            dict.update({key:value})
    return dict

def read_price(priceFile):
    price_dict = {}
    
    ''' Input: Energy price
        Input file: price_ga.csv
        format: date(date), price(float)
    '''
    try:
        with open(priceFile, encoding='utf-8') as price_csv:
            reader = csv.DictReader(price_csv)
            for row in reader:
                price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})
    except:
        print("Unexpected error when reading energy price:", sys.exc_info()[0]) 
        exit()
    return price_dict

def read_job(jobFile):
    job_dict = {}
    
    ''' Input: List of jobs (original schedule)
        Input file: jobInfo_ga.csv
        format: index(int), duration(float), power(float)
    '''
    try:
        with open(jobFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                job_dict.update({int(row['ID']):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"), 
                                                 datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"), float(row['Power'])]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return job_dict 

class GA(object):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict, start_time):
        self.dna_size = dna_size
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.start_time = start_time
        
#         self.pop = np.vstack([np.random.permutation(range(1, dna_size+1)) for _ in range(pop_size)]) # Job index start from 1 instead of 0
        self.pop = np.vstack([ np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])
        
    def get_fitness(self, value):
        ''' Calculate the fitness of every individual in a generation.
        '''
        return value
    
    def select(self, fitness):
        ''' Nature selection with individuals' fitnesses.
        '''
        idx = np.random.choice(np.arange(self.pop_size), size=self.pop_size, replace=True, p = fitness/fitness.sum())
#         print("idx:", idx)
        return self.pop[idx] 
    
    def crossover(self, winner_loser): # crossover for loser
        if np.random.rand() < self.cross_rate:
            cross_points = np.random.randint(0, 2, self.dna_size).astype(np.bool)
            keep_job =  winner_loser[1][~cross_points]
#             print("keep_job: ", keep_job)
#             print("choose: ", np.isin(winner_loser[0].ravel(), keep_job, invert=True))
            swap_job = winner_loser[0, np.isin(winner_loser[0].ravel(), keep_job, invert=True)]
            winner_loser[1][:] = np.concatenate((keep_job, swap_job))
        return winner_loser
    
    def mutate(self, winner_loser): # mutation for loser
        for point in range(self.dna_size):
            if np.random.rand() < self.mutation_rate:
                swap_point = np.random.randint(0, self.dna_size)
#                 print("swap_point: ", swap_point)
                swap_A, swap_B = winner_loser[1][point], winner_loser[1][swap_point]
                winner_loser[1][point], winner_loser[1][swap_point] = swap_B, swap_A 
        return winner_loser
        
    def evolve(self, n):
        for _ in range(n): # randomly pick and compare n times
            sub_pop_idx = np.random.choice(np.arange(0, self.pop_size), size=2, replace=False)
            sub_pop = self.pop[sub_pop_idx] # pick 2 individuals from pop
#             print('Sub_pop: ', sub_pop)
            value = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in sub_pop]
            fitness = self.get_fitness(value)
#             print('Fitness: ', fitness)
            winner_loser_idx = np.argsort(fitness)
            winner_loser = sub_pop[winner_loser_idx] # the first is winner and the second is loser
#             print('Winner_loser: ', winner_loser)
            winner_loser = self.crossover(winner_loser)
            winner_loser = self.mutate(winner_loser)
#             print('Winner_loser after crossover and mutate: ', winner_loser)
            self.pop[sub_pop_idx] = winner_loser
        
        space = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in self.pop]
#         print(self.start_time)
#         print(self.pop)
#         print(space)
        return self.pop, space
    
if __name__ == '__main__':
    
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    start_time = datetime(2016, 1, 19, 14, 0)
    end_time = datetime(2017, 11, 15, 8, 0)
    
#     price_dict = {}
#     job_dict = {}
#     
#     ''' Input: Energy price
#         Input file: price_ga.csv
#         format: date(date), price(float)
#     '''
#     try:
#         with open('price.csv', encoding='utf-8') as price_csv:
#             reader = csv.DictReader(price_csv)
#             for row in reader:
#                 price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})
#     except:
#         print("Unexpected error when reading energy price:", sys.exc_info()[0]) 
#         exit()
# 
#     ''' Input: List of jobs (original schedule)
#         Input file: jobInfo_ga.csv
#         format: index(int), duration(float), power(float)
#     '''
#     try:
#         with open('jobInfo.csv', encoding='utf-8') as jobInfo_csv:
#             reader = csv.DictReader(jobInfo_csv)
#             for row in reader:
#                 job_dict.update({int(row['ID']):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"), 
#                                                  datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"), float(row['Power'])]})
#     except:
#         print("Unexpected error when reading job information:", sys.exc_info()[0]) 
#         exit()
     
#     print(price_dict)        
#     print(job_dict)        
    
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfo.csv"))
    price_dict_new = select_prices(start_time, end_time, read_price("price.csv"))
    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule
    
    print("Waiting jobs: ", waiting_jobs)
    print("Prices: ", price_dict_new)

#     print(price_dict_new) 


    '''Optimization possibility 1: Add maintenance events.
        Rules: 1. 
    '''
    
    '''Optimization possibility 2: From Xu's paper, machine different power states.
        Rules: 
    '''
    
    ''' Optimization possibility 3: Job with different power profile.
    '''
    ts = time.time()
#     elite_cost = float('inf')
#     elite_schedule = []
    
    ga = GA(dna_size=DNA_SIZE, cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, start_time=first_start_time)
    for generation in range(N_GENERATIONS):
        print("Gen: ", generation)
        pop, res = ga.evolve(8)          # natural selection, crossover and mutation
        best_index = np.argmin(res)
        print("Most fitted DNA: ", pop[best_index])
        print("Most fitted cost: ", res[best_index])

    

     
    print()
    original_schedule = waiting_jobs        
    print("Original schedule: ", original_schedule)
    print("Original schedule start time:", first_start_time)
    print("DNA_SIZE: ", DNA_SIZE) 
    print("Original cost: ", get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new))
#     print("Elite schedule: ", elite_schedule)
#     print("Elite cost:", elite_cost)
    te = time.time()
    print("Time consumed: ", te - ts)
    
#     ''' Compare with the brute force method
#     '''
#     print()
#     r1 = waiting_jobs[0]
#     r2 = waiting_jobs[-1]
#     ts = time.time()
#     print("Brute force method: ")
#     space = list(itertools.permutations(range(r1, r2+1)))
#     costs = [get_energy_cost(item, start_time, job_dict, price_dict) for item in space]
#     print("Minimal cost: ", locate_min(costs)[0])
#     best_schedules = locate_min(costs)[1]   # print all possible schedules
#     for i in best_schedules:
#         print("Best schedule: ", space[i]) 
#     te = time.time()
#     print("Time consumed: ", te - ts)