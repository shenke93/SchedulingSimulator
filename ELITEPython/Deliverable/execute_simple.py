import re
import os, sys
from population_simple import SimpleSchedule
from helperfunctions import GA_settings
from scheduler_simple import run_opt

curdir = os.path.abspath(sys.path[0])
os.chdir(curdir)

#from SchedulerV000 import run_opt
#from visualise_lib import show_ga_results, plot_gantt, show_energy_plot

NUM = 50
FILENAME = r'OR dataset\wt{}.txt'.format(NUM)
OUTPUT_FILENAME = r'OR dataset\wtself{}.txt'.format(NUM)

def read_file_num(filename, num_jobs):
    with open(filename) as f:
        read_data = f.read()
        
    temp = re.findall(r"\d+", read_data)
    temp = [int(t) for t in temp]
    
    list_jobs = []
    list_priorities = []
    list_duedate = []
    for t, i in zip(temp, range(len(temp))):
        j = (i % (num_jobs*3))
        k = j // (num_jobs*3)
        if (j == 0):
            temp_jobs = []
            temp_priorities = []
            temp_duedate = []
        if (0 <= j < num_jobs):
            temp_jobs.append(t)
        elif (num_jobs <= j < num_jobs*2):
            temp_priorities.append(t)
        elif (num_jobs*2 <= j < num_jobs*3):
            temp_duedate.append(t)
        if (j == num_jobs*3 - 1):
            list_jobs.append(temp_jobs)
            list_priorities.append(temp_priorities)
            list_duedate.append(temp_duedate)
        
            
    return list_jobs, list_priorities, list_duedate

if __name__ == "__main__":
    # Read the input file
    job_list, priority_list, duedate_list = read_file_num(FILENAME, NUM)
    
    list_optimal = []
    
    num = 0
    
    for (job, priority, duedate) in zip(job_list, priority_list, duedate_list):
        
        # Convert the input file to a SimpleSchedule object
        simplesched = SimpleSchedule(list(range(len(job))), 
                                     job, priority, duedate)
    
        # Get the settings for the scheduler
        settings = GA_settings(pop_size=20, cross_rate=0.7, mutation_rate=0.5,
                               num_mutations=5, iterations=100000,
                               adapt_ifin=[25000, 50000, 75000, 100000])
    
        num += 1
        print('Run #'+ str(num))
        
        # Run the optimizer
        total_cost, original_cost, candidate_schedule,\
        original_schedule, lists_result =\
        run_opt(simplesched, settings)
        
        list_optimal.append(total_cost)
    
    # Save the output file
    file = open(OUTPUT_FILENAME, "w")  
    for l in list_optimal:   
        file.write('{:10d}\n'.format(l))
    file.close()