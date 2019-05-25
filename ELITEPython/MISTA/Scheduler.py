''' 
Customized scheduler for the MISTA challenge.
Design the data input format.
Decide the fitness function.

Input format:
Activity Project ReleaseTime RequiredDuration ResourceMode1 ResourceMode2

Output format:
Activity Project Mode StartTime
'''
import csv
import os
import configparser

import numpy as np


class Activity(object):
    
    def __init__(self, idx, idx_project, release_time, duration_mode1, duration_mode2, consumption_mode1, consumption_mode2):
        """ The constructor, called when a job instance is created.
            Initialization of all job attributes.
            Attributes:
            idx: index 
            duration: expected duration for execution
            article_name: name of product
            article_type: type of product
        """
        self.idx = idx
        self.idx_project = idx_project
        self.release_time = release_time
        self.duration_mode1 = duration_mode1
        self.duration_mode2 = duration_mode2
        self.consumption_mode1 = consumption_mode1
        self.consumption_mode2 = consumption_mode2
        
    def __str__(self):
        res = "idx: %d \n idx_project: %d \n release_time: %d \n duration_mode1: %d \n duration_mode2: %d \n consumption_mode1: %d \n consumption_mode2: %d" % \
         (self.idx, self.idx_project, self.release_time, self.duration_mode1, self.duration_mode2, self.consumption_mode1, self.consumption_mode2)
         
        return res


def initializeJobs(jobInfoFile):
    """ Read job information from jobInfoFile.
    """
    
    shared_list = []
    
    try:
        with open(jobInfoFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                idx = int(row['Activity'])
                idx_project = int(row['Project'])
                release_time = int(row['ReleaseTime'])
                duration_mode1 = int(row['DurationMode1'])
                duration_mode2 = int(row['DurationMode2'])
                consumption_mode1 = int(row['ResourceMode1'])
                consumption_mode2 = int(row['ResourceMode2'])
               
                # Create job instances
                job = Activity(idx, idx_project, release_time, duration_mode1, duration_mode2, consumption_mode1, consumption_mode2)
                shared_list.append(job)
    except:
        print("Unexpected error when initializing jobs from {}:".format(jobInfoFile))
        raise
    
    return shared_list
    

def build_consumption_matrix(job):
    '''
    Build the consumption matrix of a job. Format:
           Duration Resource
    Mode1  **       **
    Mode2  **       **
    '''
    res = np.zeros(shape=(2,2))
    res[0] = [job.duration_mode1, job.consumption_mode1]
    res[1] = [job.duration_mode2, job.consumption_mode2]
    return res
       
def calculate_fitness(pop, con_matrix):
    for i, j in zip(pop, con_matrix):
        print(i*j)
    
        
    
           
if __name__ == '__main__':
    
    # Parameter Settings
    configParser = configparser.RawConfigParser()   
    configFilePath = 'config.txt'
    configParser.read(configFilePath)
    
    original_folder = configParser.get('input-config', 'input_data_folder')
    job_info_file = os.path.join(original_folder, configParser.get('input-config', 'job_info_file'))
    
    
    waiting_jobs = initializeJobs(job_info_file)
    
#     Test Code
#     for i in waiting_jobs:
#         print(i)
#         print(build_consumption_matrix(i))
         
    size_individual = len(waiting_jobs)
    modes = np.random.randint(0, 2, size=size_individual)
    print(modes)
    
    con_matrix = [build_consumption_matrix(i) for i in waiting_jobs]
    
#     Test Code
    for i in con_matrix:
        print(i)
        print(type(i))

    calculate_fitness(modes, con_matrix)