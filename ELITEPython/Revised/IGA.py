'''An Improved Genetic Algorithm (IGA) is implemented in this file.
    Features: 
    1. Use the same IGA mentioned in the paper published in Sensors.
    2. Apply failure model by Joachim: (1) MTBF
    3. Modification of Input, Output.
    4. Output modification to improve clarity.
    5. Output details of each item in the job list.
    6. Add peak and off-peak energy policy.
    7. Add run-down scenario.
'''
# Core modules
import sys
import csv
import collections
from datetime import timedelta, datetime
from operator import add
# import pickle

# 3rd-party modules
import numpy as np

# Global variables
POP_SIZE = 12
CROSS_RATE = 0.7
MUTATION_RATE = 0.7
TIMES_MUTATE = 5
N_GENERATIONS = 2000
N_STOPPING = 500

C1 = 10 # Used for failure cost calculation in run-down scenario
C2 = 30

# Used files:
folder = "files//"
downtimes = folder + "downDurations.csv"
failure_rate = folder + "hourly_failure_rate.csv"
product_related = folder + "productRelatedCharacteristics_joa.csv"
prices_file = folder + "price_joa.csv"
jobinfo = folder + "jobInfoProd_joa.csv"
output1 = folder + "best_schedule.txt"

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


def read_down_durations(downDurationFile):
    '''
    Create a dictionary to restore down duration information.

    Parameters
    ----------
    downDurationFile: string
        Name of file containing job information.

    Returns
    -------
    A dictionary containing downtime duration indexes, startTime and endTime, key: int, value: list.
    '''
    down_duration_dict = {}
    try:
        with open(downDurationFile, encoding='utf-8') as downDurationInfo_csv:
            reader = csv.DictReader(downDurationInfo_csv)
            for row in reader:
                down_duration_dict.update({row['ID']:[datetime.strptime(row['StartDateUTC'], "%Y-%m-%d %H:%M:%S.%f"),
                                                 datetime.strptime(row['EndDateUTC'], "%Y-%m-%d %H:%M:%S.%f")]})
    except:
        print("Unexpected error when reading down duration information:", sys.exc_info()[0])
        exit()
    return down_duration_dict


def select_down_durations(daterange1, daterange2, down_duration_dict):
    ''' 
    Create a dictionary to restore selected downtime durations in a time range.

    Parameters
    ----------
    daterange1: Date
        Start datestamp of selected jobs.

    daterange2: Date
        End datestemp of selected jobs.
        
    down_duration_dict: dict
        Dictionary of downtime durations.
    
    Returns
    -------
    A dictionary containing downtime periods in the selected date range.
    '''
    res_dict = collections.OrderedDict()
    for key, value in down_duration_dict.items():
        if value[0] >= daterange1 and value[1] <= daterange2:
            res_dict.update({key:value})
    return res_dict


def read_product_related_characteristics(productFile):
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
                product_related_characteristics_dict.update({row['Product']:[round(float(row['UnitPrice']),3), float(row['Power']),
                                                            float(row['TargetProductionRate'])]})
    except:
        print("Unexpected error when reading product related information:", sys.exc_info()[0])
        exit()
    return product_related_characteristics_dict


# TODO: Depend on context of maintenance file
def read_failure_data(maintenanceFile):
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


# def read_failure(maintenanceFile, price_dict):
#     '''
#     Create a list to store influences of maintenances.
#
#     Parameters
#     ----------
#     maintenanceFile: string
#         Name of file containing maintenance records.
#
#     price_dict: dictionary
#         Dict of hourly dependent energy price whose time range will be used in the dict for failure rate.
#
#     Returns
#     -------
#     A dictionary of hourly dependent failure rate, key: Date, value: float.
#     '''
#     maintenance_influence = read_failure_data(maintenanceFile)
#     # Given a timestamp -> time before maintenance -> time after maintenance -> pick the max
#     health_dict = {}
#     for key in price_dict:
#         d = key.weekday()
#         h = key.hour
#         if d == 5: # Saturday, 0 day
#             health_dict.update({key:maintenance_influence[96+h]})
#         if d == 6: # Sunday, 1 day after
#             health_dict.update({key:maintenance_influence[120+h]})
#         if d == 4: # Friday, 1 day before
#             health_dict.update({key:maintenance_influence[72+h]})
#         if d == 3: # Thursday, 2 days before
#             health_dict.update({key:maintenance_influence[48+h]})
#         if d == 0: # Monday, 2 days after
#             health_dict.update({key:maintenance_influence[144+h]})
#         if d == 1: # Tuesday, 4 days before, 3 days after
#             health_dict.update({key:max(maintenance_influence[168+h], maintenance_influence[h])})
#         if d == 2: # Wednesday, 3 days before, 4 days after
#             health_dict.update({key:max(maintenance_influence[24+h], maintenance_influence[192+h])})
#
#     return health_dict


