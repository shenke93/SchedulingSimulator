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

from geneticAlgorithm013Conventional import select_jobs, read_job, select_prices, read_price, read_maintenance, read_product_related_characteristics
from geneticAlgorithm013Conventional import get_energy_cost, get_failure_cost, GA

POP_SIZE = 8   
CROSS_RATE = 0.6
MUTATION_RATE = 0.8
N_GENERATIONS = 200
weight1 = 1 # weight of failure cost
weight2 = 1 # weight of energy cost

def run_GA(x_ax, y_ax):
#     global best_cost 
    
    best_cost = float('inf')
    for generation in range(1, N_GENERATIONS+1): 
        failure_cost = [weight1*get_failure_cost(i, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict) for i in ga.pop]
        energy_cost = [weight2*get_energy_cost(i, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict) for i in ga.pop]
        fitness = np.array(ga.get_fitness(failure_cost, energy_cost))
#         print("Fitness:", fitness)

        best_index = np.argmin(fitness)
#         best_cost = fitness[best_index]
        if fitness[best_index] < best_cost:
            best_cost = fitness[best_index]
            
        ga.evolve(fitness)
        
        if (generation % 25 == 0) :
            x_ax.append(generation)
            y_ax.append(best_cost)
# #         print("generation:", generation)
#         popu, res = ga.evolve(1)          # natural selection, crossover and mutation
#         best_index = np.argmin(res)
# #         print("Most fitted DNA: ", pop[best_index])
# #         print("Most fitted cost: ", res[best_index])
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


#         print("Best_schedule place3:", candidate_schedule)    
#     print("Test:", popu[best_index])
#     ax.plot(x, y, marker='o')
    return ga.pop[best_index]
    
#     print("Best_schedule place5:", candidate_schedule)

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
    best_cost = 1e10
    
   
    
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
    
    fig = plt.figure(figsize=(7, 5))
#     ax = fig.add_subplot(111)
    
    x_ax = []
    y_ax = []
    while x < 50:
        candidate_schedule = run_GA(x_ax, y_ax)
        print("x:", x)
        x += 1
    
#     print(x_ax)
#     print(y_ax)
    avg = [0] * 8
    for i in range(len(y_ax)):
        if (i % 8 == 0):
            avg[0] += y_ax[i]
        if (i % 8 == 1):
            avg[1] += y_ax[i]
        if (i % 8 == 2):
            avg[2] += y_ax[i]
        if (i % 8 == 3):
            avg[3] += y_ax[i]
        if (i % 8 == 4):
            avg[4] += y_ax[i]
        if (i % 8 == 5):
            avg[5] += y_ax[i]
        if (i % 8 == 6):
            avg[6] += y_ax[i]
        if (i % 8 == 7):
            avg[7] += y_ax[i]
    
    avg = [e / 50 for e in avg]
#     print(avg)     
# Add data of other methods.
    avg2 = [12310.473759458153, 12309.918693662166, 12309.217362086078, 12309.217362086078, 12309.071228887069, 12309.041775716567, 12308.720202884926, 12308.720202884926]
    avg3 = [13510.247495874377, 13421.143581355014, 13510.009394722294, 13393.547880957962, 13614.693493175668, 13421.621106683828, 13585.140896015942, 13478.93352650872]

    x = [25, 50, 75, 100, 125, 150, 175, 200]
    plt.plot(x, avg, marker='o', label='CGA')
    plt.plot(x, avg2, marker='^', label='IGA')
    plt.plot(x, avg3, marker='s', label='RCA')

    plt.xlabel("GA Generation", fontsize='xx-large')
    plt.ylabel("Average Cost (€)", fontsize='xx-large')
    plt.xticks(fontsize='xx-large')
    plt.yticks(fontsize='xx-large')
    plt.legend()
    plt.show()
#     
#     plt.xlabel("GA Generation", fontsize='xx-large')
#     plt.ylabel("Total Cost (€)", fontsize='xx-large')
#     plt.xticks(fontsize='xx-large')
#     plt.yticks(fontsize='xx-large')
#     plt.text(100, 13750, 'Population size: 8\nCrossover rate: 0.6\nMutation rate: 0.8\nMaximal iteration: 200', fontdict={'size': 'xx-large', 'color': 'black'})
    
#     print("Most fitted cost:", best_cost)
#     print("Most fitted schedule:", candidate_schedule)
    
#     plt.show()

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
    