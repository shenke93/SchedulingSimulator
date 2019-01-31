'''Soubry schedulor version 0.0.0
    Features: 
    1. Runnable script from cmd.
    2. Rewrite functions, make better reuse of code. 
    3. Normalization of input/output.
'''
# Core modules
import sys
import csv
import collections
import argparse
from datetime import timedelta, datetime
from operator import add
# import pickle

# 3rd-party modules
import numpy as np

# Global variables
# POP_SIZE = 8   
# CROSS_RATE = 0.6
# MUTATION_RATE = 0.8
# N_GENERATIONS = 200

C1 = 10 # Used for failure cost calculation in run-down scenario
C2 = 30


def ceil_dt(dt, delta):
    ''' 
    Ceil a data time dt according to the measurement delta.

    Parameters
    ----------
    dt : datatime
        Objective date time to ceil.
    delta : timedelta
        Measurement precision.

    Returns
    -------
    Ceiled date time

    '''
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt


def floor_dt(dt, delta):
    ''' 
    Floor a data time dt according to the measurement delta.

    Parameters
    ----------
    dt : datatime
        Objective date time to floor.
    delta : timedelta
        Measurement precision.

    Returns
    -------
    Floored date time
    '''
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt

    
def read_down_durations(downDurationFile):
    ''' 
    Create a dictionary to restore down duration information.

    Parameters
    ----------
    downDurationFile: string
        Name of file containing job information.
    
    Returns
    -------
    A dictionary containing downtime duration indexes, startTime and endTime, key: int, value: list.
    '''
    down_duration_dict = {}
    try:
        with open(downDurationFile, encoding='utf-8') as downDurationInfo_csv:
            reader = csv.DictReader(downDurationInfo_csv)
            for row in reader:
                down_duration_dict.update({row['ID']:[datetime.strptime(row['StartDateUTC'], "%Y-%m-%d %H:%M:%S.%f"), 
                                                 datetime.strptime(row['EndDateUTC'], "%Y-%m-%d %H:%M:%S.%f")]})
    except:
        print("Unexpected error when reading down duration information:", sys.exc_info()[0])
        exit()
    return down_duration_dict


def select_from_range(dateRange1, dateRange2, dict, pos1, pos2):
    '''
    Select items of dict from a time range.
    
    Parameters
    ----------
    dateRange1: Date
        Start timestamp of the range.
    
    dateRange2: Date
        End timestamp of the range.
        
    dict: Dict
        Original dictionary.
        
    Returns
    -------
    A dict containing selected items.
    '''
    res_dict = collections.OrderedDict()
    for key, value in dict.items():
        if value[pos1] >= dateRange1 and value[pos2] <= dateRange2:
            res_dict.update({key:value})
    return res_dict


def read_product_related_characteristics(productFile):
    ''' 
    Create a dictionary to store product related characteristics from productFile.

    Parameters
    ----------
    productFile : string
        Name of file containing job information. Columns contained: Product, UnitPrice, Power.

    Returns
    -------
    Dictionary containing product related characteristics, key: string, value: list of float.
    '''
    product_related_characteristics_dict = {}
    try:
        with open(productFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                product_related_characteristics_dict.update({row['Product']:[round(float(row['UnitPrice']),3), float(row['Power']),
                                                            float(row['TargetProductionRate'])]})
    except:
        print("Unexpected error when reading product related information:", sys.exc_info()[0]) 
        exit()
    return product_related_characteristics_dict


# TODO: Depend on context of maintenance file
def read_failure_data(maintenanceFile):
    ''' 
    Create a list to store influences of maintenances. 

    Parameters
    ----------
    maintenanceFile: string
        Name of file containing maintenance records.
    
    Returns
    -------
    List containing influences of maintenances.
    '''
    maintenance_influence = []
    try:
        with open(maintenanceFile, encoding='utf-8') as mainInf_csv:
            reader = csv.DictReader(mainInf_csv)
            for row in reader:
                maintenance_influence.append(float(row['Influence']))
    except:
        print("Unexpected error when reading maintenance information:", sys.exc_info()[0]) 
        exit()
    
    # Create the health dict, failure rates are based on data.
    
#     for key in price_dict:
#         if key.weekday() == 5 and key.hour == 0:    #    Find all Saturday 00:00:00
#             for i in range(216):
#                 key1 = key+timedelta(hours=(i-96))
#                 health_dict.update({key1:maintenance_influence[i]})
#     
#     for key in price_dict:
#         if key.weekday() == 5 and key.hour == 0:    #    Find all Saturday 00:00:00
#             for i in range(216):
#                 key1 = key+timedelta(hours=(i-96))
#                 tmp = health_dict.get(key1, 0)
#                 if tmp == 0:
#                     health_dict.update({key1:maintenance_influence[i]}) 
#                 else:
#                     health_dict.update({key1:max(tmp, maintenance_influence[i])})
               
    return maintenance_influence


def read_price(priceFile):
    ''' 
    Create a dictionary to restore hourly dependent energy price.

    Parameters
    ----------
    priceFile: string
        Name of file containing energy price.
    
    Returns
    -------
    A dictionary containing hourly dependent energy price, key: Date, value: float.
    '''
    price_dict = {}
    try:
        with open(priceFile, encoding='utf-8') as price_csv:
            reader = csv.DictReader(price_csv)
            for row in reader:
                price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})
    except:
        print("Unexpected error when reading energy price:", sys.exc_info()[0]) 
        exit()
    return price_dict


