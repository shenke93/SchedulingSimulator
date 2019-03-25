from datetime import timedelta, datetime
import warnings

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


class Schedule:
    def __init__(self, order, start_time, job_dict, failure_dict, prc_dict, downdur_dict, price_dict, failure_info, 
                 scenario, duration_str='duration', working_method='historical'):
        self.order = order
        self.start_time = start_time
        self.job_dict = job_dict
        self.failure_dict = failure_dict
        self.prc_dict = prc_dict
        self.downdur_dict = downdur_dict
        self.price_dict = price_dict
        self.failure_info = failure_info
        self.scenario = scenario
        self.duration_str = duration_str
        self.working_method = working_method
        self.time_dict = self.get_time()
    
    def get_time(self):
        # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
        detailed_dict = {}
        t_now = self.start_time 

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
                    t_down = 0
                    if t_end < value[0]:
                        continue
                    if t_start > value[1]:
                        continue
                    if t_start < value[0] < t_end:
                        t_down = value[1] - value[0]
                        t_end = t_end + t_down
        #                 print("Line 429, t_end:", t_end)
                    if t_start > value[0] and t_end > value[1]:
                        t_down = value[1] - t_start
                        t_end = t_end + t_down
                    if t_start > value[0] and t_end < value[1]:
                        t_down = t_end - t_start
                        t_end = t_end + t_down

            
            elif self.working_method == 'expected':
                product_type = unit1['product'] # get job product type
                unit2 = self.prc_dict.get(product_type)
                if 'availability' in unit2:
                    t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
                else:
                    raise NameError('Availability column not found, error')
            try:
                detailed_dict.update({item : dict(zip(['start', 'end', 'duration', 'product', 'type'],
                                                      [t_start, t_end, du, unit1['product'], unit1['type']])
                                                 )
                                      })
            except:
                import pdb; pdb.set_trace()
                raise
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

        # two tables: one with the job times and one with the failure times

        time_dict = self.time_dict

        if self.working_method == 'historical':
            downdur_dict = self.downdur_dict
            for item in time_dict:
                startdate = time_dict[item]['start']
                enddate = time_dict[item]['end']
                product_type = time_dict[item]['product']
                if self.scenario == 1:
                    prc = self.prc_dict.get(product_type, -1)
                    prc_up = prc['unitprice']
                    prc_tpr = prc['targetproduction']
                    downdur_select = {key: value for key, value in downdur_dict.items() 
                                                                        if (startdate < value[0] < enddate)
                                                                        and (startdate < value[1] < enddate) 
                                    }
                    if len(downdur_select) > 0:
                        loss = len(downdur_select) * prc_up * prc_tpr / 6
                        sum_len = 0
                        for item in downdur_select:
                            sum_len += downdur_select[item][2]
                        extra_loss = loss + sum_len * prc_up * prc_tpr
                    else:
                        extra_loss = 0
                if self.scenario == 2:
                    downdur_select = {key: value for key, value in downdur_dict.items() 
                                                                        if (startdate < value[0] < enddate)
                                                                        and (startdate < value[1] < enddate) 
                                    }
                    if len(downdur_select) > 0:
                        loss = len(downdur_select) * C1
                        sum_len = 0
                        for item in downdur_select:
                            sum_len += downdur_select[item][2]
                        extra_loss = loss + sum_len * C2
                    else:
                        extra_loss = 0
                if detail:
                    failure_cost.append(extra_loss)
                else:
                    failure_cost += extra_loss
                  
        
        if self.working_method == 'expected':
            for item in time_dict:
                #print(time_dict[item])
                product_type = time_dict[item]['product']
                prc = self.prc_dict.get(product_type, -1)
                prc_av = prc['availability']
                duration = time_dict[item]['duration']
                if self.scenario == 1: # using unit cost and production rate
                    prc_up = prc['unitprice']
                    prc_tpr = prc['targetproduction']
                    extra_loss = duration * (1/prc_av - 1) * prc_up * prc_tpr
                    try:
                        mean_length_downtime = prc['dt_len']
                        extra_loss += duration * (1/prc_av - 1) / mean_length_downtime * prc_up * prc_tpr / 6
                    except:
                        pass
                if self.scenario == 2: # using fixed cost C1 and variable cost C2
                    extra_loss = duration * (1/prc_av - 1) * C2
                    try:
                        mean_length_downtime = prc['dt_len']
                        extra_loss += duration * (1/prc_av - 1) / mean_length_downtime * C1
                    except:
                        pass
                if detail:
                    failure_cost.append(extra_loss)
                else:
                    failure_cost += extra_loss

        return failure_cost

        # if self.scenario == 1: # based on quantity and unit cost
        #     for item in self.order:
        #         t_start = t_now
        #         unit1 = self.job_dict.get(item, -1)
        #         if unit1 == -1:
        #             raise ValueError("No matching item in job dict: ", item)
            
        #         product_type = unit1['product']    # get job product type
        #         quantity = unit1['quantity']  # get job quantity
                
        # #         if du <= 1: # safe period of 1 hour (no failure cost)
        # #             continue;
        #         unit2 = self.prc_dict.get(product_type, -1)
        #         if unit2 == -1:
        #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
                
        #         if self.duration_str == 'duration':
        #             du = unit1['duration']
        #         elif self.duration_str == 'quantity':
        #             try:
        #                 du = quantity / unit2['targetproduction'] # get job duration
        #             except:
        #                 print('Error calculating duration:', du)
        #                 raise

        #         uc = unit2['unitprice'] # get job raw material unit price

        #         if self.working_method == 'historical':
        #             t_o = t_start + timedelta(hours=du) # Without downtime duration
        #             t_end = t_o
        #             #print(down_duration_dict)
                    
        #             for key, value in self.downdur_dict.items():
        #                 # DowntimeDuration already added
        #                 if t_end < value[0]:
        #                     continue
        #                 if t_start > value[1]:
        #                     continue
        #                 if t_start < value[0] < t_end:
        #                     t_end = t_end + (value[1]-value[0])
        #     #                 print("Line 429, t_end:", t_end)
        #                 if t_start > value[0] and t_end > value[1]:
        #                     t_end = t_end + (value[1] - t_start)
        #                 if t_start > value[0] and t_end < value[1]:
        #                     t_end = t_end + (t_end - t_start)
        #                 else:
        #                     break
                
        #         elif self.working_method == 'expected':
        #             if 'availability' in unit2:
        #                 t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
        #             else:
        #                 raise NameError('Availability column not found, error')
                
        # #         t_start = t_start+timedelta(hours=1) # exclude safe period, find start of sensitive period
        # #         t_end = t_start + timedelta(hours=(du-1)) # end of sensitive period

        #         t_su = ceil_dt(t_start, timedelta(hours=1)) #    t_start right border
        #         t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
        #         t_sd = floor_dt(t_start, timedelta(hours=1))  #    t_start left border
                
            
        # #         if health_dict.get(t_sd, -1) == -1 or health_dict.get(t_ed, -1) == -1:
        # #             raise ValueError("For item %d: In boundary conditions, no matching item in the health dict for %s or %s" % (item, t_sd, t_ed))
                
        #         step = timedelta(hours=1)
        #         tmp = self.failure_dict.get(t_sd, 0)*((t_su - t_start)/step) + self.failure_dict.get(t_ed, 0)*((t_end - t_ed)/step)

        #         while t_su < t_ed:
        #             if self.failure_dict.get(t_su, -1) == -1:
        #                 raise ValueError("For item %d: No matching item in the health dict for %s" % (item, t_su))
        #             tmp += self.failure_dict.get(t_su, 0)
        #             t_su += step
        # #         
        # #         if product_related_characteristics_dict.get(product_type, -1) == -1:
        # #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))
        #         if detail:
        #             failure_cost.append(tmp * quantity * uc)
        #         else:
        #             failure_cost += tmp * quantity * uc
        #         t_now = t_end
        
        # if self.scenario == 2: # based on two costs (fixed and variable cost C1 and)
        #     for item in self.order:
        #         fc_temp = 0
        #         t_start = t_now
        #         unit1 = self.job_dict.get(item, -1)
        #         if unit1 == -1:
        #             raise ValueError("No matching item in job dict: ", item)
            
        #         product_type = unit1['product']  # get job product type
                
                
        # #         if du <= 1: # safe period of 1 hour (no failure cost)
        # #             continue;
        #         unit2 = self.prc_dict.get(product_type, -1)
        #         if unit2 == -1:
        #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

        #         if self.duration_str == 'duration':
        #             du = unit1['duration']
        #         if self.duration_str == 'quantity':
        #             quantity = unit1['quantity']  # get job quantity
        #             du = quantity / unit2['targetproduction'] # get job duration
                
        # #        du = quantity / unit2[2] # get job duration
        # #         print("Duration:", du)
        # #         uc = unit2[0] # get job raw material unit price
                
        #         if self.working_method == 'historical':
        #             t_o = t_start + timedelta(hours=du) # Without downtime duration
        #             #print("t_o:", t_o)
        #             t_end = t_o
        #             for key, value in self.downdur_dict.items():
        #                 # DowntimeDuration already added
        #                 if t_end < value[0]:
        #                     continue
        #                 if t_start > value[1]:
        #                     continue
        #                 if t_start < value[0] < t_end:
        #                     t_end = t_end + (value[1]-value[0])
        #                     fc_temp += C1 + (value[1] - value[0]) / timedelta(hours=1) * C2
        #                     # print("Line 429, t_end:", t_end)
        #                 if t_start > value[0] and t_end > value[1]:
        #                     t_end = t_end + (value[1] - t_start)
        #                     fc_temp += C1 + (value[1] - t_start) / timedelta(hours=1) * C2
        #                 if t_start > value[0] and t_end < value[1]:
        #                     t_end = t_end + (t_end - t_start)
        #                     fc_temp += C1 + (t_end- t_start) / timedelta(hours=1) * C2
        #                 else:
        #                     break
                
        #         elif self.working_method == 'expected':
        #             if 'availability' in unit2:
        #                 t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
        #                 fc_temp += C2 * ((timedelta(hours = float(du)) * (1 / float(unit2['availability']) - 1)) / timedelta(hours=1))
        #             else:
        #                 raise NameError('Availability column not found, error')
                
        #         t_now = t_end
        #         if detail:
        #             failure_cost.append(fc_temp)
        #         else:
        #             failure_cost += fc_temp  
        # return failure_cost

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
        #import pdb; pdb.set_trace()
        if detail:
            energy_cost = []
        else:
            energy_cost = 0

        time_dict = self.time_dict
        price_dict = self.price_dict
        prc_dict = self.prc_dict


        for item in time_dict:
            job_en_cost = 0

            product_type = time_dict[item]['product'] # get job product type
            unit2 = prc_dict.get(product_type, -1)
            power = unit2['power']

            t_start = time_dict[item]['start']
            t_end = time_dict[item]['end']

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
            job_en_cost *= power
            
            t_now = t_end
            if detail:
                energy_cost.append(job_en_cost)
            else:
                energy_cost += job_en_cost
        return energy_cost
        
    #     t_now = self.start_time # current timestamp
    #     i = 0
    #     for item in self.order:
    # #         print("For job:", item)
    #         t_start = t_now
    # #         print("Time start: " + str(t_now))
    #         unit1 = self.job_dict.get(item, -1)
    #         if unit1 == -1:
    #             raise ValueError("No matching item in the job dict for %d" % item)
        
    #         product_type = unit1['product'] # get job product type
            
    #         unit2 = self.prc_dict.get(product_type, -1)
    #         if unit2 == -1:
    #             raise ValueError("For item %d: No matching item in the product related characteristics dict for %s" % (item, product_type))

    #         if self.duration_str == 'duration':
    #             du = unit1['duration']
    #         if self.duration_str == 'quantity':
    #             quantity = unit1['quantity']
    #             du = quantity / unit2['targetproduction'] # get job duration
    # #         print("Duration:", du)
    #         po = unit2['power'] # get job power profile
    #         job_en_cost = 0
            
    #         if self.working_method == 'historical':
    #             #print(du)
    #             t_o = t_start + timedelta(hours=du) # Without downtime duration
    #     #         print("t_o:", t_o)
    #             t_end = t_o
                
    #             for key, value in self.downdur_dict.items():
    #                 # Add the total downtimeduration
    #                 if t_end < value[0]:
    #                     continue
    #                 if t_start > value[1]:
    #                     continue
    #                 if t_start < value[0] < t_end:
    #                     t_end = t_end + (value[1]-value[0])
    #     #                 print("Line 429, t_end:", t_end)
    #                 if t_start > value[0] and t_end > value[1]:
    #                     t_end = t_end + (value[1] - t_start)
    #                 if t_start > value[0] and t_end < value[1]:
    #                     t_end = t_end + (t_end - t_start)
    #         elif self.working_method == 'expected':
    #             if 'availability' in unit2:
    #                 t_end = t_start + timedelta(hours = float(du) / float(unit2['availability'])) #TODO import availability
    #             else:
    #                 raise NameError('Availability column not found, error')
            
    #         # calculate sum of head price, tail price and body price

    #         t_su = ceil_dt(t_start, timedelta(hours=1)) # t_start right border
    #         t_ed = floor_dt(t_end, timedelta(hours=1)) #  t_end left border
    #         t_sd = floor_dt(t_start, timedelta(hours=1)) # t_start_left border

    #         if self.price_dict.get(t_sd, 0) == 0 or self.price_dict.get(t_ed, 0) == 0:
    #             raise ValueError("For item %d: In boundary conditions, no matching item in the price dict for %s or %s" % (item, t_sd, t_ed))
    #         # calculate the head and tail prices and add them up
    #         tmp = self.price_dict.get(t_sd, 0)*((t_su - t_start)/timedelta(hours=1)) + self.price_dict.get(t_ed, 0)*((t_end - t_ed)/timedelta(hours=1))

    #         step = timedelta(hours=1)
    #         while t_su < t_ed:
    #             if self.price_dict.get(t_su, 0) == 0:
    #                 raise ValueError("For item %d: No matching item in the price dict for %s" % (item, t_su))
    #             job_en_cost += self.price_dict.get(t_su, 0)
    #             t_su += step
            
    #         job_en_cost += tmp
    #         job_en_cost *= po
            
    #         t_now = t_end
    #         if detail:
    #             energy_cost.append(job_en_cost)
    #         else:
    #             energy_cost += job_en_cost
    #         i += 1  
    #     return energy_cost

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
            first_product = self.job_dict[item1]['product']
            second_product = self.job_dict[item2]['product']

            try:
                first_product_type = self.job_dict[item1]['type']
                second_product_type = self.job_dict[item2]['type']
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

        for item in self.time_dict:
            deadline_cost = 0
            if 'before' in self.job_dict[item]: # assume not all jobs have deadlines
                # check deadline condition
                beforedate = self.job_dict[item]['before']
                if self.time_dict[item]['end'] > beforedate: # did not get deadline
                    deadline_cost = (self.time_dict[item]['end'] - beforedate).total_seconds() / 3600

            if 'after' in self.job_dict[item]: # assume not all jobs have deadlines
                # check after condition
                afterdate = self.job_dict[item]['after']
                if self.time_dict[item]['end'] < afterdate: # produced before deadline
                    deadline_cost = (afterdate - self.time_dict[item]['end']).total_seconds() / 3600

            if detail:
                constraint_cost.append(deadline_cost)
            elif deadline_cost > 0:
                constraint_cost += deadline_cost
        return constraint_cost

    def validate(self):
        # validate time
        time_dict = self.get_time()
    #     print(time_dict)
        flag = True
        for key, value in time_dict.items():
            due = self.job_dict[key]['before'] # due date of a job
            if value[1] > due:
                print("For candidate schedule:", self.order)
                print("Job %d will finish at %s over the due date %s" % (key, value[1], due))
                flag = False
                break
        return flag
    #     # # validate precedence (DISABLED)
    #     # ind = set(self.order)
    #     # jobs = ind.copy()
    # #     for item in ind:
    # #         if item in precedence_dict:
    # #             prec = set(precedence_dict[item])
    # #             jobs.remove(item)
    # # #             print("Item:", item)
    # # #             print("Prec:", prec)
    # # #             print("afters:", jobs)
    # #             if not prec.isdisjoint(jobs): # prec set and remain jobs have intersections
    # #                 flag = False
    # #                 break                
    # #         else:
    # #             jobs.remove(item)
                
    #     return flag