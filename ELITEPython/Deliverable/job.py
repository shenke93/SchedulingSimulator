# define jobs
from enum import Enum
from multiprocessing import Manager, Process
import csv 
from datetime import datetime

class JobState(Enum):
    Created = 1
    Waiting = 2
    Running = 3
    Blocked = 4
    Terminated = 5

class Job(object):
    """
    The base(meta, abstract) class of job.
    """
    def __init__(self, idx, article_name, article_type, quantity):
        """ The constructor, called when a job instance is created.
            Initialization of all job attributes.
            Attributes:
            idx: index 
            duration: expected duration for execution
            article_name: name of product
            article_type: type of product
        """
        self.idx = idx
        self.article_name = article_name
        self.article_type = article_type
        self.quantity = quantity
        self.state = JobState.Created
    
    def __str__(self):
        """ Customized information when printing. 
        """
        return "idx: %d \n article_name: %s \n article_type: %s \n quantity: %d \n state: %s \n" % (self.idx, self.article_name, self.article_type, self.quantity, self.state)
        
    def __del__(self):
        """ The destructor, called when a job instance is cleaned.
        """
        pass
    
class JobHis(Job):
    """ Jobs from historical records.
    """
    def __init__(self, idx, article_name, article_type, quantity, duration, start_date, end_date):
        super().__init__(idx, article_name, article_type, quantity)
        self.duration = duration
        self.start_date = start_date
        self.end_date = end_date
    
    def __str__(self):
        return super().__str__() + " duration: %.2f \n start_date: %s \n end_date: %s \n" % (self.duration, self.start_date, self.end_date)
    
    def __del__(self):
        pass
    
class JobFut(Job):
    """ Jobs for future planning.
    """
    def __init__(self, idx, article_name, article_type, quantity, exp_duration):
        Job.__init__(self, idx, article_name, article_type, quantity)
        self.exp_duration = exp_duration
    
    def __str__(self):
        return super().__str__() + " exp_duration: %.2f \n" % (self.exp_duration)
    def __del__(self):
        pass


def initializeJobs(jobInfoFile):
    """ Read job information from jobInfoFile.
    """
    manager = Manager()
    shared_list = manager.list()
    
    try:
        with open(jobInfoFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                index = int(row['ProductionRequestId'])
                start = datetime.strptime(row['StartDateUTC'], "%Y-%m-%d %H:%M:%S.%f")
                end = datetime.strptime(row['EndDateUTC'], "%Y-%m-%d %H:%M:%S.%f")
                duration = float(row['Duration'])
                articleName = row['ArticleName']
                quantity = int(row['Quantity'])
                articleType = row['ArticleType']
                # Create job instances
                job = JobHis(index, articleName, articleType, quantity, duration, start, end)
                shared_list.append(job)
    except:
        print("Unexpected error when initializing jobs from {}:".format(jobInfoFile))
        raise
    
    return shared_list

def addJob(list, job):
    list.append(job)

def addJobsFromFile(list, jobInfoFile):
    try:
        with open(jobInfoFile, encoding='utf-8') as jobInfo_csv:
            reader = csv.DictReader(jobInfo_csv)
            for row in reader:
                index = int(row['ProductionRequestId'])
                start = datetime.strptime(row['StartDateUTC'], "%Y-%m-%d %H:%M:%S.%f")
                end = datetime.strptime(row['EndDateUTC'], "%Y-%m-%d %H:%M:%S.%f")
                duration = float(row['Duration'])
                articleName = row['ArticleName']
                quantity = int(row['Quantity'])
                articleType = row['ArticleType']
                # Create job instances
                job = JobHis(index, articleName, articleType, quantity, duration, start, end)
                list.append(job)
    except:
        print("Unexpected error when adding jobs from {}:".format(jobInfoFile))
        raise
    
def updateOneJob(list, job):
    # Run a process to add one job into the waiting job list
    p = Process(target=addJob, args=(list, job))
    p.start()
    p.join()
    
def updateJobs(list, jobInfoFile):
    p = Process(target=addJobsFromFile, args=(list, jobInfoFile))
    p.start()
    p.join()

if __name__ == '__main__':
    
    # Unit test with direct input
    job1 = Job(1, 'name1', 'type1', 100)
    job2 = JobHis(2, 'name2', 'type2', 200, 4.0, 'start_date2', 'end_date2')
    job3 = JobFut(3, 'name3', 'type3', 300, 5.5)
    print(job1)
    print(job2)
    print(job3)