def read_jobs(jobFile):
    ''' 
    Create a dictionary to restore job information.

    Parameters
    ----------
    jobFile: string
        Name of file containing job information.
    
    Returns
    -------
    A dictionary containing job indexes and characteristics, key: int, value: list.
    '''
    job_dict = {}
    try:
        with open(jobFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                job_dict.update({int(row['ID']):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"), 
                                                 datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"),
                                                 float(row['Quantity']), row['Product']]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return job_dict 


def get_hourly_failrue_dict(start_time, end_time, failure_list, down_duration_dict):
    ''' 
    Get the hourly failure rate between a determined start time and end time.
    '''
    hourly_failure_dict = {}
    t_sd = floor_dt(start_time, timedelta(hours=1)) # start time left border
    t_eu = ceil_dt(end_time, timedelta(hours=1)) # end time right border
    
    # Filtering down time, get all down durations longer than one hour
    down_duration_dict_filtered = collections.OrderedDict()
    for key, value in down_duration_dict.items():
        if (value[1] - value[0]) / timedelta(hours=1) >= 1:
            down_duration_dict_filtered.update({key:[floor_dt(value[0], timedelta(hours=1)), floor_dt(value[1], timedelta(hours=1))]})
    
#     print("down_duration_dict_filtered:", down_duration_dict_filtered)
    i = t_sd
    index=0
    for value in down_duration_dict_filtered.values():
        while i < value[0]:
            hourly_failure_dict.update({i:failure_list[index]})
            i = i + timedelta(hours=1)
            index = index+1
        while i <= value[1]:
            hourly_failure_dict.update({i:float(0)})
            i = i + timedelta(hours=1)
        index = 0
    
#     print("i:", i)
#     print("index:", index)
    
    while i <= t_eu:
        hourly_failure_dict.update({i:failure_list[index]})
        i = i + timedelta(hours=1)
        index = index+1
        
    return hourly_failure_dict


def get_failure_cost(indiviaual, start_time, job_dict, hourly_failure_dict, product_related_characteristics_dict, down_duration_dict, scenario):
    ''' 
    Calculate the falure cost of an individual.
 
    Parameters
    ----------
    individual: List
        A list of job indexes.
     
    start_time: Date
        Start time of the individual.
         
    job_dict: dict
        Dictionary of jobs.
         
    health_dict: dict
        Dictionary of houly dependent failure rates.
         
    product_related_characteristics_dict: dict
        Dictionary of product related characteristics.
     
    Returns
    -------
    The failure cost of an individual.
    '''
    if scenario == 1:  
        failure_cost = 0
        t_now = start_time
     
        for item in indiviaual:
            t_start = t_now
            unit1 = job_dict.get(item, -1)
            if unit1 == -1:
                raise ValueError("No matching item in job dict: ", item)
         
            product_type = unit1[4]    # get job product type
            quantity = unit1[3]  # get job quantity
             
    #         if du <= 1: # safe period of 1 hour (no failure cost)
    #             continue;
            unit2 = product_related_characteristics_dict.get(product_type, -1)
            if unit2 == -1:
                raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
            
            du = quantity / unit2[2] # get job duration
    #         print("Duration:", du)
            uc = unit2[0] # get job raw material unit price
             
            t_o = t_start + timedelta(hours=du) # Without downtime duration
    #         print("t_o:", t_o)
            t_end = t_o
            
            for key, value in down_duration_dict.items():
                # DowntimeDuration already added
                if t_end < value[0]:
                    continue
                if t_start > value[1]:
                    continue
                if t_start < value[0] < t_end:
                    t_end = t_end + (value[1]-value[0])
    #                 print("Line 429, t_end:", t_end)
                if t_start > value[0] and t_end > value[1]:
                    t_end = t_end + (value[1] - t_start)
                if t_start > value[0] and t_end < value[1]:
                    t_end = t_end + (t_end - t_start)
                else:
                    break
             
    #         t_start = t_start+timedelta(hours=1) # exclude safe period, find start of sensitive period
    #         t_end = t_start + timedelta(hours=(du-1)) # end of sensitive period
             
            t_su = ceil_dt(t_start, timedelta(hours=1)) #    t_start right border
            t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
            t_sd = floor_dt(t_start, timedelta(hours=1))  #    t_start left border
             
           
    #         if health_dict.get(t_sd, -1) == -1 or health_dict.get(t_ed, -1) == -1:
    #             raise ValueError("For item %d: In boundary conditions, no matching item in the health dict for %s or %s" % (item, t_sd, t_ed))
             
            tmp = (1 - hourly_failure_dict.get(t_sd, 0)) * (1 - hourly_failure_dict.get(t_ed, 0))
            step = timedelta(hours=1)
            while t_su < t_ed:
                if hourly_failure_dict.get(t_su, -1) == -1:
                    raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
                tmp *= (1-hourly_failure_dict.get(t_su, 0)) 
                t_su += step
    #         
    #         if product_related_characteristics_dict.get(product_type, -1) == -1:
    #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
            failure_cost += (1-tmp) * quantity * uc   
            t_now = t_end
    
    
    if scenario == 2:
        failure_cost = 0
        t_now = start_time
     
        for item in indiviaual:
            t_start = t_now
            unit1 = job_dict.get(item, -1)
            if unit1 == -1:
                raise ValueError("No matching item in job dict: ", item)
         
            product_type = unit1[4]    # get job product type
            quantity = unit1[3]  # get job quantity
             
    #         if du <= 1: # safe period of 1 hour (no failure cost)
    #             continue;
            unit2 = product_related_characteristics_dict.get(product_type, -1)
            if unit2 == -1:
                raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
            
            du = quantity / unit2[2] # get job duration
    #         print("Duration:", du)
    #         uc = unit2[0] # get job raw material unit price
             
            t_o = t_start + timedelta(hours=du) # Without downtime duration
    #         print("t_o:", t_o)
            t_end = t_o
             
            for key, value in down_duration_dict.items():
                # DowntimeDuration already added
        
                if t_end < value[0]:
                    continue
                if t_start > value[1]:
                    continue
                if t_start < value[0] < t_end:
                    t_end = t_end + (value[1]-value[0])
                    failure_cost += C1 + (value[1] - value[0]) / timedelta(hours=1) * C2
    #                 print("Line 429, t_end:", t_end)
                if t_start > value[0] and t_end > value[1]:
                    t_end = t_end + (value[1] - t_start)
                    failure_cost += C1 + (value[1] - t_start) / timedelta(hours=1) * C2
    
                if t_start > value[0] and t_end < value[1]:
                    t_end = t_end + (t_end - t_start)
                    failure_cost += C1 + (t_end- t_start) / timedelta(hours=1) * C2
                       
                else:
                    break
             
            t_now = t_end
         
    return failure_cost


def get_energy_cost(indiviaual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict):
    ''' 
    Calculate the energy cost of an individual.

    Parameters
    ----------
    individual: List
        A list of job indexes.
    
    start_time: Date
        Start time of the individual.
        
    job_dict: dict
        Dictionary of jobs.
        
    health_dict: dict
        Dictionary of houly dependent failure rates.
        
    product_related_characteristics_dict: dict
        Dictionary of product related characteristics.
    
    Returns
    -------
    The energy cost of an individual.
    '''
#     print("Line 401, downDurationIndex:", downDurationIndex)
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
#         print("For job:", item)
        t_start = t_now
#         print("Time start: " + str(t_now))
        unit1 = job_dict.get(item, -1)
        if unit1 == -1:
            raise ValueError("No matching item in the job dict for %d" % item)
       
        product_type = unit1[4] # get job product type
        quantity = unit1[3]
        
        unit2 = product_related_characteristics_dict.get(product_type, -1)
        if unit2 == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
       
        du = quantity / unit2[2] # get job duration
#         print("Duration:", du)
        po = unit2[1] # get job power profile
        
        t_o = t_start + timedelta(hours=du) # Without downtime duration
#         print("t_o:", t_o)
        t_end = t_o
        
        for key, value in down_duration_dict.items():
            # DowntimeDuration already added
            
            if t_end < value[0]:
                continue
            if t_start > value[1]:
                continue
            if t_start < value[0] < t_end:
                t_end = t_end + (value[1]-value[0])
#                 print("Line 429, t_end:", t_end)
            if t_start > value[0] and t_end > value[1]:
                t_end = t_end + (value[1] - t_start)
            if t_start > value[0] and t_end < value[1]:
                t_end = t_end + (t_end - t_start)
            
#         for key, value in down_duration_dict.items():
#         print("Job", item)
#         print('Line 416, du:', du)
#         t_end = t_start + timedelta(hours=du)
#         print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start right border
        t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        t_sd = floor_dt(t_start, timedelta(hours=1)) # t_start_left border
#         print("Ceil time start to the next hour:" + str(t_u))
#         print("Floor time end to the previous hour:" + str(t_d))
        if price_dict.get(t_sd, 0) == 0 or price_dict.get(t_ed, 0) == 0:
            raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
        tmp = price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) + price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))
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
    