# Possible to use for machine with low RAM.
# def select_maintenance(daterange1, daterange2, health_dict):
#     dict = {}
#     for key, value in health_dict.items():
#         if key >= daterange1 and key <= daterange2:
#             dict.update({key:value})
#     return dict


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
                price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"): float(row['Euro'])})
    except:
        print("Unexpected error when reading energy price:", sys.exc_info()[0])
        exit()
    return price_dict


def read_jobs(jobFile):
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
                job_dict.update({int(float(row['ID'])):[float(row['Duration']), datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f"),
                                                 datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f"),
                                                 float(row['Quantity']), row['Product']]})
    except:
        print("Unexpected error when reading job information:", sys.exc_info()[0])
        raise
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


def get_hourly_failrue_dict(start_time, end_time, failure_list, down_duration_dict):
    '''
    Get the hourly failure rate between a determined start time and end time.
    '''
    hourly_failure_dict = {}
    t_sd = floor_dt(start_time, timedelta(hours=1)) # start time left border
    t_eu = ceil_dt(end_time, timedelta(hours=1)) # end time right border

    # Filtering down time, get all down durations longer than one hour
    down_duration_dict_filtered = collections.OrderedDict()
    for key, value in down_duration_dict.items():
        if (value[1] - value[0]) / timedelta(hours=1) >= 1:
            down_duration_dict_filtered.update({key:[floor_dt(value[0], timedelta(hours=1)), floor_dt(value[1], timedelta(hours=1))]})

#     print("down_duration_dict_filtered:", down_duration_dict_filtered)
    i = t_sd
    index=0
    for value in down_duration_dict_filtered.values():
        while i < value[0]:
            hourly_failure_dict.update({i:failure_list[index]})
            i = i + timedelta(hours=1)
            index = index+1
        while i <= value[1]:
            hourly_failure_dict.update({i:float(0)})
            i = i + timedelta(hours=1)
        index = 0

#     print("i:", i)
#     print("index:", index)

    while i <= t_eu:
        hourly_failure_dict.update({i:failure_list[index]})
        i = i + timedelta(hours=1)
        index = index+1

    return hourly_failure_dict


def get_failure_cost_v2(indiviaual, start_time, job_dict,  product_related_characteristics_dict, down_duration_dict):
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

    ''' TODO: Another assumption 
            1. No failure cost for runtime durations
            2. Machine stop/restart cost + failure cost for downtime durations
    '''
    failure_cost = 0
    t_now = start_time

    for item in indiviaual:
        t_start = t_now
        unit1 = job_dict.get(item, -1)
        if unit1 == -1:
            raise ValueError("No matching item in job dict: ", item)

        product_type = unit1[4]    # get job product type
        quantity = unit1[3]  # get job quantity

#         if du <= 1: # safe period of 1 hour (no failure cost)
#             continue;
        unit2 = product_related_characteristics_dict.get(product_type, -1)
        if unit2 == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

        du = quantity / unit2[2] # get job duration
#         print("Duration:", du)
#         uc = unit2[0] # get job raw material unit price

        t_o = t_start + timedelta(hours=du) # Without downtime duration
