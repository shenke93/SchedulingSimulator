from datetime import timedelta, datetime
import warnings
import numpy as np

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
        self.failure_prob = []

    def get_failure_prob(self):
        t_now = self.start_time
        t_last_maint = t_now
        total_duration_nofail = 0
        cur_rel = 1
        cumulative_failure_prob = []

        for item in self.order:
            t_start = t_now
            
            unit1 = self.job_dict.get(item, -1)
            
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

            if self.working_method == 'expected':
                product_type = unit1['product'] # get job product type
                product_cat = unit1['type']
                #print(self.prc_dict)
                unit2 = self.prc_dict.get(product_type)
                if self.failure_info is not None:
                    failure_info = self.failure_info
                    # suppose we started just after maintenance
                    t_repair = failure_info[2]
                    
                    # if there would be no failure (suppose)
                    #total_duration_nofail += du
                    t_end = t_start + timedelta(hours = float(du))
                    val2 = (total_duration_nofail + du)
                    val1 = total_duration_nofail
                    if val2 >= failure_info[3]:
                        t_end_maint = t_start + timedelta(hours=failure_info[4])
                        t_start = t_end_maint
                        t_end = t_end + timedelta(hours=failure_info[4])
                        ran = np.arange(0, failure_info[4], 1/3)
                        fp = [0 for i in ran]
                        cumulative_failure_prob.extend(fp)
                        t_last_maint = t_start
                        total_duration_nofail = 0
                        val2 = (t_end - t_last_maint).total_seconds() / 3600
                        val1 = (t_start - t_last_maint).total_seconds() / 3600
                        cur_rel = 1
                    if product_cat != 'NONE':
                        #import pdb; pdb.set_trace()
                        fail_dist = failure_info[0][product_cat]
                        duration = val2 - val1
                        v_start_time = fail_dist.get_t_from_reliability(cur_rel)
                        t_down = t_repair * (fail_dist.failure_cdf(v_start_time+duration) - fail_dist.failure_cdf(v_start_time))
                        ran = np.arange(v_start_time, v_start_time + duration, 1/3)
                        fp = [fail_dist.failure_cdf(i) for i in ran]
                        #print(fp)
                        cumulative_failure_prob.extend(fp)
                        cur_rel = fail_dist.reliability_cdf(v_start_time + duration)
                        #print(t_repair, (fail_dist[product_cat].failure_cdf(val2) - fail_dist[product_cat].failure_cdf(val1)))
                    else:
                        t_down = 0
                    t_end = t_start + timedelta(hours = float(du)) + timedelta(hours = t_down)
                    total_duration_nofail += du
                    #t_downtime += t_down
            
    
    def get_time(self):
        # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
        detailed_dict = {}
        t_now = self.start_time
        t_last_maint = t_now
        total_duration_nofail = 0
        #cumulative_failure_prob = []
        cur_rel= 1

        for i in range(len(self.order)):
            item = self.order[i]
            t_start = t_now
            #t_downtime = 0
            
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
                t_down = 0
                t_changeover = 0
            
                for value in self.downdur_dict.values():
                    # DowntimeDuration already added
                    t_down = 0
                    if t_end < value[0]:
                        continue
                    if t_start > value[1]:
                        continue
                    if t_start < value[0] < t_end:
                        t_d= value[1] - value[0]
                        t_end = t_end + t_d
                        t_down += t_d
        #                 print("Line 429, t_end:", t_end)
                    if t_start > value[0] and t_end > value[1]:
                        t_d = value[1] - t_start
                        t_end = t_end + t_d
                        t_down += t_d
                    if t_start > value[0] and t_end < value[1]:
                        t_d = t_end - t_start
                        t_end = t_end + t_d
                        t_down += t_d
                    #t_downtime += t_down

            
            elif self.working_method == 'expected':
                product_type = unit1['product'] # get job product type
                product_cat = unit1['type']
                #print(self.prc_dict)
                unit2 = self.prc_dict.get(product_type)
                t_down = 0
                t_changeover = 0
                if self.failure_info is not None:
                    failure_info = self.failure_info
                    # suppose we started just after maintenance
                    t_repair = failure_info[2]
                    
                    # if there would be no failure (suppose)
                    #total_duration_nofail += du
                    t_end = t_start + timedelta(hours = float(du))
                    val2 = (total_duration_nofail + du)
                    val1 = total_duration_nofail
                    if val2 >= failure_info[3]:    # a maintenance should be planned after a fixed time
                        t_end_maint = t_start + timedelta(hours=failure_info[4])
                        detailed_dict.update({0 : dict(zip(['start', 'end', 'duration', 'product', 'type', 'down_duration', 'changeover_duration'],
                                                      [t_start, t_end_maint, failure_info[4], 'MAINTENANCE', 'NONE', failure_info[4], 0]))
                                            })
                        t_start = t_end_maint
                        t_end = t_end + timedelta(hours=failure_info[4])
                        #ran = np.arange(0, failure_info[4], 1/3)
                        #fp = [0 for i in ran]
                        #cumulative_failure_prob.extend(fp)
                        t_last_maint = t_start
                        total_duration_nofail = 0
                        val2 = (t_end - t_last_maint).total_seconds() / 3600
                        val1 = (t_start - t_last_maint).total_seconds() / 3600
                        cur_rel = 1
                    if product_cat != 'NONE':    # all products except breaks should be extended
                        #import pdb; pdb.set_trace()
                        fail_dist = failure_info[0][product_cat]
                        duration = val2 - val1
                        v_start_time = fail_dist.get_t_from_reliability(cur_rel)
                        t_down += t_repair * (fail_dist.failure_cdf(v_start_time+duration) - fail_dist.failure_cdf(v_start_time))
                        #ran = np.arange(v_start_time, v_start_time+duration, 1/3)
                        #fp = [fail_dist.failure_cdf(i) for i in ran]
                        #print(fp)
                        #cumulative_failure_prob.extend(fp)
                        cur_rel = fail_dist.reliability_cdf(v_start_time+duration)
                        #print(t_repair, (fail_dist[product_cat].failure_cdf(val2) - fail_dist[product_cat].failure_cdf(val1)))

                        # extend with changeover time
                        if i < len(self.order) - 1:
                            next_item = self.order[i+1]
                            next_unit = self.job_dict.get(next_item, -1)
                            next_product_cat = next_unit['type']
                            changeover_time = float(failure_info[5].loc[product_cat, next_product_cat])
                            t_changeover += (changeover_time / 3600)           

                        # extend with cleaning time
                        cleaning_times = float(failure_info[6].loc[product_cat])
                        t_down += (cleaning_times / 3600)
                        #import pdb; pdb.set_trace()
                    
                    t_end = t_start + timedelta(hours = float(du)) + timedelta(hours = t_down + t_changeover)
                    total_duration_nofail += du
                    #t_downtime += t_down

                if 'availability' in unit2:
                    t_down += float(du) * (1/float(unit2['availability'])- 1)
                    t_end = t_start + timedelta(hours = float(du)) + timedelta(hours = t_down + t_changeover)
                else:
                    raise NameError('Availability column not found, error')
            try:
                detailed_dict.update({item : dict(zip(['start', 'end', 'duration', 'product', 'type', 'down_duration', 'changeover_duration'],
                                                      [t_start, t_end, du+t_down, unit1['product'], unit1['type'], t_down, t_changeover]))
                                      })
            except:
                import pdb; pdb.set_trace()
                raise
            t_now = t_end

        #self.failure_prob = cumulative_failure_prob
        #import pdb; pdb.set_trace()

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
        detailed_dict = self.time_dict

        if self.working_method == 'historical':
            downdur_dict = self.downdur_dict
            for item in time_dict:
                # get one product
                startdate = time_dict[item]['start']
                enddate = time_dict[item]['end']
                product_type = time_dict[item]['product']
                if self.scenario == 1: # using unit cost and production rate
                    # get product info
                    prc = self.prc_dict.get(product_type, -1)
                    prc_up = prc['unitprice']
                    prc_tpr = prc['targetproduction']
                    # get total downtime duration
                    downdur_select = {key: value for key, value in downdur_dict.items() 
                                                                        if (startdate < value[0] < enddate)
                                                                        and (startdate < value[1] < enddate) 
                                    }
                    if len(downdur_select) > 0:
                        # len downdur_select means the number of failures during a certain production
                        loss = len(downdur_select) * prc_up * prc_tpr / 6 # suppose for each failure 10 minutes of production gets lost
                        sum_len = 0
                        for item in downdur_select: # add up all failure times
                            sum_len += downdur_select[item][2]
                        extra_loss = loss + sum_len * prc_up * prc_tpr # add the failure time X the production loss cost
                    else:
                        extra_loss = 0
                if self.scenario == 2: # using fixed cost C1 and variable cost C2
                    # same method, but with fixed prices
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
            for item in detailed_dict:
                product_type = detailed_dict[item]['product']
                prc = self.prc_dict.get(product_type, -1)
                prc_av = prc['availability']
                down_duration = detailed_dict[item]['down_duration']
                if self.scenario == 1:
                    prc_up = prc['unitprice']
                    prc_tpr = prc['targetproduction']
                    extra_loss = down_duration * prc_up * prc_tpr
                    if self.failure_info is not None:
                        if 'dt_len' in prc:
                            mean_length_downtime = prc['dt_len']
                        else:
                            failure_info = self.failure_info
                            mean_length_downtime = failure_info[2]
                        # get the total calculated downtime and divide by the mean downtime length = estimated number of downtimes
                        extra_loss += down_duration / mean_length_downtime * prc_up * prc_tpr
                if self.scenario == 2:
                    # same, but with C1 and C2 as constants
                    extra_loss = down_duration * C2
                    try:
                        if 'dt_len' in prc:
                            mean_length_downtime = prc['dt_len']
                        else:
                            failure_info = self.failure_info
                            mean_length_downtime = failure_info[2]
                        extra_loss += down_duration / mean_length_downtime * C1
                    except:
                        import pdb; pdb.set_trace()
                        raise
                
                if detail:
                    if product_type == 'MAINTENANCE':
                        failure_cost[-1] += extra_loss # add maintenance cost to the task before the maintenance
                    else:
                        failure_cost.append(extra_loss)
                else:
                    failure_cost += extra_loss
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
            #if product_type == 'MAINTENANCE': product_type = 'NONE'
            unit2 = prc_dict.get(product_type, -1)
            try:
                power = unit2['power']
            except:
                print(product_type)
                raise

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
                if product_type == 'MAINTENANCE':
                    energy_cost[-1] += job_en_cost
                else:
                    energy_cost.append(job_en_cost)
            else:
                energy_cost += job_en_cost
        return energy_cost

    def get_conversion_cost(self, detail=False):
        if detail:
            conversion_cost = []
        else:
            conversion_cost = 0

        if len(self.order) <= 1:
            print('No conversion cost')
            return conversion_cost

        for item1, item2 in zip(list(self.time_dict.keys())[:-1], list(self.time_dict.keys())[1:]):
            if item2 == 0:
                pass
            elif item1 == 0:
                if detail:
                    conversion_cost.append(0)
            elif self.failure_info is not None:
                first_product_type = self.job_dict[item1]['type']
                second_product_type = self.job_dict[item2]['type']
                fi = self.failure_info[5]
                conversion_time = int(fi.loc[first_product_type, second_product_type]) / 3600 # get the conversion time and convert to hours
                #import pdb; pdb.set_trace()
                first_product = self.job_dict[item1]['product']
                prc_up = self.prc_dict[first_product]['unitprice']
                prc_tp = self.prc_dict[first_product]['targetproduction']
                total_availability = conversion_time * prc_up * prc_tp
                if detail:
                    conversion_cost.append(total_availability)
                else:
                    conversion_cost += total_availability
            else:
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
                # self.failure_info[6]
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
        #import pdb; pdb.set_trace()
        if detail:
            constraint_cost = []
        else:
            constraint_cost = 0
        t_now = self.start_time

        for item in self.time_dict:
            deadline_cost = 0
            if item in self.job_dict:
                if 'before' in self.job_dict[item]: # assume not all jobs have deadlines
                    # check deadline condition
                    beforedate = self.job_dict[item]['before']
                    if self.time_dict[item]['end'] > beforedate: # did not get deadline
                        deadline_cost += (self.time_dict[item]['end'] - beforedate).total_seconds() / 3600

                if 'after' in self.job_dict[item]: # assume not all jobs have deadlines
                    # check after condition
                    afterdate = self.job_dict[item]['after']
                    if self.time_dict[item]['end'] < afterdate: # produced before deadline
                        deadline_cost += (afterdate - self.time_dict[item]['end']).total_seconds() / 3600
                #if beforedate < afterdate:
                    #import pdb; pdb.set_trace()
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