''' Version 0.0.4
    Features: 1. Apply basic evolution strategy to Soubry case
'''
import sys
import numpy as np
import csv
from datetime import timedelta, datetime

POP_SIZE = 20  
N_KID = 10  # n kids per generation
N_GENERATIONS = 100


def ceil_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt

def floor_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt

def get_energy_cost(indiviaual, start_time, job_dict, price_dict):
    ''' Give an individual (a possible schedule in our case), calculate its energy cost '''
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
#         print("\nFor job: %d" % item)
        t_start = t_now
#         print("Time start: " + str(t_now))
        unit = job_dict.get(item, -1)
        if unit == -1:
            raise ValueError("No matching item in the job dict for %d" % item)
        du = unit[0] # get job duration
        po = unit[3] # get job power profile
        t_end = t_start + timedelta(hours=du)
#         print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start up
        t_ed = floor_dt(t_end, timedelta(hours=1)) #    t_end down
        t_sd = floor_dt(t_now, timedelta(hours=1))
#         print("Ceil time start to the next hour:" + str(t_u))
#         print("Floor time end to the previous hour:" + str(t_d))
        if price_dict.get(t_sd, 0) == 0 or price_dict.get(t_ed, 0) == 0:
            raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
        tmp = price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) +  price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))
#         print("Head price: %f" % price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0))
#         print("Tail price: %f" % price_dict.get(t_d, 0))
#         print("Head and tail cost: %f" % tmp)
        step = timedelta(hours=1)
        while t_su < t_ed:
            if price_dict.get(t_su, 0) == 0:
                raise ValueError("For item %d: No matching item in the price dict for %s" % (item, t_su))
            energy_cost += price_dict.get(t_su, 0) * po
            t_su += step
        
        energy_cost += tmp * po
        t_now = t_end
    
    return energy_cost

def locate_min(a):
    ''' Find the smallest value of a list and all its indexes.
    '''
    smallest = min(a)
    return smallest, [index for index, element in enumerate(a) 
                      if smallest == element]

def select_jobs(daterange1, daterange2, job_dict):
    ''' Select jobs between daterange1 and daterange2 from original job_dict and
    return a new dict.
    '''
    dict = {}
    for key, value in job_dict.items():
        if value[1] >= daterange1 and value[2] <= daterange2:
            dict.update({key:value})
    return dict
        
        
def select_prices(daterange1, daterange2, price_dict):
    ''' Select prices between deterange1 and daterange2 form original price_dict and
    return a new dict.
    '''
    dict = {}
    for key, value in price_dict.items():
        if key >= daterange1 and key <= daterange2:
            dict.update({key:value})
    return dict

def read_price(priceFile):
    price_dict = {}
    
    ''' Input: Energy price
        Input file: price_ga.csv
        format: date(date), price(float)
    '''
    try:
        with open(priceFile, encoding='utf-8') as price_csv:
            reader = csv.DictReader(price_csv)
            for row in reader:
                price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})
    except:
        print("Unexpected error when reading energy price:", sys.exc_info()[0]) 
        exit()
    return price_dict

