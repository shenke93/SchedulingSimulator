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
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
        print("\nFor job: %d" % item)
        t_start = t_now
        print("Time start: " + str(t_now))
        du = job_dict.get(item, -1)
        # TODO: if get duration failed (du == -1), handle this situation
        t_end = t_start + timedelta(hours=du)
        print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_u = ceil_dt(t_start, timedelta(hours=1))
        t_d = floor_dt(t_end, timedelta(hours=1)) 
        print("Ceil time start to the next hour:" + str(t_u))
        print("Floor time end to the previous hour:" + str(t_d))
        tmp = price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0)*((t_u - t_start)/timedelta(hours=1)) +  price_dict.get(t_d, 0)*((t_end - t_d)/timedelta(hours=1))
        print("Head price: %f" % price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0))
        print("Tail price: %f" % price_dict.get(t_d, 0))
        print("Head and tail cost: %f" % tmp)
        step = timedelta(hours=1)
        while t_u < t_d:
            energy_cost += price_dict.get(t_u, 0)
            t_u += step
        
        energy_cost += tmp
        t_now = t_end
    
    return energy_cost

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
#     np.random.shuffle(arr)
    print(arr)
    
    print(get_fitness(arr, start_time, job_dict, price_dict))