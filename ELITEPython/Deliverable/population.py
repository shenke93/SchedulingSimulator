from datetime import timedelta
from SchedulerV000 import ceil_dt, floor_dt
import warnings

C1 = 10 # Used for failure cost calculation in run-down scenario
C2 = 30

class Schedule:
    def __init__(self, order, start_time, job_dict, failure_dict, prc_dict, downdur_dict, price_dict,
                 scenario, duration_str='duration', working_method='historical'):
        self.order = order
        self.start_time = start_time
        self.job_dict = job_dict
        self.failure_dict = failure_dict
        self.prc_dict = prc_dict
        self.downdur_dict = downdur_dict
        self.price_dict = price_dict
        self.scenario = scenario
        self.duration_str = duration_str
        self.working_method = working_method
        self.time_dict = self.get_time()
    
    def get_time(self):
        # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
        detailed_dict = {}
        t_now = self.start_time 

        #print(duration_str)
        #input()
        
        for item in self.order:
            t_start = t_now
            
            unit1 = self.job_dict.get(item, -1)
            
            #quantity = unit1['quantity'] # get job objective quantity
            
            #du = quantity / unit2[2] # get job duration
            if self.duration_str == 'duration':
                du = unit1['duration']
            elif self.duration_str == 'quantity':
                quantity = unit1['quantity']
                product_type = unit1['product'] # get job product type
                unit2 = self.prc_dict.get(product_type)
                try:
                    du = quantity / unit2['targetproduction'] # get job duration
                except:
                    print(quantity, unit2['targetproduction'])
                    raise
            else:
                raise NameError('Faulty value inserted')
            
            if self.working_method == 'historical':
                t_o = t_start + timedelta(hours=du) # Without downtime duration
                t_end = t_o
            
                for key, value in self.downdur_dict.items():
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
            elif self.working_method == 'expected':
                if 'availability' in unit2:
                    t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
                else:
                    raise NameError('Availability column not found, error')
            
            detailed_dict.update({item:[t_start, t_end, du, unit1['product'], unit1['type']]})
            t_now = t_end

        return detailed_dict

    def get_failure_cost(self, detail=False):
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
        t_now = self.start_time
        if self.scenario == 1:
            for item in self.order:
                t_start = t_now
                unit1 = self.job_dict.get(item, -1)
                if unit1 == -1:
                    raise ValueError("No matching item in job dict: ", item)
            
                product_type = unit1['product']    # get job product type
                quantity = unit1['quantity']  # get job quantity
                
        #         if du <= 1: # safe period of 1 hour (no failure cost)
        #             continue;
                unit2 = self.prc_dict.get(product_type, -1)
                if unit2 == -1:
                    raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
                
                if self.duration_str == 'duration':
                    du = unit1['duration']
                if self.duration_str == 'quantity':
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

                if self.working_method == 'historical':
                    t_o = t_start + timedelta(hours=du) # Without downtime duration
                    t_end = t_o

                    #print(down_duration_dict)
                    
                    for key, value in self.downdur_dict.items():
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
                elif self.working_method == 'expected':
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
                
                tmp = (1 - self.failure_dict.get(t_sd, 0)) * (1 - self.failure_dict.get(t_ed, 0))
                step = timedelta(hours=1)
                while t_su < t_ed:
                    if self.failure_dict.get(t_su, -1) == -1:
                        raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
                    tmp *= (1 - self.failure_dict.get(t_su, 0)) 
                    t_su += step
        #         
        #         if product_related_characteristics_dict.get(product_type, -1) == -1:
        #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
                if detail:
                    failure_cost.append((1-tmp) * quantity * uc)
                else:
                    failure_cost += (1-tmp) * quantity * uc 
                t_now = t_end
        
        
        if self.scenario == 2:
            for item in self.order:
                fc_temp = 0
                t_start = t_now
                unit1 = self.job_dict.get(item, -1)
                if unit1 == -1:
                    raise ValueError("No matching item in job dict: ", item)
            
                product_type = unit1['type']    # get job product type
                quantity = unit1['quant']  # get job quantity
                
        #         if du <= 1: # safe period of 1 hour (no failure cost)
        #             continue;
                unit2 = self.prc_dict.get(product_type, -1)
                if unit2 == -1:
                    raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

                if self.duration_str == 'duration':
                    du = unit1['duration']
                if self.duration_str == 'quantity':
                    du = quantity / unit2['targetproduction'] # get job duration
                
        #        du = quantity / unit2[2] # get job duration
        #         print("Duration:", du)
        #         uc = unit2[0] # get job raw material unit price
                
                if self.working_method == 'historical':
                    t_o = t_start + timedelta(hours=du) # Without downtime duration
                    #print("t_o:", t_o)
                    t_end = t_o
                    for key, value in self.downdur_dict.items():
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
                elif self.working_method == 'expected':
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

    def get_energy_cost(self, detail=False):
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
        t_now = self.start_time # current timestamp
        i = 0
        for item in self.order:
    #         print("For job:", item)
            t_start = t_now
    #         print("Time start: " + str(t_now))
            unit1 = self.job_dict.get(item, -1)
            if unit1 == -1:
                raise ValueError("No matching item in the job dict for %d" % item)
        
            product_type = unit1['product'] # get job product type
            
            unit2 = self.prc_dict.get(product_type, -1)
            if unit2 == -1:
                raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

            if self.duration_str == 'duration':
                du = unit1['duration']
            if self.duration_str == 'quantity':
                quantity = unit1['quantity']
                du = quantity / unit2['targetproduction'] # get job duration
    #         print("Duration:", du)
            po = unit2['power'] # get job power profile
            job_en_cost = 0
            
            if self.working_method == 'historical':
                #print(du)
                t_o = t_start + timedelta(hours=du) # Without downtime duration
        #         print("t_o:", t_o)
                t_end = t_o
                
                for key, value in self.downdur_dict.items():
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
            elif self.working_method == 'expected':
                if 'availability' in unit2:
                    t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
                else:
                    raise NameError('Availability column not found, error')
            
            # calculate sum of head price, tail price and body price

            t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start right border
            t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
            t_sd = floor_dt(t_start, timedelta(hours=1)) # t_start_left border

            if self.price_dict.get(t_sd, 0) == 0 or self.price_dict.get(t_ed, 0) == 0:
                raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
            # calculate the head and tail prices and add them up
            tmp = self.price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) + self.price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))

            step = timedelta(hours=1)
            while t_su < t_ed:
                if self.price_dict.get(t_su, 0) == 0:
                    raise ValueError("For item %d: No matching item in the price dict for %s" % (item, t_su))
                job_en_cost += self.price_dict.get(t_su, 0)
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

    def get_conversion_cost(self, detail=False):
        if detail:
            conversion_cost = []
        else:
            conversion_cost = 0

        if len(self.order) <= 1:
            print('No conversion cost')
            return conversion_cost

        for item1, item2 in zip(self.order[:-1], self.order[1:]):
            # find product made:
            first_product = self.order[item1]['product']
            second_product = self.order[item2]['product']

            try:
                first_product_type = self.order[item1]['type']
                second_product_type = self.order[item2]['type']
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

    def get_constraint_cost(self, detail=False):
        if detail:
            constraint_cost = []
        else:
            constraint_cost = 0
        t_now = self.start_time

        for item in self.order:
            t_start = t_now

            #duration = job_info_dict[item]['duration']

            if self.duration_str == 'duration':
                du = self.job_dict[item]['duration']
            if self.duration_str == 'quantity':
                quantity = self.job_dict[item]['quantity']
                product_type = self.job_dict[item]['product'] # get job product type
                unit2 = self.prc_dict.get(product_type, -1)
                du = quantity / unit2['targetproduction'] # get job duration

            if self.working_method == 'historical':
                t_end = t_start + timedelta(hours=du) # Without downtime duration
                for key, value in self.downdur_dict.items():
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
            if self.working_method == 'expected':
                if 'availability' in unit2:
                    t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
                else:
                    raise NameError('Availability column not found, error')

            deadline_cost = 0
            if 'before' in self.job_dict[item]: # assume not all jobs have deadlines
                # check deadline condition
                beforedate = self.job_dict[item]['before']
                if t_end > beforedate: # did not get deadline
                    deadline_cost = (t_end-beforedate).total_seconds() / 3600

            if 'after' in self.job_dict[item]: # assume not all jobs have deadlines
                # check after condition
                afterdate = self.job_dict[item]['after']
                if t_end < afterdate: # produced before deadline
                    deadline_cost = (afterdate - t_end).total_seconds() / 3600

            if detail:
                constraint_cost.append(deadline_cost)
            elif deadline_cost > 0:
                constraint_cost += deadline_cost

            t_now = t_end
        return constraint_cost