#         print("t_o:", t_o)
        t_end = t_o

        for key, value in down_duration_dict.items():
            # DowntimeDuration already added

            if t_end < value[0]:
                continue
            if t_start > value[1]:
                continue
            if t_start < value[0] < t_end:
                t_end = t_end + (value[1]-value[0])
                failure_cost += C1 + (value[1] - value[0]) / timedelta(hours=1) * C2
#                 print("Line 429, t_end:", t_end)
            if t_start > value[0] and t_end > value[1]:
                t_end = t_end + (value[1] - t_start)
                failure_cost += C1 + (value[1] - t_start) / timedelta(hours=1) * C2

            if t_start > value[0] and t_end < value[1]:
                t_end = t_end + (t_end - t_start)
                failure_cost += C1 + (t_end- t_start) / timedelta(hours=1) * C2
                   
            else:
                break

#         t_start = t_start+timedelta(hours=1) # exclude safe period, find start of sensitive period
#         t_end = t_start + timedelta(hours=(du-1)) # end of sensitive period

#         t_su = ceil_dt(t_start, timedelta(hours=1)) #    t_start right border
#         t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
#         t_sd = floor_dt(t_start, timedelta(hours=1))  #    t_start left border
#

#         if health_dict.get(t_sd, -1) == -1 or health_dict.get(t_ed, -1) == -1:
#             raise ValueError("For item %d: In boundary conditions, no matching item in the health dict for %s or %s" % (item, t_sd, t_ed))

#         tmp = (1 - hourly_failure_dict.get(t_sd, 0)) * (1 - hourly_failure_dict.get(t_ed, 0))
#         step = timedelta(hours=1)
#         while t_su < t_ed:
#             if hourly_failure_dict.get(t_su, -1) == -1:
#                 raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
#             tmp *= (1-hourly_failure_dict.get(t_su, 0))
#             t_su += step
# #
# #         if product_related_characteristics_dict.get(product_type, -1) == -1:
# #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
#         failure_cost += (1-tmp) * quantity * uc
        t_now = t_end

    return failure_cost


def get_failure_cost(indiviaual, start_time, job_dict, hourly_failure_dict, product_related_characteristics_dict, down_duration_dict):
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
        unit1 = job_dict.get(item, -1)
        if unit1 == -1:
            raise ValueError("No matching item in job dict: ", item)

        product_type = unit1[4]    # get job product type
        quantity = unit1[3]  # get job quantity

#         if du <= 1: # safe period of 1 hour (no failure cost)
#             continue;
        unit2 = product_related_characteristics_dict.get(product_type, -1)
        if unit2 == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

        du = quantity / unit2[2] # get job duration
#         print("Duration:", du)
        uc = unit2[0] # get job raw material unit price

        t_o = t_start + timedelta(hours=du) # Without downtime duration
#         print("t_o:", t_o)
        t_end = t_o

        for key, value in down_duration_dict.items():
            # DowntimeDuration already added
            if t_end < value[0]:
                continue
            if t_start > value[1]:
                continue
            if t_start < value[0] < t_end:
                t_end = t_end + (value[1]-value[0])
#                 print("Line 429, t_end:", t_end)
            if t_start > value[0] and t_end > value[1]:
                t_end = t_end + (value[1] - t_start)
            if t_start > value[0] and t_end < value[1]:
                t_end = t_end + (t_end - t_start)
            else:
                break

#         t_start = t_start+timedelta(hours=1) # exclude safe period, find start of sensitive period
#         t_end = t_start + timedelta(hours=(du-1)) # end of sensitive period

        t_su = ceil_dt(t_start, timedelta(hours=1)) #    t_start right border
        t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        t_sd = floor_dt(t_start, timedelta(hours=1))  #    t_start left border


#         if health_dict.get(t_sd, -1) == -1 or health_dict.get(t_ed, -1) == -1:
#             raise ValueError("For item %d: In boundary conditions, no matching item in the health dict for %s or %s" % (item, t_sd, t_ed))

        tmp = (1 - hourly_failure_dict.get(t_sd, 0)) * (1 - hourly_failure_dict.get(t_ed, 0))
        step = timedelta(hours=1)
        while t_su < t_ed:
            if hourly_failure_dict.get(t_su, -1) == -1:
                raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
            tmp *= (1-hourly_failure_dict.get(t_su, 0))
            t_su += step