#     print("Finish time:", t_now)
    return energy_cost


# def overlap(startA, endA, startB, endB):
#     # Test if two ranges overlap
#     return (startA <= endB) and (endA >= startB)


def visualize(individual, start_time, job_dict, product_related_characteristics_dict, down_duration_dict):
    # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
    detail_dict = {}
    t_now = start_time 
    
    for item in individual:
        t_start = t_now
        
        unit1 = job_dict.get(item, -1)
        product_type = unit1[4] # get job product type
        quantity = unit1[3] # get job objective quantity
        
        unit2 = product_related_characteristics_dict.get(product_type, -1)
        du = quantity / unit2[2] # get job duration
        
        t_o = t_start + timedelta(hours=du) # Without downtime duration
        t_end = t_o
    
        for key, value in down_duration_dict.items():
            # DowntimeDuration already added

            if t_end < value[0]:
                continue
            if t_start > value[1]:
                continue
            if t_start < value[0] < t_end:
                t_end = t_end + (value[1]-value[0])
#                 print("Line 429, t_end:", t_end)
            if t_start > value[0] and t_end > value[1]:
                t_end = t_end + (value[1] - t_start)
            if t_start > value[0] and t_end < value[1]:
                t_end = t_end + (t_end - t_start)
        
        detail_dict.update({item:[t_start, t_end, du]})
        t_now = t_end

    return detail_dict


