'''Version 0.1.3
Features: 1. Add memory features
          2. Change mutation process
          3. Reuse all inputs of version 0.1.2, output in the new file
          4. Make unit production cost static
'''

import sys
import numpy as np
import csv
import time
from datetime import timedelta, datetime
from operator import add

POP_SIZE = 8   
CROSS_RATE = 0.6
MUTATION_RATE = 0.8
N_GENERATIONS = 100

def ceil_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt

def floor_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt

def read_material_price(productFile):
    raw_material_unit_price_dict = {}
    try:
        with open(productFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                # raw material price is between [1, 2] euro/kg
                raw_material_unit_price_dict.update({row['Product']:float(row['UnitPrice'])})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return raw_material_unit_price_dict

def read_maintenance(maintenanceFile, price_dict):
    ''' Input: List of maintenance events: timestamp when maintenance is evaluated
        Output: health_dict: key = Date, value = health
    '''
    # Input maintenance influence
    maintenance_influence = []
    try:
        with open(maintenanceFile, encoding='utf-8') as mainInf_csv:
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
    
    return health_dict

def select_maintenance(daterange1, daterange2, health_dict):
    dict = {}
    for key, value in health_dict.items():
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

def select_prices(daterange1, daterange2, price_dict):
    ''' Select prices between deterange1 and daterange2 form original price_dict and
    return a new dict.
    '''
    dict = {}
    for key, value in price_dict.items():
        if key >= daterange1 and key <= daterange2:
            dict.update({key:value})
    return dict

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
                                                 datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"), float(row['Power']),
                                                 row['Product'], float(row['Quantity'])]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return job_dict 

def select_jobs(daterange1, daterange2, job_dict):
    ''' Select jobs between daterange1 and daterange2 from original job_dict and
    return a new dict.
    '''
    dict = {}
    for key, value in job_dict.items():
        if value[1] >= daterange1 and value[2] <= daterange2:
            dict.update({key:value})
    return dict

def get_failure_cost(indiviaual, start_time, job_dict, health_dict, raw_material_unit_price_dict):
    ''' Given an individual (a possible schedule), calculate its failure cost '''
    failure_cost = 0
    t_now = start_time
    for item in indiviaual:
        t_start = t_now
        unit = job_dict.get(item, -1)
        if unit == -1:
            raise ValueError("No matching item in health dict: ", item)
        du = unit[0]    # get job duration
        product_type = unit[4]    # get job product type
        quantity = unit[5]  # get job quantity
        
        if du <= 1: # safe period of 1 hour (no failure cost)
            continue;
        
        t_start = t_start+timedelta(hours=1) # exclude safe period, find start of sensitive period
        t_end = t_start + timedelta(hours=(du-1)) # end of sensitive period
        
        t_su = ceil_dt(t_start, timedelta(hours=1)) #    t_start right border
        t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        t_sd = floor_dt(t_now, timedelta(hours=1))  #    t_start left border
        
        if health_dict.get(t_sd, -1) == -1 or health_dict.get(t_ed, -1) == -1:
            raise ValueError("For item %d: In boundary conditions, no matching item in the health dict for %s or %s" % (item, t_sd, t_ed))
        
        tmp = health_dict.get(t_sd, 0) +  health_dict.get(t_ed, 0)
        step = timedelta(hours=1)
        while t_su < t_ed:
            if health_dict.get(t_su, -1) == -1:
                raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
            tmp += health_dict.get(t_su, 0) 
            t_su += step
        
        if raw_material_unit_price_dict.get(product_type, -1) == -1:
            raise ValueError("For item %d: No matching item in the raw material unit price dict for %s" % (item, product_type))
        failure_cost += tmp * quantity * raw_material_unit_price_dict.get(product_type, 0)
        t_now = t_end
    
    return failure_cost

def get_energy_cost(indiviaual, start_time, job_dict, price_dict):
    ''' Give an individual (a possible schedule in our case), calculate its energy cost '''
#     print('Individual:', indiviaual)
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
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
    
class GA(object):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict, failure_dict, 
                 raw_material_unit_price_dict, start_time):
        self.dna_size = dna_size
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.failure_dict = failure_dict
        self.raw_material_unit_price_dict = raw_material_unit_price_dict
        self.start_time = start_time
        
#         self.pop = np.vstack([np.random.permutation(range(1, dna_size+1)) for _ in range(pop_size)]) # Job index start from 1 instead of 0
        self.pop = np.vstack([ np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])
        
    def get_fitness(self, value1, value2):
        ''' Calculate the fitness of every individual in a generation.
        '''
        return list(map(add, value1, value2))
    
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
#         for point in range(self.dna_size):
        if np.random.rand() < self.mutation_rate:
            point, swap_point = np.random.randint(0, self.dna_size, size=2)
