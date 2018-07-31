import salabim as sim

class Group(sim.Component):
    '''
    Machines in the same group are parallel machines. 
    Attributes: name, idle_machine list, job list, job_select_method
    '''
    def setup(self, job_select_method, number_of_machines, fraction):
        '''
        Initialize with scheduling strategy, machine numbers
        ''' 
        
        if job_select_method.lower() == 'fifo':
            self.job_select = self.job_select_fifo
        else:
            raise AssertionError('wrong selection method:', job_select_method)
        
        self.fraction = fraction
        
        self.machines = [Machine(group=self, name=self.name()+'.') for _ in range(number_of_machines)]

        self.idle_machines = sim.Queue(self.name() + '.idle_machines')
        
        self.jobs = sim.Queue(self.name() + '.jobs')
            
    def job_select_fifo(self):
        '''
        Simple strategy: first in first out
        '''
        return self.jobs.head()
    
class Machine(sim.Component):
    '''
    Machine is the unit who processes jobs.
    Attributes: group, current running task     
    '''
    def setup(self, group):
        self.group = group
        self.task = None # Current task running on machine
        
    def process(self):
        while True:
            # Initialize
            self.task = None
            self.enter(self.group.idle_machines) # After initializing, the machine is idle without any task running
            
            while not self.group.jobs:  # If no jobs (of the group) need to be processed, passivate the machine
                yield self.passivate()
            
            self.leave(self.group.idle_machines) # If there are jobs to run, make the machine run
            job = self.group.job_select() # Select the job using methods defined in the Group class
            job.leave(self.group.jobs)
            self.task = job.tasks.pop()
            self.task.enter(job.task_in_execution)
            yield self.hold(self.task.duration)
            self.task.leave(job.task_in_execution)
            
            if job.tasks:   # Even if one task of job is done, there are remaining tasks to do
                task1 = job.tasks.head()
                job.enter(task1.group.jobs) # Add the job to to-do-job list of the group
                if task1.group.idle_machines:
                    task1.group.idle_machines.head().activate() # Activate an idle machine
            else:
                job.leave(plant) # All tasks of job is finished, the job can leave the plant


class JobGenerator(sim.Component):
    '''
    JobGenerator is used to generate jobs (from file)
    '''
    def setup(self, file_name, group_dist):
        '''
        Arguments: arriving time between jobs, number of tasks of each job, group, expected processing duration
        '''
        # This block should use the input from jobInfo.txt
#         self.inter_arrival_time_dist = inter_arrival_time_dist
#         self.number_of_task_dist = number_of_tasks_dist
#         self.group_dist = group_dist
#         self.duration_dist = duration_dist
        self.config_file = file_name
        self.group_dist = group_dist
                
    def process(self):
        with open(self.config_file, encoding='utf-8') as csvfile:
            for line in csvfile:
                inter_arrival_time_dist, number_of_tasks_dist, duration_dist = line.split(',', 3)
                self.inter_arrival_time_dist = int(inter_arrival_time_dist)
                self.number_of_tasks_dist = int(number_of_tasks_dist)
                self.duration_dist = int(duration_dist)
                yield self.hold(self.inter_arrival_time_dist)
                Job(job_generator=self)
        

class Job(sim.Component):
    '''
    Jobs are processing objects on machines.
    Attribites: tasks, task_in_execution
    '''
    def setup(self, job_generator):
        self.tasks = sim.Queue(fill=[Task(job_generator=job_generator, job=self, 
                                          name='Task '+str(self.sequence_number()) + '.')
                                          for _ in range(job_generator.number_of_tasks_dist)], name='tasks.') # Fill in the job tasks
        self.task_in_execution = sim.Queue(name='task_in_execution')
        self.enter(self.tasks[0].group.jobs) # Add job to a group list
        if self.tasks.head().group.idle_machines:
            self.tasks.head().group.idle_machines.head().activate() # Activate the first idle machine of the group
        self.enter(plant)
        
class Task(sim.Component):
    '''
    Smallest processing unit on machines.
    Attributes:group, duration
    '''
    def setup(self, job_generator, job):
        self.group = job_generator.group_dist()
        self.duration = job_generator.duration_dist
        

        
env = sim.Environment(trace=True)

groups=[]

with sim.ItemFile('config.txt') as f:
    job_select_method = f.read_item()
    
    while True:
        name = f.read_item()
        if name == '//':
            break
        number_of_machines = f.read_item_int()
        fraction = f.read_item_float()
        groups.append(Group(name = name, job_select_method = job_select_method, 
                            number_of_machines = number_of_machines, fraction = fraction))

plant = sim.Queue('plant') # Job list of the plant        

# bug with reading things from file! Do not use package format!
# with open('jobInfo.csv', encoding='utf-8') as csvfile:
#     for line in csvfile:
#         inter_arrival_time_dist, number_of_tasks_dist, group_dist, duration_dist = line.split(',', 4)
#         print(inter_arrival_time_dist)
#         print(number_of_tasks_dist)
#         print(group_dist)
#         print(duration_dist)

group_dist = sim.Pdf(groups, probabilities=[group.fraction for group in groups])

JobGenerator(file_name = 'JobInfo.csv', group_dist = group_dist)
        
env.run(200)
        
        
        


        
        
        
        
        
        
        
        
        
        