def hamming_distance(s1, s2):
    ''' 
    Calculate the hamming distance (the number of positions at which the corresponding symbols are different) of two list.

    Parameters
    ----------
    s1: List
        A list of job indexes.
    
    s2: list
        A list of job indexes.
    
    Returns
    -------
    The hamming distance of two lists.
    '''
    assert len(s1) == len(s2)
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))
 
                
class GA(object):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict, failure_dict, 
                 product_related_characteristics_dict, down_duration_dict, start_time, weight1, weight2, scenario):
        # Attributes assignment
        self.dna_size = dna_size 
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.failure_dict = failure_dict
        self.product_related_characteristics_dict = product_related_characteristics_dict
        self.down_duration_dict = down_duration_dict
        self.start_time = start_time
        self.w1 = weight1
        self.w2 = weight2
        self.scenario = scenario
        # generate N random individuals (N = pop_size)
        self.pop = np.vstack([np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])
        
        self.memory = []
        
    def get_fitness(self, value1, value2):
        ''' Get fiteness values for all individuals in a generation.
        '''
        # There are 2 sub-objectives, the fitness is the sum of these two
        return list(map(add, value1, value2))
    
#     def select(self, fitness):
#         ''' Nature selection with individuals' fitnesses.
#         '''
#         idx = np.random.choice(np.arange(self.pop_size), size=self.pop_size, replace=True, p = fitness/fitness.sum())
# #         print("idx:", idx)
#         return self.pop[idx] 
    
    def crossover(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, the crossover result is used to represent the loser.
        '''
        # crossover for loser
        if np.random.rand() < self.cross_rate:
            cross_points = np.random.randint(0, 2, self.dna_size).astype(np.bool)
            keep_job =  winner_loser[1][~cross_points] # see the progress explained in the paper
            swap_job = winner_loser[0, np.isin(winner_loser[0].ravel(), keep_job, invert=True)]
            winner_loser[1][:] = np.concatenate((keep_job, swap_job))
        return winner_loser
    
    def mutate(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        '''
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            point, swap_point = np.random.randint(0, self.dna_size, size=2)
            swap_A, swap_B = winner_loser[1][point], winner_loser[1][swap_point]
            winner_loser[1][point], winner_loser[1][swap_point] = swap_B, swap_A 
        
        return winner_loser
        
    def evolve(self, n):
        ''' 
        Execution of the provided GA.

        Parameters
        ----------
        n: int
            Number of iteration times 
    
        Returns
        -------
        The hamming distance of two lists.
        '''
        i = 1
        while i <= n: # n is the number of evolution times in one iteration
            sub_pop_idx = np.random.choice(np.arange(0, self.pop_size), size=2, replace=False)
            sub_pop = self.pop[sub_pop_idx] # pick 2 individuals from pop
            
#             print('sub_pop', sub_pop)
            
            failure_cost = [self.w1*get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.product_related_characteristics_dict, self.down_duration_dict, self.scenario) for i in sub_pop]
            energy_cost = [self.w2*get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict) for i in sub_pop]
            fitness = self.get_fitness(failure_cost, energy_cost) # get the fitness values of the two
            