#
#         if product_related_characteristics_dict.get(product_type, -1) == -1:
#             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
        failure_cost += (1-tmp) * quantity * uc
        t_now = t_end

    return failure_cost


def get_energy_cost(individual, start_time, job_dict, price_dict, product_related_characteristics_dict):
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
#     print("Line 401, downDurationIndex:", downDurationIndex)
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in individual:
#         print("For job:", item)
        t_start = t_now
        #print("Time start: " + str(t_now), end='\t')
        unit1 = job_dict.get(item, -1)
        if unit1 == -1:
            raise ValueError("No matching item in the job dict for %d" % item)

        product_type = unit1[4] # get job product type
        #quantity = unit1[3]

        unit2 = product_related_characteristics_dict.get(product_type, -1)
        if unit2 == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

        #du = quantity / unit2[2] # get job duration
        du = unit1[0]
        #print("Duration:", du)
        po = unit2[1] # get job power profile

        t_o = t_start + timedelta(hours=du) # Without downtime duration
#         print("t_o:", t_o)
        t_end = t_o

#         for key, value in down_duration_dict.items():
#             # DowntimeDuration already added
#
#             if t_end < value[0]:
#                 continue
#             if t_start > value[1]:
#                 continue
#             if t_start < value[0] < t_end:
#                 t_end = t_end + (value[1]-value[0])
# #                 print("Line 429, t_end:", t_end)
#             if t_start > value[0] and t_end > value[1]:
#                 t_end = t_end + (value[1] - t_start)
#             if t_start > value[0] and t_end < value[1]:
#                 t_end = t_end + (t_end - t_start)

#         for key, value in down_duration_dict.items():
#         print("Job", item)
#         print('Line 416, du:', du)
#         t_end = t_start + timedelta(hours=du)
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

#     print("Finish time:", t_now)
    return energy_cost


# def overlap(startA, endA, startB, endB):
#     # Test if two ranges overlap
#     return (startA <= endB) and (endA >= startB)


def visualize(individual, start_time, job_dict, product_related_characteristics_dict, down_duration_dict):
    # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
    detail_dict = {}
    t_now = start_time

    for item in individual:
        t_start = t_now

        unit1 = job_dict.get(item, -1)
        product_type = unit1[4] # get job product type
        quantity = unit1[3] # get job objective quantity

        unit2 = product_related_characteristics_dict.get(product_type, -1)
        du = quantity / unit2[2] # get job duration

        t_o = t_start + timedelta(hours=du) # Without downtime duration
        t_end = t_o

        for key, value in down_duration_dict.items():
            # DowntimeDuration already added

            if t_end < value[0]:
                continue
            if t_start > value[1]:
                continue
            if t_start < value[0] < t_end:
                t_end = t_end + (value[1]-value[0])
#                 print("Line 429, t_end:", t_end)
            if t_start > value[0] and t_end > value[1]:
                t_end = t_end + (value[1] - t_start)
            if t_start > value[0] and t_end < value[1]:
                t_end = t_end + (t_end - t_start)

        detail_dict.update({item:[t_start, t_end, du]})
        t_now = t_end

    return detail_dict


def hamming_distance(s1, s2):
    '''
    Calculate the hamming distance (the number of positions at which the corresponding symbols are different) of two list.

    Parameters
    ----------
    s1: List
        A list of job indexes.

    s2: list
        A list of job indexes.

    Returns
    -------
    The hamming distance of two lists.
    '''
    assert len(s1) == len(s2)
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))


