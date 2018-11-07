''' Random choice algorithm is used as baseline comparison of CGA and IGA.
'''

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from geneticAlgorithm013 import read_price, select_jobs, read_job, read_maintenance, read_product_related_characteristics
from geneticAlgorithm013 import get_energy_cost, get_failure_cost

weight1 = 1
weight2 = 1
np.random.seed(1234)

def run_randomSelection(y_ax):
#     candidate = []
#     cost = float('inf')
    cost = weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)+weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, failure_dict_new, raw_material_unit_price_dict)
    for i in range(1, 208): 
        s = np.random.permutation(waiting_jobs)
        energy_cost = get_energy_cost(s, first_start_time, job_dict_new, price_dict_new, raw_material_unit_price_dict)
        failure_cost = get_failure_cost(s, first_start_time, job_dict_new, 
                                             failure_dict_new, raw_material_unit_price_dict)
        
        if ((energy_cost + failure_cost) < cost):
            cost = energy_cost + failure_cost
        
        if (((i-7) % 25 == 0) & (i != 7)):
#             print(i)
            y_ax.append(cost)
        
        


if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
    Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    
    #     case 1
    start_time = datetime(2016, 11, 3, 6, 0)
    end_time = datetime(2016, 11, 8, 0, 0)

    # case 1 year
#     start_time = datetime(2016, 1, 19, 14, 0)
#     end_time = datetime(2016, 12, 24, 0, 0)
    
    price_dict_new = read_price("price.csv")
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfoProd_ga_013.csv"))
    failure_dict_new = read_maintenance("maintenanceInfluenceb4a4.csv", price_dict_new)
    raw_material_unit_price_dict = read_product_related_characteristics("productProd_ga_013.csv")

    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
        
    original_schedule = waiting_jobs
    
    y_ax = []
    
    for x in range(0, 50):
        print("x:", x)
        d = run_randomSelection(y_ax)
    

    # Calculate avg of simulation results.
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
    
    # Calculate min of simulation results.
    t = [float('inf')] * 8
    for i in range(len(y_ax)):
        if (i % 8 == 0):
            t[0] = min(t[0], y_ax[i])
        if (i % 8 == 1):
            t[1] = min(t[1], y_ax[i])
        if (i % 8 == 2):
            t[2] = min(t[2], y_ax[i])
        if (i % 8 == 3):
            t[3] = min(t[3], y_ax[i])
        if (i % 8 == 4):
            t[4] = min(t[4], y_ax[i])
        if (i % 8 == 5):
            t[5] = min(t[5], y_ax[i])
        if (i % 8 == 6):
            t[6] = min(t[6], y_ax[i])
        if (i % 8 == 7):
            t[7] = min(t[7], y_ax[i])
            
    # Calculate max of simulation results.
    u = [0] * 8
    for i in range(len(y_ax)):
        if (i % 8 == 0):
            u[0] = max(u[0], y_ax[i])
        if (i % 8 == 1):
            u[1] = max(u[1], y_ax[i])
        if (i % 8 == 2):
            u[2] = max(u[2], y_ax[i])
        if (i % 8 == 3):
            u[3] = max(u[3], y_ax[i])
        if (i % 8 == 4):
            u[4] = max(u[4], y_ax[i])
        if (i % 8 == 5):
            u[5] = max(u[5], y_ax[i])
        if (i % 8 == 6):
            u[6] = max(u[6], y_ax[i])
        if (i % 8 == 7):
            u[7] = max(u[7], y_ax[i])

    
    x = [25, 50, 75, 100, 125, 150, 175, 200]
    plt.figure(figsize=(10, 6))
    plt.plot(x, t, marker='s', label='MIN', color = 'blue')
    plt.plot(x, u, marker='o', label='MAX', color = 'darkblue')
    plt.plot(x, avg, marker='^', label='AVG', color = 'mediumblue')
    plt.xlabel("Iteration", fontsize='xx-large')
    plt.ylabel("Total Cost (€)", fontsize='xx-large')
    plt.xticks(fontsize='xx-large')
    plt.yticks(fontsize='xx-large')
    plt.legend()
    
    plt.show()
    print(avg)