import numpy as np

class SimpleSchedule:
    """
    A simple schedule class which implements the most basic
    functionality of the schedule using lists.
    """
    def __init__(self, job_list, length_list, priority_list, duedate_list, weights=None):
        self.job_list = job_list
        self.length_list = length_list
        self.priority_list = priority_list
        self.duedate_list = duedate_list
        self.timing_dict = self.get_time()
        
        if weights is None:
            self.weights = dict()
            self.weights['weighted_tardiness'] = 1
        else:
            self.weights = weights
    
    def change_order(self, new_job_list):
        """ 
        Change the order of the job list
        """
        self.job_list = new_job_list
        self.timing_list = self.get_time()
        
    def copy_random(self):
        """ 
        Make a random copy of the current schedule
        Returns the schedule itself
        """
        return_sched = SimpleSchedule(np.random.choice(self.job_list, size=len(self.job_list), 
                                      replace=False), self.length_list, self.priority_list,
                                      self.duedate_list)
        return return_sched
    
    def copy_neworder(self, assign_order):
        """
        Copy the schedule in the order assigned by the 
        list assign_order
        """
        assert (set(assign_order) == set(self.job_list)), 'The keys inserted are not the same as the key of the jobs'
        return_sched = SimpleSchedule(assign_order,
                                      self.length_list, self.priority_list,
                                      self.duedate_list)
        return return_sched
                
    def get_time(self):
        """ 
        Get a new timing list, each job is assigned a
        timing acccording to its position in the job_list
        """
        timing_dict = {}
        
        #timing_list = [None]*len(self.job_list)
        current_time = 0
        for job in self.job_list:
            start_time = current_time
            current_time += self.length_list[job]
            timing_dict[job] = {'start': start_time,
                                'end': current_time,
                                'priority': self.priority_list[job],
                                'duedate': self.duedate_list[job]}
            #timing_list[job] = current_time             
        return timing_dict
            
    def get_weighted_tardiness_cost(self, detail=False):
        """
        Get the weighted tardiness cost for a certain
        job_list order
        """
        if detail:
            current_cost = []
        else:
            current_cost = 0
        for job in self.job_list:
            current_duedate = self.duedate_list[job]
            current_time = self.timing_dict[job]['end']
            if current_time > current_duedate:
                current_priority = self.priority_list[job]
                extra_cost = (current_time - current_duedate)\
                             * current_priority
                if detail:
                    current_cost.append(extra_cost)
                else:
                    current_cost += extra_cost
            else:
                if detail:
                    current_cost.append(0)
        return current_cost
            
    def get_fitness(self, detail=False):
        """
        Get fitness values for a generation
        """
        
        if self.weights['weighted_tardiness']:
            tardiness_cost = self.get_weighted_tardiness_cost(detail=detail)
            
        total_cost = np.array(tardiness_cost) * self.weights['weighted_tardiness']
        
        return total_cost
    
    def print_fitness(self):
        """
        Print fitness values
        """
        print("Total weighted tardiness cost is:", self.get_weighted_tardiness_cost())
        print("Total fitness value is:", self.get_fitness())
