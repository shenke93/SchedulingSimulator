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
import warnings
from datetime import timedelta, datetime
from operator import add
import operator
#import logging
import os
import math
import itertools
import time
import msvcrt
from population import Schedule
from collections import OrderedDict
from helperfunctions import JobInfo

# import pickle
# duration_str = 'quantity' 

# 3rd-party modules
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)
from sympy.printing.precedence import precedence

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
    tempdelta = dt - datetime.min
    if tempdelta % delta != 0:
        return dt + (delta - (tempdelta % delta))
    else:
        return tempdelta
    # q, r = divmod(dt - datetime.min, delta)
    # return (datetime.min + (q+1)*delta) if r else dt


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
    tempdelta = dt - datetime.min
    if tempdelta % delta != 0:
        return dt - (tempdelta % delta)
    else:
        return tempdelta
    # q, r = divmod(dt - datetime.min, delta)
    # return (datetime.min + (q)*delta) if r else dt

    
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
                start = datetime.strptime(row['StartDateUTC'], "%Y-%m-%d %H:%M:%S.%f")
                end = datetime.strptime(row['EndDateUTC'], "%Y-%m-%d %H:%M:%S.%f")
                duration = (end - start).total_seconds() / 3600
                down_duration_dict.update({row['ID']:[start, 
                                                      end,
                                                      duration]})
    except:
        print("Unexpected error when reading down duration information from '{}'".format(downDurationFile))
        raise
    return down_duration_dict


def read_breakdown_record(breakdownRecordFile):
    try:
        with open(breakdownRecordFile, encoding='utf-8') as breakdown_csv:
            reader = csv.DictReader(breakdown_csv)
            for row in reader:
                stamp = datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f")
    except:
        print("Unexpected error when reading breakdown record from {}:".format(breakdownRecordFile))
        raise
               
    return stamp


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
                job_entry = dict(zip(['unitprice', 'power', 'targetproduction'],
                [round(float(row['UnitPrice']),3), float(row['Power']), float(row['TargetProductionRate'])]))
                product_related_characteristics_dict.update({row['Product']: job_entry})
                if 'Type' in row:
                    product_related_characteristics_dict[row['Product']]['type'] = row['Type']
                    #print('Added type')
                if 'Availability' in row:
                    product_related_characteristics_dict[row['Product']]['availability'] = float(row['Availability'])
                if 'Downtime_len' in row:
                    product_related_characteristics_dict[row['Product']]['dt_len'] = float(row['Downtime_len'])

    except:
        print("Unexpected error when reading product related information from '{}'".format(productFile))
        raise
    return product_related_characteristics_dict


def read_precedence(precedenceFile):
    precedence_dict = {}
    try:
        with open(precedenceFile, encoding='utf-8') as prec_csv:
            reader = csv.DictReader(prec_csv)
            for row in reader:
                key = int(row['Before'])
#                 print(key)
                if key in precedence_dict: 
#                     print("In")
                    precedence_dict[key].append(int(row['After']))
                else:
#                     print("Not In")
                    precedence_dict.update({key:[int(row['After'])]})
    except:
        print("Unexpected error when reading precedence information from '{}'".format(precedenceFile)) 
        raise
    
#     print(precedence_dict)
    return precedence_dict

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
        print("Unexpected error when reading maintenance information from {}:".format(maintenanceFile))
        print(maintenanceFile)
        raise
               
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


def get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict):
    ''' 
    Get the hourly failure rate between a determined start time and end time.
    '''
    hourly_failure_dict = {}
    t_sd = floor_dt(start_time, timedelta(hours=1)) # start time left border
    t_eu = ceil_dt(end_time, timedelta(hours=1)) # end time right border
    print("down duration dict", down_duration_dict)
    
    # Filtering down time, get all down durations longer than one hour
    down_duration_dict_filtered = collections.OrderedDict()
    for key, value in down_duration_dict.items():
        if (value[1] - value[0]) / timedelta(hours=1) >= 1:
            down_duration_dict_filtered.update({key:[floor_dt(value[0], timedelta(hours=1)), floor_dt(value[1], timedelta(hours=1))]})
    
    print("down_duration_dict_filtered:", down_duration_dict_filtered)
    i = t_sd
    index = 0
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


class Scheduler(object):
    def __init__(self, job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict,
                  start_time, weights, scenario, duration_str, working_method):
        # Attributes assignment
        self.dna_size = len(job_dict)
        self.pop = job_dict.keys()
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.failure_dict = failure_dict
        self.product_related_characteristics_dict = product_related_characteristics_dict
        self.down_duration_dict = down_duration_dict
        # self.failure_info = failure_info
        # TODO: replace with input data from precedence file
        self.precedence_dict = precedence_dict
        self.start_time = start_time
        self.weights = weights
        self.scenario = scenario
        self.duration_str = duration_str
        self.working_method = working_method 

    def get_fitness(self, sub_pop, split_types=False, detail=False):
        ''' 
        Get fitness values for all individuals in a generation.
        '''
        wf = self.weights.get('weight_failure', 0); wvf =self.weights.get('weight_virtual_failure', 0)
        we = self.weights.get('weight_energy', 0); wc = self.weights.get('weight_conversion', 0)
        wb = self.weights.get('weight_constraint', 0); wft = self.weights.get('weight_flowtime', 0)
        factors = (wf, wvf, we, wc, wb)
        if wf or wvf:
            #failure_cost, virtual_failure_cost = [np.array(i.get_failure_cost(detail=detail, split_costs=True)) for i in sub_pop]
            failure_cost = []
            virtual_failure_cost = []
            for i in sub_pop:
                f_cost, vf_cost = i.get_failure_cost(detail=detail, split_costs=True)
            failure_cost.append(np.array(f_cost)); virtual_failure_cost.append(np.array(vf_cost))
        else:
            failure_cost = [0 for i in sub_pop]
            virtual_failure_cost = [0 for i in sub_pop]
        if we:
            #energy_cost = [self.w2*np.array(get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict,
            #                detail=detail, duration_str=self.duration_str, working_method=self.working_method)) for i in sub_pop]
            energy_cost = [np.array(i.get_energy_cost(detail=detail)) for i in sub_pop]
        else:
            energy_cost = [0 for i in sub_pop]
        if wc:
            conversion_cost = [np.array(i.get_conversion_cost(detail=detail)) for i in sub_pop]
        else:
            conversion_cost = [0 for i in sub_pop]
        if wb:
            constraint_cost = [np.array(i.get_constraint_cost(detail=detail)) for i in sub_pop]
        else:
            constraint_cost = [0 for i in sub_pop]
        if wft:
            flowtime_cost = [np.array(i.get_flowtime_cost(detail=detail)) for i in sub_pop]
        else:
            flowtime_cost = [0 for i in sub_pop]
        if split_types:
            total_cost = (np.array(failure_cost), np.array(virtual_failure_cost), np.array(energy_cost), 
                          np.array(conversion_cost), np.array(constraint_cost), np.array(flowtime_cost), factors)
        else:
            try:
                total_cost = wf * np.array(failure_cost) + wvf * np.array(virtual_failure_cost) +\
                             we * np.array(energy_cost) + wc * np.array(conversion_cost) + wb * np.array(constraint_cost) +\
                             wft * np.array(flowtime_cost)
            except:
                print(np.array(failure_cost).shape, np.array(virtual_failure_cost).shape, np.array(energy_cost).shape,
                      np.array(conversion_cost).shape, np.array(flowtime_cost).shape, np.array(constraint_cost).shape)
                print(detail)
                print(constraint_cost)
                raise
        return total_cost     
    
 