def read_job(jobFile):
    job_dict = {}
    
    ''' Input: List of jobs (original schedule)
        Input file: jobInfo_ga.csv
        format: index(int), duration(float), power(float)
    '''
    try:
        with open(jobFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                job_dict.update({int(row['ID']):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"), 
                                                 datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"), float(row['Power'])]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return job_dict
def get_fitness(pred): return pred

def make_kid(pop, n_kid, dna_size, pop_size): 
    ''' Generate n kids from parents
    '''
#     print('Enter make_kid procedure:')
    kids = {'DNA': np.empty((n_kid, dna_size))}
    kids['mut_strength'] = np.empty_like(kids['DNA'])
    for kv, ks in zip(kids['DNA'], kids['mut_strength']):
        p1, p2 = np.random.choice(np.arange(pop_size), size=2, replace=False)
#         print('p1, p2:', p1, p2)
        cp = np.random.randint(0, 2, dna_size, dtype=np.bool)   # crossover point
#         print('cp:', cp)
#         print('''pop['DNA'][p1]:''',pop['DNA'][p1])
        kv[cp] = pop['DNA'][p1, cp]
#         print('tmp:', kv[cp])
#         print('''pop['DNA'][p2]:''',pop['DNA'][p2])        
        kv[~cp] = pop['DNA'][p2, np.isin(pop['DNA'][p2], pop['DNA'][p1, cp], invert=True)]  # can not have repeated jobs
#         print('New DNA after crossover:', kv)
        ks[cp] = pop['mut_strength'][p1, cp]
        ks[~cp] = pop['mut_strength'][p2, ~cp]
#         print('New mut_strength after crossover:', ks)
        
        # mutate (change the largest with smallest)
        i1, i2 = np.argmax(ks), np.argmin(ks)
        swap_1, swap_2 = kv[i1], kv[i2]
        kv[i1], kv[i2] = swap_2, swap_1
        ks[:] = np.maximum(ks + (np.random.rand(*ks.shape) - 0.5), 0.)

#         print(ks)  
#     print(kids)     
    return kids

def kill_bad(pop, kids, start_time, job_dict, price_dict):
#     print('Enter kill bad procedure:')
    for key in ['DNA', 'mut_strength']:
#         print('key:', key)
        pop[key] = np.vstack((pop[key], kids[key]))
#         print('pop[key]:', pop[key])

    fitness = get_fitness([get_energy_cost(i, start_time, job_dict, price_dict) for i in pop['DNA']])    # calculate global fitness
#     print('fitness:', fitness)
    idx = np.arange(pop['DNA'].shape[0])
#     print('idx:', idx)
    good_idx = idx[np.array(fitness).argsort()]   # selected by fitness ranking (not value)
#     print('good_idx:', good_idx)
    for key in ['DNA', 'mut_strength']:
        pop[key] = pop[key][good_idx]

    return pop
    
if __name__ == '__main__':
    
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-19 14:21:43.910 to 2017-11-15 07:45:24.243
    '''
    start_time = datetime(2016, 2, 20, 15, 0)
    end_time = datetime(2016, 2, 26, 0, 0)
    
    job_dict_new = select_jobs(start_time, end_time, read_job("jobInfo.csv"))
    price_dict_new = select_prices(start_time, end_time, read_price("price.csv"))
    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule
    
    print("Waiting jobs: ", waiting_jobs)
    print("Prices: ", price_dict_new)
    
    
    
    pop = dict(DNA=np.vstack([np.random.choice(waiting_jobs, size=DNA_SIZE, replace=False) for _ in range(POP_SIZE)]),
           mut_strength=np.random.rand(POP_SIZE, DNA_SIZE))
    
#     print("pop:", pop)
    
#     result_dict = {}
#     original_schedule = waiting_jobs 
#     result_dict.update({0:get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new)})
    for generation in range(1, N_GENERATIONS+1):
        if (generation % 10) == 0:
            print("Gen: ", generation)
        kids = make_kid(pop, N_KID, DNA_SIZE, POP_SIZE)
#         print("kids:", kids)
        pop = kill_bad(pop, kids, first_start_time, job_dict_new, price_dict_new)
#         print("pop:", pop)
#         print('Candidate schedule:', pop['DNA'][0])
#         result_dict.update({generation:get_energy_cost(pop['DNA'][0], first_start_time, job_dict_new, price_dict_new)})

    
    print('Optimal schedule:', pop['DNA'][0])
    print("Optimal cost:", get_energy_cost(pop['DNA'][0], first_start_time, job_dict_new, price_dict_new))
    
    # write the result to csv for plot
#     with open('ga_004_analyse_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in result_dict.items():
#             writer.writerow([key, value])    