#             print('fitness', fitness)
            # Elitism Selection
            
            winner_loser_idx = np.argsort(fitness)
            
#             print('winner_loser_idx', winner_loser_idx)

            winner_loser = sub_pop[winner_loser_idx] # the first is winner and the second is loser
            
#             print('winner_loser', winner_loser)

            origin = sub_pop[winner_loser_idx][1] # pick up the loser for genetic operations

            # Crossover (of the winner and the loser)
            winner_loser = self.crossover(winner_loser)
            
            # Mutation (only on the child)
            winner_loser = self.mutate(winner_loser)
            
#             print('Winner_loser after crossover and mutate: ', winner_loser)
#             print('Winner', winner_loser[0])
#             print('Loser', winner_loser[1])
#             print('Origin2:', origin)
            
#             print(hamming_distance(origin, winner_loser[1]))
            # Distance evaluation:
            if hamming_distance(origin, winner_loser[1]) > (self.dna_size / 5):
            # Memory search：
                child = winner_loser[1]
                
#             print("Child:", child)           
#             print("Current memory:", self.memory)    
        
                flag = 0 # 0 means the new generated child is not in the memory  
                for item in self.memory:
                    if (item == child).all():
#                     print("In memory!")
                        flag = 1
                        break
                
                if flag == 0:
#                     print("Not in memory!")
                    if (len(self.memory) >= self.pop_size * 5):
                        self.memory.pop()
                    self.memory.append(child)
            
                    self.pop[sub_pop_idx] = winner_loser
                    i = i + 1 # End of procedure
                else:
                    pass
#                     print("In memory, start genetic operation again!")
            else:
                pass
#                 print("Distance too small, start genetic operation again!")
                
#         space = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in self.pop]
        
        failure_cost_space = [self.w1 * get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.product_related_characteristics_dict, self.down_duration_dict, self.scenario) for i in self.pop]
        energy_cost_space = [self.w2 * get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict) for i in self.pop]
        
#         print(self.start_time)
#         print(self.pop)
#         print(space)
#         print("failure_cost_space:", failure_cost_space)
#         print("energy_cost_space:", energy_cost_space)

        return self.pop, list(map(add, failure_cost_space, energy_cost_space))
      
        
if __name__ == '__main__':
    
    # Read parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("historical_down_periods_file", help="File containing records of historical down duration periods.") # downDurations.csv
    parser.add_argument("failure_rate_file", help="File containing failure rate of each hour from the failure model.") # hourly_failure_rate.csv
    parser.add_argument("product_related_characteristics_file", help="File containing product related characteristics.") # productRelatedCharacteristics.csv
    parser.add_argument("energy_price_file", help="File containing energy price of each hour.") # price.csv
    parser.add_argument("job_info_file", help="File containing job information.") # jobInfoProd_ga_013.csv
    parser.add_argument("scenario", type=int, help="Choose scenario: 1-MTBF 2-Machine stop/restart") # number of scenario
    parser.add_argument("pop_size", type=int, help="Population size") # pupulation size
    parser.add_argument("generations", type=int, help="Number of generations")
    parser.add_argument("crossover_rate", type=float, help="Crossover rate")
    parser.add_argument("mutation_rate", type=float, help="Mutation rate")
    args = parser.parse_args()
        
