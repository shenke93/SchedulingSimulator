''' Plot the objective-generation plot for a GA method.
    Help to analyse the performance of the GA.
'''
from datetime import datetime
import time
import numpy as np
import csv
from geneticAlgorithm003 import read_job, read_price, select_jobs, select_prices, GA, get_energy_cost

POP_SIZE = 8   
CROSS_RATE = 0.3
MUTATION_RATE = 0.3
N_GENERATIONS = 200

if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    start_time = datetime(2016, 1, 19, 14, 0)
    end_time = datetime(2017, 11, 15, 8, 0) # Soubry range: 1124 jobs
    
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfo.csv"))
    price_dict_new = select_prices(start_time, end_time, read_price("price.csv"))
    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
        
#     print(waiting_jobs) 
#     elite_cost = float('inf')
#     elite_schedule = []
    analyse_dict = {}
    
    original_schedule = waiting_jobs 
    analyse_dict.update({0:get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new)}) # Add origin to index 0
    
    start_stamp = time.time()
    ga = GA(dna_size=DNA_SIZE, cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, start_time=first_start_time)
    for generation in range(1, N_GENERATIONS+1):
        if (generation % 20) == 0:
            print("Gen: ", generation)
        pop, res = ga.evolve(8)          # natural selection, crossover and mutation
        best_index = np.argmin(res)
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
        analyse_dict.update({generation:res[best_index]})

    end_stamp = time.time()
    
    print()
#     print("Optimal cost:", elite_cost)
#     print("Optimal schedule:", elite_schedule)
    print("Time consumption:", end_stamp-start_stamp)
    
    print()
          
    print("Original schedule: ", original_schedule)
    print("Original schedule start time:", first_start_time)
    print("Original cost: ", get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new))
    
    
    # write the result to csv for plot
    with open('ga_003_analyse_plot.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in analyse_dict.items():
            writer.writerow([key, value])
    