import numpy as np
import csv
import math
from datetime import timedelta, datetime

# DNA_SIZE
# POP_SIZE
# CROSS_RATE
# MUTATION_RATE
# N_GENERATIONS

def ceil_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt

def floor_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt

def get_fitness(indiviaual, start_time, job_dict, price_dict):
    ''' Give an individual (a possible schedule in our case), calculate its energy cost '''
    t_now = start_time # current timestamp
    for item in indiviaual:
        print("For job: %d" % item)
        t_start = t_now
        print("Time start: " + str(t_now))
        du = job_dict.get(item, -1)
        # TODO: if get duration failed (du == -1), handle this situation
        t_end = t_start + timedelta(hours=du)
        print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price
        print("Ceil time start to the next hour:" + str(ceil_dt(t_start, timedelta(hours=1))))
        print("Floor time end to the previous hour:" + str(floor_dt(t_end, timedelta(hours=1))))

        t_now = t_end
    
        

if __name__ == '__main__':
    
    start_time = datetime(2016, 11, 7, 1, 0)
    price_dict = {}
    job_dict = {}
    
    # TODO: handle exceptions: file not exist etc.
    ''' Input: Energy price
        Input file: price_ga.csv
        format: date(date), price(float)
    '''
    with open('price_ga.csv', encoding='utf-8') as price_csv:
        reader = csv.DictReader(price_csv)
        for row in reader:
            price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})

    ''' Input: List of jobs (original schedule)
        Input file: jobInfo_ga.csv
        format: index(int), duration(float)
    '''
    with open('jobInfo_ga.csv', encoding='utf-8') as jobInfo_csv:
        reader = csv.DictReader(jobInfo_csv)
        for row in reader:
            job_dict.update({int(row['ID']):float(row['Duration'])})
     
    print(price_dict)        
    print(job_dict)        
 
    # We use an individual for test: 
    arr = np.arange(1, 6)
    np.random.shuffle(arr)
    print(arr)
    
    get_fitness(arr, start_time, job_dict, price_dict)