class BF(Scheduler):
    def __init__(self, job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict,
                  start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method):
        # Attributes assignment
        super().__init__(job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict,
                start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method)

    
    def check_all(self):
        if len(self.pop) > 10:
            raise ValueError('The input is too long, no brute force recommended')
        tot_cost_min = np.inf
        best_sched = []
        tot_cost_max = 0
        worst_sched = []
        import itertools
        allperm = itertools.permutations(self.pop)
        totallen = math.factorial(len(self.pop))
        i = 0
        while i < totallen:
            test = next(allperm)
            tot_cost = self.get_fitness([Schedule(test, 
                                        self.start_time, self.job_dict, self.failure_dict, 
                                        self.product_related_characteristics_dict,
                                        self.down_duration_dict, self.price_dict, self.failure_info,
                                        self.scenario, self.duration_str, self.working_method, self.weights)])[0]
            if tot_cost < tot_cost_min:
                tot_cost_min = tot_cost
                best_sched = test
            if tot_cost > tot_cost_max:
                tot_cost_max = tot_cost
                worst_sched = test
            i += 1
            print(str(i) + '/' + str(totallen) + '\t {:}'.format(tot_cost_min), end='\r')
            if msvcrt.kbhit() == True:
                char = msvcrt.getch()
                if char in [b'c', b'q']:
                    print('User hit c or q button, exiting...')
                    break
        print('\n')

        return tot_cost_min, tot_cost_max, best_sched, worst_sched

                
