''' Idea: 
    1. Choose date range for 9 jobs: [69, 70, 71, 72, 73, 74, 75, 76, 77], from 2016.2.20 15:00:00 to 2016.2.26 00:00:00
    2. Run GA method for size [3 - 9], monitoring execution time and result
'''
import time
import csv
import numpy as np
from datetime import datetime
from geneticAlgorithm002 import read_job, read_price, select_jobs, select_prices, GA, get_energy_cost

POP_SIZE = 4   
CROSS_RATE = 0.3
MUTATION_RATE = 0.3
N_GENERATIONS = 100

def run_GA(dna_size, cross_rate, mutation_rate, pop_size, pop, n_generations, start_time, job_dict, price_dict):
    elite_cost = float('inf')
    elite_schedule = []
        
    ga = GA(dna_size, cross_rate, mutation_rate, pop_size, pop)
    for _ in range(n_generations):
        cost = [get_energy_cost(i, start_time, job_dict, price_dict) for i in ga.pop]
        fitness = ga.get_fitness(cost)
    
#         best_idx = np.argmax(fitness)
#         print('Gen:', generation, '| best fit %.2f' % fitness[best_idx])
#         print("Most fitted DNA: ", ga.pop[np.argmax(fitness)])
#         print("Most fitted cost: ", cost[np.argmax(fitness)])
        
        if cost[np.argmax(fitness)] < elite_cost:
            elite_cost = cost[np.argmax(fitness)]
            elite_schedule = ga.pop[np.argmax(fitness)]
        
        ga.evolve(fitness)
        
    return {elite_cost:elite_schedule}

if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    start_time = datetime(2016, 2, 20, 15, 0)
    end_time = datetime(2016, 2, 26, 0, 0) # size 9

    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfo.csv"))
    price_dict_new = select_prices(start_time, end_time, read_price("price.csv"))
#     DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
        
    print(waiting_jobs)
    
    GAResult_dict = {}
    
    for i in range(3, 10):
        jobs = waiting_jobs[0:i]
        print("Selected jobs: ", jobs)
        start_stamp = time.time() 
        # Running GA methond here
        ga = run_GA(dna_size=len(jobs), cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE,
                    pop=jobs, n_generations=N_GENERATIONS, start_time=first_start_time, job_dict=job_dict_new,
                    price_dict=price_dict_new)
        
        end_stamp = time.time()
        
        print("Optimal cost:", ga.keys())
        print("Optimal schedule:", ga.values())
        print("Time consumption:", end_stamp-start_stamp)
        GAResult_dict.update({i:(end_stamp-start_stamp)})
    
    # write the result to csv for plot
    with open('ga_plot.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in GAResult_dict.items():
            writer.writerow([key, value])