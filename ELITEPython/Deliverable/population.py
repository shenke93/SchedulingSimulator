from datetime import timedelta, datetime
import warnings
import numpy as np
import pandas as pd
import logging

C1 = 10 # Used for failure cost calculation in run-down scenario
C2 = 30
num_seconds_lost = 600 # the number of seconds of production that go lost if failure

standard_weights = {'weight_energy': 1,
                    'weight_virtual_failure': 0,
                    'weight_failure': 1,
                    'weight_constraint': 0}

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
    def __init__(self, order, job_dict, start_time, downdur_dict, price_dict, precedence_dict, failure_info, 
                 scenario, duration_str='duration', working_method='historical', weights=standard_weights):
        self.order = order
        self.job_dict = job_dict
        self.start_time = start_time
        self.downdur_dict = downdur_dict
        self.price_dict = price_dict
        self.precedence_dict = precedence_dict
        self.failure_info = failure_info
        self.scenario = scenario
        self.duration_str = duration_str
        self.working_method = working_method
        self.weights = weights
        self.time_dict = self.get_time()
        
        temp_df = pd.DataFrame.from_dict(self.job_dict).T
        #temp_mean = temp_df.mean(axis=0)
        self.mean_up = temp_df['unitprice'].mean()
        self.mean_tpr = temp_df['targetproductionrate'].mean()
        
    def set_starttime(self, time):
        self.start_time = time
        
    def copy_random(self):
        return_sched = Schedule(np.random.choice(self.order, size=len(self.order), replace=False),
                                self.job_dict, self.start_time, self.downdur_dict, self.price_dict, 
                                self.precedence_dict, self.failure_info, self.scenario, 
                                self.duration_str, self.working_method, 
                                self.weights)
        return return_sched
    
    def copy_neworder(self, assign_order):
        assert (set(assign_order) == set(self.job_dict.keys())), 'The keys inserted are not the same as the key of the jobs'
        return_sched = Schedule(assign_order,
                                self.job_dict, self.start_time, self.downdur_dict, self.price_dict, 
                                self.precedence_dict, self.failure_info, self.scenario, 
                                self.duration_str, self.working_method, 
                                self.weights)
        return return_sched
        
    
    def get_failure_prob(self, cumulative=True):
        '''Assistant function to visualize the processing of a candidate schedule throughout the time horizon
        Parameters
        ----------
        cumulative : boolean
            Sets the output to a cdf if True, else uses a pdf.
        Returns
        -------
        
        '''
        detailed_dict = {}
        t_now = t_start_begin = self.start_time
        t_last_maint = t_now
        cumulative_failure_prob = pd.Series([])
        cur_rel = 1
        if self.working_method == 'expected':
            total_duration_nofail = 0

        for i in range(len(self.order)):
            item = self.order[i]
            t_start = t_now
            #t_downtime = 0
            
            unit1 = self.job_dict[item]
       
            
            # calculate duration based on quantity or based on expected uptime duration
            if self.duration_str == 'duration':
                du = unit1['uptime']
            elif self.duration_str == 'quantity':
                quantity = unit1['quantity']
                #product_type = unit1['product'] # get job product type
                #unit2 = self.prc_dict.get(item)
                try:
                    du = quantity / unit1['targetproductionrate'] # get job duration
                except:
                    print(quantity, unit1['targetproductionrate'])
                    raise
            else:
                raise NameError('Faulty value inserted')

            if self.working_method == 'historical':
                raise ValueError("not possible to get failure probability in '{}' mode".format(self.working_method))
            elif self.working_method == 'expected':
                product_type = unit1['product'] # get job product type
                product_cat = unit1['type']
                # the total duration without failure (ideal case)
                t_down = 0
                t_changeover = 0
                t_clean = 0
                if self.failure_info is not None:
                    failure_info = self.failure_info
                    # suppose we started just after maintenance
                    t_repair = failure_info['rep_mean']
                    # if there would be no failure (suppose)
                    #total_duration_nofail += du
                    t_end = t_start + timedelta(hours = float(du))
                    if product_cat != "NONE":
                        val2 = (total_duration_nofail + du)
                        val1 = total_duration_nofail
                    else:
                        val2 = total_duration_nofail
                        val1 = total_duration_nofail
                    # a maintenance should be planned after a fixed time
                    if val2 >= failure_info['maint_time']:
                        # first do maintenance
                        t_end_maint = t_start + timedelta(hours=failure_info['repair_time'])

                        time_ran = np.arange((t_start - t_start_begin).total_seconds(), 
                                             (t_end_maint- t_start_begin).total_seconds(), 60)
                        extend_df = pd.Series(index=time_ran, data='NaN')
                        cumulative_failure_prob = cumulative_failure_prob.append(extend_df)
                        
                        t_start = t_end_maint
                        t_end = t_end + timedelta(hours=failure_info['repair_time'])

                        t_last_maint = t_start
                        
                        val2 = (t_end - t_last_maint).total_seconds() / 3600
                        val1 = (t_start - t_last_maint).total_seconds() / 3600

                        total_duration_nofail = 0
                        cur_rel = 1
                    if product_cat != 'NONE':    # all products except breaks should be extended
                        fail_dist = failure_info['fail_dict'][product_cat]
                        duration = du
                        v_start_time = fail_dist.get_t_from_reliability(cur_rel)
                        t_down += t_repair * (fail_dist.failure_cdf(v_start_time+du) - fail_dist.failure_cdf(v_start_time))

                        # if 'availability' in unit1:
                        #     t_down += float(du) * (1/float(unit1['availability'])- 1)
                            
                        t_down += float(du) * (1/float(failure_info['availability_dict'][product_cat])-1)

                        #if get_failure_schedule
                        #extend_df = pd.DataFrame(data = ran + v_start_time)
                        
                        time_ran = np.arange((t_start - t_start_begin).total_seconds(), ((t_start + timedelta(hours=du + t_down)) - t_start_begin).total_seconds(), 60)
                        ran = np.linspace(v_start_time, v_start_time + du, num=len(time_ran))
                        if cumulative:
                            fp = [fail_dist.failure_cdf(i) for i in ran]
                        else:
                            fp = [fail_dist.failure_pdf(i) for i in ran]
                        extend_df = pd.Series(index=time_ran, data=fp)
                        cumulative_failure_prob = cumulative_failure_prob.append(extend_df)

                        cur_rel = fail_dist.reliability_cdf(v_start_time+du)
                        #print(t_repair, (fail_dist[product_cat].failure_cdf(val2) - fail_dist[product_cat].failure_cdf(val1)))

                        # extend with changeover time
                        if i < len(self.order) - 1:
                            next_item = self.order[i+1]
                            next_unit = self.job_dict.get(next_item, -1)
                            next_product_cat = next_unit['type']
                            changeover_time = float(failure_info['conversion_times'].loc[product_cat, next_product_cat])
                            t_changeover += (changeover_time / 3600)           

                        if failure_info['cleaning_time'] != None:
                            # extend with cleaning time
                            cleaning_times = float(failure_info['cleaning_time'].loc[product_cat])
                            t_clean += (cleaning_times / 3600)

                        # get the changeover time and extend the current graph
                        time_ran = np.arange(((t_start + timedelta(hours=du + t_down)) - t_start_begin).total_seconds(), 
                                            ((t_start + timedelta(hours=du + t_down + t_changeover + t_clean)) - t_start_begin).total_seconds(), 60)
                        extend_df = pd.Series(index=time_ran, data='NaN')
                        cumulative_failure_prob = cumulative_failure_prob.append(extend_df)
                    else:
                        time_ran = np.arange((t_start - t_start_begin).total_seconds(), ((t_start + timedelta(hours=du + t_down)) - t_start_begin).total_seconds(), 60)
                        extend_df = pd.Series(index=time_ran, data='NaN')
                        cumulative_failure_prob = cumulative_failure_prob.append(extend_df)
                        #import pdb; pdb.set_trace()
                    
                    t_end = t_start + timedelta(hours = float(du + t_down + t_changeover + t_clean))
                    total_duration_nofail += du
                    #t_downtime += t_down
                else:
                    time_ran = np.arange((t_start - t_start_begin).total_seconds(), ((t_start + timedelta(hours=du + t_down)) - t_start_begin).total_seconds(), 60)
                    extend_df = pd.Series(index=time_ran, data='NaN')
                    cumulative_failure_prob = cumulative_failure_prob.append(extend_df)
                    
                
                #print(t_end)
            t_now = t_end

        cumulative_failure_prob.index = \
        [(t_start_begin + timedelta(hours = ( l / 3600))) for l in cumulative_failure_prob.index.tolist()]

        return cumulative_failure_prob

    def get_time(self):
        # Assistant function to visualize the processing of a candidate schedule throughout the time horizon
        detailed_dict = {}
        t_now = self.start_time
        t_last_maint = t_now
        # if get_failure_schedule:
        #     cumulative_failure_prob = pd.DataFrame([], columns=['cfp'])
        cur_rel= 1
        maintenance_int = 0
        if self.working_method == 'expected':
            total_duration_nofail = 0
            
        #import pdb; pdb.set_trace()

        for i in range(len(self.order)):
            item = self.order[i]
            t_start = t_now
            #t_downtime = 0
            
            unit1 = self.job_dict[item]
            try:
                product_type = unit1['product'] # get job product type
                #unit2 = self.prc_dict.get(item)
            except:
                logging.warning("No product related information found for + '" + str(product_type) + "'.")
            
            # calculate duration based on quantity or based on expected uptime duration
            if self.duration_str == 'duration':
                try:
                    du = unit1['uptime']
                    if 'quantity' in unit1:
                        quantity = unit1['quantity']
                    else:
                        try:
                            #calculate quantity
                            quantity = du * unit1['targetproductionrate']
                        except:
                            logging.warning('No target production rate found')
                except:
                    logging.warning('No correct duration information found, go to debugging')
                    import pdb; pdb.set_trace()
            elif self.duration_str == 'quantity':
                quantity = unit1['quantity']
                product_type = unit1['product'] # get job product type
                #unit2 = self.prc_dict.get(item)
                try:
                    du = quantity / unit1['targetproductionrate'] # get job duration
                except:
                    #du = quantity
                    import pdb; pdb.set_trace()
                    print(quantity, unit1['targetproductionrate'])
                    raise
            else:
                raise NameError('Faulty value inserted: {}'.format(str(self.duration_str)))

            if self.working_method == 'historical':
                t_o = t_start + timedelta(hours=du) # Without downtime duration
                t_end = t_o # End date
                #print(t_end)
                t_down = 0 # Downtime (hours) as int
                t_changeover = 0 # Changeover time (hours) as int
                t_clean = 0

                for value in self.downdur_dict.values():
                    # DowntimeDuration already added
                    #t_down = 0
                    #print(value)
                    if t_end < value[0]:
                        continue
                    elif t_start > value[1]:
                        continue
                    elif t_start < value[0] < t_end:
                        t_d = value[1] - value[0]
                        t_end = t_end + t_d
                        t_down += t_d.total_seconds() / 3600
                    elif t_start > value[0] and t_end > value[1]:
                        t_d = value[1] - t_start
                        t_end = t_end + t_d
                        t_down += t_d.total_seconds() / 3600
                    elif t_start > value[0] and t_end < value[1]:
                        t_d = t_end - t_start
                        t_end = t_end + t_d
                        t_down += t_d.total_seconds() / 3600
                    #t_downtime += t_down

            elif self.working_method == 'expected':
                product_type = unit1['product'] # get job product type
                product_cat = unit1['type']
                #print(self.prc_dict)
                #unit2 = self.prc_dict.get(item)
                t_down = 0
                t_changeover = 0
                t_clean = 0
                #import pdb; pdb.set_trace()
                if self.failure_info is not None:
                    failure_info = self.failure_info
                    # suppose we started just after maintenance
                    t_repair = failure_info['rep_mean']
                    # if there would be no failure (suppose)
                    #total_duration_nofail += du
                    t_end = t_start + timedelta(hours = float(du))
                    if product_type != 'NONE':
                        val2 = (total_duration_nofail + du)
                        val1 = total_duration_nofail
                    else:
                        val2 = total_duration_nofail
                        val1 = total_duration_nofail
                    if (val2 >= failure_info['maint_time']) and (product_type != 'NONE'):    # a maintenance should be planned after a fixed time
                        t_end_maint = t_start + timedelta(hours=failure_info['repair_time'])
                        while maintenance_int in detailed_dict:
                            maintenance_int -= 1
                        detailed_dict.update({maintenance_int : dict(zip(
                            ['start', 'end', 'totaltime', 'uptime', 'product', 'type', 'down_duration', 
                             'changeover_duration', 'cleaning_time', 'quantity', 'unitprice', 'power',
                             'weight', 'targetproductionrate', 'releasedate', 'duedate',],
                            [t_start, t_end_maint, failure_info['repair_time'], 0, 'MAINTENANCE', 'NONE', failure_info['repair_time'], 
                             0, 0, failure_info['repair_time'], 0, 0, 
                             0, 1, pd.Timestamp.min, pd.Timestamp.max]))
                                              })
                        #import pdb; pdb.set_trace()
                        t_start = t_end_maint
                        t_end = t_end + timedelta(hours=failure_info['repair_time'])

                        # if get_failure_schedule:
                        #     ran = np.arange(0, failure_info[4], 1/3)
                        #     fp = [1 for i in ran]
                        #     cumulative_failure_prob.extend(fp)

                        t_last_maint = t_start
                        total_duration_nofail = 0
                        val2 = (t_end - t_last_maint).total_seconds() / 3600
                        val1 = (t_start - t_last_maint).total_seconds() / 3600
                        cur_rel = 1
                    if product_type != 'NONE':    # all products except breaks should be extended
                        try:
                            fail_dist = failure_info['fail_dict'][product_cat]
                        except:
                            import pdb; pdb.set_trace()
                        duration = val2 - val1
                        v_start_time = fail_dist.get_t_from_reliability(cur_rel)
                        t_down += t_repair * (fail_dist.failure_cdf(v_start_time+duration) - fail_dist.failure_cdf(v_start_time))
                        #import pdb; pdb.set_trace()

                        #if 'availability' in unit2:
                        #    t_down += float(du) * (1/float(unit2['availability'])- 1)
                        t_down += float(du) * (1/float(failure_info['availability_dict'][product_cat])-1)
                        #import pdb; pdb.set_trace()

                        # if get_failure_schedule:
                        #     ran = np.arange(v_start_time, v_start_time + duration, 1/3)
                        #     fp = [fail_dist.failure_cdf(i) for i in ran]
                        #     cumulative_failure_prob.extend(fp)

                        cur_rel = fail_dist.reliability_cdf(v_start_time+duration)
                        #print(t_repair, (fail_dist[product_cat].failure_cdf(val2) - fail_dist[product_cat].failure_cdf(val1)))

                        # extend with changeover time
                        if (i < len(self.order) - 1):
                            next_item = self.order[i+1]
                            next_unit = self.job_dict.get(next_item, -1)
                            next_product_cat = next_unit['type']
                            changeover_time = float(failure_info['conversion_times'].loc[product_cat, next_product_cat])
                            t_changeover += (changeover_time / 3600)           

                        if failure_info['cleaning_time'] != None:
                            # extend with cleaning time
                            cleaning_times = float(failure_info['cleaning_time'].loc[product_cat])
                            t_clean += (cleaning_times / 3600)
                    else:
                        # if get_failure_schedule:
                        #     ran = np.arange(v_start_time, v_start_time + duration, 1/3)
                        #     fp = [fail_dist.failure_cdf(i) for i in ran]
                        #     cumulative_failure_prob.extend(fp)
                        pass
                    
                    t_end = t_start + timedelta(hours = du + t_down + t_changeover + t_clean)
                    total_duration_nofail += du
                    # t_downtime += t_down
                else:
                    t_end = t_start + timedelta(hours = du + t_down + t_changeover + t_clean)
                    total_duration_nofail += du
            try:
                # get all other info used by the input parser
                #import pdb; pdb.set_trace()
                detailed_dict.update({item : dict(zip(['start', 'end', 'totaltime', 'uptime', 
                                                       'product', 'type', 
                                                       'down_duration', 'changeover_duration', 
                                                       'cleaning_time', 'releasedate', 'duedate', 'quantity',
                                                       'unitprice', 'power', 'weight',
                                                       'targetproductionrate'],
                                                      [t_start, t_end, du + t_down + t_changeover + t_clean, 
                                                       du, unit1['product'], unit1['type'],
                                                       t_down, t_changeover, 
                                                       t_clean,  unit1['releasedate'], unit1['duedate'], quantity,
                                                       unit1['unitprice'], unit1['power'],
                                                       unit1['weight'], unit1['targetproductionrate']]))
                                      })
            except:
                # Start a debugger to find out what the cause was
                #import pdb; pdb.set_trace()
                raise
            t_now = t_end

        #self.failure_prob = cumulative_failure_prob
        #import pdb; pdb.set_trace()
        # if get_failure_schedule:
        #     return detailed_dict, cumulative_failure_prob
        # else:
        return detailed_dict

    def get_failure_cost(self, detail=False, split_costs=False):
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
            if split_costs:
                virtual_failure_cost = []
        else:
            failure_cost = 0
            if split_costs:
                virtual_failure_cost = 0
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
                #import pdb; pdb.set_trace()
                if self.scenario == 1: # using unit cost and production rate
                    # get product info
                    prc_up = detailed_dict[item]['unitprice']
                    prc_tpr = detailed_dict[item]['targetproductionrate']
                    # get total downtime duration
                    downdur_select = {key: value for key, value in downdur_dict.items() 
                                                                        if (startdate < value[0] < enddate)
                                                                        and (startdate < value[1] < enddate) 
                                    }
                    if len(downdur_select) > 0:
                        # len downdur_select means the number of failures during a certain production

                        # product loss
                        loss = len(downdur_select) * prc_up * prc_tpr / 3600 * num_seconds_lost # suppose for each failure 10 minutes of production gets lost
                        sum_len = 0
                        for item in downdur_select: # add up all failure times
                            sum_len += downdur_select[item][2]

                        # loss of time (virtual loss)
                        virtual_loss = sum_len * prc_up * prc_tpr # add the failure time X the production loss cost
                    else:
                        loss = 0; virtual_loss = 0
                if self.scenario == 2: # using fixed cost C1 and variable cost C2
                    # same method, but with fixed prices
                    downdur_select = {key: value for key, value in downdur_dict.items() 
                                                                        if (startdate < value[0] < enddate)
                                                                        and (startdate < value[1] < enddate) 
                                    }
                    if len(downdur_select) > 0:
                        # product loss
                        loss = len(downdur_select) * C1
                        sum_len = 0
                        for item in downdur_select:
                            sum_len += downdur_select[item][2]
                        # add time loss
                        virtual_loss = sum_len * C2
                    else:
                        loss = 0; virtual_loss = 0
                if detail:
                    if split_costs:
                        virtual_failure_cost.append(virtual_loss)
                        failure_cost.append(loss)
                    else:
                        failure_cost.append(loss + virtual_loss)
                else:
                    if split_costs:
                        virtual_failure_cost += virtual_loss
                        failure_cost += loss
                    else:
                        failure_cost += loss + virtual_loss

        if self.working_method == 'expected':
            for item in detailed_dict:
                product_type = detailed_dict[item]['product']
                #prc = self.prc_dict.get(item)
                #prc_av = prc['availability']
                down_duration = detailed_dict[item]['down_duration']
                loss = 0; virtual_loss = 0
                if self.scenario == 1:
                    prc_up = detailed_dict[item]['unitprice']
                    prc_tpr = detailed_dict[item]['targetproductionrate']
                    mean_up = self.mean_up; mean_tpr = self.mean_tpr
                    # time loss
                    virtual_loss += down_duration * mean_up * mean_tpr
                    if self.failure_info is not None:
                        if 'dt_len' in detailed_dict[item]:
                            mean_length_downtime = prc['dt_len']
                        else:
                            failure_info = self.failure_info
                            mean_length_downtime = failure_info['rep_mean']
                        # get the total calculated downtime and divide by the mean downtime length 
                        # = estimated number of downtimes
                        #
                        # item loss
                        loss += (down_duration / mean_length_downtime) * prc_up * prc_tpr / 3600 * num_seconds_lost
                if self.scenario == 2:
                    # same, but with C1 and C2 as constants
                    # time loss
                    virtual_loss += down_duration * C2
                    try:
                        if 'dt_len' in prc:
                            mean_length_downtime = prc['dt_len']
                        else:
                            failure_info = self.failure_info
                            mean_length_downtime = failure_info['rep_mean']
                        # item loss
                        loss += down_duration / mean_length_downtime * C1
                    except:
                        import pdb; pdb.set_trace()
                        raise
                
                if detail:
                    #if product_type == 'MAINTENANCE':
                     #   if split_costs:
                     #      virtual_failure_cost[-1] += virtual_loss
                     #      failure_cost[-1] += loss
                     #   else:
                     #       failure_cost[-1] += loss + virtual_loss
                    #else:
                    if split_costs:
                        virtual_failure_cost.append(virtual_loss)
                        failure_cost.append(loss)
                    else:
                        failure_cost.append(loss + virtual_loss)
                else:
                    if split_costs:
                        virtual_failure_cost += virtual_loss
                        failure_cost += loss
                    else:
                        failure_cost += loss + virtual_loss
        if split_costs:
            return failure_cost, virtual_failure_cost
        else:
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
        #prc_dict = self.prc_dict

        for item in time_dict:
            job_en_cost = 0

            unit1 = self.time_dict[item]
            product_type = unit1['product'] # get job product type
            #if product_type == "MAINTENANCE":
                #import pdb; pdb.set_trace()
            #if product_type == 'MAINTENANCE': product_type = 'NONE'
            #unit2 = prc_dict.get(str(item))
            try:
                power = unit1['power']
            except:
                # doesn't occur within the database; assume it is a break
                #power = 0
                import pdb; pdb.set_trace()
                print(product_type)
                print(unit1)
                raise

            t_start = unit1['start']
            t_end = unit1['end']

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
                #if product_type == 'MAINTENANCE':
                #    try:
                #        energy_cost[-1] += job_en_cost # don't add the cost if the list if still empty
                #    except:
                #        #import pdb; pdb.set_trace()
                #        pass
                #else:
                energy_cost.append(job_en_cost)
            else:
                energy_cost += job_en_cost
        return energy_cost

    def get_num_changeovers(self, detail=False):
        if detail:
            num_changeovers = []
        else:
            num_changeovers = 0
        for item1, item2 in zip(list(self.time_dict.keys())[:-1], list(self.time_dict.keys())[1:]):
            # if item2 == 0:
            #     pass
            # elif item1 == 0:
            #     if detail:
            #         changeover_cost.append(0)
            try:
                first_product_type = self.job_dict[item1]['type']
            except:
                first_product_type = "NONE"
            try:
                second_product_type = self.job_dict[item2]['type']
            except:
                second_product_type = "NONE"
            if first_product_type != second_product_type:
                if detail:
                    num_changeovers.append(1)
                else:
                    num_changeovers += 1
            else:
                if detail:
                    num_changeovers.append(0)
        if detail:
            num_changeovers.append(0)
        return num_changeovers

    def get_changeover_cost(self, detail=False):
        if detail:
            changeover_cost = []
        else:
            changeover_cost = 0

        if len(self.order) <= 1:
            print('No changeover cost')
            return changeover_cost


        if self.working_method == 'expected':
            for item1, item2 in zip(list(self.time_dict.keys())[:-1], list(self.time_dict.keys())[1:]):
                # if item2 == 0:
                #     pass
                # elif item1 == 0:
                #     if detail:
                #         changeover_cost.append(0)
                try:
                    first_product_type = self.job_dict[item1]['type']
                except:
                    first_product_type = "NONE"
                    #if detail:
                    #    changeover_cost.append(0)
                    #continue
                try:
                    second_product_type = self.job_dict[item2]['type']
                except:
                    second_product_type = "NONE"
                    #continue
                if self.failure_info is not None:
                    fi = self.failure_info['conversion_times']
                    changeover_time = int(fi.loc[first_product_type, second_product_type]) / 3600 # get the changeover time and convert to hours
                    #import pdb; pdb.set_trace()
                    # first_product = self.job_dict[item1]['product']
                    # prc_up = self.prc_dict[first_product]['unitprice']
                    # prc_tp = self.prc_dict[first_product]['targetproduction']
                    # if False:
                    #     mean = self.prc_dict.get('MEAN', -1)
                    #     mean_up = mean['unitprice']; mean_tpr = mean['targetproduction']

                    total_availability = changeover_time * self.mean_up * self.mean_tpr
                    if detail:
                        changeover_cost.append(total_availability)
                    else:
                        changeover_cost += total_availability
                else:
                    # Alternatively get the product info from another database
                    # self.failure_info[6]
                    # first_product_type = related_chars_dict[first_product][4]
                    # second_product_type = related_chars_dict[second_product][4]
                    if first_product_type != second_product_type:
                        # add changeover cost
                        # suppose cost is fixed
                        if detail:
                            changeover_cost.append(1)
                        else:
                            changeover_cost += 1
                    else:
                        if detail:
                            changeover_cost.append(0)
            if detail:
                changeover_cost.append(0)
            return changeover_cost
        elif self.working_method == 'historical':
            if detail:
                changeover_cost = [0] * len(self.order)
            else:
                changeover_cost = 0
            return changeover_cost

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
                if 'duedate' in self.job_dict[item]: # assume not all jobs have deadlines
                    # check deadline condition
                    beforedate = self.job_dict[item]['duedate']
                    if self.time_dict[item]['end'] > beforedate: # produced after deadline
                        deadline_cost += (self.time_dict[item]['end'] - beforedate).total_seconds() / 3600\
                                         * self.job_dict[item]['weight']
                if 'releasedate' in self.job_dict[item]: # assume not all jobs have deadlines
                    # check after condition
                    afterdate = self.job_dict[item]['releasedate']
                    if self.time_dict[item]['start'] < afterdate: # produced before release date
                        deadline_cost += (afterdate - self.time_dict[item]['start']).total_seconds() / 3600\
                                       * self.job_dict[item]['weight']
                #if beforedate < afterdate:
                    #import pdb; pdb.set_trace()
            else:
                deadline_cost += 0
            if detail:
                constraint_cost.append(deadline_cost)
            elif deadline_cost > 0:
                constraint_cost += deadline_cost
        return constraint_cost

    def get_flowtime_cost(self, detail=False):
        if detail:
            flowtime_cost = []
        else:
            flowtime_cost = 0
        t_now = self.start_time

        for item in self.time_dict:
            #count = True
            #if item in self.job_dict: # this function eliminates all maintenance jobs
            product = self.time_dict[item]['product']
            try:
                weight = self.job_dict[item]['weight']
            except:
                weight = 0
            flowtime = weight * (self.time_dict[item]['end'] - t_now).total_seconds() / 3600
            #if (product != 'NONE') and (product != 'MAINTENANCE'):
            #    enddate = self.time_dict[item]['end']
            #    flowtime = (enddate - t_now).total_seconds() / 3600
            #elif product == 'NONE':
            #    flowtime = 0
            #else:
            #    print('Error')
            if detail:
                flowtime_cost.append(flowtime)
            elif flowtime > 0:
                flowtime_cost += flowtime
        return flowtime_cost

    def get_precedence_cost(self, detail=False):
        if detail:
            precedence_cost = [0]*len(self.time_dict)
        else:
            precedence_cost = 0
        if self.precedence_dict: 
            for beforeitem in self.precedence_dict:
                for afteritem in self.precedence_dict[beforeitem]:
                    if beforeitem in list(self.order):
                        if afteritem not in self.order[list(self.order).index(beforeitem):]:
                            if detail:
                                precedence_cost[list(self.order).index(afteritem)] += 1
                            else:
                                precedence_cost += 1
        return precedence_cost
  
    # def get_weighted_tardiness_cost(self, detail=False):
    #     """
    #     Get the weighted tardiness cost for a certain
    #     job_list order
    #     """
    #     #import pdb; pdb.set_trace()
    #     if detail:
    #         current_cost = []
    #     else:
    #         current_cost = 0
    #     for item in self.time_dict:
    #         if item in self.job_dict:
    #             current_duedate = self.job_dict[item]['duedate']
    #             current_releasedate = self.job_dict[item]['releasedate']
    #             current_time = self.time_dict[item]['end']
    #             # print(current_releasedate)
    #             # print(current_time)
    #             # print(current_duedate)
    #             # import pdb; pdb.set_trace()
    #             if current_time > current_duedate:
    #                 #import pdb; pdb.set_trace()
    #                 current_priority = self.job_dict[item]['weight']
    #                 extra_cost = (current_time - current_duedate).total_seconds() / 60\
    #                             * current_priority
    #                 if detail:
    #                     current_cost.append(extra_cost)
    #                 else:
    #                     current_cost += extra_cost
    #             elif current_time < current_releasedate:
    #                 #import pdb; pdb.set_trace()
    #                 current_priority = self.job_dict[item]['weight']
    #                 extra_cost = (current_releasedate - current_time).total_seconds() / 60\
    #                        * current_priority
    #                 if detail:
    #                     current_cost.append(extra_cost)
    #                 else:
    #                     current_cost += extra_cost
    #             else:
    #                 if detail:
    #                     current_cost.append(0)
    #     return current_cost
    
    def validate_duedate(self):
        """Validate due date """
        time_dict = self.get_time()
        # validate due date
        for key, value in time_dict.items():
            if key in self.job_dict.keys():
                due = self.job_dict[key]['duedate'] # due date of a job
                if value['end'] > due:
                    print("For candidate schedule:", self.order)
                    print(f"Job {key} will finish at {value['end']} over the due date {due}")
                    return False
                release= self.job_dict[key]['releasedate']
                if value['start'] < release:
                    print("For candidate schedule:", self.order)
                    print(f"Job {key} will finish at {value['start']} below the release date {release}")
                    return False
        return True

    def validate_precedence(self):
        """ validate precedence """
        #jobs = list(self.order.copy())
        return True if self.get_precedence_cost() == 0 else False 

    def validate(self):
        # validate due date
        flag = self.validate_duedate()
        if not flag:
            return flag
        else:
            self.validate_precedence()
        return flag
    
    # def fix_validation(self):
    #     # get time
    #     time_dict = self.get_time()
    #     # print (time_dict)
    #     #fix due dates:
    #     for key, value in time_dict.items():
    #         if key in self.job_dict.keys():
    #             due = self.job_dict[key]['duedate'] # due date of a job
    #             if value['end'] > due:
    #                 print("For candidate schedule:", self.order)
    #                 print(f"Job {key} will finish at {value['end']} over the due date {due}")
            

    def get_fitness(self, split_types=False, detail=False, weights=None):
        ''' 
        Get fitness values for all individuals in a generation.
        '''
        if weights is None:
            wf = self.weights.get('weight_failure', 0); wvf =self.weights.get('weight_virtual_failure', 0)
            we = self.weights.get('weight_energy', 0); wc = self.weights.get('weight_changeover', 0)
            wb = self.weights.get('weight_constraint', 0); wft = self.weights.get('weight_flowtime', 0);
            wp = self.weights.get('weight_precedence', 0); wnc = self.weights.get('num_changeovers', 0)
           
        else:
            wf = weights.get('weight_failure', 0); wvf = weights.get('weight_virtual_failure', 0)
            we = weights.get('weight_energy', 0); wc = weights.get('weight_changeover', 0)
            wb = weights.get('weight_constraint', 0); wft = weights.get('weight_flowtime', 0)
            wp = weights.get('weight_precedence', 0); wnc = weights.get('num_changeovers', 0)
        factors = (wf, wvf, we, wc, wb, wft, wp, wnc)
        if wf or wvf:
            #failure_cost, virtual_failure_cost = [np.array(i.get_failure_cost(detail=detail, split_costs=True)) for i in sub_pop]
            #for i in sub_pop:
            failure_cost, virtual_failure_cost = self.get_failure_cost(detail=detail, split_costs=True)
            #failure_cost.append(np.array(f_cost)); virtual_failure_cost.append(np.array(vf_cost))
        else:
            failure_cost = 0
            virtual_failure_cost = 0
        if we:
            #energy_cost = [self.w2*np.array(get_energy_cost(i, self.start_time, self.job_dict, self.price_dict, self.product_related_characteristics_dict, self.down_duration_dict,
            #                detail=detail, duration_str=self.duration_str, working_method=self.working_method)) for i in sub_pop]
            energy_cost = self.get_energy_cost(detail=detail)
        else:
            energy_cost = 0
        if wc:
            changeover_cost = self.get_changeover_cost(detail=detail)
        else:
            changeover_cost = 0
        if wb:
            constraint_cost = self.get_constraint_cost(detail=detail)
        else:
            constraint_cost = 0
        if wft:
            flowtime_cost = self.get_flowtime_cost(detail=detail)
        else:
            flowtime_cost = 0
        if wp:
            precedence_cost = self.get_precedence_cost(detail=detail)
        else:
            precedence_cost = 0
        if wnc:
            num_changeovers = self.get_num_changeovers(detail=detail)
        else:
            num_changeovers = 0
        if split_types:
            total_cost = (np.array(failure_cost), np.array(virtual_failure_cost), np.array(energy_cost), 
                          np.array(changeover_cost), np.array(constraint_cost),
                          np.array(flowtime_cost), np.array(precedence_cost), 
                          np.array(num_changeovers), factors)
        else:
            try:
                # if (type(changeover_cost) is list) and (type(energy_cost) is list):
                #     changeover_cost = np.array(changeover_cost[:len(energy_cost)])
                # if (type(changeover_cost) is list) and (type(constraint_cost) is list):
                #     changeover_cost = np.array(changeover_cost[:len(constraint_cost)])
                # if (type(changeover_cost) is list) and (type(failure_cost) is list):
                #     changeover_cost = np.array(changeover_cost[:len(failure_cost)])
                # if (type(changeover_cost) is list) and (type(virtual_failure_cost) is list):
                #     changeover_cost = np.array(changeover_cost[:len(virtual_failure_cost)])
                # if (type(changeover_cost) is list) and (type(flowtime_cost) is list):
                #     changeover_cost = np.array(changeover_cost[:len(flowtime_cost)])
                # changeover_cost has sometimes a length which is too long, solve it here temporarily
                total_cost = wf * np.array(failure_cost) + wvf * np.array(virtual_failure_cost) +\
                             we * np.array(energy_cost) + wc * np.array(changeover_cost) + wb * np.array(constraint_cost) +\
                             wft * np.array(flowtime_cost) + wp * np.array(precedence_cost) +\
                             wnc * np.array(num_changeovers)
            except:
                print()
                print(np.array(failure_cost).shape, np.array(virtual_failure_cost).shape, np.array(energy_cost).shape,
                      np.array(changeover_cost).shape, np.array(constraint_cost).shape, np.array(flowtime_cost).shape,
                      np.array(precedence_cost).shape, np.array(num_changeovers))
                print(detail)
                print(energy_cost)
                print(changeover_cost)
                print(constraint_cost)
                print(flowtime_cost)
                print(precedence_cost)
                print(num_changeovers)
                import pdb; pdb.set_trace()
                raise
            
        return total_cost

    def print_fitness(self, inputstr="Total"):
        f_cost, vf_cost, e_cost, c_cost, d_cost, ft_cost, prec_cost, num_conv, factors = self.get_fitness(split_types=True)
        total_cost = f_cost * factors[0] + vf_cost * factors[1] + e_cost  * factors[2] + c_cost * factors[3]\
                   + d_cost * factors[4] + ft_cost * factors[5] + prec_cost * factors[6] + num_conv * factors[7]
        #import pdb; pdb.set_trace()

        logging.info(inputstr + " failure cost: " + str(f_cost))
        logging.info(inputstr + " virtual failure cost: " + str(vf_cost))
        logging.info(inputstr + " energy cost: " + str(e_cost))    
        logging.info(inputstr + " changeover cost: " + str(c_cost))
        logging.info(inputstr + " deadline cost: " + str(d_cost))
        logging.info(inputstr + " flowtime cost: " + str(ft_cost))
        logging.info(inputstr + " precedence cost: " + str(prec_cost))
        logging.info("Factors: " + str(factors))
        logging.info("Total cost: " + str(total_cost))

        logging.info("Number of changeovers: " + str(self.get_num_changeovers()))
    
    def fitness_csv(self):
        f_cost, vf_cost, e_cost, c_cost, d_cost, ft_cost, prec_cost, num_conv, factors = self.get_fitness(split_types=True)
        unweighted_total_cost = f_cost + vf_cost + e_cost + d_cost + ft_cost + prec_cost
        weighted_total_cost = f_cost * factors[0] + vf_cost * factors[1] + e_cost  * factors[2] + c_cost * factors[3]\
                              + d_cost * factors[4] + ft_cost * factors[5] * prec_cost * factors[6] + num_conv * factors[7]
        indexcol = ['failure', 'virtual_failure', 'energy', 'changeover', 'due', 'flowtime', 'precedence', 'num_conv', 'total']
        series1 = pd.Series(data=[f_cost, vf_cost, e_cost, c_cost, d_cost, ft_cost, prec_cost, num_conv, unweighted_total_cost], 
                            index=indexcol, name='Unweighted costs')
        series2 = pd.Series(data=factors, index=indexcol[:-1], name='Multiply factors')
        series3 = pd.Series(data=[f_cost * factors[0], vf_cost * factors[1], 
                                  e_cost * factors[2], c_cost * factors[3],
                                  d_cost * factors[4], ft_cost * factors[5],
                                  prec_cost * factors[6], num_conv * factors[7]
                                  , weighted_total_cost], index=indexcol, name='Weighted costs')
        output_frame = pd.DataFrame([series1, series2, series3]).T
        return output_frame
        
