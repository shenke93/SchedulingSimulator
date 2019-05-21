import sys
import pandas as pd
from datetime import datetime
import configparser
import os
from time import localtime, strftime
import logging
import csv

class JobInfo(object):
    '''
    A class which contains the JobInfo dictionary.
    It can also add breaks and other info to the dictionary
    It can also change the job file based on start and end date
    '''
    def __init__(self):
        '''
        Initialise the job dictionary
        '''
        self.job_dict = {}
        self.job_order = []
    
    def __str__(self):
        return ("Job order: " + str(self.job_order))

    def __add__(self, other):
        job_dict = self.job_dict + other.job_dict
        job_order = self.job_order + other.job_order
        new_ji = JobInfo()
        new_ji.job_dict = job_dict
        new_ji.job_order = job_order
        return new_ji

    def read_from_file(self, job_file, get_totaltime=False):
        '''
        Create a dictionary to restore job information.

        Parameters
        ----------
        jobFile: string
            Name of file containing job information.
        Returns
        -------
        A dictionary containing job indexes and characteristics, key: int, value: list.
        '''
        job_dict = {}
        job_order = []
        # Choose between total time and uptime
        if get_totaltime:
            str_time = 'Totaltime'
        else:
            str_time = 'Uptime'
        try:
            with open(job_file, encoding='utf-8') as jobInfo_csv:
                reader = csv.DictReader(jobInfo_csv)
                for row in reader:
                    job_num = int(row['ID'])
                    # insert product name
                    job_entry = dict({'product': row['Product']})
                    # time string or quantity should be in the row
                    if (str_time in row) and row[str_time] is not None:
                        job_entry['duration'] = float(row[str_time])
                    if ('Quantity' in row) and row['Quantity'] is not None:
                        job_entry['quantity'] = float(row['Quantity'])
                    if ('Start' in row) and row['Start'] is not None:
                        job_entry['start'] = datetime.strptime(row['Start'], "%Y-%m-%d %H:%M:%S.%f")
                    if ('End' in row) and row['End'] is not None:
                        job_entry['end'] = datetime.strptime(row['End'], "%Y-%m-%d %H:%M:%S.%f")
                    # Add product type
                    if ('Type' in row) and row['Type'] is not None:
                        job_entry['type'] = row['Type']
                        #print('Added type')
                    else:
                        job_entry['type'] = 'unknown'
                    # Add due date
                    if ('Before' in row) and (row['Before'] is not None):
                        job_entry['before'] = datetime.strptime(row['Before'], "%Y-%m-%d %H:%M:%S.%f")
                        #print('Before date read')
                    else:
                        job_entry['before'] = datetime.max
                    # Add after date
                    if ('After' in row) and (row['After'] is not None):
                        job_entry['after'] = datetime.strptime(row['After'], "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        job_entry['after'] = datetime.min

                    # add the item to the job dictionary
                    job_dict[job_num] = job_entry
                    job_order.append(job_num)
        except:
            print("Unexpected error when reading job information from {}:".format(job_file))
            raise
        self.job_dict = job_dict
        self.job_order = job_order


    def insert_urgent_jobs(self, urgent_dict):
        stamp = min(x.get('ReleaseDate') for x in urgent_dict.values()) # Find the smallest release date
        print(stamp)
        res_dict = {}
        for key, value in origin_dict.items():
            try:
                if value['start'] >= stamp: # All jobs whose start time after the stamp needs to be re-organized
                    res_dict.update({key:value})
            except TypeError:
                print("Wrong type when comparing jobs.")
                raise
        
        res_dict.update(urgent_dict)

        return res_dict

    def limit_range(self, date_range1, date_range2):
        '''
        Select items of dict from a time range.
        
        Parameters
        ----------
        dateRange1: Date
            Start timestamp of the range.
        
        dateRange2: Date
            End timestamp of the range.
            
        dict: Dict
            Original dictionary.
            
        Returns
        -------
        A dict containing selected items.
        '''
        #res_dict = collections.OrderedDict()
        job_dict = self.job_dict
        job_dict_copy = self.job_dict.copy()
        job_order = self.job_order
        #res_dict = {}
        assert date_range1 < date_range2, "The end date should be larger then the start date"
        for key, value in job_dict.items():
            if value['start'] < date_range1 or value['end'] > date_range2:
                try:
                    del job_dict_copy[key]
                    job_order.remove(key)
                except KeyError:
                    print(value['start'], date_range1, value['end'], date_range2)
                    print("Key {} not found".format(key))
                    raise
        self.job_dict = job_dict_copy
        self.job_order = job_order

    def add_breaks(self, break_hours):
        ''' 
        Add a number of hours of breaks at the end of the file
        '''
        job_dict = self.job_dict
        min_key = min(job_dict.keys())
        job_order = self.job_order
        while break_hours > 0:
            min_key -= 1
            dur = 2 if break_hours > 2 else break_hours
            new_dict = {'product': 'NONE', 'duration': dur, 'quantity': dur, 'type': 'NONE', 
                        'before': datetime.max, 'after': datetime.min}
            job_dict[min_key] = new_dict
            job_order.append(min_key)
            break_hours -= 2
        self.job_dict = job_dict
        self.job_order = job_order


# Construct energy two tariffs between two dates
def construct_energy_2tariffs(ran, daytarif=12, nighttarif=8, starttime=21, endtime=6):
    '''
    Construct energy prices in 2 tariffs (day-night schedule)
    '''
    ind = pd.date_range(freq='H', start=ran[0], end=ran[1])
    prices = pd.DataFrame([daytarif] * len(ind), index=ind)
    night = (ind.weekday >= 5) | (ind.hour < endtime) | (ind.hour >= starttime) 
    # saturday or sunday, after 21 and before 6 is nighttarif
    prices[night] = nighttarif
    prices.columns = ['Euro']
    prices.index.name = 'Date'
    #prices = prices.loc[prices['Euro'].diff(1) != 0]
    return prices

def print_ul(strin):
    ''' 
    Print a text with a line below
    '''
    print(strin)
    print('-'*len(strin))

def make_df(dict):
    '''
    Make a dataframe from a dictionary
    '''
    all_cols = ['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName', 'Type', 'Down_duration', 'Changeover_duration', 'Cleaning_duration']
    df = pd.DataFrame.from_dict(dict, orient='index')
    df.columns = all_cols
    df = df.reindex(list(dict.keys()))
    return df

class writer :
    ''' 
    Edit the standard writer so that there is also written to a file
    '''
    def __init__(self, *writers):
        self.writers = writers

    def write(self, text) :
        for w in self.writers:
            w.write(text)
    
    def flush(self):
        pass

def read_failure_info(file):
    '''
    Read a certain failure file in XML format.
    Throw errors if in a wrong format.
    '''
    import xml.etree.ElementTree as ET
    tree = ET.parse(file)
    root = tree.getroot()
    fail_type = root.find('fail_dist').text
    if fail_type == "weibull":
        fail_dist = root.find('fail_dist')
        fail_dict = {}
        for dist in fail_dist:
            text = dist.text
            lamb = float(dist.get('lambda'))
            rho = float(dist.get('rho'))
            from probdist import Weibull
            fail_dist = Weibull(lamb, rho)
            fail_dict[text] = fail_dist
    elif fail_type == "exp":
        fail_dist = root.find('fail_dist')
        fail_dict = {}
        for dist in fail_dist:
            text = dist.text
            lamb = float(dist.get('lambda'))
            from probdist import Exponential
            fail_dist = Exponential(1/lamb)
            fail_dict[text] = fail_dist
    else:
        print('Faulty distribution detected!')
    repair_type = root.find('repair_dist').text
    if repair_type == 'lognormal':
        sigma = float(root.find('repair_dist').get('sigma'))
        mu = float(root.find('repair_dist').get('mu'))
        from probdist import Lognormal
        rep_dist = Lognormal(sigma, mu)
        mean = float(root.find('repair_dist').get('mean'))
    else:
        print('Faulty distribution detected!')
        raise NameError("Error")
    maint_time = int(root.find('maint_time').text)
    repair_time = float(root.find('repair_time').text)

    conversion_file = root.find('files').find('conversion_times').text
    conversion_times = pd.read_csv(os.path.join(os.path.split(file)[0], conversion_file), index_col = 0)

    if 'cleaning_time' in root.find('files'):
        cleaning_file = root.find('files').find('cleaning_time').text
        cleaning_time = pd.read_csv(os.path.join(os.path.split(file)[0], cleaning_file), index_col = 0)
    else:
        cleaning_time = None       

    failure_info = (fail_dict, rep_dist, mean, maint_time, repair_time, conversion_times, cleaning_time)
    return failure_info

def read_config_file(path):
    '''
    Read a configuration file using a certain path
    '''
    config = configparser.ConfigParser()
    config.read(path)
    sections = config.sections()
    return_sections = {}
    pathname = os.path.dirname(path)
    if 'input-config' in sections:
        input_config = {}
        this_section = config['input-config']
        input_config['original'] = orig_folder =  this_section['original_folder']
        orig_folder = os.path.join(pathname, orig_folder)
        input_config['prc_file'] = os.path.join(orig_folder, this_section['product_related_characteristics_file'])
        input_config['ep_file'] = os.path.join(orig_folder, this_section['energy_price_file'])
        input_config['hdp_file'] = os.path.join(orig_folder, this_section['historical_down_periods_file'])
        input_config['ji_file'] = os.path.join(orig_folder, this_section['job_info_file'])
        if 'urgent_job_info_file' in this_section:
            input_config['urgent_ji_file'] = os.path.join(orig_folder, this_section['urgent_job_info_file'])
        else:
            input_config['urgent_ji_file'] = None
        if 'failure_info_path' in this_section:
            failure_info_path = os.path.join(orig_folder, this_section['failure_info_path'])
            if os.path.exists(failure_info_path):
                input_config['failure_info'] = read_failure_info(os.path.join(failure_info_path, 'outputfile.xml'))
        else:
            input_config['failure_info'] = None
        if 'failure_rate_file' in this_section:
            input_config['fr_file'] = os.path.join(orig_folder, this_section['failure_rate_file'])
        else:
            input_config['fr_file'] = None
        return_sections['input_config'] = input_config
    
    if 'output-config' in sections:
        output_config = {}
        this_section = config['output-config']
        output_config['export_folder'] = export_folder = os.path.join(pathname, this_section['export_folder'] + '_' + strftime("%Y%m%d_%H%M", localtime()))
        output_config['output_init'] = os.path.join(export_folder, this_section['output_init'])
        output_config['output_final'] = os.path.join(export_folder, this_section['output_final'])
        output_config['interactive'] = config.getboolean('output-config', 'interactive')
        output_config['export'] = config.getboolean('output-config', 'export')
        if 'export_paper' in this_section:
            output_config['export_paper'] = config.getboolean('output-config', 'export_paper')
        else:
            output_config['export_paper'] = False
        return_sections['output_config'] = output_config

    if 'scenario-config' in sections:
        scenario_config = {}
        this_section = config['scenario-config']
        # Read scenario-config
        scenario_config['test'] = config.get('scenario-config', 'test').replace(' ', '').split(',')
        scenario_config['scenario'] = config.getint('scenario-config', 'scenario')
        scenario_config['validation'] = config.getboolean('scenario-config', 'validation')
        scenario_config['pre_selection'] = config.getboolean('scenario-config', 'pre_selection')
        
        scenario_config['weights'] = {}
        scenario_config['weights']['weight_energy'] = config.getfloat('scenario-config', 'weight_energy')
        scenario_config['weights']['weight_constraint'] = config.getfloat('scenario-config', 'weight_constraint')
        scenario_config['weights']['weight_failure'] = config.getfloat('scenario-config', 'weight_failure')
        if 'weight_virtual_failure' in this_section:
            scenario_config['weights']['weight_virtual_failure'] = config.getfloat('scenario-config', 'weight_virtual_failure')
        else:
            scenario_config['weights']['weight_virtual_failure'] = scenario_config['weight_failure']
        if 'weight_flowtime' in this_section:
            scenario_config['weights']['weight_flowtime'] = config.getfloat('scenario-config', 'weight_flowtime')
        scenario_config['weights']['weight_conversion'] = config.getfloat('scenario-config', 'weight_conversion')

        scenario_config['pop_size'] = config.getint('scenario-config', 'pop_size')
        scenario_config['crossover_rate'] = config.getfloat('scenario-config', 'crossover_rate')
        scenario_config['mutation_rate'] = config.getfloat('scenario-config', 'mutation_rate')
        scenario_config['num_mutations'] = config.getint('scenario-config', 'num_mutations')
        scenario_config['iterations'] = config.getint('scenario-config', 'iterations')
        
        scenario_config['stop_condition'] = config.get('scenario-config', 'stop_condition')
        scenario_config['stop_value'] = config.getint('scenario-config', 'stop_value')
        scenario_config['duration_str'] = config.get('scenario-config', 'duration_str')
        scenario_config['evolution_method'] = config.get('scenario-config', 'evolution_method')
        scenario_config['working_method'] = config.get('scenario-config', 'working_method')
        
        adapt_ifin_low = config.getint('scenario-config', 'adapt_ifin_low')
        adapt_ifin_high = config.getint('scenario-config', 'adapt_ifin_high')
        adapt_ifin_step = config.getint('scenario-config', 'adapt_ifin_step')
        scenario_config['adapt_ifin'] = [i for i in range(adapt_ifin_low, adapt_ifin_high+adapt_ifin_step, adapt_ifin_step)]

        if 'add_time' in this_section:
            scenario_config['add_time'] = config.getint('scenario-config', 'add_time')
        else:
            scenario_config['add_time'] = 0
        if 'add_time_list' in this_section:
            time_list = config.get('scenario-config', 'add_time_list')
            time_list = map(int, time_list.split(' '))
            scenario_config['add_time_list'] = time_list
        return_sections['scenario_config'] = scenario_config
    
    if 'start-end' in sections:
        start_end = {}
        start_end['start_time'] = datetime(config.getint('start-end', 'start_year'), config.getint('start-end', 'start_month'), 
                        config.getint('start-end', 'start_day'), config.getint('start-end', 'start_hour'), 
                        config.getint('start-end', 'start_minute'), config.getint('start-end', 'start_second')) # Date range of jobs to choose
        start_end['end_time'] = datetime(config.getint('start-end', 'end_year'), config.getint('start-end', 'end_month'), 
                                config.getint('start-end', 'end_day'), config.getint('start-end', 'end_hour'), 
                                config.getint('start-end', 'end_minute'), config.getint('start-end', 'end_second'))
    elif 'start' in sections:
        start_end = {}
        start_end['start_time'] = datetime(config.getint('start', 'start_year'), config.getint('start', 'start_month'), 
                                config.getint('start', 'start_day'), config.getint('start', 'start_hour'), 
                                config.getint('start', 'start_minute'), config.getint('start', 'start_second')) # Date range of jobs to choose
        start_end['end_time'] = None
    else:
        raise NameError('No section with start date found!')
    return_sections['start_end'] = start_end
    
    return return_sections

def start_logging(filename):
    ''' 
    Start logging in a file during the execution of this program
    Also output to a file
    '''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=filename,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

if __name__ == "__main__":
    if (len(sys.argv) == 4):
        startdate = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        enddate = datetime.strptime(sys.argv[2], "%Y-%m-%d")
        prices = construct_energy_2tariffs((startdate, enddate))
        prices.to_csv(sys.argv[3])
    else:
        print('Error')
