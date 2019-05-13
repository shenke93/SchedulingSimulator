'''Soubry schedulor version 0.0.0
    Features: 
    1. Runnable script from cmd.
    2. Rewrite functions, make better reuse of code. 
    3. Normalization of input/output.
'''
# Core modules
import sys
import csv
import collections
import argparse
import warnings
from datetime import timedelta, datetime
from operator import add
import operator
import logging
import os
import math
import itertools
import time
import msvcrt
from collections import OrderedDict

# import pickle
from configfile import duration_str

# 3rd-party modules
import numpy as np
import pandas as pd

# Global variables
# POP_SIZE = 8   
# CROSS_RATE = 0.6
# MUTATION_RATE = 0.8
# N_GENERATIONS = 200

C1 = 10 # Used for failure cost calculation in run-down scenario
C2 = 30


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
    tempdelta = dt - datetime.min
    if tempdelta % delta != 0:
        return dt + (delta - (tempdelta % delta))
    else:
        return tempdelta
    # q, r = divmod(dt - datetime.min, delta)
    # return (datetime.min + (q+1)*delta) if r else dt


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
    tempdelta = dt - datetime.min
    if tempdelta % delta != 0:
        return dt - (tempdelta % delta)
    else:
        return tempdelta
    # q, r = divmod(dt - datetime.min, delta)
    # return (datetime.min + (q)*delta) if r else dt

    
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
        print("Unexpected error when reading down duration information from '{}'".format(downDurationFile))
        raise
    return down_duration_dict


def select_from_range(dateRange1, dateRange2, dict, pos1, pos2):
    '''
    Select items of dict from a time range.
    
    Parameters
    ----------
    dateRange1: Date
        Start timestamp of the range.
    
    dateRange2: Date
        End timestamp of the range.
        
    dict: Dict
        Original dictionary.
        
    Returns
    -------
    A dict containing selected items.
    '''
    res_dict = collections.OrderedDict()
    for key, value in dict.items():
        try:
            if value[pos1] >= dateRange1 and value[pos2] <= dateRange2:
                res_dict.update({key:value})
        except TypeError:
            print(value[pos1], dateRange1, value[pos2], dateRange2)
            raise
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
                job_entry = dict(zip(['product', 'power', 'targetproduction'],
                [round(float(row['UnitPrice']),3), float(row['Power']), float(row['TargetProductionRate'])]))
                product_related_characteristics_dict.update({row['Product']: job_entry})
                if 'Type' in row:
                    product_related_characteristics_dict[row['Product']]['type'] = row['Type']
                    #print('Added type')
                
                if 'Availability' in row:
                    product_related_characteristics_dict[row['Product']]['availability'] = row['Availability']

    except:
        print("Unexpected error when reading product related information from '{}'".format(productFile))
        raise
    return product_related_characteristics_dict


def read_precedence(precedenceFile):
    precedence_dict = {}
    try:
        with open(precedenceFile, encoding='utf-8') as prec_csv:
            reader = csv.DictReader(prec_csv)
            for row in reader:
                key = int(row['Before'])
#                 print(key)
                if key in precedence_dict: 
#                     print("In")
                    precedence_dict[key].append(int(row['After']))
                else:
#                     print("Not In")
                    precedence_dict.update({key:[int(row['After'])]})
    except:
        print("Unexpected error when reading precedence information from '{}'".format(precedenceFile)) 
        raise
    
#     print(precedence_dict)
    return precedence_dict

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
        print("Unexpected error when reading maintenance information from {}:".format(maintenanceFile))
        raise
               
    return maintenance_influence


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


def read_jobs(jobFile, get_totaltime=False):
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
    if get_totaltime:
        str_time = 'Totaltime'
    else:
        str_time = 'Uptime'
    try:
        with open(jobFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                job_num = int(row['ID'])
                # insert product name
                job_entry = dict({'product': row['Product']})
                # time string or quantity should be in the row
                if ('ReleaseDate' in row) and row['ReleaseDate'] is not None:
                    job_entry['ReleaseDate'] = datetime.strptime(row['ReleaseDate'], "%Y-%m-%d %H:%M:%S.%f")
                if (str_time in row) and row[str_time] is not None:
                    job_entry['duration'] = float(row[str_time])
                if ('Quantity' in row) and row['Quantity'] is not None:
                    job_entry['quantity'] = float(row['Quantity'])
                
                if ('Start' in row) and row['Start'] is not None:
                    job_entry['start'] = datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f")
                if ('End' in row) and row['End'] is not None:
                    job_entry['end'] = datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f")
                
                # Add product type
                if ('Type' in row) and row['Type'] is not None:
                    job_entry['type'] = row['Type']
                    #print('Added type')
                else:
                    job_entry['type'] = 'unknown'

                # Add due date
                if ('Before' in row) and (row['Before'] != ""):
                    job_entry['before'] = datetime.strptime(row['Before'], "%Y-%m-%d %H:%M:%S.%f")
                    #print('Before date read')
                else:
                    job_entry['before'] = datetime.max

                # Add after date
                if ('After' in row) and (row['After'] !=""):
                    job_entry['after'] = datetime.strptime(row['After'], "%Y-%m-%d %H:%M:%S.%f")
                else:
                    job_entry['after'] = datetime.min

                # add the item to the job dictionary
                job_dict[job_num] = job_entry
    except:
        print("Unexpected error when reading job information from {}:".format(jobFile))
        raise
    return job_dict


# def read_urgent_jobs(jobFile, get_totaltime=False):
#     """
#     TODO: Add attribute checks.
#     """
#     job_dict = {}
#     if get_totaltime:
#         str_time = 'Totaltime'
#     else:
#         str_time = 'Uptime'
#     try:
#         with open(jobFile, encoding='utf-8') as jobInfo_csv:
#             reader = csv.DictReader(jobInfo_csv)
#             for row in reader:
#                 job_num = int(row['ID'])
#                 # insert product name
#                 job_entry = dict({'product': row['Product']})
#                 # time string or quantity should be in the row
#                 if (str_time in row) and row[str_time] is not None:
#                     job_entry['duration'] = float(row[str_time])
#                 if ('Quantity' in row) and row['Quantity'] is not None:
#                     job_entry['quantity'] = float(row['Quantity'])
#                 
#                 if ('Start' in row) and row['Start'] is not None:
#                     job_entry['start'] = datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f")
#                 if ('End' in row) and row['End'] is not None:
#                     job_entry['end'] = datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f")
#                 
#                 # Add product type
#                 if ('Type' in row) and row['Type'] is not None:
#                     job_entry['type'] = row['Type']
#                     #print('Added type')
#                 else:
#                     job_entry['type'] = 'unknown'
# 
#                 # Add due date
#                 if ('Before' in row) and (row['Before'] is not None):
#                     job_entry['before'] = datetime.strptime(row['Before'], "%Y-%m-%d %H:%M:%S.%f")
#                     #print('Before date read')
#                 else:
#                     job_entry['before'] = datetime.max
# 
#                 # Add after date
#                 if ('After' in row) and (row['After'] is not None):
#                     job_entry['after'] = datetime.strptime(row['After'], "%Y-%m-%d %H:%M:%S.%f")
#                 else:
#                     job_entry['after'] = datetime.min
# 
#                 # add the item to the job dictionary
#                 job_dict[job_num] = job_entry
#     except:
#         print("Unexpected error when reading job information from {}:".format(jobFile))
#         raise
#     return job_dict



def get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict):
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
    index = 0
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


