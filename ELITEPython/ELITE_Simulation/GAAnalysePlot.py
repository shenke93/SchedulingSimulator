''' Plot the objective-generation plot for a GA method
'''
from datetime import datetime
import numpy as np
import csv
from geneticAlgorithm002 import read_job, read_price, select_jobs, select_prices, GA, get_energy_cost

POP_SIZE = 4   
CROSS_RATE = 0.4
MUTATION_RATE = 0.5
N_GENERATIONS = 300

if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    start_time = datetime(2016, 1, 19, 14, 0)
    end_time = datetime(2017, 11, 15, 8, 0) # Soubry range: 1124 jobs
    
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfo.csv"))
    price_dict_new = select_prices(start_time, end_time, read_price("price.csv"))
#     DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
        
#     print(waiting_jobs) 
    elite_cost = float('inf')
    elite_schedule = []
    analyse_dict = {}
    
    original_schedule = waiting_jobs 
    analyse_dict.update({0:get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new)})
    
    ga = GA(dna_size=len(waiting_jobs), cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, pop = waiting_jobs)
    for generation in range(1, N_GENERATIONS+1):
        cost = [get_energy_cost(i, first_start_time, job_dict_new, price_dict_new) for i in ga.pop]
        fitness = ga.get_fitness(cost)
    
        best_idx = np.argmax(fitness)
#         print('Gen:', generation, '| best fit %.2f' % fitness[best_idx])
#         print("Most fitted DNA: ", ga.pop[np.argmax(fitness)])
#         print("Most fitted cost: ", cost[np.argmax(fitness)])
        analyse_dict.update({generation:cost[np.argmax(fitness)]})
        
        if cost[np.argmax(fitness)] < elite_cost:
            elite_cost = cost[np.argmax(fitness)]
            elite_schedule = ga.pop[np.argmax(fitness)]
        
        ga.evolve(fitness)

    print()
    print("Optimal cost:", elite_cost)
    print("Optimal schedule:", elite_schedule)
    
    print()
          
    print("Original schedule: ", original_schedule)
    print("Original schedule start time:", first_start_time)
    print("Original cost: ", get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new))
    
    
    # write the result to csv for plot
    with open('ga_analyse_plot.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in analyse_dict.items():
            writer.writerow([key, value])
    