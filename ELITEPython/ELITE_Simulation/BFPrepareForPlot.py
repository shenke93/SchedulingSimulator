''' Idea: 
    1. Choose date range for 9 jobs: [69, 70, 71, 72, 73, 74, 75, 76, 77], from 2016.2.20 15:00:00 to 2016.2.26 00:00:00
    2. Run brute force method for size [3 - 9], monitoring execution time and result
'''
import time
import csv
from datetime import datetime
from bruteForce import brute_force
from geneticAlgorithm002 import read_job, read_price, select_jobs, select_prices

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
    
    BFResult_dict = {}
    
    for i in range(3, 10):
        jobs = waiting_jobs[0:i]
        print("Selected jobs: ", jobs)
        start_stamp = time.time() 
        brute = brute_force(jobs[0], jobs[-1]+1, first_start_time, job_dict_new, price_dict_new)
        end_stamp = time.time()
        
        print("Optimal cost:", brute.keys())
        print("Optimal schedule:", brute.values())
        print("Time consumption:", end_stamp-start_stamp)
        BFResult_dict.update({i:(end_stamp-start_stamp)})
    
    # write the result to csv for plot
    with open('bf_plot.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in BFResult_dict.items():
            writer.writerow([key, value])