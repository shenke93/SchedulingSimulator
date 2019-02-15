''' Apply 1-1 ES to the scheduler.
    Possible improvements: 1. Make sure each iteration can lead to a better solution.
                           2. Check if MUT_STRENGTH goes too low, is it possible to stop the iterations.
                           3. Considering the measuremets, compare with the IGA (from Sensor paper).
'''
import sys
import csv
import numpy as np
from datetime import timedelta, datetime

N_GENERATIONS = 200
POP_SIZE = 8 
MUT_STRENGTH = 5


def ceil_dt(dt, delta):
    ''' 
    Ceil a data time dt according to the measurement delta.

    Parameters
    ----------
    dt : datatime
        Objective date time to ceil.
    delta : timedelta
        Measurement precision.

    Returns
    -------
    Ceiled date time

    '''
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt


def floor_dt(dt, delta):
    ''' 
    Floor a data time dt according to the measurement delta.

    Parameters
    ----------
    dt : datatime
        Objective date time to floor.
    delta : timedelta
        Measurement precision.

    Returns
    -------
    Floored date time
    '''
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt


def get_failure_cost(indiviaual, start_time, job_dict, health_dict, product_related_characteristics_dict):
    ''' 
    Calculate the falure cost of an individual.

    Parameters
    ----------
    individual: List
        A list of job indexes.
    
    start_time: Date
        Start time of the individual.
        
    job_dict: dict
        Dictionary of jobs.
        
    health_dict: dict
        Dictionary of houly dependent failure rates.
        
    product_related_characteristics_dict: dict
        Dictionary of product related characteristics.
    
    Returns
    -------
    The failure cost of an individual.
    '''
    failure_cost = 0
    t_now = start_time
    for item in indiviaual:
        t_start = t_now
        unit = job_dict.get(item, -1)
        if unit == -1:
            raise ValueError("No matching item in job dict: ", item)
        du = unit[0]    # get job duration
        product_type = unit[4]    # get job product type
        quantity = unit[3]  # get job quantity
        
        if du <= 1: # safe period of 1 hour (no failure cost)
            continue;
        
        t_start = t_start+timedelta(hours=1) # exclude safe period, find start of sensitive period
        t_end = t_start + timedelta(hours=(du-1)) # end of sensitive period
        
        t_su = ceil_dt(t_start, timedelta(hours=1)) #    t_start right border
        t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        t_sd = floor_dt(t_start, timedelta(hours=1))  #    t_start left border
        
        if health_dict.get(t_sd, -1) == -1 or health_dict.get(t_ed, -1) == -1:
            raise ValueError("For item %d: In boundary conditions, no matching item in the health dict for %s or %s" % (item, t_sd, t_ed))
        
        tmp = (1 - health_dict.get(t_sd, 0)) * (1 - health_dict.get(t_ed, 0))
        step = timedelta(hours=1)
        while t_su < t_ed:
            if health_dict.get(t_su, -1) == -1:
                raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
            tmp *= (1-health_dict.get(t_su, 0)) 
            t_su += step
        
        if product_related_characteristics_dict.get(product_type, -1) == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
        failure_cost += (1-tmp) * quantity * product_related_characteristics_dict.get(product_type)[0]
        t_now = t_end
    
    return failure_cost


def get_energy_cost(indiviaual, start_time, job_dict, price_dict, product_related_characteristics_dict):
    ''' 
    Calculate the energy cost of an individual.

    Parameters
    ----------
    individual: List
        A list of job indexes.
    
    start_time: Date
        Start time of the individual.
        
    job_dict: dict
        Dictionary of jobs.
        
    health_dict: dict
        Dictionary of houly dependent failure rates.
        
    product_related_characteristics_dict: dict
        Dictionary of product related characteristics.
    
    Returns
    -------
    The energy cost of an individual.
    '''
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
        t_start = t_now
#         print("Time start: " + str(t_now))
        unit1 = job_dict.get(item, -1)
        if unit1 == -1:
            raise ValueError("No matching item in the job dict for %d" % item)
       
        du = unit1[0] # get job duration
        product_type = unit1[4] # get job product type
        
        unit2 = product_related_characteristics_dict.get(product_type, -1)
        if unit2 == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
        
        po = unit2[1] # get job power profile
        
        t_end = t_start + timedelta(hours=du)
#         print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start right border
        t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        t_sd = floor_dt(t_start, timedelta(hours=1)) # t_start_left border
#         print("Ceil time start to the next hour:" + str(t_u))
#         print("Floor time end to the previous hour:" + str(t_d))
        if price_dict.get(t_sd, 0) == 0 or price_dict.get(t_ed, 0) == 0:
            raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
        tmp = price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) + price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))
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