#             print("swap_point: ", swap_point)
#             print("point: ", point)
            swap_A, swap_B = winner_loser[1][point], winner_loser[1][swap_point]
            winner_loser[1][point], winner_loser[1][swap_point] = swap_B, swap_A 
        
        return winner_loser
        
    def evolve(self, n):
        for _ in range(n): # randomly pick and compare n times
            sub_pop_idx = np.random.choice(np.arange(0, self.pop_size), size=2, replace=False)
            sub_pop = self.pop[sub_pop_idx] # pick 2 individuals from pop
#             print('Start_time:', self.start_time)
#             print('Sub_pop: ', sub_pop)
#             value = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in sub_pop]
            failure_cost = [get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.raw_material_unit_price_dict) for i in sub_pop]
            energy_cost = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in sub_pop]
#             fitness = self.get_fitness(value)
            fitness = self.get_fitness(failure_cost, energy_cost)
#             print('Fitness: ', fitness)
            winner_loser_idx = np.argsort(fitness)
            winner_loser = sub_pop[winner_loser_idx] # the first is winner and the second is loser
#             print('Winner_loser: ', winner_loser)
            winner_loser = self.crossover(winner_loser)
            winner_loser = self.mutate(winner_loser)
#             print('Winner_loser after crossover and mutate: ', winner_loser)
            self.pop[sub_pop_idx] = winner_loser
        
#         space = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in self.pop]
        failure_cost_space = [get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.raw_material_unit_price_dict) for i in self.pop]
        energy_cost_space = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in self.pop]
        print(self.start_time)
#         print(self.pop)
#         print(space)
        return self.pop, list(map(add, failure_cost_space, energy_cost_space))
        
if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-23 17:03:58.780 to 2017-11-15 07:15:20.500
    '''
    start_time = datetime(2016, 1, 23, 17, 0)
    end_time = datetime(2017, 12, 29, 8, 0)
    
    # Generate raw material unit price
    raw_material_unit_price_dict = read_material_price("productPack_ga_013.csv")
    
#     print(raw_material_unit_price_dict)
#     exit()
    
    price_dict_new = read_price("price.csv")
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfoPack_ga_012.csv"))

#     print(job_dict_new)
#     exit()

    failure_dict_new = read_maintenance("maintenanceInfluence.csv", price_dict_new)
    
    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule
    
#     print("Waiting jobs: ", waiting_jobs)
#     print("Prices: ", price_dict_new)
#     print("Failures: ", failure_dict_new)

#     exit()
    
    '''Optimization possibility 1: Add maintenance events.

       Optimization possibility 2: Job with different power profile.
    '''
#     ts = time.time()
#     elite_cost = float('inf')
#     elite_schedule = []
    result_dict = {}
    original_schedule = waiting_jobs  
    result_dict.update({0:get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new)+
                        get_failure_cost(original_schedule, first_start_time, job_dict_new, 
                                         failure_dict_new, raw_material_unit_price_dict)})
#     ga = GA(dna_size=DNA_SIZE, cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, pop = waiting_jobs,
#             job_dict=job_dict_new, price_dict=price_dict_new, failure_dict = failure_dict_new, 
#             raw_material_unit_price_dict = raw_material_unit_price_dict, start_time = first_start_time)
#      
#     for generation in range(1, N_GENERATIONS+1):
#         print("Gen: ", generation)
#         pop, res = ga.evolve(8)          # natural selection, crossover and mutation
#         best_index = np.argmin(res)
# #         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
#         result_dict.update({generation:res[best_index]})
    

     
    print()      
    print("Original schedule: ", original_schedule)
    print("Original schedule start time:", first_start_time)
    print("DNA_SIZE: ", DNA_SIZE) 
    original_energy_cost = get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new)
    original_failure_cost = get_failure_cost(original_schedule, first_start_time, job_dict_new, 
                                             failure_dict_new, raw_material_unit_price_dict)
    print("Original energy cost: ", original_energy_cost)
    print("Original failure cost: ", original_failure_cost)
    print("Original total cost:", original_energy_cost+original_failure_cost)

#     print("Elite schedule: ", elite_schedule)
#     print("Elite cost:", elite_cost)
#     te = time.time()
#     print("Time consumed: ", te - ts)  

# write the result to csv for plot
    with open('ga_013_analyse_plot.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict.items():
            writer.writerow([key, value])