class GA(object):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict,
                 product_related_characteristics_dict,  start_time, weight1, weight2,
                 failure_dict=[], down_duration_dict= []):
        # Attributes assignment
        self.dna_size = dna_size
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.failure_dict = failure_dict
        self.product_related_characteristics_dict = product_related_characteristics_dict
        self.down_duration_dict = down_duration_dict
        self.start_time = start_time
        self.w1 = weight1
        self.w2 = weight2
        # generate N random individuals (N = pop_size)
        self.pop = np.vstack([np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])

        self.memory = []

    def get_fitness(self, sub_pop):
        ''' Get fitness values for all individuals in a generation.
        '''
        # There are 2 sub-objectives, the fitness is the sum of these two
        if self.w1 > 0:
            failure_cost = [self.w1 * get_failure_cost_v2(i, self.start_time, self.job_dict,
                                                          self.product_related_characteristics_dict,
                                                          self.down_duration_dict) for i in sub_pop]
        else:
            failure_cost = [self.w1 for i in sub_pop]
        if self.w2 > 0:
            energy_cost = [self.w2 * get_energy_cost(i, self.start_time, self.job_dict, self.price_dict,
                                                     self.product_related_characteristics_dict) for i in sub_pop]
        else:
            energy_cost = [self.w2 for i in sub_pop]
        return list(map(add, failure_cost, energy_cost))

