'''This is the script for finding the optimal solution using brute force method in comparison with near-optimal methods.
Features: 1. For permutation of size 9 
          2. Output to tmp file.
'''

import itertools
import time
import csv
import sys
from datetime import datetime
from geneticAlgorithm002 import select_jobs, select_prices, get_energy_cost, read_job, read_price

def brute_force(range1, range2, start_time, job_dict, price_dict):
    space = itertools.permutations(range(range1, range2))
    optimal_cost = float('inf')
    optimal_schedule = []
    for item in space:
        ind_cost = get_energy_cost(item, start_time, job_dict, price_dict)
        if  ind_cost <= optimal_cost:
            optimal_cost = ind_cost
            optimal_schedule.append(item)
    return {optimal_cost: optimal_schedule}
    
    
if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    start_time = datetime(2016, 2, 20, 15, 0)
    end_time = datetime(2016, 2, 24, 0, 0)
    
#     price_dict = {}
#     job_dict = {}
#     
#     ''' Input: Energy price
#         Input file: price_ga.csv
#         format: date(date), price(float)
#     '''
#     try:
#         with open('price.csv', encoding='utf-8') as price_csv:
#             reader = csv.DictReader(price_csv)
#             for row in reader:
#                 price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})
#     except:
#         print("Unexpected error when reading energy price:", sys.exc_info()[0]) 
#         exit()
# 
#     ''' Input: List of jobs (original schedule)
#         Input file: jobInfo_ga.csv
#         format: index(int), duration(float), power(float)
#     '''
#     try:
#         with open('jobInfo.csv', encoding='utf-8') as jobInfo_csv:
#             reader = csv.DictReader(jobInfo_csv)
#             for row in reader:
#                 job_dict.update({int(row['ID']):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"), 
#                                                  datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"), float(row['Power'])]})
#     except:
#         print("Unexpected error when reading job information:", sys.exc_info()[0]) 
#         exit()
     
#     print(price_dict)        
#     print(job_dict)        
    
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfo.csv"))
    price_dict_new = select_prices(start_time, end_time, read_price("price.csv"))
#     DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  
        
    
    sys.stdout = open('bruteForceOut.txt', 'w')

    print("Waiting jobs: ", waiting_jobs) 
    print("Prices: ", price_dict_new) 
        
    print()
    original_schedule = waiting_jobs        
    print("Original schedule: ", original_schedule)
    print("Original schedule start time:", first_start_time)
    print("Original cost: ", get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new))
    
    start_stamp = time.time() 
    brute = brute_force(waiting_jobs[0], waiting_jobs[-1]+1, first_start_time, job_dict_new, price_dict_new)
    end_stamp = time.time()
    
    print("Optimal cost:", brute.keys())
    print("Optimal schedule:", brute.values())
    print("Time consumption:", end_stamp-start_stamp)
        