class GA(Scheduler):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict, failure_dict, 
                 product_related_characteristics_dict, down_duration_dict, precedence_dict, start_time, weights, scenario,
                 num_mutations=1, duration_str='expected', evolution_method='roulette', validation=False, pre_selection=False,
                 working_method='historical', failure_info=None):
        # Attributes assignment
        super().__init__(job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict, 
                       start_time, weights, scenario, duration_str, working_method)
        self.dna_size = dna_size 
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        self.num_mutations = num_mutations
        self.evolution_method = evolution_method
        self.validation = validation
        self.pre_selection = pre_selection
        self.failure_info = failure_info
        # generate N random individuals (N = pop_size)
        # BETTER METHOD: FUTURE WORK
        # Add functionality: first due date first TODO:
        if self.pre_selection == True:
            # In this case, EDD rule has already been applied on the pop
            # Such procedure is executed in run_opt()
            self.pop = np.array([Schedule(pop, 
                                 self.start_time, self.job_dict, self.failure_dict, 
                                 self.product_related_characteristics_dict,
                                 self.down_duration_dict, self.price_dict, self.precedence_dict,
                                 self.failure_info,
                                 self.scenario, self.duration_str, self.working_method, self.weights)
                                 for _ in range(pop_size)])
            #self.pop = np.vstack(pop for _ in range(pop_size))
        else:
            self.pop = np.array([Schedule(np.random.choice(pop, size=self.dna_size, replace=False), 
                                 self.start_time, self.job_dict, self.failure_dict, 
                                 self.product_related_characteristics_dict,
                                 self.down_duration_dict, self.price_dict, self.precedence_dict, 
                                 self.failure_info,
                                 self.scenario, self.duration_str, self.working_method, self.weights)
                                 for _ in range(pop_size)])
            #self.pop = np.vstack([np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])
        self.memory = []
        self.fitness = self.get_fitness(self.pop)
    
    def crossover(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, the crossover result is used to represent the loser.
        '''
        # crossover for loser
        if np.random.rand() < self.cross_rate:
            try:
                cross_points = np.random.randint(0, 2, self.dna_size).astype(np.bool)
                keep_job =  winner_loser[1][~cross_points] # see the progress explained in the paper
                swap_job = winner_loser[0, np.isin(winner_loser[0].ravel(), keep_job, invert=True)]
                winner_loser[1][:] = np.concatenate((keep_job, swap_job))
            except:
                print(keep_job)
                raise
        return winner_loser
    
    def mutate(self, loser, prob=False):
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        '''
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            if prob:
                tmpl = list(range(self.dna_size))
                try:
                    point = np.random.choice(tmpl, size=1, replace=False, p=prob)
                except:
                    import pdb; pdb.set_trace()
                tmpl.pop(int(point))
                # prob.pop(int(point))
                # inverse = list(np.array(prob).max() - np.array(prob))
                # inverse = inverse / sum(inverse)
                swap_point = np.random.choice(tmpl, size=1, replace=False)
            else:
                point, swap_point = np.random.choice(range(self.dna_size), size=2, replace=False)
            # point, swap_point = np.random.randint(0, self.dna_size, size=2)
            swap_A, swap_B = loser[point], loser[swap_point]
            loser[point], loser[swap_point] = swap_B, swap_A
        return loser
        
    def evolve(self, n, evolution=None):
        ''' 
        Execution of the provided GA.

        Parameters
        ----------
        n: int
            Number of iteration times 
        '''

        i = 1
        if evolution == None:
            evolution = self.evolution_method
        num_couples = 1

        while i <= n: # n is the number of evolution times in one iteration

            if evolution == 'roulette':
                fitness = self.fitness
                self.pop = self.pop[np.argsort(fitness)]
                self.fitness = np.sort(fitness)

                # choose sub-population according to roulette principle
                idx = range(len(self.pop))
                prob = [1/(x+2) for x in idx]
                prob = [p / sum(prob) for p in prob]
                # roulette wheel 
                sub_pop_idx = np.random.choice(idx, size=num_couples * 2, replace=False, p=prob)
            else: # if evolution = 'random':
                sub_pop_idx = np.random.choice(np.arange(0, self.pop_size), size=2, replace=False)

            # for each pair of schedules:
            for j in list(range(len(sub_pop_idx) >> 1)):
                temp_pop_idx = sub_pop_idx[j:j+2]
                #sub_pop = self.pop[temp_pop_idx] # pick 2 individuals from pop
                #fitness = self.get_fitness(sub_pop) # get the fitness values of the two
            
                # Elitism Selection
                #winner_loser_idx = np.argsort(fitness)
                if evolution == 'roulette':
                    winner_loser_idx = np.sort(temp_pop_idx)
                else:
                    sub_pop = self.pop[temp_pop_idx] # pick 2 individuals from pop
                    fitness = self.fitness[temp_pop_idx]
                    #fitness = self.get_fitness(sub_pop) # get the fitness values of the two
                    winner_loser_idx = temp_pop_idx[np.argsort(fitness)]
            
#               print('winner_loser_idx', winner_loser_idx)

                winner_loser = np.array([np.array(p.order) for p in self.pop[winner_loser_idx]])
                winner = winner_loser[0]; loser = winner_loser[1] # the first is winner and the second is loser

                #print('\nsubpop', winner_loser)
                #time.sleep(0.1)
            
                origin = loser.copy() # pick up the loser for genetic operations

                # Crossover (of the winner and the loser)
                winner_loser = self.crossover(winner_loser)
            
                # Mutation (only on the child)
                loser = winner_loser[1]
                for k in range(self.num_mutations):
                    # determine mismatch for each task
                    if evolution == 'roulette':
                        detailed_fitness = self.get_fitness([Schedule(loser, self.start_time, self.job_dict, self.failure_dict, 
                                                                      self.product_related_characteristics_dict,
                                                                      self.down_duration_dict, self.price_dict, self.precedence_dict, self.failure_info,
                                                                      self.scenario, self.duration_str, self.working_method, self.weights)], detail=True)[0]
                        #print(detailed_fitness)
                        mutation_prob = [f/sum(detailed_fitness) for f in detailed_fitness]
                        loser = self.mutate(loser, mutation_prob)
                    else:
                        loser = self.mutate(loser)
                winner_loser[1] = loser

                # for i in np.arange(, self.pop_size):
                #     other = self.pop[i]
                #     for j in range(self.num_mutations):
                #         other = self.mutate(other)
                #     self.pop[i] = other

#                 print("Start validate:")
                flag = 0
                #print('validation step')
                if self.validation:
                    if not loser.validate():
                        #self.pop[sub_pop_idx] = winner_loser
                        #i = i + 1 # End of an evolution procedure
                        flag = 1

                loser = Schedule(loser, self.start_time, self.job_dict, self.failure_dict, self.product_related_characteristics_dict,
                                 self.down_duration_dict, self.price_dict, self.precedence_dict, self.failure_info, self.scenario, self.duration_str, self.working_method, self.weights)

                if flag == 0:
                    if evolution == 'roulette':
                        bottomlist = list(range(self.pop_size >> 1, self.pop_size))
                        choice = np.random.choice(bottomlist)
                        self.pop[choice] = loser
                        # sort the fitness values
                        # fitness = self.fitness
                        # replace one of the least values for fitness
                        self.fitness[choice] = self.get_fitness([loser])[0]
                    else:
                        self.pop[winner_loser_idx[1]] = loser
                        self.fitness[winner_loser_idx[1]] = self.get_fitness([loser])[0]


                    #print('After:', self.get_fitness(self.pop))
                    i = i + 1 # End of procedure
                else:
                    #print("In memory, start genetic operation again!")
                    pass
                #else:
                    #print("Distance too small, start genetic operation again!")
                #    pass

        #if evolution != 'roulette':
        #    fitness = self.get_fitness(self.pop)

        return self.pop, self.fitness


def run_bf(start_time, end_time, down_duration_file, failure_file, prod_rel_file, energy_file, job_file,
           scenario, weights, duration_str='duration', 
           working_method='historical', failure_info=None):
    # Generate raw material unit price
    if working_method == 'historical':
        try:
            down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
            #print('test')
            if weight_failure != 0:
                if (failure_file is not None):
                    failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
                    #print(weight_failure)
                    #hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)
                    #with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
                    #    writer = csv.writer(csv_file)
                    #    for key, value in hourly_failure_dict.items():
                    #        writer.writerow([key, value])
                    failure_info = None
                elif (failure_info is not None):
                    hourly_failure_dict = {}
                else:
                    raise ValueError('No failure info found!')
            else:
                hourly_failure_dict = {}
                failure_info = None
        except:
            warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
            failure_downtimes = True
    if (working_method != 'historical') or failure_downtimes:
        warnings.warn('No import of downtime durations.')
        hourly_failure_dict = {}
        down_duration_dict = {}

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
    
    price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py
    if (start_time != None) and (end_time != None):
        job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
    elif (start_time != None):
        job_dict_new = read_jobs(job_file)
    else:
        raise NameError('No start time found!')

    job_dict_new = job_dict_new.astype(job_dict)

    # TODO: change
#     print("failure_dict", failure_dict)
#     exit()
#     # write corresponding failure dict into file
#     with open('ga_013_failure_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in failure_dict_new.items():
#             writer.writerow([key, value])

    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        try:
            first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
        except:
            first_start_time = start_time

    bf = BF(job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            start_time=first_start_time, weights=weights, scenario=scenario, working_method=working_method, 
            duration_str=duration_str, failure_info=failure_info)
    
    best_result, worst_result, best_schedule, worst_schedule = bf.check_all()

    best_schedule = Schedule(best_schedule, first_start_time, job_dict_new, hourly_failure_dict, product_related_characteristics_dict,
                             down_duration_dict, price_dict_new, failure_info, scenario, duration_str, working_method, weights)

    f_cost, vf_cost, e_cost, c_cost, d_cost, ft_cost, factors = best_schedule.get_fitness(split_types=True)
    total_cost = f_cost * factors[0] + vf_cost * factors[1] + e_cost  * factors[2] + c_cost * factors[3] + d_cost * factors[4] + ft_cost * factors[5]
    #total_cost = list(itertools.chain(*total_cost))
    #import pdb; pdb.set_trace()

    print("Best failure cost: " + str(f_cost))
    print("Best virtual failure cost: " + str(vf_cost))
    print("Best energy cost: " + str(e_cost))    
    print("Best conversion cost: " + str(c_cost))
    print("Best deadline cost: " + str(d_cost))
    print("Best flowtime cost: " + str(ft_cost))
    print("Factors: " + str(factors))
    print("Best total cost: " + str(total_cost))
    print()
    

    worst_schedule = Schedule(worst_schedule, first_start_time, job_dict_new, hourly_failure_dict, product_related_characteristics_dict,
                              down_duration_dict, price_dict_new, failure_info, scenario, duration_str, working_method, weights)

    f_cost, vf_cost, e_cost, c_cost, d_cost, ft_cost, factors = worst_schedule.get_fitness(split_types=True)
    total_cost = f_cost * factors[0] + vf_cost * factors[1] + e_cost  * factors[2] + c_cost * factors[3] + d_cost * factors[4] + ft_cost * factors[5]
    #total_cost = list(itertools.chain(*total_cost))
    #import pdb; pdb.set_trace()

    print("Worst failure cost: " + str(f_cost))
    print("Worst virtual failure cost: " + str(vf_cost))
    print("Worst energy cost: " + str(e_cost))    
    print("Worst conversion cost: " + str(c_cost))
    print("Worst deadline cost: " + str(d_cost))
    print("Worst flowtime cost: " + str(ft_cost))
    print("Factors: " + str(factors))
    print("Worst total cost: " + str(total_cost))

    # best_result_dict = best_schedule.get_time()
    # worst_result_dict = worst_schedule.get_time()

    return best_result, worst_result, best_schedule, worst_schedule 

        
def run_opt(start_time, end_time, down_duration_file, failure_file, prod_rel_file, precedence_file, energy_file, job_file, 
            scenario, iterations, cross_rate, mut_rate, pop_size,  num_mutations=5, adaptive=[],
            stop_condition='num_iterations', stop_value=None, weights={},
            duration_str='duration', evolution_method='roulette', validation=False, pre_selection=False, working_method='historical', failure_info=None, add_time=0,
            urgent_job_info=None, breakdown_record_file=None):
    logging.info('Using '+ str(working_method) + ' method')
    # filestream = open('previousrun.txt', 'w')
    # logging.basicConfig(level=20, stream=filestream)
    # Generate raw material unit price
    failure_downtimes = False
    if working_method == 'historical':
        try:
            down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
            #print('test')
            weight_failure = weights.get('weight_failure', 0)
            if weight_failure != 0:
                if (failure_file is not None):
                    print(failure_file)
                    failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
                    #print(weight_failure)
                    #hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)
                    #with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
                    #    writer = csv.writer(csv_file)
                    #    for key, value in hourly_failure_dict.items():
                    #        writer.writerow([key, value])
                    hourly_failure_dict = {}
                    failure_info = None
                elif (failure_info is not None):
                    hourly_failure_dict = {}
                else:
                    raise ValueError('no failure info found!')
            else:
                hourly_failure_dict = {}
                failure_info = None
        except:
            warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
            failure_downtimes = True
            raise
    if (working_method != 'historical') or failure_downtimes:
        warnings.warn('No import of downtime durations.')
        #weight_failure = 0
        down_duration_dict = {}
        hourly_failure_dict = {}

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
    if precedence_file is not None:
        precedence_dict = read_precedence(precedence_file)
    else:
        precedence_dict = None
    price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py

    ji = JobInfo()
    ji.read_from_file(job_file)
    
    if (start_time != None) and (end_time != None):
        #job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
        ji.limit_range(start_time, end_time)
    elif (start_time != None):
        #job_dict_new = read_jobs(job_file)
        pass
    else:
        raise NameError('No start time found!')

    if breakdown_record_file:
        record = read_breakdown_record(breakdown_record_file)
        ji.limit_range(record)
    
    if urgent_job_info:
        urgent_ji = JobInfo()
        urgent_ji.read_from_file(urgent_job_info)
        ji = urgent_ji + ji

    if add_time > 0:
        ji.add_breaks(add_time)
    
    job_dict_new = ji.job_dict

    DNA_SIZE = len(job_dict_new)
    waiting_jobs = ji.job_order
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        #try:
        #    first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
        #except:
        if not breakdown_record_file:
            first_start_time = start_time
        else:
            first_start_time = record

    
#     exit()
    ga = GA(dna_size=DNA_SIZE, cross_rate=cross_rate, mutation_rate=mut_rate, pop_size=pop_size, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            precedence_dict=precedence_dict, start_time = first_start_time, weights=weights, scenario=scenario,
            num_mutations = num_mutations, duration_str=duration_str, evolution_method=evolution_method, validation=validation,
            pre_selection=pre_selection, working_method=working_method, failure_info=failure_info)
    result_dict = {}
    #original_schedule = waiting_jobs
    #print(original_schedule)
    original_schedule = Schedule(waiting_jobs, first_start_time, job_dict_new, hourly_failure_dict,
                                 product_related_characteristics_dict, down_duration_dict, price_dict_new, precedence_dict,
                                 failure_info, scenario, duration_str, working_method, weights=weights)

    #import pdb; pdb.set_trace()
    total_result = original_schedule.get_fitness()
    original_schedule.validate()
    #total_result = ga.get_fitness([original_schedule])
    result_dict.update({0: total_result})

    best_result_list = []
    worst_result_list = [] 
    mean_result_list = []
    generation = 0
    stop = False
    timer0 = time.monotonic()
    while not stop:
        if generation in adaptive:
            print()
            print(str(generation) + ' reached - changing parameters of the GA')
            ga.cross_rate /= 2
            ga.mutation_rate = (ga.mutation_rate + 1) / 2
#         print("Gen: ", generation)
        pop, res = ga.evolve(1)          # natural selection, crossover and mutation
        #print("pop:", pop)
        #print("res:", res)
        #import pdb; pdb.set_trace()
        best_index = np.argmin(res)
        worst_index = np.argmax(res)
        mean = np.mean(res)
        print(str(generation) + '/' + str(iterations) + ':\t' +  str(res[best_index]), end=''); print('\r', end='') # overwrite this line continually
        generation += 1

        best_result_list.append(res[best_index])
        worst_result_list.append(res[worst_index])
        mean_result_list.append(mean)

        if stop_condition == 'num_iterations':
            if generation >= iterations:
                stop = True
        if stop_condition == 'end_value':
            if res[best_index] < stop_value:
                stop = True
        if stop_condition == 'abs_time':
            timer1 = time.monotonic()  # returns time in seconds
            elapsed_time = timer1-timer0
            if elapsed_time >= stop_value:
                stop = True
        if msvcrt.kbhit() == True: # Only works on Windows
            char = msvcrt.getche()
            if char in [b'c', b'q']:
                print('User hit c or q button, exiting...')
                stop = True
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
#         result_dict.update({generation:res[best_index]})
    
    # Used to store intermediate result for large-size problems
#     with open('IGAlarge.pkl', 'wb') as f:
#         pickle.dump(pop[best_index], f

    timer1 = time.monotonic()
    elapsed_time = timer1-timer0
    print()
    print('Elapsed time: {:.2f} s'.format(elapsed_time))

    print()      
    print("Candidate schedule " + str(pop[best_index].order))
    candidate_schedule = pop[best_index]

    candidate_schedule.print_fitness()

    total_cost = candidate_schedule.get_fitness()
    
#     print("Most fitted cost: ", res[best_index])

    print("\nOriginal schedule: ", original_schedule.order)
#     print("DNA_SIZE:", DNA_SIZE) 
    print("Original schedule start time:", first_start_time)
    original_schedule.print_fitness()

    original_cost = original_schedule.get_fitness()
    
    #print(duration_str)
    result_dict = candidate_schedule.get_time()
    #result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
    #                        down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
    #import pdb; pdb.set_trace()
    result_dict_origin = original_schedule.get_time()
    #result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
    #                               down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
#     print("Visualize_dict_origin:", result_dict)
#     print("Down_duration", down_duration_dict)


    # Output for visualization
    with open('executionRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict.items():
            writer.writerow([key, value['start'], value['end'], value['totaltime']])
            
    with open('originalRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict_origin.items():
            writer.writerow([key, value['start'], value['end'], value['totaltime']])
            
    with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in down_duration_dict.items():
            writer.writerow([key, value[0], value[1]])

    #filestream.close()

    return total_cost, original_cost, candidate_schedule, original_schedule, best_result_list, mean_result_list, worst_result_list, generation


# def run_opt_urgent(start_time, end_time, down_duration_file, failure_file, prod_rel_file, precedence_file, energy_file, job_file, urgent_job_file,
#             scenario, iterations, cross_rate, mut_rate, pop_size,  num_mutations=5, adaptive=[],
#             stop_condition='num_iterations', stop_value=None, weight_conversion = 0, weight_constraint = 0, weight_energy = 0, weight_failure = 0,
#             duration_str='duration', evolution_method='roulette', validation=False, pre_selection=False, working_method='expected'):
#     print('Using', working_method, 'method')
#     filestream = open('previousrun.txt', 'w')
#     logging.basicConfig(level=20, stream=filestream)
#     # Generate raw material unit price
#     failure_downtimes = False
#     if working_method == 'historical':
#         try:
#             down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
#             #print('test')
#             if weight_failure != 0:
#                 failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
#                 print(weight_failure)
#                 hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)
#                 with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
#                     writer = csv.writer(csv_file)
#                     for key, value in hourly_failure_dict.items():
#                         writer.writerow([key, value])
#             else:
#                 failure_list = []
#                 hourly_failure_dict = {}                
#         except:
#             warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
#             failure_downtimes = True
#     if (working_method != 'historical') or failure_downtimes:
#         warnings.warn('No import of downtime durations.')
#         weight_failure = 0
#         down_duration_dict = {}
#         failure_list = []
#         hourly_failure_dict = {}

# #     print("down_duration_dict: ", down_duration_dict)
# #     print("hourly_failure_dict: ", hourly_failure_dict)
# #     exit()
    
#     product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
#     precedence_dict = read_precedence(precedence_file)
#     price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
# #     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py

# #     if (start_time != None) and (end_time != None):
# #         job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
# #     elif (start_time != None):
# #         job_dict_new = read_jobs(job_file)
# #     else:
# #         raise NameError('No start time found!')

#     if (start_time != None) and (end_time != None):
#         job_dict_origin = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
#     elif (start_time != None):
#         job_dict_origin = read_jobs(job_file)
#     else:
#         raise NameError('No start time found!')
                
#     job_dict_urgent = read_jobs(urgent_job_file)
#     job_dict_new = make_new_jobs_dict(job_dict_origin, job_dict_urgent)
#     # TODO: change
# #     print("failure_dict", failure_dict)
# #     exit()
# #     # write corresponding failure dict into file
# #     with open('ga_013_failure_plot.csv', 'w', newline='\n') as csv_file:
# #         writer = csv.writer(csv_file)
# #         for key, value in failure_dict_new.items():
# #             writer.writerow([key, value])

#     DNA_SIZE = len(job_dict_new)
#     waiting_jobs = [*job_dict_new]
    
# #     print(job_dict_new)
#     if pre_selection == True:
#         sorted_jobs = OrderedDict(sorted(job_dict_new.items(), key=lambda kv: kv[1].get('before')))
#         waiting_jobs = [*sorted_jobs]
# #         print("Sorted_job:", sorted_job)
    
# #     print(sorted_job)
# #     print(waiting_jobs)
# #     exit()
    
#     if not waiting_jobs:
#         raise ValueError("No waiting jobs!")
#     else:
#         try:
#             first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
#         except:
#             first_start_time = start_time
    
# #     print("Waiting jobs: ", waiting_jobs)
# #     print("Prices: ", price_dict_new)
# #     print("Failures: ", failure_dict_new)

#     # result_dict = {}
#     # original_schedule = waiting_jobs  
#     # total_result = 0
#     # if weight_energy:
#     #     total_result += weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
#     # if weight_failure:
#     #     total_result += weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
#     #                                     product_related_characteristics_dict, down_duration_dict, scenario)
#     # if weight_conversion:
#     #     total_result += weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
#     # if weight_before:
#     #     total_result += weight_before * get_before_cost(original_schedule, first_start_time, job_dict_new)
#     # result_dict.update({0: total_result}) # generation 0 is the original schedule

#     #import pdb; pdb.set_trace()

#     # Remove the downtimes from the job dict (the product is not produced during this period)
#     #job_dict_new = remove_downtimes(job_dict_new)

    
# #     exit()
#     ga = GA(dna_size=DNA_SIZE, cross_rate=cross_rate, mutation_rate=mut_rate, pop_size=pop_size, pop=waiting_jobs,
#             job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
#             product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
#             precedence_dict = precedence_dict,
#             start_time = first_start_time, weight1=weight_failure, weight2=weight_energy, weightc=weight_conversion, 
#             weightb = weight_constraint, scenario=scenario,
#             num_mutations = num_mutations, duration_str=duration_str, evolution_method=evolution_method, validation=validation,
#             pre_selection=pre_selection, working_method=working_method)

#     result_dict = {}
#     original_schedule = waiting_jobs
#     #print(original_schedule)
#     total_result = ga.get_fitness([original_schedule])
#     result_dict.update({0: total_result})

#     best_result_list = []
#     worst_result_list = [] 
#     mean_result_list = []
#     generation = 1
#     stop = False
#     timer0 = time.monotonic()
#     while not stop:
#         if generation in adaptive:
#             print()
#             print(str(generation) + ' reached - changing parameters of the GA')
#             ga.cross_rate /= 2
#             ga.mutation_rate = (ga.mutation_rate + 1) / 2
# #         print("Gen: ", generation)
#         pop, res = ga.evolve(1)          # natural selection, crossover and mutation
# #         print("res:", res)
#         best_index = np.argmin(res)
#         worst_index = np.argmax(res)
#         mean = np.mean(res)
#         print(str(generation) + '/' + str(iterations) + ':\t' +  str(res[best_index]), end=''); print('\r', end='') # overwrite this line continually
#         generation += 1

#         best_result_list.append(res[best_index])
#         worst_result_list.append(res[worst_index])
#         mean_result_list.append(mean)

#         if stop_condition == 'num_iterations':
#             if generation >= iterations:
#                 stop = True
#         if stop_condition == 'end_value':
#             if res[best_index] < stop_value:
#                 stop = True
#         if stop_condition == 'abs_time':
#             timer1 = time.monotonic()  # returns time in seconds
#             elapsed_time = timer1-timer0
#             if elapsed_time >= stop_value:
#                 stop = True
#         if msvcrt.kbhit() == True: # Only works on Windows
#             char = msvcrt.getche()
#             if char in [b'c', b'q']:
#                 print('User hit c or q button, exiting...')
#                 stop = True
# #         print("Most fitted DNA: ", pop[best_index])
# #         print("Most fitted cost: ", res[best_index])
# #         result_dict.update({generation:res[best_index]})
    
#     # Used to store intermediate result for large-size problems
# #     with open('IGAlarge.pkl', 'wb') as f:
# #         pickle.dump(pop[best_index], f

#     timer1 = time.monotonic()
#     elapsed_time = timer1-timer0
#     print()
#     print('Elapsed time: {:.2f} s'.format(elapsed_time))

#     print()      
#     print("Candidate schedule", pop[best_index])
#     candidate_schedule = pop[best_index]

#     # if weight_energy:
#     #     candidate_energy_cost = weight_energy * get_energy_cost(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
#     # else:
#     #     candidate_energy_cost = weight_energy
#     # if weight_failure:
#     #     candidate_failure_cost = weight_failure * get_failure_cost(candidate_schedule, first_start_time, job_dict_new, hourly_failure_dict,
#     #                                     product_related_characteristics_dict, down_duration_dict, scenario)
#     # else:
#     #     candidate_failure_cost = weight_failure
#     # if weight_conversion:
#     #     candidate_conversion_cost = weight_conversion * get_conversion_cost(candidate_schedule, job_dict_new, product_related_characteristics_dict)
#     # else:
#     #     candidate_conversion_cost = weight_conversion

#     total_cost = ga.get_fitness([candidate_schedule], split_types=True)
#     total_cost = list(itertools.chain(*total_cost))

#     print("Candidate failure cost:", total_cost[0])
#     print("Candidate energy cost:", total_cost[1])
#     print("Candidate conversion cost:", total_cost[2])
#     print("Candidate deadline cost", total_cost[3])
#     print("Candidate total cost:", sum(total_cost))
    
# #     print("Most fitted cost: ", res[best_index])

#     print("\nOriginal schedule:", original_schedule)
# #     print("DNA_SIZE:", DNA_SIZE) 
#     print("Original schedule start time:", first_start_time)
#     # if weight_energy:
#     #     original_energy_cost = weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
#     # else:
#     #     original_energy_cost = 0
#     # if weight_failure:
#     #     original_failure_cost = weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
#     #                                                             product_related_characteristics_dict, down_duration_dict, scenario=scenario)
#     # else:
#     #     original_failure_cost = weight_failure
#     # if weight_conversion:
#     #     original_conversion_cost = weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
#     # else:
#     #     original_conversion_cost = weight_conversion
#     original_cost = ga.get_fitness([original_schedule], split_types=True)
#     original_cost = list(itertools.chain(*original_cost))
#     print("Original failure cost: ", original_cost[0])
#     print("Original energy cost: ", original_cost[1])
#     print("Original conversion cost:", original_cost[2])
#     print("Original deadline cost", original_cost[3])
#     print("Original total cost:", sum(original_cost))
    
#     #print(duration_str)
#     result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
#                             down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
#     #import pdb; pdb.set_trace()
#     result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
#                                    down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
# #     print("Visualize_dict_origin:", result_dict)
# #     print("Down_duration", down_duration_dict)


#     # Output for visualization
#     with open('executionRecords.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in result_dict.items():
#             writer.writerow([key, value[0], value[1], value[2]])
            
#     with open('originalRecords.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in result_dict_origin.items():
#             writer.writerow([key, value[0], value[1], value[2]])
            
#     with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in down_duration_dict.items():
#             writer.writerow([key, value[0], value[1]])

#     filestream.close()

#     return sum(total_cost), sum(original_cost), result_dict, result_dict_origin, best_result_list, mean_result_list, worst_result_list, generation

def read_breakdown_record(breakdownRecordFile):
    try:
        with open(breakdownRecordFile, encoding='utf-8') as breakdown_csv:
            reader = csv.DictReader(breakdown_csv)
            for row in reader:
                stamp = datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f")
    except:
        print("Unexpected error when reading breakdown record from {}:".format(breakdownRecordFile))
        raise
               
    return stamp


def make_new_jobs_dict_breakdown(origin_dict, timestamp):
    res_dict = {}
    for key, value in origin_dict.items():
        try:
            if value['start'] >= timestamp: # All jobs whose start time after the stamp needs to be re-organized
                res_dict.update({key:value})
        except TypeError:
            print("Wrong type when comparing jobs.")
            raise
    
    return res_dict


def run_opt_breakdowns(start_time, end_time, down_duration_file, failure_file, prod_rel_file, precedence_file, energy_file, job_file, breakdown_record_file,
            scenario, iterations, cross_rate, mut_rate, pop_size,  num_mutations=5, adaptive=[],
            stop_condition='num_iterations', stop_value=None, weight_conversion = 0, weight_constraint = 0, weight_energy = 0, weight_failure = 0,
            duration_str='duration', evolution_method='roulette', validation=False, pre_selection=False, working_method='expected'):
    print('Using', working_method, 'method')
    filestream = open('previousrun.txt', 'w')
    logging.basicConfig(level=20, stream=filestream)
    # Generate raw material unit price
    failure_downtimes = False
    if working_method == 'historical':
        try:
            down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
            #print('test')
            if weight_failure != 0:
                failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
                print(weight_failure)
                hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)
                with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
                    writer = csv.writer(csv_file)
                    for key, value in hourly_failure_dict.items():
                        writer.writerow([key, value])
            else:
                failure_list = []
                hourly_failure_dict = {}                
        except:
            warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
            failure_downtimes = True
    if (working_method != 'historical') or failure_downtimes:
        warnings.warn('No import of downtime durations.')
        weight_failure = 0
        down_duration_dict = {}
        failure_list = []
        hourly_failure_dict = {}

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
    precedence_dict = read_precedence(precedence_file)
    price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py

#     if (start_time != None) and (end_time != None):
#         job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
#     elif (start_time != None):
#         job_dict_new = read_jobs(job_file)
#     else:
#         raise NameError('No start time found!')

    if (start_time != None) and (end_time != None):
        job_dict_origin = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
    elif (start_time != None):
        job_dict_origin = read_jobs(job_file)
    else:
        raise NameError('No start time found!')
                
    breakdown_timestamp = read_breakdown_record(breakdown_record_file)
   
   
    job_dict_new = make_new_jobs_dict_breakdown(job_dict_origin, breakdown_timestamp)
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
    
#     print(job_dict_new)
    if pre_selection == True:
        sorted_jobs = OrderedDict(sorted(job_dict_new.items(), key=lambda kv: kv[1].get('before')))
        waiting_jobs = [*sorted_jobs]
#         print("Sorted_job:", sorted_job)
    
#     print(sorted_job)
#     print(waiting_jobs)
#     exit()
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        try:
            first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
        except:
            first_start_time = start_time
    
#     print("Waiting jobs: ", waiting_jobs)
#     print("Prices: ", price_dict_new)
#     print("Failures: ", failure_dict_new)

    # result_dict = {}
    # original_schedule = waiting_jobs  
    # total_result = 0
    # if weight_energy:
    #     total_result += weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # if weight_failure:
    #     total_result += weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                     product_related_characteristics_dict, down_duration_dict, scenario)
    # if weight_conversion:
    #     total_result += weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
    # if weight_before:
    #     total_result += weight_before * get_before_cost(original_schedule, first_start_time, job_dict_new)
    # result_dict.update({0: total_result}) # generation 0 is the original schedule

    #import pdb; pdb.set_trace()

    # Remove the downtimes from the job dict (the product is not produced during this period)
    #job_dict_new = remove_downtimes(job_dict_new)

    
#     exit()
    ga = GA(dna_size=DNA_SIZE, cross_rate=cross_rate, mutation_rate=mut_rate, pop_size=pop_size, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            precedence_dict = precedence_dict,
            start_time = first_start_time, weight1=weight_failure, weight2=weight_energy, weightc=weight_conversion, 
            weightb = weight_constraint, scenario=scenario,
            num_mutations = num_mutations, duration_str=duration_str, evolution_method=evolution_method, validation=validation,
            pre_selection=pre_selection, working_method=working_method)

    result_dict = {}
    original_schedule = waiting_jobs
    #print(original_schedule)
    total_result = ga.get_fitness([original_schedule])
    result_dict.update({0: total_result})

    best_result_list = []
    worst_result_list = [] 
    mean_result_list = []
    generation = 1
    stop = False
    timer0 = time.monotonic()
    while not stop:
        if generation in adaptive:
            print()
            print(str(generation) + ' reached - changing parameters of the GA')
            ga.cross_rate /= 2
            ga.mutation_rate = (ga.mutation_rate + 1) / 2
#         print("Gen: ", generation)
        pop, res = ga.evolve(1)          # natural selection, crossover and mutation
#         print("res:", res)
        best_index = np.argmin(res)
        worst_index = np.argmax(res)
        mean = np.mean(res)
        print(str(generation) + '/' + str(iterations) + ':\t' +  str(res[best_index]), end=''); print('\r', end='') # overwrite this line continually
        generation += 1

        best_result_list.append(res[best_index])
        worst_result_list.append(res[worst_index])
        mean_result_list.append(mean)

        if stop_condition == 'num_iterations':
            if generation >= iterations:
                stop = True
        if stop_condition == 'end_value':
            if res[best_index] < stop_value:
                stop = True
        if stop_condition == 'abs_time':
            timer1 = time.monotonic()  # returns time in seconds
            elapsed_time = timer1-timer0
            if elapsed_time >= stop_value:
                stop = True
        if msvcrt.kbhit() == True: # Only works on Windows
            char = msvcrt.getche()
            if char in [b'c', b'q']:
                print('User hit c or q button, exiting...')
                stop = True
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
#         result_dict.update({generation:res[best_index]})
    
    # Used to store intermediate result for large-size problems
#     with open('IGAlarge.pkl', 'wb') as f:
#         pickle.dump(pop[best_index], f

    timer1 = time.monotonic()
    elapsed_time = timer1-timer0
    print()
    print('Elapsed time: {:.2f} s'.format(elapsed_time))

    print()      
    print("Candidate schedule", pop[best_index])
    candidate_schedule = pop[best_index]

    # if weight_energy:
    #     candidate_energy_cost = weight_energy * get_energy_cost(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # else:
    #     candidate_energy_cost = weight_energy
    # if weight_failure:
    #     candidate_failure_cost = weight_failure * get_failure_cost(candidate_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                     product_related_characteristics_dict, down_duration_dict, scenario)
    # else:
    #     candidate_failure_cost = weight_failure
    # if weight_conversion:
    #     candidate_conversion_cost = weight_conversion * get_conversion_cost(candidate_schedule, job_dict_new, product_related_characteristics_dict)
    # else:
    #     candidate_conversion_cost = weight_conversion

    total_cost = ga.get_fitness([candidate_schedule], split_types=True)
    total_cost = list(itertools.chain(*total_cost))

    print("Candidate failure cost:", total_cost[0])
    print("Candidate energy cost:", total_cost[1])
    print("Candidate conversion cost:", total_cost[2])
    print("Candidate deadline cost", total_cost[3])
    print("Candidate total cost:", sum(total_cost))
    
#     print("Most fitted cost: ", res[best_index])

    print("\nOriginal schedule:", original_schedule)
#     print("DNA_SIZE:", DNA_SIZE) 
    print("Original schedule start time:", first_start_time)
    # if weight_energy:
    #     original_energy_cost = weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # else:
    #     original_energy_cost = 0
    # if weight_failure:
    #     original_failure_cost = weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                                             product_related_characteristics_dict, down_duration_dict, scenario=scenario)
    # else:
    #     original_failure_cost = weight_failure
    # if weight_conversion:
    #     original_conversion_cost = weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
    # else:
    #     original_conversion_cost = weight_conversion
    original_cost = ga.get_fitness([original_schedule], split_types=True)
    original_cost = list(itertools.chain(*original_cost))
    print("Original failure cost: ", original_cost[0])
    print("Original energy cost: ", original_cost[1])
    print("Original conversion cost:", original_cost[2])
    print("Original deadline cost", original_cost[3])
    print("Original total cost:", sum(original_cost))
    
    #print(duration_str)
    result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                            down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
    #import pdb; pdb.set_trace()
    result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                                   down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
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

    filestream.close()

    return sum(total_cost), sum(original_cost), result_dict, result_dict_origin, best_result_list, mean_result_list, worst_result_list, generation


if __name__ == '__main__':
    
    # Read parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=int, help="The running mode of the scheduler: 1-User 2-Demo", default=1)
    # TODO: procedures after the user choose mode
    parser.add_argument("historical_down_periods_file", help="File containing records of historical down duration periods.") # downDurations.csv
    parser.add_argument("failure_rate_file", help="File containing failure rate of each hour from the failure model.") # hourly_failure_rate.csv
    parser.add_argument("product_related_characteristics_file", help="File containing product related characteristics.") # productRelatedCharacteristics.csv
    parser.add_argument("energy_price_file", help="File containing energy price of each hour.") # price.csv
    parser.add_argument("job_info_file", help="File containing job information.") # jobInfoProd_ga_013.csv
    parser.add_argument("scenario", type=int, help="Choose scenario: 1-MTBF 2-Machine stop/restart") # number of scenario
    parser.add_argument("objective", type=int, help="Choose objectives: 1-Energy+Failure 2-Energy Only 3-Failure Only", default=1) 
    # TODO: prodedures after the user choose objectives
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

    run_opt(start_time, end_time, args.historical_down_periods_file, 
           args.failure_rate_file, args.product_related_characteristics_file, 
           args.energy_price_file, args.job_info_file,
           args.scenario, args.generations, args.crossover_rate, args.mutation_rate, args.pop_size)