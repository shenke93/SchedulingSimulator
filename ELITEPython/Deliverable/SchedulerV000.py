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
from helperfunctions import JobInfo, read_down_durations, read_product_related_characteristics, read_precedence, read_price,\
read_breakdown_record

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
    def __init__(self, schedule):
    # def __init__(self, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict,
    #               start_time, weights, scenario, duration_str, working_method):
        self.dna_size = len(schedule.order)
        # Attributes assignment
        #self.dna_size = len(job_dict)
        self.pop = schedule.job_dict.keys()
        self.job_dict = schedule.job_dict
        self.price_dict = schedule.price_dict
        #self.product_related_characteristics_dict = schedule.prc_dict
        self.down_duration_dict = schedule.downdur_dict
        # self.failure_info = failure_info
        # TODO: replace with input data from precedence file
        self.precedence_dict = schedule.precedence_dict
        self.start_time = schedule.start_time
        self.weights = schedule.weights
        self.scenario = schedule.scenario
        self.duration_str = schedule.duration_str
        self.working_method = schedule.working_method 

    def get_fitness(self, sub_pop, split_types=False, detail=False):
        ''' 
        Get fitness values for all individuals in a generation.
        '''
        wf = self.weights.get('weight_failure', 0); wvf =self.weights.get('weight_virtual_failure', 0)
        we = self.weights.get('weight_energy', 0); wc = self.weights.get('weight_conversion', 0)
        wb = self.weights.get('weight_constraint', 0); wft = self.weights.get('weight_flowtime', 0)
        factors = (wf, wvf, we, wc, wb)
        #import pdb; pdb.set_trace()
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
                import pdb; pdb.set_trace()
                raise
        return total_cost     
    
 
# class BF(Scheduler):
#     def __init__(self, job_dict, price_dict,  product_related_characteristics_dict, down_duration_dict, precedence_dict,
#                   start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method):
#         # Attributes assignment
#         super().__init__(job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict,
#                 start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method)

    
#     def check_all(self):
#         if len(self.pop) > 10:
#             raise ValueError('The input is too long, no brute force recommended')
#         tot_cost_min = np.inf
#         best_sched = []
#         tot_cost_max = 0
#         worst_sched = []
#         import itertools
#         allperm = itertools.permutations(self.pop)
#         totallen = math.factorial(len(self.pop))
#         i = 0
#         while i < totallen:
#             test = next(allperm)
#             tot_cost = self.get_fitness([Schedule(test, 
#                                         self.job_dict, self.start_time, 
#                                         self.product_related_characteristics_dict,
#                                         self.down_duration_dict, self.price_dict, self.failure_info,
#                                         self.scenario, self.duration_str, self.working_method, self.weights)])[0]
#             if tot_cost < tot_cost_min:
#                 tot_cost_min = tot_cost
#                 best_sched = test
#             if tot_cost > tot_cost_max:
#                 tot_cost_max = tot_cost
#                 worst_sched = test
#             i += 1
#             print(str(i) + '/' + str(totallen) + '\t {:}'.format(tot_cost_min), end='\r')
#             if msvcrt.kbhit() == True:
#                 char = msvcrt.getch()
#                 if char in [b'c', b'q']:
#                     print('User hit c or q button, exiting...')
#                     break
#         print('\n')

#         return tot_cost_min, tot_cost_max, best_sched, worst_sched


