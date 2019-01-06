import sys
import csv
from datetime import timedelta, datetime

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
    
#     print("Start time:", first_start_time)

    original_schedule = selected_jobs