#     def select(self, fitness):
#         ''' Nature selection with individuals' fitnesses.
#         '''
#         idx = np.random.choice(np.arange(self.pop_size), size=self.pop_size, replace=True, p = fitness/fitness.sum())
# #         print("idx:", idx)
#         return self.pop[idx]

    def crossover(self, winner_loser):
        ''' Using microbial genetic evolution strategy, the crossover result is used to represent the loser.
        the winner stays the same
        '''
        # crossover for loser
        if np.random.rand() < self.cross_rate:
            cross_points = np.random.randint(0, 2, self.dna_size).astype(np.bool)
            keep_job =  winner_loser[1][~cross_points] # see the progress explained in the paper
            swap_job = winner_loser[0, np.isin(winner_loser[0].ravel(), keep_job, invert=True)]
            winner_loser[1][:] = np.concatenate((keep_job, swap_job))
        return winner_loser

    def mutate(self, schedule):
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        '''
        #print(schedule)
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            equal = True
            while equal:
                point, swap_point = np.random.randint(self.dna_size, size=2)
                equal = (point == swap_point)
            #print(point, swap_point)
            swap_A, swap_B = schedule[point], schedule[swap_point]
            schedule[point], schedule[swap_point] = swap_B, swap_A
        #print(schedule)
        return schedule

    def evolve(self, n, with_crossover=True):
        '''
        Execution of the provided GA.

        Parameters
        ----------
        n: int
            Number of iteration times

        Returns
        -------
        The hamming distance of two lists.
        '''
        for i in range(n): # n is the number of evolution times in one iteration
            # population start
            # get the population fitness
            fitness = np.array(self.get_fitness(self.pop))
            best = np.argsort(fitness)

            #print(fitness[best])

            # sort population by fitness
            self.pop = self.pop[best]

            # use the top half for crossover and mutation, do only mutation on the bottom half
            # round to a multiple of two
            top_length = int(int(self.pop_size*0.5) >> 1 << 1)

            #get pairs of random parents from the top half
            sub_pop_idx = np.random.choice(np.arange(0, top_length), size=top_length, replace=False)

            for i in range(int(top_length / 2)):
                sub_pop = self.pop[sub_pop_idx[i*2:i*2+2]]
                # get the fitness values of the two
                fitness = self.get_fitness(sub_pop)
                #print(fitness)

                # Elitism Selection
                winner_loser_idx = np.argsort(fitness)
#               print('winner_loser_idx', winner_loser_idx)

                sorted_idx = sub_pop_idx[i*2:i*2+2][winner_loser_idx]

                winner_loser = self.pop[sorted_idx] # the first is winner and the second is loser
#               print('winner_loser', winner_loser)

                #origin = winner_loser[1] # pick up the loser for genetic operations

                # Crossover (of the winner and the loser)
                #print(winner_loser)
                if with_crossover:
                    winner_loser = self.crossover(winner_loser)
                #print(winner_loser)

                # Mutation (only on the child) (should affect fitness)
                for m in range(TIMES_MUTATE):
                    loser = self.mutate(winner_loser[1])

                winner_loser[1] = loser
                #sub_pop_idx = np.random.choice(np.arange(int(self.pop_size/2), self.pop_size), size=2,
                #                               replace=False)
                # sub_pop = self.pop[sub_pop_idx]
                #fitness = self.get_fitness(winner_loser)
                #print(fitness.min())
                rang = np.arange(top_length, self.pop_size)
                sub_pop_id = np.random.choice(rang, size=1, replace=False)

                self.pop[sub_pop_id] = loser # take the original places of the parents

            np.arange(top_length, self.pop_size + 1)


#         space = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in self.pop]
        
#         failure_cost_space = [self.w1 * get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.product_related_characteristics_dict, self.down_duration_dict) for i in self.pop]
        failure_cost_space = [self.w1 * get_failure_cost_v2(i, self.start_time, self.job_dict, self.product_related_characteristics_dict, self.down_duration_dict) for i in self.pop]
        energy_cost_space = [self.w2 * get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict) for i in self.pop]
        
#         print(self.start_time)
#         print(self.pop)
#         print(space)
#         print("failure_cost_space:", failure_cost_space)
#         print("energy_cost_space:", energy_cost_space)

        return self.pop, list(map(add, failure_cost_space, energy_cost_space))
      
        
if __name__ == '__main__':
    ''' Use start_time and end_time to determine a waiting job list from records
        Available range: 2016-01-23 17:03:58.780 to 2017-11-15 07:15:20.500
    '''
#     case 1 week
    start_time = datetime(2015, 11, 2, 0, 0)
    end_time = datetime(2015, 12, 1, 0, 0)

    weight1 = 0 # failure weight
    weight2 = 1 # energy weight
    weight_mksp = 1

#     case 2 years
#     start_time = datetime(2016, 1, 19, 14, 0)
#     end_time = datetime(2017, 11, 15, 0, 0)

    # Generate raw material unit price
    #down_duration_dict = select_down_durations(start_time, end_time, read_down_durations(downtimes)) # File from EnergyConsumption/InputOutput
    # down_duration_dict = read_down_durations(downtimes)
    # failure_list = read_failure_data(failure_rate) # File from failuremodel-master/analyse_production
    # hourly_failure_dict = get_hourly_failrue_dict(start_time, end_time, failure_list, down_duration_dict)
    #
    # with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
    #     writer = csv.writer(csv_file)
    #     for key, value in hourly_failure_dict.items():
    #         writer.writerow([key, value])

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()

    product_related_characteristics_dict = read_product_related_characteristics(product_related)

    if weight2 != 0:  # All code related to energy prices:
        price_dict_new = read_price(prices_file) # File from EnergyConsumption/InputOutput
    #job_dict_new = select_jobs(start_time, end_time, read_jobs(jobinfo)) # File from EnergyConsumption/InputOutput
    job_dict_new = read_jobs(jobinfo)

    # TODO: change
#     print("failure_dict", failure_dict)
#     exit()
#     # write corresponding failure dict into file
#     with open('ga_013_failure_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in failure_dict_new.items():
#             writer.writerow([key, value])

    DNA_SIZE = len(job_dict_new)
    waiting_jobs = [*job_dict_new]

    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule

#     print("Waiting jobs: ", waiting_jobs)
#     print("Prices: ", price_dict_new)
#     print("Failures: ", failure_dict_new)

    result_dict = {}
    original_schedule = waiting_jobs
    firstresult = 0
    if weight2 > 0:
        firstresult += weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new,
                                  product_related_characteristics_dict)
    if weight1 > 0:
        firstresult += weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
                                   product_related_characteristics_dict, down_duration_dict)

    result_dict.update({0: firstresult}) # generation 0 is the original schedule

#     result_dict.update({0: weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)+
#                         weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
#                                         product_related_characteristics_dict, down_duration_dict)}) # generation 0 is the original schedule
    
    result_dict.update({0: weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)+
                        weight1 * get_failure_cost_v2(original_schedule, first_start_time, job_dict_new,
                                        product_related_characteristics_dict, down_duration_dict)}) # generation 0 is the original schedule
#     exit()
    ga = GA(dna_size=DNA_SIZE, cross_rate=CROSS_RATE, mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, # failure_dict=hourly_failure_dict,
            product_related_characteristics_dict = product_related_characteristics_dict, #down_duration_dict=down_duration_dict,
            start_time = first_start_time, weight1=weight1, weight2=weight2)

    best_cost_list = []
    worst_cost_list = []
    generation = 0
    while generation < N_GENERATIONS+N_STOPPING:
        generation += 1
        #print("Gen: ", generation)
        co = (generation < N_GENERATIONS)
        pop, res = ga.evolve(1, with_crossover=co)          # natural selection, crossover and mutation
        #print(pop)
#         print("res:", res)
        best_index = np.argmin(res); worst_index = np.argmax(res)
#         print("Most fitted DNA: ", pop[best_index])
        best_cost = res[best_index]
        #print("Most fitted cost: ", best_cost)
        best_cost_list.append(best_cost)
        worst_cost_list.append(res[worst_index])
#         result_dict.update({generation:res[best_index]})
        print(str(generation) + '/' + str(N_GENERATIONS+ N_STOPPING) + ':\t' + str(best_cost), end='')
        print('\r', end='')
    
    # Used to store intermediate result for large-size problems
#     with open('IGAlarge.pkl', 'wb') as f:
#         pickle.dump(pop[best_index], f)

    print()
    best_index = np.argmin(res)
    candidate_schedule = list(pop[best_index])
    print("Candidate schedule", candidate_schedule)

    candidate_energy_cost = weight2 * get_energy_cost(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict)
    if weight1 > 0:
        candidate_failure_cost = weight1 * get_failure_cost(candidate_schedule, first_start_time, job_dict_new, hourly_failure_dict,
                                             product_related_characteristics_dict, down_duration_dict)
    else:
        candidate_failure_cost = weight1
    print("Candidate energy cost:", candidate_energy_cost)
    print("Candidate failure cost:", candidate_failure_cost)
    candidate_cost = candidate_energy_cost + candidate_failure_cost
    print("Candidate total cost:", candidate_cost)
    
#     print("Most fitted cost: ", res[best_index])

    print("\nOriginal schedule:", original_schedule)
    print("DNA_SIZE:", DNA_SIZE) 
    print("Original schedule start time:", first_start_time)
    original_energy_cost = weight2 * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict)
    if weight1 > 0:
        original_failure_cost = weight1 * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
                                             product_related_characteristics_dict, down_duration_dict)
    else:
        original_failure_cost = weight1
    print("Original energy cost: ", original_energy_cost)
    print("Original failure cost: ", original_failure_cost)
    original_total_cost = original_energy_cost + original_failure_cost
    print("Original total cost:", original_total_cost)
    
    #result_dict = visualize(original_schedule, first_start_time, job_dict_new, product_related_characteristics_dict, down_duration_dict)
    #print("Visualize_dict_origin:", result_dict)
    #print("Down_duration", down_duration_dict)

    print('Percentage saved:', (1-candidate_cost/original_total_cost)*100, '%' )

    print(candidate_schedule)
    print(list(candidate_schedule), file=open(output1, 'w'))
    import os
    print(os.path.abspath(output1))

    # Output for visualization
    # with open('executionRecords.csv', 'w', newline='\n') as csv_file:
    #     writer = csv.writer(csv_file)
    #     print(result_dict)
    #     for key, value in result_dict.items():
    #         writer.writerow([key, value[0], value[1], value[2]])
            
   # with open('originalRecords.csv', 'w', newline='\n') as csv_file:
   #     writer = csv.writer(csv_file)
   #     for key, value in result_dict_origin.items():
    #         writer.writerow([key, value[0], value[1], value[2]])
            
    # with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
    #     writer = csv.writer(csv_file)
    #     for key, value in down_duration_dict.items():
    #         writer.writerow([key, value[0], value[1]])
    
#     print("Elite schedule: ", elite_schedule)
#     print("Elite cost:", elite_cost)
#     te = time.time()
#     print("Time consumed: ", te - ts)  

# write the result to csv for plot
#     with open('ga_013_analyse_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in result_dict.items():
#             writer.writerow([key, value])