class GA(Scheduler):
    def __init__(self, schedule, settings):
    # def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict, 
    #              product_related_characteristics_dict, down_duration_dict, precedence_dict, start_time, weights, scenario,
    #              num_mutations=1, duration_str='expected', evolution_method='roulette', validation=False, pre_selection=False,
    #              working_method='historical', failure_info=None):
        # Attributes assignment
        super().__init__(schedule)
        self.schedule = schedule
        self.pop_size = settings.pop_size
        self.cross_rate = settings.cross_rate
        self.mutation_rate = settings.mutation_rate
        self.num_mutations = settings.num_mutations
        self.evolution_method = settings.evolution_method
        self.validation = settings.validation
        self.pre_selection = settings.pre_selection
        # generate N random individuals (N = pop_size)
        # BETTER METHOD: FUTURE WORK
        # Add functionality: first due date first TODO:
        if self.pre_selection == True:
            # In this case, EDD rule has already been applied on the pop
            # Such procedure is executed in run_opt()
            self.pop = np.array([schedule for _ in range(self.pop_size)])
            #self.pop = np.vstack(pop for _ in range(pop_size))
        else:
            self.pop = np.array([schedule.copy_random()
                                 for _ in range(self.pop_size)])
            #self.pop = np.vstack([np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])
        self.memory = []
        self.fitness = self.get_fitness(self.pop)
    
    def crossover(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, the crossover result is used to represent the loser.
        An example image of this can be found in 'Production Scheduling and Rescheduling with Genetic Algorithms, C. Bierwirth, page 6'.
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

    def crossover_similar(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, the crossover result is used 
        to represent the loser.
        This algorithm keeps the jobs which are common between two lists at the same place.
        An example image of this can be found in 
        'A genetic algorithm for hybrid flowshops, page 788'.
        '''
        # determine common points
        #print(winner_loser.shape)
        # crossover for loser
        if np.random.rand() < self.cross_rate:
            try:
                winner = np.array(winner_loser[0])
                loser = np.array(winner_loser[1])
                winner_out = winner.copy()
                loser_out = loser.copy()
                same = (winner == loser)

                cross_point = int(np.random.choice(np.arange(len(winner)), size=1))
                same[:cross_point] = True
                different = np.invert(same)

                np.putmask(loser_out, different, winner[np.isin(winner, different)])
                np.putmask(winner_out, different, loser[np.isin(loser, different)])
            except:
                raise
            #winner_loser = np.array([winner_out, loser_out])
        return winner_loser

    def mutate(self, loser, prob=False, perimeter=3):
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        Two random points change place here.
        '''
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            tmpl = list(range(self.dna_size))
            try:
                if prob:
                    point = np.random.choice(tmpl, size=1, replace=False, p=prob)
                else:
                    point = np.random.choice(tmpl, size=1, replace=False)
            except:
                import pdb; pdb.set_trace()
            # tmpl.pop(int(point))
            # prob.pop(int(point))
            # inverse = list(np.array(prob).max() - np.array(prob))
            # inverse = inverse / sum(inverse)
            perimeter = 3
            random_number = np.random.choice(list(range(-perimeter, 1)) + list(range(1, perimeter+1)), size=1)
            swap_point = int(point) + int(random_number)
            if swap_point >= len(loser):
                swap_point = len(loser)-1
            if swap_point < 0:
                swap_point = 0
            #swap_point = np.random.choice(tmpl, size=1, replace=False)
            #import pdb; pdb.set_trace()
            swap_point = int(swap_point); point = int(point)
            # point, swap_point = np.random.randint(0, self.dna_size, size=2)
            swap_A, swap_B = loser[point], loser[swap_point]
            loser[point], loser[swap_point] = swap_B, swap_A
        return loser
    

    def mutate_swap(self, loser, prob=False):
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        One job changes place here.
        '''
        loser = list(loser)
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            if prob:
                tmpl = list(range(self.dna_size))
                try:
                    point = int(np.random.choice(tmpl, size=1, replace=False, p=prob))
                except:
                    import pdb; pdb.set_trace()
                tmpl.pop(int(point))
                # prob.pop(int(point))
                # inverse = list(np.array(prob).max() - np.array(prob))
                # inverse = inverse / sum(inverse)
                insert_point = int(np.random.choice(tmpl, size=1, replace=False))
            else:
                point, insert_point = np.random.choice(range(self.dna_size), size=2, replace=False)
                point = int(point); insert_point = int(insert_point)
            # point, swap_point = np.random.randint(0, self.dna_size, size=2)
            #import pdb; pdb.set_trace()
            loser.insert(insert_point, loser.pop(point))
            #swap_A, swap_B = loser[point], loser[swap_point]
            #loser[point], loser[swap_point] = swap_B, swap_A
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
                        detailed_fitness = self.get_fitness([self.schedule.copy_neworder(loser)], detail=True)[0]
                        # detailed_fitness = self.get_fitness([Schedule(loser, self.job_dict, self.start_time, 
                        #                                               self.product_related_characteristics_dict,
                        #                                               self.down_duration_dict, self.price_dict, self.precedence_dict, self.failure_info,
                        #                                               self.scenario, self.duration_str, self.working_method, self.weights)], detail=True)[0]
                        #print(detailed_fitness)
                        mutation_prob = [f/sum(detailed_fitness) for f in detailed_fitness]
                        #loser = self.mutate(loser)
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
                
                loser = self.schedule.copy_neworder(loser)
                # loser = Schedule(loser, self.job_dict, self.start_time, self.product_related_characteristics_dict,
                #                  self.down_duration_dict, self.price_dict, self.precedence_dict, self.failure_info, 
                #                  self.scenario, self.duration_str, self.working_method, self.weights)
                
                #print('validation step')
                flag = 0
                if self.validation:
                    if not loser.validate():
                        pass
                        #self.pop[sub_pop_idx] = winner_loser
                        #i = i + 1 # End of an evolution procedure
                        #flag = 1

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
                else:
                    raise ValueError('No failure info found!')
        except:
            warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
            failure_downtimes = True
    if (working_method != 'historical') or failure_downtimes:
        warnings.warn('No import of downtime durations.')
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

    bf = BF(job_dict=job_dict_new, price_dict=price_dict_new,
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            start_time=first_start_time, weights=weights, scenario=scenario, working_method=working_method, 
            duration_str=duration_str, failure_info=failure_info)
    
    best_result, worst_result, best_schedule, worst_schedule = bf.check_all()

    best_schedule = Schedule(best_schedule, job_dict_new, first_start_time, product_related_characteristics_dict,
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
    

    worst_schedule = Schedule(worst_schedule, job_dict_new, first_start_time, product_related_characteristics_dict,
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

       
# def run_opt(start_time, end_time, down_duration_file, failure_file, prod_rel_file, precedence_file, energy_file, job_file, failure_info,
#             urgent_job_info, breakdown_record_file, scenario, iterations, cross_rate, mut_rate, pop_size,  num_mutations=5, adaptive=[],
#             stop_condition='num_iterations', stop_value=None, weights={},
#             duration_str='duration', evolution_method='roulette', validation=False, pre_selection=False, working_method='historical', add_time=0,
#             remove_breaks=False):

def run_opt(original_schedule, settings, start_time=None):

    iterations = settings.iterations
    stop_condition = settings.stop_condition
    stop_value = settings.stop_value
    adaptive = settings.adapt_ifin
    
    # if multiple schedules of course the costs of both the schedules will be saved
    # after the first schedule is calculated the end time is saved and then the next schedule is calculated from then on
    # initialise some data structures to save all of this
    try:
        logging.info('Using '+ str(original_schedule.working_method) + ' method')
        if start_time == None:
            logging.info("Original schedule start time: " +  str(original_schedule.start_time.isoformat()))
        else:
            logging.info("Schedule start time: " +  str(start_time.isoformat()))
            original_schedule.set_starttime(start_time)
    except: 
        pass
    
    total_result = original_schedule.get_fitness()
    # original_schedule.validate()
    result_dict = {}
    result_dict.update({0:total_result})
    
    ga = GA(original_schedule, settings)

    best_result_list = []
    worst_result_list = [] 
    mean_result_list = []
    best_result_list_no_constraint = []
    worst_result_list_no_constraint = [] 
    generation = 0
    stop = False
    timer0 = time.monotonic()
    
    no_constraint = original_schedule.weights.copy()
    no_constraint['weight_constraint'] = 0
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
        print(f'{generation}/{iterations}:\t{res[best_index]:15.3f}', end='')
        #print(str(generation) + '/' + str(iterations) + ':\t' +  str(res[best_index]), end=''); 
        print('\r', end='') # overwrite this line continually
        generation += 1

        best_result_list.append(res[best_index])
        worst_result_list.append(res[worst_index])
        mean_result_list.append(mean)
        
        best_result_list_no_constraint.append(pop[best_index].get_fitness(weights=no_constraint))
        worst_result_list_no_constraint.append(pop[worst_index].get_fitness(weights=no_constraint))

        if (stop_condition == 'num_iterations') and (generation >= iterations):
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
    
    lists_result = pd.DataFrame({'best': best_result_list, 'mean': mean_result_list, 'worst': worst_result_list})
    lists_result_no_constraint = pd.DataFrame({'best': best_result_list_no_constraint, 'worst': worst_result_list_no_constraint})
    
    timer1 = time.monotonic()
    elapsed_time = timer1-timer0
    
    logging.info('Stopping after ' + str(iterations) + ' iterations. Elapsed time: ' + str(round(elapsed_time, 2)))

    print()
    logging.info("Candidate schedule " + str(pop[best_index].order))
    candidate_schedule = pop[best_index]

    candidate_schedule.print_fitness()

    total_cost = candidate_schedule.get_fitness()
    
#     print("Most fitted cost: ", res[best_index])

    logging.info("\nOriginal schedule: " +  str(original_schedule.order))
#     print("DNA_SIZE:", DNA_SIZE) 
    
    original_schedule.print_fitness()

    original_cost = original_schedule.get_fitness()
    
    #print(duration_str)
    #result_dict = candidate_schedule.get_time()
    #result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
    #                        down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
    #import pdb; pdb.set_trace()
    #result_dict_origin = original_schedule.get_time()
    #result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
    #                               down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
#     print("Visualize_dict_origin:", result_dict)
#     print("Down_duration", down_duration_dict)


    # # Output for visualization
    # with open('executionRecords.csv', 'w', newline='\n') as csv_file:
    #     writer = csv.writer(csv_file)
    #     for key, value in result_dict.items():
    #         writer.writerow([key, value['start'], value['end'], value['totaltime']])
            
    # with open('originalRecords.csv', 'w', newline='\n') as csv_file:
    #     writer = csv.writer(csv_file)
    #     for key, value in result_dict_origin.items():
    #         writer.writerow([key, value['start'], value['end'], value['totaltime']])
            
    # with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
    #     writer = csv.writer(csv_file)
    #     for key, value in original_schedule.downdur_dict.items():
    #         writer.writerow([key, value[0], value[1]])       
    
    return total_cost, original_cost, candidate_schedule, original_schedule, lists_result, lists_result_no_constraint


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