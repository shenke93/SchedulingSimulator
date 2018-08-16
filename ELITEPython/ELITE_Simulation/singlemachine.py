import salabim as sim
import csv
import math

class Group(sim.Component):
    '''
    Machines in the same group are parallel machines. 
    Attributes: 
        name: name of group
        idle_machine list: idle machines of group
        job_list: jobs to do of group
        job_select_method: way of choosing jobs (scheduling strategy)
        fraction: fraction of group in the workshop
        file_name: name of configuration file
    '''
    def setup(self, job_select_method, number_of_machines, fraction, file_name):
        '''
        Initialize with scheduling strategy, machine numbers
        '''     
        if job_select_method.lower() == 'fifo': 
            self.job_select = self.job_select_fifo
        else:
            raise AssertionError('wrong selection method:', job_select_method)
        
        self.fraction = fraction
        
        self.machines = [Machine(group=self, name=self.name()+' Machine.') for _ in range(number_of_machines)]

        self.idle_machines = sim.Queue(self.name() + '.idle_machines')
        
        self.jobs = sim.Queue(self.name() + '.jobs')
        
        self.config_file = file_name
        
        self.price_list = []
        
        # read price information from file into list (format: string) 
        with open(self.config_file, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.price_list.append((row['Date'], row['Euro'])) 
        
#         print(self.price_list[0][0])
    def job_select_fifo(self):
        '''
        Simple strategy: first in first out
        '''
#         print('Using strategy: fifo')
        return self.jobs.head()
    
class Machine(sim.Component):
    '''
    Machine is the unit who processes jobs.
    Attributes: group, current running task     
    '''
    def setup(self, group):
        self.group = group
        self.task = None # Current task running on machine
        self.energy_cost = 0
        self.current_energy_price = 0

        
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
            if not self.task.flag_dist:
                self.calculate_energy_cost_task()
            yield self.hold(self.task.duration)
            # Calculate energy cost
#             self.energy_cost += self.task.duration * self.current_energy_price
#             print(self.name)
#             print(self.energy_cost)
            self.task.leave(job.task_in_execution)
            if job.tasks:   # Even if one task of job is done, there are remaining tasks to do
                task1 = job.tasks.head()
                job.enter(task1.group.jobs) # Add the job to to-do-job list of the group
                if task1.group.idle_machines:
                    task1.group.idle_machines.head().activate() # Activate an idle machine
            else:
                job.leave(plant) # All tasks of job is finished, the job can leave the plant

    def calculate_energy_cost_task(self):
        '''
        Read price info from group's price list and calculating the energy cost of current task.
        '''
        print('flag: %d' % self.task.flag_dist)
        print('energy_cost: %f' % self.energy_cost)
        t_start = env.now()   # start_time
        print('t_start: %f' % t_start)
        t_end = t_start + self.task.duration  # end_time
        print('t_end: %f' % t_end)
        
        tmp = float(self.group.price_list[math.floor(t_start)][1]) * (math.ceil(t_start) - t_start) + float(self.group.price_list[math.floor(t_end)][1]) * (t_end - math.floor(t_end)) # Head price and tail price
#         print('head: %f' % (float(self.group.price_list[math.floor(t_start)][1]) * (math.ceil(t_start) - t_start)))
#         print('tail: %f' % (float(self.group.price_list[math.floor(t_end)][1]) * (t_end - math.floor(t_end))))
#         print('tmp: %f' % tmp)

        for i in range(math.ceil(t_start), math.floor(t_end)):
#            print('price:'+self.group.price_list[i][1])
            self.energy_cost += float(self.group.price_list[i][1])
        
        self.energy_cost += tmp   
            
#         with open(self.config_file, encoding='utf-8') as file:
#             for line in file:
#                 key, value = line.split(',', 2)
#                 time = pd.to_datetime(key).strftime('%Y-%m-%d %H:%M:%S')
# #                 print(time)
#                 price = float(value)
#                 if (env.now() < time):
#                     break
#                 t = price
#         self.current_energy_price = t
        
            
        
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
        # file context format (inter_arrival_time, number_of_tasks, duration_dist)
        with open(self.config_file, encoding='utf-8') as csvfile:
            for line in csvfile:
                inter_arrival_time_dist, number_of_tasks_dist, duration_dist, flag_dist = line.split(',', 4)
                self.inter_arrival_time_dist = int(inter_arrival_time_dist)
                self.number_of_tasks_dist = int(number_of_tasks_dist)
                self.duration_dist = float(duration_dist)
                self.flag_dist = int(flag_dist)
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
        self.group = job_generator.group_dist.sample()
        self.duration = job_generator.duration_dist
        self.flag_dist = job_generator.flag_dist
        

        
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
                            number_of_machines = number_of_machines, fraction = fraction, file_name = 'price.csv'))

plant = sim.Queue('plant') # Job list of the plant        

group_dist = sim.Pdf(groups, probabilities=[group.fraction for group in groups])

JobGenerator(file_name = 'jobInfo.csv', group_dist = group_dist)
        
env.run(200)

print(groups[0].machines[0].energy_cost)        
# plant.print_statistics()    
# plant.print_info()    
        


        
        
        
        
        
        
        
        
        
        