def get_failure_cost(individual, start_time, job_dict, hourly_failure_dict, product_related_characteristics_dict, down_duration_dict, scenario, detail=False,
                     duration_str='duration', working_method='historical'):
    ''' 
    Calculate the failure cost of an individual scheme.
 
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
    if detail:
        failure_cost = []
    else:
        failure_cost = 0
    t_now = start_time
    if scenario == 1:
        for item in individual:
            t_start = t_now
            unit1 = job_dict.get(item, -1)
            if unit1 == -1:
                raise ValueError("No matching item in job dict: ", item)
         
            product_type = unit1['product']    # get job product type
            quantity = unit1['quantity']  # get job quantity
             
    #         if du <= 1: # safe period of 1 hour (no failure cost)
    #             continue;
            unit2 = product_related_characteristics_dict.get(product_type, -1)
            if unit2 == -1:
                raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
            
            if duration_str == 'duration':
                du = unit1['duration']
            if duration_str == 'quantity':
                try:
                    du = quantity / unit2['targetproduction'] # get job duration
                except:
                    print('Error calculating duration:', du)
                    raise
            #print("Jobdict:", unit1)
            #print("Product characteristics:", unit2)
            #print("Duration:", du)
            uc = unit2[0] # get job raw material unit price
             
            
    #         print("t_o:", t_o)

            if working_method == 'historical':
                t_o = t_start + timedelta(hours=du) # Without downtime duration
                t_end = t_o

                #print(down_duration_dict)
                
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
            elif working_method == 'expected':
                if 'availability' in unit2:
                    t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
                else:
                    raise NameError('Availability column not found, error')
             
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
            if detail:
                failure_cost.append((1-tmp) * quantity * uc)
            else:
                failure_cost += (1-tmp) * quantity * uc 
            t_now = t_end
    
    
    if scenario == 2:
        for item in individual:
            fc_temp = 0
            t_start = t_now
            unit1 = job_dict.get(item, -1)
            if unit1 == -1:
                raise ValueError("No matching item in job dict: ", item)
         
            product_type = unit1['type']    # get job product type
            quantity = unit1['quant']  # get job quantity
             
    #         if du <= 1: # safe period of 1 hour (no failure cost)
    #             continue;
            unit2 = product_related_characteristics_dict.get(product_type, -1)
            if unit2 == -1:
                raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

            if duration_str == 'duration':
                du = unit1['duration']
            if duration_str == 'quantity':
                du = quantity / unit2['targetproduction'] # get job duration
            
    #        du = quantity / unit2[2] # get job duration
    #         print("Duration:", du)
    #         uc = unit2[0] # get job raw material unit price
             
            if working_method == 'historical':
                t_o = t_start + timedelta(hours=du) # Without downtime duration
                #print("t_o:", t_o)
                t_end = t_o
                for key, value in down_duration_dict.items():
                    # DowntimeDuration already added
                    if t_end < value[0]:
                        continue
                    if t_start > value[1]:
                        continue
                    if t_start < value[0] < t_end:
                        t_end = t_end + (value[1]-value[0])
                        fc_temp += C1 + (value[1] - value[0]) / timedelta(hours=1) * C2
                        # print("Line 429, t_end:", t_end)
                    if t_start > value[0] and t_end > value[1]:
                        t_end = t_end + (value[1] - t_start)
                        fc_temp += C1 + (value[1] - t_start) / timedelta(hours=1) * C2
                    if t_start > value[0] and t_end < value[1]:
                        t_end = t_end + (t_end - t_start)
                        fc_temp += C1 + (t_end- t_start) / timedelta(hours=1) * C2
                    else:
                        break
            elif working_method == 'expected':
                if 'availability' in unit2:
                    t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
                else:
                    raise NameError('Availability column not found, error')
            
            t_now = t_end
            if detail:
                failure_cost.append(fc_temp)
            else:
                failure_cost += fc_temp  
    return failure_cost

def get_energy_cost(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, detail=False,
                    duration_str='duration', working_method='historical'):
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
    if detail:
        energy_cost = []
    else:
        energy_cost = 0
    t_now = start_time # current timestamp
    i = 0
    for item in individual:
#         print("For job:", item)
        t_start = t_now
#         print("Time start: " + str(t_now))
        unit1 = job_dict.get(item, -1)
        if unit1 == -1:
            raise ValueError("No matching item in the job dict for %d" % item)
       
        product_type = unit1['product'] # get job product type
        
        unit2 = product_related_characteristics_dict.get(product_type, -1)
        if unit2 == -1:
            raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

        if duration_str == 'duration':
            du = unit1['duration']
        if duration_str == 'quantity':
            quantity = unit1['quantity']
            du = quantity / unit2['targetproduction'] # get job duration
#         print("Duration:", du)
        po = unit2['power'] # get job power profile
        job_en_cost = 0
        
        if working_method == 'historical':
            #print(du)
            t_o = t_start + timedelta(hours=du) # Without downtime duration
    #         print("t_o:", t_o)
            t_end = t_o
            
            for key, value in down_duration_dict.items():
                # Add the total downtimeduration
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
        elif working_method == 'expected':
            if 'availability' in unit2:
                t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
            else:
                raise NameError('Availability column not found, error')
        
        # calculate sum of head price, tail price and body price

        t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start right border
        t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        t_sd = floor_dt(t_start, timedelta(hours=1)) # t_start_left border

        if price_dict.get(t_sd, 0) == 0 or price_dict.get(t_ed, 0) == 0:
            raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
        # calculate the head and tail prices and add them up
        tmp = price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) + price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))

        step = timedelta(hours=1)
        while t_su < t_ed:
            if price_dict.get(t_su, 0) == 0:
                raise ValueError("For item %d: No matching item in the price dict for %s" % (item, t_su))
            job_en_cost += price_dict.get(t_su, 0)
            t_su += step
        
        job_en_cost += tmp
        job_en_cost *= po
        
        t_now = t_end
        if detail:
            energy_cost.append(job_en_cost)
        else:
            energy_cost += job_en_cost
        i += 1  
    return energy_cost

def get_conversion_cost(schedule, job_info_dict, related_chars_dict, detail=False):
    if detail:
        conversion_cost = []
    else:
        conversion_cost = 0

    if len(schedule) <= 1:
        print('No conversion cost')
        return conversion_cost

    for item1, item2 in zip(schedule[:-1], schedule[1:]):
        # find product made:
        first_product = job_info_dict[item1]['product']
        second_product = job_info_dict[item2]['product']

        try:
            first_product_type = job_info_dict[item1]['type']
            second_product_type = job_info_dict[item2]['type']
        except KeyError:
            warnings.warn('No type found, continuing without conversion cost')
            if detail:
                conversion_cost.append(0)
            else:
                conversion_cost += 0

        # Alternatively get the product info from another database
        # first_product_type = related_chars_dict[first_product][4]
        # second_product_type = related_chars_dict[second_product][4]

        if first_product_type != second_product_type:
            # add conversion cost
            # suppose cost is fixed
            if detail:
                conversion_cost.append(1)
            else:
                conversion_cost += 1
        else:
            if detail:
                conversion_cost.append(0)
    if detail:
        conversion_cost.append(0)
    return conversion_cost

def get_constraint_cost(schedule, start_time, job_info_dict, product_related_characteristics_dict, down_duration_dict, detail=False, duration_str='duration', working_method='historical'):
    if detail:
        constraint_cost = []
    else:
        constraint_cost = 0
    t_now = start_time

    for item in schedule:
        t_start = t_now

        #duration = job_info_dict[item]['duration']

        if duration_str == 'duration':
            du = job_info_dict[item]['duration']
        if duration_str == 'quantity':
            quantity = job_info_dict[item]['quantity']
            product_type = job_info_dict[item]['product'] # get job product type
            unit2 = product_related_characteristics_dict.get(product_type, -1)
            du = quantity / unit2['targetproduction'] # get job duration

        if working_method == 'historical':
            t_end = t_start + timedelta(hours=du) # Without downtime duration
            for key, value in down_duration_dict.items():
                # Add the total downtimeduration
                if t_end < value[0]:
                    continue
                if t_start > value[1]:
                    continue
                if t_start < value[0] < t_end:
                    t_end = t_end + (value[1]-value[0])
                if t_start > value[0] and t_end > value[1]:
                    t_end = t_end + (value[1] - t_start)
                if t_start > value[0] and t_end < value[1]:
                    t_end = t_end + (t_end - t_start)
        if working_method == 'expected':
            if 'availability' in unit2:
                t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
            else:
                raise NameError('Availability column not found, error')

        deadline_cost = 0
        if 'before' in job_info_dict[item]: # assume not all jobs have deadlines
            # check deadline condition
            beforedate = job_info_dict[item]['before']
            if t_end > beforedate: # did not get deadline
                deadline_cost = (t_end-beforedate).total_seconds() / 3600

        if 'after' in job_info_dict[item]: # assume not all jobs have deadlines
            # check after condition
            afterdate = job_info_dict[item]['after']
            if t_end < afterdate: # produced before deadline
                deadline_cost = (afterdate - t_end).total_seconds() / 3600

        if detail:
            constraint_cost.append(deadline_cost)
        elif deadline_cost > 0:
            constraint_cost += deadline_cost

        t_now = t_end
    return constraint_cost


# def visualize(individual, start_time, job_dict, product_related_characteristics_dict, down_duration_dict):
#     # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
#     detail_dict = {}
#     t_now = start_time 
    
#     for item in individual:
#         itemlist = []
#         t_start = t_now
        
#         unit1 = job_dict.get(item, -1)
#         product_type = unit1['product'] # get job product name
#         #quantity = unit1['quantity'] # get job objective quantity

        
#         #unit2 = product_related_characteristics_dict.get(product_type, -1)
#         du = unit1['duration']
#         #du = quantity / unit2[2] # get job duration
        
#         t_o = t_start + timedelta(hours=du) # Without downtime duration
#         t_end = t_o
    
#         for key, value in down_duration_dict.items():
#             # DowntimeDuration already added

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
        
#         itemlist.extend([t_start, t_end, du, product_type])

#         if 'type' in unit1:
#             type = unit1['type']  # get job product type
#             itemlist.append(type)

#         detail_dict.update({item:itemlist})
#         t_now = t_end

#     return detail_dict

def calc_times_dt(individual, start_time, job_dict, down_duration_dict):
    # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
    detail_dict = {}
    t_now = start_time 
    
    for item in individual:
        itemlist = []
        t_start = t_now
        
        unit1 = job_dict.get(item, -1)
        product_type = unit1['product'] # get job product name
        du = unit1['duration']
        
        t_o = t_start + timedelta(hours=du) # Without downtime duration
        t_end = t_o
    
        for key, value in down_duration_dict.items():
            # DowntimeDuration already added
            # value0 is start time and value1 is end time of downtime duration
            if t_end < value[0]:
                continue
            if t_start > value[1]:
                continue
            if t_start < value[0] < t_end:
                t_end = t_end + (value[1]-value[0])
            if t_start > value[0] and t_end > value[1]:
            # t_start > startvalue downtime and t_end > endvalue downtime
                t_end = t_end + (value[1] - t_start)
            if t_start > value[0] and t_end < value[1]:
                t_end = t_end + (t_end - t_start)
        
        itemlist.extend([t_start, t_end, du, product_type])

        if 'type' in unit1:
            type = unit1['type']  # get job product type
            itemlist.append(type)

        detail_dict.update({item:itemlist})
        t_now = t_end

    return detail_dict

def get_time(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, duration_str='duration', working_method='historical'):
    # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
    detailed_dict = {}
    t_now = start_time 

    #print(duration_str)
    #input()
     
    for item in individual:
        t_start = t_now
         
        unit1 = job_dict.get(item, -1)
        
        #quantity = unit1['quantity'] # get job objective quantity
         
        #du = quantity / unit2[2] # get job duration
        if duration_str == 'duration':
            du = unit1['duration']
        elif duration_str == 'quantity':
            quantity = unit1['quantity']
            product_type = unit1['product'] # get job product type
            unit2 = product_related_characteristics_dict.get(product_type)
            try:
                du = quantity / unit2['targetproduction'] # get job duration
            except:
                print(quantity, unit2['targetproduction'])
                raise
        else:
            raise NameError('Faulty value inserted')
         
        if working_method == 'historical':
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
        elif working_method == 'expected':
            if 'availability' in unit2:
                t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
            else:
                raise NameError('Availability column not found, error')
         
        detailed_dict.update({item:[t_start, t_end, du, unit1['product'], unit1['type']]})
        t_now = t_end

    return detailed_dict

    
def visualize(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, hourly_failure_dict, scenario=1, energy_on=True, failure_on=True, duration_str='duration', 
              working_method='historical'):
    # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
    #print(duration_str)
    detailed_dict = get_time(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, duration_str=duration_str, working_method=working_method)
    #print(detailed_dict)
    
    #if energy_on:
    #    energy_dict = get_energy_cost(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, detail=True)
    # 
    #if failure_on:
    #    failure_dict = get_failure_cost(individual, start_time, job_dict, hourly_failure_dict, product_related_characteristics_dict, down_duration_dict, scenario, detail=True)    
    #
    #for item in individual:    
    #    detailed_dict[item].append(energy_dict[0])
    #    detailed_dict[item].append(failure_dict[0])

    #import pdb; pdb.set_trace()
           
    return detailed_dict

def validate(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, precedence_dict, duration_str=duration_str, working_method='historical'):
    # validate time
    time_dict = get_time(individual, start_time, job_dict, price_dict, product_related_characteristics_dict, down_duration_dict, duration_str=duration_str, working_method=working_method)
#     print(time_dict)
    flag = True
    for key, value in time_dict.items():
        due = job_dict[key]['before'] # due date of a job
        if value[1] > due:
            print("For candidate schedule:", individual)
            print("Job %d will finish at %s over the due date %s" % (key, value[1], due))
            flag = False
            break
    
    if flag == False:
        return flag
    # validate precedence
    ind = set(individual)
    jobs = ind.copy()
    for item in ind:
        if item in precedence_dict:
            prec = set(precedence_dict[item])
            jobs.remove(item)
#             print("Item:", item)
#             print("Prec:", prec)
#             print("afters:", jobs)
            if not prec.isdisjoint(jobs): # prec set and remain jobs have intersections
                flag = False
                break                
        else:
            jobs.remove(item)
            
    return flag

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


class Scheduler(object):
    def __init__(self, job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict,
                  start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method):
        # Attributes assignment
        self.dna_size = len(job_dict)
        self.pop = job_dict.keys()
        self.job_dict = job_dict
        self.price_dict = price_dict
        self.failure_dict = failure_dict
        self.product_related_characteristics_dict = product_related_characteristics_dict
        self.down_duration_dict = down_duration_dict
        # TODO: replace with input data from precedence file
        self.precedence_dict = {}
        self.start_time = start_time
        self.w1 = weight1
        self.w2 = weight2
        self.wc = weightc
        self.wb = weightb
        self.scenario = scenario
        self.duration_str = duration_str
        self.working_method = working_method

    def get_fitness(self, sub_pop, split_types=False, detail=False):
        ''' Get fitness values for all individuals in a generation.
        '''
        if self.w1:
            failure_cost = [self.w1*np.array(get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.product_related_characteristics_dict, self.down_duration_dict, self.scenario,
                            detail=detail, duration_str=self.duration_str, working_method=self.working_method)) for i in sub_pop]
        else:
            failure_cost = [self.w1 for i in sub_pop]
        if self.w2:
            energy_cost = [self.w2*np.array(get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict,
                            detail=detail, duration_str=self.duration_str, working_method=self.working_method)) for i in sub_pop]
        else:
            energy_cost = [self.w2 for i in sub_pop]
        if self.wc:
            conversion_cost = [self.wc*np.array(get_conversion_cost(i, self.job_dict, self.product_related_characteristics_dict, detail=detail)) for i in sub_pop]
        else:
            conversion_cost = [self.wc for i in sub_pop]
        if self.wb:
            constraint_cost = [self.wb*np.array(get_constraint_cost(i, self.start_time, self.job_dict, self.product_related_characteristics_dict, 
                                                            self.down_duration_dict, detail=detail, duration_str=self.duration_str, working_method=self.working_method)) for i in sub_pop]
        else:
            constraint_cost = [self.wb for i in sub_pop]
        if split_types:
            total_cost = (failure_cost, energy_cost, conversion_cost, constraint_cost)
        else:
            #import pdb; pdb.set_trace()
            total_cost = np.array(failure_cost) + np.array(energy_cost) + np.array(conversion_cost) + np.array(constraint_cost)
        return total_cost     
    
 
class BF(Scheduler):
    def __init__(self, job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict,
                  start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method):
        # Attributes assignment
        super().__init__(job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict,
                start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method)

    
    def check_all(self):
        if len(self.pop) > 10:
            raise ValueError('The input is too long, no brute force recommended')
        tot_cost_min = np.inf
        best_sched = []
        tot_cost_max = 0
        worst_sched = []
        import itertools
        allperm = itertools.permutations(self.pop)
        totallen = math.factorial(len(self.pop))
        i = 0
        while i < totallen:
            test = next(allperm)
            tot_cost = self.get_fitness([test])[0]
            if tot_cost < tot_cost_min:
                tot_cost_min = tot_cost
                best_sched = test
            if tot_cost > tot_cost_max:
                tot_cost_max = tot_cost
                worst_sched = test
            i += 1
            print(str(i) + '/' + str(totallen) + '\t {:}'.format(tot_cost_min), end='\r')
            if msvcrt.kbhit() == True:
                char = msvcrt.getche()
                if char in [b'c', b'q']:
                    print('User hit c or q button, exiting...')
                    break
        print('\n')
        return tot_cost_min, tot_cost_max, best_sched, worst_sched

                
class GA(Scheduler):
    def __init__(self, dna_size, cross_rate, mutation_rate, pop_size, pop, job_dict, price_dict, failure_dict, 
                 product_related_characteristics_dict, down_duration_dict, start_time, weight1, weight2, weightc, 
                 weightb, scenario,
                 num_mutations= 1, duration_str=duration_str, evolution_method='roulette', validation=False, pre_selection=False,
                 working_method='historical'):
        # Attributes assignment
        super().__init__(job_dict, price_dict, failure_dict, product_related_characteristics_dict, down_duration_dict,
                start_time, weight1, weight2, weightc, weightb, scenario, duration_str, working_method)
        self.dna_size = dna_size 
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.pop_size = pop_size
        self.num_mutations = num_mutations
        self.evolution_method = evolution_method
        self.validation = validation
        self.pre_selection = pre_selection
        # generate N random individuals (N = pop_size)
        # BETTER METHOD: FUTURE WORK
        # Add functionality: first due date first TODO:
        if self.pre_selection == True:
            # In this case, EDD rule has already been applied on the pop
            # Such procedure is executed in run_opt()
            self.pop = np.vstack(pop for _ in range(pop_size))
        else:
            self.pop = np.vstack([np.random.choice(pop, size=self.dna_size, replace=False) for _ in range(pop_size)])
        self.memory = []
    
    def crossover(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, the crossover result is used to represent the loser.
        '''
        # crossover for loser
        if np.random.rand() < self.cross_rate:
            cross_points = np.random.randint(0, 2, self.dna_size).astype(np.bool)
            keep_job =  winner_loser[1][~cross_points] # see the progress explained in the paper
            swap_job = winner_loser[0, np.isin(winner_loser[0].ravel(), keep_job, invert=True)]
            winner_loser[1][:] = np.concatenate((keep_job, swap_job))
        return winner_loser
    
    def mutate(self, loser, prob=False):
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        '''
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            if prob:
                tmpl = list(range(self.dna_size))
                point = np.random.choice(tmpl, size=1, replace=False, p=prob)
                tmpl.pop(int(point))
                # prob.pop(int(point))
                # inverse = list(np.array(prob).max() - np.array(prob))
                # inverse = inverse / sum(inverse)
                swap_point = np.random.choice(tmpl, size=1, replace=False)
            else:
                point, swap_point = np.random.choice(range(self.dna_size), size=2, replace=False)
            # point, swap_point = np.random.randint(0, self.dna_size, size=2)
            swap_A, swap_B = loser[point], loser[swap_point]
            loser[point], loser[swap_point] = swap_B, swap_A
        return loser
        
    def evolve(self, n, evolution=None):
        ''' 
        Execution of the provided GA.

        Parameters
        ----------
        n: int
            Number of iteration times 
        '''

        i = 1
        if evolution == None:
            evolution = self.evolution_method
        num_couples = 1

        while i <= n: # n is the number of evolution times in one iteration

            if evolution == 'roulette':
                fitness = self.get_fitness(self.pop)
                self.pop = self.pop[np.argsort(fitness)]

                idx = range(len(self.pop))
                prob = [1/(x+2) for x in idx]
                prob = [p / sum(prob) for p in prob]
                # roulette wheel 
                sub_pop_idx = np.random.choice(idx, size=num_couples * 2, replace=False, p=prob)
            else: # if evolution = 'random':
                sub_pop_idx = np.random.choice(np.arange(0, self.pop_size), size=2, replace=False)

            for j in list(range(len(sub_pop_idx) >> 1)):
                temp_pop_idx = sub_pop_idx[j:j+2]
                #sub_pop = self.pop[temp_pop_idx] # pick 2 individuals from pop
                #fitness = self.get_fitness(sub_pop) # get the fitness values of the two
            
                # Elitism Selection
                #winner_loser_idx = np.argsort(fitness)
                if evolution == 'roulette':
                    winner_loser_idx = np.sort(temp_pop_idx)
                else:
                    sub_pop = self.pop[temp_pop_idx] # pick 2 individuals from pop
                    fitness = self.get_fitness(sub_pop) # get the fitness values of the two
                    winner_loser_idx = temp_pop_idx[np.argsort(fitness)]
            
#               print('winner_loser_idx', winner_loser_idx)

                winner_loser = self.pop[winner_loser_idx]
                winner = winner_loser[0]; loser = winner_loser[1] # the first is winner and the second is loser

                #print('\nsubpop', winner_loser)
                #time.sleep(0.1)
            
                origin = loser.copy() # pick up the loser for genetic operations

                # Crossover (of the winner and the loser)
                winner_loser = self.crossover(winner_loser)
            
                # Mutation (only on the child)
                loser = winner_loser[1]
                for k in range(self.num_mutations):
                    # determine mismatch for each task
                    if evolution == 'roulette':
                        detailed_fitness = self.get_fitness([loser], detail=True)[0]
                        #print(detailed_fitness)
                        mutation_prob = [f/sum(detailed_fitness) for f in detailed_fitness]
                        loser = self.mutate(loser, mutation_prob)
                    else:
                        loser = self.mutate(loser)
                winner_loser[1] = loser

                # for i in np.arange(, self.pop_size):
                #     other = self.pop[i]
                #     for j in range(self.num_mutations):
                #         other = self.mutate(other)
                #     self.pop[i] = other

#                 print("Start validate:")
                flag = 0
                #print('validation step')
                if self.validation:
                    if not validate(winner_loser[1], self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict, self.precedence_dict, duration_str=self.duration_str,
                                    working_method=self.working_method):
                        #self.pop[sub_pop_idx] = winner_loser
                        #i = i + 1 # End of an evolution procedure
                        flag = 1
            
    #             print('Winner_loser after crossover and mutate: ', winner_loser)
    #             print('Winner', winner_loser[0])
    #             print('Loser', winner_loser[1])
    #             print('Origin2:', origin)
                
    #             print(hamming_distance(origin, winner_loser[1]))
                # Distance evaluation:
                #if hamming_distance(origin, loser) > (self.dna_size / 5):
                # Memory search：
                # child = loser
                    
    #             print("Child:", child)           
    #             print("Current memory:", self.memory)    
            
                #flag = 0 # 0 means the new generated child is not in the memory  
                # for item in self.memory:
                #     if (item == child).any():
                #         #print('In memory')
                #         flag = 1
                #for item in self.pop:
                #    if (item == child).any():
                #        flag = 1
                #        break
                if flag == 0:
                    #print("Not in memory!")
                    # if (len(self.memory) >= self.pop_size*2):
                    #     self.memory.pop()
                    # self.memory.append(loser)

                    #logging.info(self.get_fitness(self.pop))
            
                    #self.pop[sorted_sub_pop_idx][0] = winner
                    #print('\nsubpop', winner_loser)
                    #time.sleep(0.1)
                    if evolution == 'roulette':
                        split_half = int(self.pop_size // 2)
                        bottomlist = list(range(split_half, self.pop_size))
                        choice = np.random.choice(bottomlist)
                        self.pop[choice] = loser
                        fitness = np.sort(fitness)
                        fitness[choice] = self.get_fitness([loser])[0]
                    else:
                        self.pop[winner_loser_idx[1]] = loser


                    #print('After:', self.get_fitness(self.pop))
                    i = i + 1 # End of procedure
                else:
                    #print("In memory, start genetic operation again!")
                    pass
                #else:
                    #print("Distance too small, start genetic operation again!")
                #    pass
                
#         space = [get_energy_cost(i, self.start_time, self.job_dict, self.price_dict) for i in self.pop]
        
        # if self.w1:
        #     failure_cost_space = [self.w1 * get_failure_cost(i, self.start_time, self.job_dict, self.failure_dict, self.product_related_characteristics_dict, self.down_duration_dict, self.scenario) for i in self.pop]
        # else:
        #     failure_cost_space = [self.w1 for i in self.pop]
        # if self.w2:
        #     energy_cost_space = [self.w2 * get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict) for i in self.pop]
        # else: 
        #     energy_cost_space = [self.w2 for i in self.pop]
        # if self.wc:
        #     energy_cost_space = [self.wc * get_conversion_cost(i, self.job_dict, self.product_related_characteristics_dict) for i in self.pop]
        # else: 
        #     energy_cost_space = [self.wc for i in self.pop]

        if evolution != 'roulette':
            fitness = self.get_fitness(self.pop)
        
#         print(self.start_time)
#         print(self.pop)
#         print(space)
#         print("failure_cost_space:", failure_cost_space)
#         print("energy_cost_space:", energy_cost_space)

        return self.pop, fitness


def run_bf(start_time, end_time, down_duration_file, failure_file, prod_rel_file, energy_file, job_file,
           scenario, weight_failure=1, weight_conversion=1, weight_constraint=1, weight_energy=1, duration_str='duration', 
           working_method='historical'):
    # Generate raw material unit price
    try:
        down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
        failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
        hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)

        with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in hourly_failure_dict.items():
                writer.writerow([key, value])
    except:
        warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
        weight_failure = 0
        down_duration_dict = {}
        failure_list = []
        hourly_failure_dict = {}

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
    
    price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py
    if (start_time != None) and (end_time != None):
        job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
    elif (start_time != None):
        job_dict_new = read_jobs(job_file)
    else:
        raise NameError('No start time found!')

    # TODO: change
#     print("failure_dict", failure_dict)
#     exit()
#     # write corresponding failure dict into file
#     with open('ga_013_failure_plot.csv', 'w', newline='\n') as csv_file:
#         writer = csv.writer(csv_file)
#         for key, value in failure_dict_new.items():
#             writer.writerow([key, value])

    waiting_jobs = [*job_dict_new]
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        try:
            first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
        except:
            first_start_time = start_time

    bf = BF(job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
        product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
        start_time=first_start_time, weight1=weight_failure, weight2=weight_energy, weightc=weight_conversion, weightb=weight_constraint, 
        scenario=scenario, working_method='historical', duration_str=duration_str)
    
    best_result, worst_result, best_schedule, worst_schedule = bf.check_all()

    best_result_dict = visualize(best_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                                 down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
    worst_result_dict = visualize(worst_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                                  down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)

    return best_result, worst_result, best_result_dict, worst_result_dict

        
def run_opt(start_time, end_time, down_duration_file, failure_file, prod_rel_file, energy_file, job_file, 
            scenario, iterations, cross_rate, mut_rate, pop_size,  num_mutations=5, adaptive=[],
            stop_condition='num_iterations', stop_value=None, weight_conversion = 0, weight_constraint = 0, weight_energy = 0, weight_failure = 0,
            duration_str=duration_str, evolution_method='roulette', validation=False, pre_selection=False, working_method='expected'):
    print('Using', working_method, 'method')
    filestream = open('previousrun.txt', 'w')
    logging.basicConfig(level=20, stream=filestream)
    # Generate raw material unit price
    failure_downtimes = False
    if working_method == 'historical':
        try:
            down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
            #print('test')
            if weight_failure != 0:
                failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
                print(weight_failure)
                hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)
                with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
                    writer = csv.writer(csv_file)
                    for key, value in hourly_failure_dict.items():
                        writer.writerow([key, value])
            else:
                failure_list = []
                hourly_failure_dict = {}                
        except:
            warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
            failure_downtimes = True
    if (working_method != 'historical') or failure_downtimes:
        warnings.warn('No import of downtime durations.')
        weight_failure = 0
        down_duration_dict = {}
        failure_list = []
        hourly_failure_dict = {}

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
    
    price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py

    if (start_time != None) and (end_time != None):
        job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
    elif (start_time != None):
        job_dict_new = read_jobs(job_file)
    else:
        raise NameError('No start time found!')

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
    
#     print(job_dict_new)
    if pre_selection == True:
        sorted_jobs = OrderedDict(sorted(job_dict_new.items(), key=lambda kv: kv[1].get('before')))
        waiting_jobs = [*sorted_jobs]
#         print("Sorted_job:", sorted_job)
    
#     print(sorted_job)
#     print(waiting_jobs)
#     exit()
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        try:
            first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
        except:
            first_start_time = start_time
    
#     print("Waiting jobs: ", waiting_jobs)
#     print("Prices: ", price_dict_new)
#     print("Failures: ", failure_dict_new)

    # result_dict = {}
    # original_schedule = waiting_jobs  
    # total_result = 0
    # if weight_energy:
    #     total_result += weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # if weight_failure:
    #     total_result += weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                     product_related_characteristics_dict, down_duration_dict, scenario)
    # if weight_conversion:
    #     total_result += weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
    # if weight_before:
    #     total_result += weight_before * get_before_cost(original_schedule, first_start_time, job_dict_new)
    # result_dict.update({0: total_result}) # generation 0 is the original schedule

    #import pdb; pdb.set_trace()

    # Remove the downtimes from the job dict (the product is not produced during this period)
    #job_dict_new = remove_downtimes(job_dict_new)

    
#     exit()
    ga = GA(dna_size=DNA_SIZE, cross_rate=cross_rate, mutation_rate=mut_rate, pop_size=pop_size, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            start_time = first_start_time, weight1=weight_failure, weight2=weight_energy, weightc=weight_conversion, 
            weightb = weight_constraint, scenario=scenario,
            num_mutations = num_mutations, duration_str=duration_str, evolution_method=evolution_method, validation=validation,
            pre_selection=pre_selection, working_method=working_method)

    result_dict = {}
    original_schedule = waiting_jobs
    #print(original_schedule)
    total_result = ga.get_fitness([original_schedule])
    result_dict.update({0: total_result})

    best_result_list = []
    worst_result_list = [] 
    mean_result_list = []
    generation = 1
    stop = False
    timer0 = time.monotonic()
    while not stop:
        if generation in adaptive:
            print()
            print(str(generation) + ' reached - changing parameters of the GA')
            ga.cross_rate /= 2
            ga.mutation_rate = (ga.mutation_rate + 1) / 2
#         print("Gen: ", generation)
        pop, res = ga.evolve(1)          # natural selection, crossover and mutation
#         print("res:", res)
        best_index = np.argmin(res)
        worst_index = np.argmax(res)
        mean = np.mean(res)
        print(str(generation) + '/' + str(iterations) + ':\t' +  str(res[best_index]), end=''); print('\r', end='') # overwrite this line continually
        generation += 1

        best_result_list.append(res[best_index])
        worst_result_list.append(res[worst_index])
        mean_result_list.append(mean)

        if stop_condition == 'num_iterations':
            if generation >= iterations:
                stop = True
        if stop_condition == 'end_value':
            if res[best_index] < stop_value:
                stop = True
        if stop_condition == 'abs_time':
            timer1 = time.monotonic()  # returns time in seconds
            elapsed_time = timer1-timer0
            if elapsed_time >= stop_value:
                stop = True
        if msvcrt.kbhit() == True: # Only works on Windows
            char = msvcrt.getche()
            if char in [b'c', b'q']:
                print('User hit c or q button, exiting...')
                stop = True
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
#         result_dict.update({generation:res[best_index]})
    
    # Used to store intermediate result for large-size problems
#     with open('IGAlarge.pkl', 'wb') as f:
#         pickle.dump(pop[best_index], f

    timer1 = time.monotonic()
    elapsed_time = timer1-timer0
    print()
    print('Elapsed time: {:.2f} s'.format(elapsed_time))

    print()      
    print("Candidate schedule", pop[best_index])
    candidate_schedule = pop[best_index]

    # if weight_energy:
    #     candidate_energy_cost = weight_energy * get_energy_cost(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # else:
    #     candidate_energy_cost = weight_energy
    # if weight_failure:
    #     candidate_failure_cost = weight_failure * get_failure_cost(candidate_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                     product_related_characteristics_dict, down_duration_dict, scenario)
    # else:
    #     candidate_failure_cost = weight_failure
    # if weight_conversion:
    #     candidate_conversion_cost = weight_conversion * get_conversion_cost(candidate_schedule, job_dict_new, product_related_characteristics_dict)
    # else:
    #     candidate_conversion_cost = weight_conversion

    total_cost = ga.get_fitness([candidate_schedule], split_types=True)
    total_cost = list(itertools.chain(*total_cost))

    print("Candidate failure cost:", total_cost[0])
    print("Candidate energy cost:", total_cost[1])
    print("Candidate conversion cost:", total_cost[2])
    print("Candidate deadline cost", total_cost[3])
    print("Candidate total cost:", sum(total_cost))
    
#     print("Most fitted cost: ", res[best_index])

    print("\nOriginal schedule:", original_schedule)
#     print("DNA_SIZE:", DNA_SIZE) 
    print("Original schedule start time:", first_start_time)
    # if weight_energy:
    #     original_energy_cost = weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # else:
    #     original_energy_cost = 0
    # if weight_failure:
    #     original_failure_cost = weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                                             product_related_characteristics_dict, down_duration_dict, scenario=scenario)
    # else:
    #     original_failure_cost = weight_failure
    # if weight_conversion:
    #     original_conversion_cost = weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
    # else:
    #     original_conversion_cost = weight_conversion
    original_cost = ga.get_fitness([original_schedule], split_types=True)
    original_cost = list(itertools.chain(*original_cost))
    print("Original failure cost: ", original_cost[0])
    print("Original energy cost: ", original_cost[1])
    print("Original conversion cost:", original_cost[2])
    print("Original deadline cost", original_cost[3])
    print("Original total cost:", sum(original_cost))
    
    #print(duration_str)
    result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                            down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
    #import pdb; pdb.set_trace()
    result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                                   down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
#     print("Visualize_dict_origin:", result_dict)
#     print("Down_duration", down_duration_dict)


    # Output for visualization
    with open('executionRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict.items():
            writer.writerow([key, value[0], value[1], value[2]])
            
    with open('originalRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict_origin.items():
            writer.writerow([key, value[0], value[1], value[2]])
            
    with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in down_duration_dict.items():
            writer.writerow([key, value[0], value[1]])

    filestream.close()

    return sum(total_cost), sum(original_cost), result_dict, result_dict_origin, best_result_list, mean_result_list, worst_result_list, generation


def make_new_jobs_dict(origin_dict, urgent_dict):
    stamp = min(x.get('ReleaseDate') for x in urgent_dict.values()) # Find the smallest release date
    print(stamp)
    res_dict = {}
    for key, value in origin_dict.items():
        try:
            if value['start'] >= stamp: # All jobs whose start time after the stamp needs to be re-organized
                res_dict.update({key:value})
        except TypeError:
            print("Wrong type when comparing jobs.")
            raise
    
    res_dict.update(urgent_dict)

    return res_dict


def run_opt_urgent(start_time, end_time, down_duration_file, failure_file, prod_rel_file, energy_file, job_file, urgent_job_file,
            scenario, iterations, cross_rate, mut_rate, pop_size,  num_mutations=5, adaptive=[],
            stop_condition='num_iterations', stop_value=None, weight_conversion = 0, weight_constraint = 0, weight_energy = 0, weight_failure = 0,
            duration_str=duration_str, evolution_method='roulette', validation=False, pre_selection=False, working_method='expected'):
    print('Using', working_method, 'method')
    filestream = open('previousrun.txt', 'w')
    logging.basicConfig(level=20, stream=filestream)
    # Generate raw material unit price
    failure_downtimes = False
    if working_method == 'historical':
        try:
            down_duration_dict = select_from_range(start_time, end_time, read_down_durations(down_duration_file), 0, 1) # File from EnergyConsumption/InputOutput
            #print('test')
            if weight_failure != 0:
                failure_list = read_failure_data(failure_file) # File from failuremodel-master/analyse_production
                print(weight_failure)
                hourly_failure_dict = get_hourly_failure_dict(start_time, end_time, failure_list, down_duration_dict)
                with open('range_hourly_failure_rate.csv', 'w', newline='\n') as csv_file:
                    writer = csv.writer(csv_file)
                    for key, value in hourly_failure_dict.items():
                        writer.writerow([key, value])
            else:
                failure_list = []
                hourly_failure_dict = {}                
        except:
            warnings.warn('Import of downtime durations failed, using scheduling without failure information.')
            failure_downtimes = True
    if (working_method != 'historical') or failure_downtimes:
        warnings.warn('No import of downtime durations.')
        weight_failure = 0
        down_duration_dict = {}
        failure_list = []
        hourly_failure_dict = {}

#     print("down_duration_dict: ", down_duration_dict)
#     print("hourly_failure_dict: ", hourly_failure_dict)
#     exit()
    
    product_related_characteristics_dict = read_product_related_characteristics(prod_rel_file)
    
    price_dict_new = read_price(energy_file) # File from EnergyConsumption/InputOutput
#     price_dict_new = read_price('electricity_price.csv') # File generated from generateEnergyCost.py

#     if (start_time != None) and (end_time != None):
#         job_dict_new = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
#     elif (start_time != None):
#         job_dict_new = read_jobs(job_file)
#     else:
#         raise NameError('No start time found!')

    if (start_time != None) and (end_time != None):
        job_dict_origin = select_from_range(start_time, end_time, read_jobs(job_file), 'start', 'end') # File from EnergyConsumption/InputOutput
    elif (start_time != None):
        job_dict_origin = read_jobs(job_file)
    else:
        raise NameError('No start time found!')
                
    job_dict_urgent = read_jobs(urgent_job_file)
    job_dict_new = make_new_jobs_dict(job_dict_origin, job_dict_urgent)
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
    
#     print(job_dict_new)
    if pre_selection == True:
        sorted_jobs = OrderedDict(sorted(job_dict_new.items(), key=lambda kv: kv[1].get('before')))
        waiting_jobs = [*sorted_jobs]
#         print("Sorted_job:", sorted_job)
    
#     print(sorted_job)
#     print(waiting_jobs)
#     exit()
    
    if not waiting_jobs:
        raise ValueError("No waiting jobs!")
    else:
        try:
            first_start_time = job_dict_new.get(waiting_jobs[0])['start'] # Find the start time of original schedule
        except:
            first_start_time = start_time
    
#     print("Waiting jobs: ", waiting_jobs)
#     print("Prices: ", price_dict_new)
#     print("Failures: ", failure_dict_new)

    # result_dict = {}
    # original_schedule = waiting_jobs  
    # total_result = 0
    # if weight_energy:
    #     total_result += weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # if weight_failure:
    #     total_result += weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                     product_related_characteristics_dict, down_duration_dict, scenario)
    # if weight_conversion:
    #     total_result += weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
    # if weight_before:
    #     total_result += weight_before * get_before_cost(original_schedule, first_start_time, job_dict_new)
    # result_dict.update({0: total_result}) # generation 0 is the original schedule

    #import pdb; pdb.set_trace()

    # Remove the downtimes from the job dict (the product is not produced during this period)
    #job_dict_new = remove_downtimes(job_dict_new)

    
#     exit()
    ga = GA(dna_size=DNA_SIZE, cross_rate=cross_rate, mutation_rate=mut_rate, pop_size=pop_size, pop = waiting_jobs,
            job_dict=job_dict_new, price_dict=price_dict_new, failure_dict=hourly_failure_dict, 
            product_related_characteristics_dict = product_related_characteristics_dict, down_duration_dict=down_duration_dict,
            start_time = first_start_time, weight1=weight_failure, weight2=weight_energy, weightc=weight_conversion, 
            weightb = weight_constraint, scenario=scenario,
            num_mutations = num_mutations, duration_str=duration_str, evolution_method=evolution_method, validation=validation,
            pre_selection=pre_selection, working_method=working_method)

    result_dict = {}
    original_schedule = waiting_jobs
    #print(original_schedule)
    total_result = ga.get_fitness([original_schedule])
    result_dict.update({0: total_result})

    best_result_list = []
    worst_result_list = [] 
    mean_result_list = []
    generation = 1
    stop = False
    timer0 = time.monotonic()
    while not stop:
        if generation in adaptive:
            print()
            print(str(generation) + ' reached - changing parameters of the GA')
            ga.cross_rate /= 2
            ga.mutation_rate = (ga.mutation_rate + 1) / 2
#         print("Gen: ", generation)
        pop, res = ga.evolve(1)          # natural selection, crossover and mutation
#         print("res:", res)
        best_index = np.argmin(res)
        worst_index = np.argmax(res)
        mean = np.mean(res)
        print(str(generation) + '/' + str(iterations) + ':\t' +  str(res[best_index]), end=''); print('\r', end='') # overwrite this line continually
        generation += 1

        best_result_list.append(res[best_index])
        worst_result_list.append(res[worst_index])
        mean_result_list.append(mean)

        if stop_condition == 'num_iterations':
            if generation >= iterations:
                stop = True
        if stop_condition == 'end_value':
            if res[best_index] < stop_value:
                stop = True
        if stop_condition == 'abs_time':
            timer1 = time.monotonic()  # returns time in seconds
            elapsed_time = timer1-timer0
            if elapsed_time >= stop_value:
                stop = True
        if msvcrt.kbhit() == True: # Only works on Windows
            char = msvcrt.getche()
            if char in [b'c', b'q']:
                print('User hit c or q button, exiting...')
                stop = True
#         print("Most fitted DNA: ", pop[best_index])
#         print("Most fitted cost: ", res[best_index])
#         result_dict.update({generation:res[best_index]})
    
    # Used to store intermediate result for large-size problems
#     with open('IGAlarge.pkl', 'wb') as f:
#         pickle.dump(pop[best_index], f

    timer1 = time.monotonic()
    elapsed_time = timer1-timer0
    print()
    print('Elapsed time: {:.2f} s'.format(elapsed_time))

    print()      
    print("Candidate schedule", pop[best_index])
    candidate_schedule = pop[best_index]

    # if weight_energy:
    #     candidate_energy_cost = weight_energy * get_energy_cost(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # else:
    #     candidate_energy_cost = weight_energy
    # if weight_failure:
    #     candidate_failure_cost = weight_failure * get_failure_cost(candidate_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                     product_related_characteristics_dict, down_duration_dict, scenario)
    # else:
    #     candidate_failure_cost = weight_failure
    # if weight_conversion:
    #     candidate_conversion_cost = weight_conversion * get_conversion_cost(candidate_schedule, job_dict_new, product_related_characteristics_dict)
    # else:
    #     candidate_conversion_cost = weight_conversion

    total_cost = ga.get_fitness([candidate_schedule], split_types=True)
    total_cost = list(itertools.chain(*total_cost))

    print("Candidate failure cost:", total_cost[0])
    print("Candidate energy cost:", total_cost[1])
    print("Candidate conversion cost:", total_cost[2])
    print("Candidate deadline cost", total_cost[3])
    print("Candidate total cost:", sum(total_cost))
    
#     print("Most fitted cost: ", res[best_index])

    print("\nOriginal schedule:", original_schedule)
#     print("DNA_SIZE:", DNA_SIZE) 
    print("Original schedule start time:", first_start_time)
    # if weight_energy:
    #     original_energy_cost = weight_energy * get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, down_duration_dict)
    # else:
    #     original_energy_cost = 0
    # if weight_failure:
    #     original_failure_cost = weight_failure * get_failure_cost(original_schedule, first_start_time, job_dict_new, hourly_failure_dict,
    #                                                             product_related_characteristics_dict, down_duration_dict, scenario=scenario)
    # else:
    #     original_failure_cost = weight_failure
    # if weight_conversion:
    #     original_conversion_cost = weight_conversion * get_conversion_cost(original_schedule, job_dict_new, product_related_characteristics_dict)
    # else:
    #     original_conversion_cost = weight_conversion
    original_cost = ga.get_fitness([original_schedule], split_types=True)
    original_cost = list(itertools.chain(*original_cost))
    print("Original failure cost: ", original_cost[0])
    print("Original energy cost: ", original_cost[1])
    print("Original conversion cost:", original_cost[2])
    print("Original deadline cost", original_cost[3])
    print("Original total cost:", sum(original_cost))
    
    #print(duration_str)
    result_dict = visualize(candidate_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                            down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
    #import pdb; pdb.set_trace()
    result_dict_origin = visualize(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict, 
                                   down_duration_dict, hourly_failure_dict, energy_on=True, failure_on=True, duration_str=duration_str, working_method=working_method)
#     print("Visualize_dict_origin:", result_dict)
#     print("Down_duration", down_duration_dict)


    # Output for visualization
    with open('executionRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict.items():
            writer.writerow([key, value[0], value[1], value[2]])
            
    with open('originalRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in result_dict_origin.items():
            writer.writerow([key, value[0], value[1], value[2]])
            
    with open('downDurationRecords.csv', 'w', newline='\n') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in down_duration_dict.items():
            writer.writerow([key, value[0], value[1]])

    filestream.close()

    return sum(total_cost), sum(original_cost), result_dict, result_dict_origin, best_result_list, mean_result_list, worst_result_list, generation

if __name__ == '__main__':
    
    # Read parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=int, help="The running mode of the scheduler: 1-User 2-Demo", default=1)
    # TODO: procedures after the user choose mode
    parser.add_argument("historical_down_periods_file", help="File containing records of historical down duration periods.") # downDurations.csv
    parser.add_argument("failure_rate_file", help="File containing failure rate of each hour from the failure model.") # hourly_failure_rate.csv
    parser.add_argument("product_related_characteristics_file", help="File containing product related characteristics.") # productRelatedCharacteristics.csv
    parser.add_argument("energy_price_file", help="File containing energy price of each hour.") # price.csv
    parser.add_argument("job_info_file", help="File containing job information.") # jobInfoProd_ga_013.csv
    parser.add_argument("scenario", type=int, help="Choose scenario: 1-MTBF 2-Machine stop/restart") # number of scenario
    parser.add_argument("objective", type=int, help="Choose objectives: 1-Energy+Failure 2-Energy Only 3-Failure Only", default=1) 
    # TODO: prodedures after the user choose objectives
    parser.add_argument("pop_size", type=int, help="Population size") # pupulation size
    parser.add_argument("generations", type=int, help="Number of generations")
    parser.add_argument("crossover_rate", type=float, help="Crossover rate")
    parser.add_argument("mutation_rate", type=float, help="Mutation rate")
    args = parser.parse_args()
        
#     case 1 week
    ''' Use start_time and end_time to pick up a waiting job list from records.
        Available range: 2016-01-23 17:03:58.780 to 2017-11-15 07:15:20.500
    '''
    start_time = datetime(2016, 11, 3, 6, 0)
    end_time = datetime(2016, 11, 8, 0, 0)

    run_opt(start_time, end_time, args.historical_down_periods_file, 
           args.failure_rate_file, args.product_related_characteristics_file, 
           args.energy_price_file, args.job_info_file,
           args.scenario, args.generations, args.crossover_rate, args.mutation_rate, args.pop_size)