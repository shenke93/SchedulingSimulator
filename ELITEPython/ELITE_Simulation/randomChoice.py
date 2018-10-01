''' Random choice is a kind of brute force method which generates a random sequence of job and then calculate the cost.
'''

from geneticAlgorithm011 import get_energy_cost, get_failure_cost, read_price, read_job, select_jobs, read_maintenance
from datetime import datetime
import numpy as np
import csv

if __name__ == '__main__':
    start_time = datetime(2016, 1, 23, 17, 0)
    end_time = datetime(2017, 12, 29, 8, 0)
    
    price_dict_new = read_price("price.csv")
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfoPack_ga.csv"))
    failure_dict_new = read_maintenance("maintenanceInfluence.csv", price_dict_new)
    
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule
    
    elitism = float('inf')  
    result_dict = {} 
    for i in range(1500):
        if i % 10 == 0:
            print(i)
        possible_sequence = np.random.permutation(waiting_jobs)
        energy_cost = get_energy_cost(possible_sequence, first_start_time, job_dict_new, price_dict_new)
        failure_cost = get_failure_cost(possible_sequence, first_start_time, job_dict_new, failure_dict_new)
        elitism = min(energy_cost+failure_cost, elitism)
        result_dict.update({i:elitism})
    
    print('Elitism:', elitism)
    
    with open('randomchoice_011_analyse_plot.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict.items():
            writer.writerow([key, value])
        
    