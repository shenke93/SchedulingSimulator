''' Plot the objective-generation plot for a GA method.
    Help to analyse the performance of the GA.
    Monte Carlo simulation of GA.
'''

from datetime import datetime
import time
import numpy as np
import csv
import matplotlib
import matplotlib.pyplot as plt

from geneticAlgorithm013 import select_jobs, read_job, select_prices, read_price, read_maintenance, read_product_related_characteristics
from geneticAlgorithm013 import get_energy_cost, get_failure_cost, GA

POP_SIZE = 8   
CROSS_RATE = 0.6
MUTATION_RATE = 0.8
N_GENERATIONS = 200
weight1 = 1 # weight of failure cost
weight2 = 1 # weight of energy cost

np.random.seed(1234)

# def run_GA():
#     global best_cost 
#     x = [0]
#     y = [weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)+
#                         weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict)]
#     
#     for generation in range(1, N_GENERATIONS+1):
# #         print("generation:", generation)
#         popu, res = ga.evolve(1)          # natural selection, crossover and mutation
#         best_index = np.argmin(res)
# #         print("Most fitted DNA: ", pop[best_index])
# #         print("Most fitted cost: ", res[best_index])
#         
#         # TODO: check best_schedule
#           
#         t = best_cost
#         if (res[best_index] < t):
# #             print("Yes")     
# #             print("cond1:", res[best_index])
# #             print("cond2:", t)
#             best_cost =  res[best_index]   
#             
# #             print("Best_schedule:", popu[best_index])
#              
#         x.append(generation)
#         y.append(res[best_index])
# #         print("Best_schedule place3:", candidate_schedule)    
# #     print("Test:", popu[best_index])
#     plt.plot(x, y, marker='o', markevery=10)
#     return popu[best_index]
    
def run_GA():
#     global best_cost 
    x = [0]
    y = [weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)+
                        weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict)]
    
    for generation in range(1, N_GENERATIONS+1):
#         print("generation:", generation)
        popu, res = ga.evolve(1)          # natural selection, crossover and mutation
        best_index = np.argmin(res)
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
          
#         t = best_cost
#         if (res[best_index] < t):
# #             print("Yes")     
# #             print("cond1:", res[best_index])
# #             print("cond2:", t)
#             best_cost =  res[best_index]   
#             
# #             print("Best_schedule:", popu[best_index])
             
        x.append(generation)
        y.append(res[best_index])
#         print("Best_schedule place3:", candidate_schedule)    
#     print("Test:", popu[best_index])
    global best_cost
    global candidate_schedule
    if (res[best_index]) < best_cost:
        best_cost = res[best_index]
        print('best_cost:', best_cost)
        candidate_schedule = popu[best_index]
        print('candidate_schedule:', candidate_schedule)
    plt.plot(x, y, marker='o', markevery=10)


if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
#     case 1
    start_time = datetime(2016, 11, 3, 6, 0)
    end_time = datetime(2016, 11, 8, 0, 0)
    
#     case 2
#     start_time = datetime(2016, 11, 7, 0, 0)
#     end_time = datetime(2016, 11, 12, 0, 0)

# case 2 years
#     start_time = datetime(2016, 1, 19, 14, 0)
#     end_time = datetime(2017, 11, 15, 0, 0)
    
    price_dict_new = read_price("price.csv")
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfoProd_ga_013.csv"))
    failure_dict_new = read_maintenance("maintenanceInfluenceb4a4.csv", price_dict_new)
    raw_material_unit_price_dict = read_product_related_characteristics("productProd_ga_013.csv")

    
    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
        
#     exit()

#     print(waiting_jobs) 
#     elite_cost = float('inf')
    candidate_schedule = []
    best_cost = float('inf')
    
   
    
    original_schedule = waiting_jobs 
#     analyse_dict.update({0:get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)+
#                          get_failure_cost(original_schedule, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict)}) # Add origin to index 0
#     
#     start_stamp = time.time()
    ga = GA(dna_size=DNA_SIZE, cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=failure_dict_new,
            product_related_characteristics_dict=raw_material_unit_price_dict, start_time=first_start_time,
            weight1 = weight1, weight2 = weight2)
 
#     for generation in range(1, N_GENERATIONS+1):
# #         if (generation % 20) == 0:
# #             print("Gen: ", generation)
#         pop, res = ga.evolve(1)          # natural selection, crossover and mutation
#         best_index = np.argmin(res)
# #         print("Most fitted DNA: ", pop[best_index])
# #         print("Most fitted cost: ", res[best_index])
# #         best_schedule = pop[best_index]
# #         best_cost = res[best_index]
#         analyse_dict.update({generation:res[best_index]})
         
#     end_stamp = time.time()
    x = 0
    
    plt.figure(figsize=(10, 6))   
    while x < 50:
        run_GA()
        print("x:", x)
        x += 1
        
    plt.xlabel("GA Generation", fontsize='xx-large')
    plt.ylabel("Total Cost (€)", fontsize='xx-large')
    plt.xticks(fontsize='xx-large')
    plt.yticks(fontsize='xx-large')
    plt.text(120, 14500, 'Population size: 8\nCrossover rate: 0.6\nMutation rate: 0.8\nMaximal iteration: 200', fontdict={'size': 'xx-large', 'color': 'black'})
   
    print("Most fitted cost:", best_cost)
    print("Most fitted schedule:", candidate_schedule)
    
    plt.show()

#     print("Most fitted DNA:", best_schedule)

    
#     print()
#     print("Optimal cost:", elite_cost)
#     print("Optimal schedule:", elite_schedule)
#     print("Time consumption:", end_stamp-start_stamp)
    
#     print()
          
#     print("Original schedule: ", original_schedule)
#     print("Original schedule start time:", first_start_time)
#     print("Original cost: ", get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)+
#                          get_failure_cost(original_schedule, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict))
#     
    
    # write the result to csv for plot
#     with open('ga_013_analyse_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in analyse_dict.items():
#             writer.writerow([key, value])
    