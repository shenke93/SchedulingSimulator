''' Convergence analysis of random choice algorithm.
'''

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from geneticAlgorithm013 import read_price, select_jobs, read_job, read_maintenance, read_product_related_characteristics
from geneticAlgorithm013 import get_energy_cost, get_failure_cost

weight1 = 1 # weight of failure cost
weight2 = 1 # weight of energy cost
N_GENERATIONS = 200

np.random.seed(1234)

def run_randomSelection():
    x = []
    y = []
    
    cost = weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)+weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict)
    for i in range(1, 208): 
        s = np.random.permutation(waiting_jobs)
        energy_cost = get_energy_cost(s, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)
        failure_cost = get_failure_cost(s, first_start_time, job_dict_new, 
                                             failure_dict_new, raw_material_unit_price_dict)
        
        
        
        if ((energy_cost + failure_cost) < cost):
            cost = energy_cost + failure_cost
#         
        if (((i-7) % 25 == 0) & (i != 7)):
#             print(i)
            x.append(i-7)
            y.append(cost)
            
    plt.plot(x, y, marker='o')
    
    
if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
    Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    
    start_time = datetime(2016, 11, 3, 6, 0)
    end_time = datetime(2016, 11, 8, 0, 0)
    
    price_dict_new = read_price("price.csv")
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfoProd_ga_013.csv"))
    failure_dict_new = read_maintenance("maintenanceInfluenceb4a4.csv", price_dict_new)
    raw_material_unit_price_dict = read_product_related_characteristics("productProd_ga_013.csv")

    waiting_jobs = [*job_dict_new]
    original_schedule = waiting_jobs
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
    

    
    plt.figure(figsize=(10, 6))
    
    for x in range(0, 50):
        print("x:", x)
        d = run_randomSelection()

    plt.xlabel("Iteration", fontsize='xx-large')
    plt.ylabel("Total Cost (€)", fontsize='xx-large')
    plt.xticks(fontsize='xx-large')
    plt.yticks(fontsize='xx-large')
    
    plt.show()
#     print(avg)