def read_prcd(productFile):
    ''' 
    Create a dictionary to store product related characteristics from productFile.

    Parameters
    ----------
    productFile : string
        Name of file containing job information. Columns contained: Product, UnitPrice, Power.

    Returns
    -------
    Dictionary containing product related characteristics, key: string, value: list of float.
    '''
    product_related_characteristics_dict = {}
    try:
        with open(productFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                product_related_characteristics_dict.update({row['Product']:[float(row['UnitPrice']), float(row['Power'])]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return product_related_characteristics_dict


def read_price(priceFile):
    ''' 
    Create a dictionary to restore hourly dependent energy price.

    Parameters
    ----------
    priceFile: string
        Name of file containing energy price.
    
    Returns
    -------
    A dictionary containing hourly dependent energy price, key: Date, value: float.
    '''
    price_dict = {}
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
    ''' 
    Create a dictionary to restore job information.

    Parameters
    ----------
    jobFile: string
        Name of file containing job information.
    
    Returns
    -------
    A dictionary containing job indexes and characteristics, key: int, value: list.
    '''
    job_dict = {}
    try:
        with open(jobFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                job_dict.update({int(row['ID']):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"), 
                                                 datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"),
                                                 float(row['Quantity']), row['Product']]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0]) 
        exit()
    return job_dict 


def select_jobs(daterange1, daterange2, job_dict):
    ''' 
    Create a dictionary to restore selected job information in a time range.

    Parameters
    ----------
    daterange1: Date
        Start datestamp of selected jobs.
    
    daterange2: Date
        End datestemp of selected jobs.
        
    job_dict: dict
        Dictionary of jobs
    
    Returns
    -------
    A dictionary containing jobs in the selected date range.
    '''
    res_dict = {}
    for key, value in job_dict.items():
        if value[1] >= daterange1 and value[2] <= daterange2:
            res_dict.update({key:value})
    return res_dict


def read_failure(maintenanceFile, price_dict):
    ''' 
    Create a list to store influences of maintenances. 

    Parameters
    ----------
    maintenanceFile: string
        Name of file containing maintenance records.
        
    price_dict: dictionary
        Dict of hourly dependent energy price whose time range will be used in the dict for failure rate.
    
    Returns
    -------
    A dictionary of hourly dependent failure rate, key: Date, value: float.
    '''
    maintenance_influence = read_maintenance(maintenanceFile)
    # Given a timestamp -> time before maintenance -> time after maintenance -> pick the max
    health_dict = {}
    for key in price_dict:
        d = key.weekday()
        h = key.hour
        if d == 5: # Saturday, 0 day
            health_dict.update({key:maintenance_influence[96+h]})
        if d == 6: # Sunday, 1 day after
            health_dict.update({key:maintenance_influence[120+h]})
        if d == 4: # Friday, 1 day before
            health_dict.update({key:maintenance_influence[72+h]})
        if d == 3: # Thursday, 2 days before
            health_dict.update({key:maintenance_influence[48+h]}) 
        if d == 0: # Monday, 2 days after    
            health_dict.update({key:maintenance_influence[144+h]})
        if d == 1: # Tuesday, 4 days before, 3 days after
            health_dict.update({key:max(maintenance_influence[168+h], maintenance_influence[h])})            
        if d == 2: # Wednesday, 3 days before, 4 days after
            health_dict.update({key:max(maintenance_influence[24+h], maintenance_influence[192+h])})
    
    return health_dict   


def read_maintenance(maintenanceFile):
    ''' 
    Create a list to store influences of maintenances. 

    Parameters
    ----------
    maintenanceFile: string
        Name of file containing maintenance records.
    
    Returns
    -------
    List containing influences of maintenances.
    '''
    maintenance_influence = []
    try:
        with open(maintenanceFile, encoding='utf-8') as mainInf_csv:
            reader = csv.DictReader(mainInf_csv)
            for row in reader:
                maintenance_influence.append(float(row['Influence']))
    except:
        print("Unexpected error when reading maintenance information:", sys.exc_info()[0]) 
        exit()
    
    # Create the health dict, failure rates are based on data.
    
#     for key in price_dict:
#         if key.weekday() == 5 and key.hour == 0:    #    Find all Saturday 00:00:00
#             for i in range(216):
#                 key1 = key+timedelta(hours=(i-96))
#                 health_dict.update({key1:maintenance_influence[i]})
#     
#     for key in price_dict:
#         if key.weekday() == 5 and key.hour == 0:    #    Find all Saturday 00:00:00
#             for i in range(216):
#                 key1 = key+timedelta(hours=(i-96))
#                 tmp = health_dict.get(key1, 0)
#                 if tmp == 0:
#                     health_dict.update({key1:maintenance_influence[i]}) 
#                 else:
#                     health_dict.update({key1:max(tmp, maintenance_influence[i])})
               
    return maintenance_influence

class OneOneES(object):
    def __init__(self, dna_size, pop_size, pop, job_dict, price_dict,
                 failure_dict, prc_dict, start_time, weight1, weight2):
        # Attribute assignment
        self.dna_size = dna_size
        self.pop_size = pop_size
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.failure_dict = failure_dict
        self.prc_dict = prc_dict
        self.start_time = start_time
        self.w1 = weight1
        self.w2 = weight2
        # Initialization
        # generate N random individuals (N = pop_size)
        self.pop = np.vstack([np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(self.pop_size)])
        
    def get_fitness(self, candidate):
        # calculate the fitness of a candidate schedule
        return (self.w1 * get_energy_cost(candidate, self.start_time, self.job_dict, self.price_dict, self.prc_dict) +
            self.w2 * get_failure_cost(candidate, self.start_time, self.job_dict, self.failure_dict, self.prc_dict))
        
    def make_kid(self, parent):
        ''' Make a kid from a parent, only mutation
        '''
        kid = parent
        if np.random.rand() < (1 - 1.0 / MUT_STRENGTH):
            point, swap_point = np.random.randint(0, DNA_SIZE, size=2)
            swap_A, swap_B = kid[point], kid[swap_point]
            kid[point], kid[swap_point] = swap_B, swap_A
        return kid

    def kill_bad(self, parent, kid):
        ''' From a parent and a kid, choose the better one
        '''
        global MUT_STRENGTH
#         print("Line 409, parent:", parent)
        fp = self.get_fitness(parent)
#         print("Line 411, kid:", kid)
        fk = self.get_fitness(kid)
        p_target = 1 / 5
        if fk < fp: # kid better than parent
            parent = kid
            ps = 1 # kid win -> ps = 1
        else:
            ps = 0
        # adjust global mutation strength
        MUT_STRENGTH *= np.exp(1/np.sqrt(DNA_SIZE+1) * (ps-p_target) / (1-p_target))
        print("MUT_STRENGTH:", MUT_STRENGTH)
        return parent

    def evolve(self, n):
        print("self.pop:", self.pop)
        i = 1
        while i <= n:
            candidate_index = np.random.choice(np.arange(0, self.pop_size)) 
            print("candidate_index:", candidate_index)
            candidate = self.pop[candidate_index] # randomly pick one individual from pop
            print("original candidate:", candidate)
            kid = self.make_kid(candidate)
#             py, ky = self.get_fitness(candidate), self.get_fitness(kid)
            candidate = self.kill_bad(candidate, kid)
            print("new candidate:", candidate)
            self.pop[candidate_index] = candidate           
            i = i + 1
            
        costs = [self.get_fitness(i) for i in self.pop]  
        return self.pop, costs
        
if __name__ == '__main__':
    ''' Use jobs_start_time and jobs_end_time to determine the set of waiting jobs.
        Available range: 2016-01-23 17:03:58 to 2017-11-15 07:15:20
    '''
    
    # case 1 week
    jobs_start_time = datetime(2016, 11, 3, 6, 0)
    jobs_end_time = datetime(2016, 11, 8, 0, 0)
    
    # Get product specific characteristics (product related characteristics dict(prcd))
    prc_dict = read_prcd("productProd_ga_013.csv")
    price_dict = read_price("price.csv")
    selected_jobs_dict = select_jobs(jobs_start_time, jobs_end_time, read_job("jobInfoProd_ga_013.csv"))
    failure_dict = read_failure("maintenanceInfluenceb4a4.csv", price_dict)
    
    # TODO: possible to add buffers and maintenances
    DNA_SIZE = len(selected_jobs_dict)
    selected_jobs = [*selected_jobs_dict]
    
    if not selected_jobs:
        raise ValueError("No waitting jobs!")
    else:
        first_start_time = selected_jobs_dict.get(selected_jobs[0])[1]  # Find the start time of the original schedule
    
#     ("Start time:", first_start_time)
    
    original_schedule = selected_jobs
    w1 = 1
    w2 = 1
#     print(original_schedule)
#     print(make_kid(original_schedule))
#     print(get_fitness(original_schedule, 1, 1))

    ga = OneOneES(dna_size=DNA_SIZE, pop_size=POP_SIZE, pop=selected_jobs, job_dict=selected_jobs_dict, price_dict=price_dict,
                 failure_dict=failure_dict, prc_dict=prc_dict, start_time=first_start_time, weight1=w1, weight2=w2)
    
#     print(ga.get_fitness(original_schedule))
    for generation in range(1, N_GENERATIONS):
        print("Gen: ", generation)
        pop, costs = ga.evolve(1)
        best_index = np.argmin(costs)
        
    print()
    print("Candidate schedule", pop[best_index])
    print("Most fitted cost: ", costs[best_index])