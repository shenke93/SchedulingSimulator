import numpy as np
import time
import logging
import msvcrt
import pandas as pd
import sys

class SimpleGA:
    def __init__(self, schedule, settings):
        self.schedule = schedule
        self.dna_size = len(schedule.job_list)
        self.pop_size = settings.pop_size
        self.cross_rate = settings.cross_rate
        self.mutation_rate = settings.mutation_rate
        self.num_mutations = settings.num_mutations
        self.evolution_method = settings.evolution_method
        self.validation = settings.validation
        self.perimeter = 10
        self.pop = np.array([schedule.copy_random()
                             for _ in range(self.pop_size)])
        self.fitness = [popul.get_fitness() for popul in self.pop]
    
    def crossover(self, winner_loser): 
        ''' Using microbial genetic evolution strategy,
        the crossover result is used to represent the loser.
        An example image of this can be found in
        'Production Scheduling and Rescheduling 
        with Genetic Algorithms, C. Bierwirth, page 6'.
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
            # random_number = np.random.choice(list(range(-perimeter, 1)) + \
            #                                   list(range(1, perimeter+1)), size=1)
            # swap_point = int(point) + int(random_number)
            # if swap_point >= len(loser):
            #     swap_point = len(loser)-1
            # if swap_point < 0:
            #     swap_point = 0
            swap_point = np.random.choice(tmpl, size=1, replace=False)
            swap_point = int(swap_point); point = int(point)
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
                # the schedule is sorted here
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
            
                #print('winner_loser_idx', winner_loser_idx)

                winner_loser = np.array([np.array(p.job_list) for p in self.pop[winner_loser_idx]])
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
                    #    import pdb; pdb.set_trace()
                        #detailed_fitness = self.schedule.copy_neworder(loser).get_fitness()
                        # detailed_fitness = self.get_fitness([Schedule(loser, self.job_dict, self.start_time, 
                        #                                               self.product_related_characteristics_dict,
                        #                                               self.down_duration_dict, self.price_dict, self.precedence_dict, self.failure_info,
                        #                                               self.scenario, self.duration_str, self.working_method, self.weights)], detail=True)[0]
                        #print(detailed_fitness)
                        #mutation_prob = [f/sum(detailed_fitness) for f in detailed_fitness]
                        loser = self.mutate(loser)
                        #loser = self.mutate(loser, mutation_prob)
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
                        self.fitness[choice] = loser.get_fitness()
                    else:
                        self.pop[winner_loser_idx[1]] = loser
                        self.fitness[winner_loser_idx[1]] = loser.get_fitness()


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
    
def run_opt(original_schedule, settings):
    """ 
    Run the complete optimization step.
    Uses a starting schedule and GA settings.
    """ 
    iterations = settings.iterations
    stop_condition = settings.stop_condition
    stop_value = settings.stop_value
    adaptive = settings.adapt_ifin
    
    # if multiple schedules of course the costs of both the schedules will be saved
    # after the first schedule is calculated the end time is saved and then the next schedule is calculated from then on
    # initialise some data structures to save all of this
    
    total_result = original_schedule.get_fitness()
    # original_schedule.validate()
    result_dict = {}
    result_dict.update({0:total_result})
    
    ga = SimpleGA(original_schedule, settings)

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
        print(f'{generation}/{iterations}:\t{res[best_index]:15.1f}', end='')
        print('\r', end='')
        #print('\r ', end='\r') # overwrite this line continually
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
    logging.info("Candidate schedule " + str(pop[best_index].job_list))
    candidate_schedule = pop[best_index]

    print('Candidate schedule: ', end='\t')
    candidate_schedule.print_fitness()

    total_cost = candidate_schedule.get_fitness()
    
#     print("Most fitted cost: ", res[best_index])

    logging.info("\nOriginal schedule: " +  str(original_schedule.job_list))
#     print("DNA_SIZE:", DNA_SIZE) 
    
    print('Original schedule: ', end='\t')
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