#     case 1 week
    ''' Use start_time and end_time to pick up a waiting job list from records.
        Available range: 2016-01-23 17:03:58.780 to 2017-11-15 07:15:20.500
    '''
    start_time = datetime(2016, 11, 3, 6, 0)
    end_time = datetime(2016, 11, 8, 0, 0)

#     case 2 years
#     start_time = datetime(2016, 1, 19, 14, 0)
#     end_time = datetime(2017, 11, 15, 0, 0)

    # Generate raw material unit price
    down_duration_dict = select_from_range(start_time, end_time, read_down_durations(args.historical_down_periods_file), 0, 1) # File from EnergyConsumption/InputOutput
    failure_list = read_failure_data(args.failure_rate_file) # File from failuremodel-master/analyse_production
    hourly_failure_dict = get_hourly_failrue_dict(start_time, end_time, failure_list, down_duration_dict)
    
    with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in hourly_failure_dict.items():
            writer.writerow([key, value])

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(args.product_related_characteristics_file)
    
    price_dict_new = read_price(args.energy_price_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py
    job_dict_new = select_from_range(start_time, end_time, read_jobs(args.job_info_file), 1, 2) # File from EnergyConsumption/InputOutput

    # TODO: change
#     print("failure_dict", failure_dict)
#     exit()
#     # write corresponding failure dict into file
#     with open('ga_013_failure_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in failure_dict_new.items():
#             writer.writerow([key, value])

    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule
    
#     print("Waiting jobs: ", waiting_jobs)
#     print("Prices: ", price_dict_new)
#     print("Failures: ", failure_dict_new)
    
    weight1 = 1
    weight2 = 1
    result_dict = {}
    original_schedule = waiting_jobs  
    result_dict.update({0: weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)+
                        weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
                                        product_related_characteristics_dict, down_duration_dict, args.scenario)}) # generation 0 is the original schedule
    
#     exit()
    ga = GA(dna_size=DNA_SIZE, cross_rate=args.crossover_rate, mutation_rate=args.mutation_rate, pop_size=args.pop_size, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            start_time = first_start_time, weight1=weight1, weight2=weight2, scenario=args.scenario)
      
    for generation in range(1, args.generations+1):
#         print("Gen: ", generation)
        pop, res = ga.evolve(1)          # natural selection, crossover and mutation
#         print("res:", res)
        best_index = np.argmin(res)
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
#         result_dict.update({generation:res[best_index]})
    
    # Used to store intermediate result for large-size problems
#     with open('IGAlarge.pkl', 'wb') as f:
#         pickle.dump(pop[best_index], f)

    print()      
    print("Candidate schedule", pop[best_index])
    candidate_schedule = pop[best_index]
    candidate_energy_cost = weight2 * get_energy_cost(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    candidate_failure_cost = weight1 * get_failure_cost(candidate_schedule, first_start_time, job_dict_new, hourly_failure_dict,
                                             product_related_characteristics_dict, down_duration_dict, scenario=args.scenario)

    print("Candidate energy cost:", candidate_energy_cost)
    print("Candidate failure cost:", candidate_failure_cost)
    print("Candidate total cost:", candidate_energy_cost+candidate_failure_cost)
    
#     print("Most fitted cost: ", res[best_index])

    print("\nOriginal schedule:", original_schedule)
#     print("DNA_SIZE:", DNA_SIZE) 
    print("Original schedule start time:", first_start_time)
    original_energy_cost = weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    original_failure_cost = weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
                                             product_related_characteristics_dict, down_duration_dict, args.scenario)
    print("Original energy cost: ", original_energy_cost)
    print("Original failure cost: ", original_failure_cost)
    print("Original total cost:", original_energy_cost+original_failure_cost)
    
    result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, product_related_characteristics_dict, down_duration_dict)
    result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, product_related_characteristics_dict, down_duration_dict)
#     print("Visualize_dict_origin:", result_dict)
#     print("Down_duration", down_duration_dict)

    # Output for visualization
    with open('executionRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict.items():
            writer.writerow([key, value[0], value[1], value[2]])
            
    with open('originalRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict_origin.items():
            writer.writerow([key, value[0], value[1], value[2]])
            
    with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in down_duration_dict.items():
            writer.writerow([key, value[0], value[1]])
    
#     print("Elite schedule: ", elite_schedule)
#     print("Elite cost:", elite_cost)
#     te = time.time()
#     print("Time consumed: ", te - ts)  

# write the result to csv for plot
#     with open('ga_013_analyse_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in result_dict.items():
#             writer.writerow([key, value])