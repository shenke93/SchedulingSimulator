import sys
import pandas as pd
from datetime import datetime
import configparser
import os
from time import localtime, strftime
import logging
import csv
import warnings



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
        if set(self.job_order).isdisjoint(set(other.job_order)):
            job_dict = self.job_dict
            job_dict.update(other.job_dict)
            job_order = self.job_order + other.job_order
            new_ji = JobInfo()
            new_ji.job_dict = job_dict
            new_ji.job_order = job_order
            return new_ji
        else:
            raise Exception('The two input sets overlap, please fix this first')
            exit

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
        
        def raiseerror(): raise ValueError('Product name missing')
        def donothing(): pass
        def parsedate(x): y = datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"); return y
        def notypefound(): 
            logging.warning('Unknown type, adding the type as unknown')
            return 'unknown'
        def noduedate():
            logging.warning("Due date could not be parsed")
            return datetime.max
        def noreleasedate(): 
            logging.warning("Release date could not be parsed")
            return datetime.min
            
        
        operations = {
            'Product': ['product', str, raiseerror],
            'Totaltime': ['totaltime', float, donothing],
            'Uptime': ['uptime', float, donothing],
            'Quantity': ['quantity', float, donothing],
            #'Start': ['start', parsedate, donothing],
            #'End': ['end', parsedate, donothing],
            'Type': ['type', str, notypefound],
            'Duedate': ['duedate', parsedate, noduedate],
            'Releasedate': ['releasedate', parsedate, noreleasedate]
        }
        
        try:
            with open(job_file, encoding='utf-8') as jobInfo_csv:
                reader = csv.DictReader(jobInfo_csv)
                for row in reader:
                    if row['Product'] != 'MAINTENANCE': # Do not read maintenance tasks
                        job_num = int(row['ID'])
                        # insert product name
                        job_entry = dict({'product': row['Product']})
                        
                        job_entry = {}
                        for key, value in operations.items():
                            try:
                                job_entry[value[0]] = value[1](row[key])
                            except:
                                othervalue = value[2]()
                                if othervalue != None:
                                    job_entry[value[0]] = othervalue
                        
                    # add the item to the job dictionary
                        job_dict[job_num] = job_entry
                        job_order.append(job_num)
        except:
            print("Unexpected error when reading job information from {}:".format(job_file))
            raise
        self.job_dict = job_dict
        self.job_order = job_order


    def insert_urgent_jobs(self, urgent_dict):
        stamp = min(x.get('releasedate') for x in urgent_dict.values()) # Find the smallest release date
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

    def limit_range(self, date_range1, date_range2=None):
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
        job_dict_copy = job_dict.copy()
        job_order = self.job_order
        #res_dict = {}
        for key, value in job_dict.items():
            if value['start'] < date_range1: 
                try:
                    del job_dict_copy[key]
                    job_order.remove(key)
                except KeyError:
                    print(value['start'], date_range1, value['end'], date_range2)
                    print("Key {} not found".format(key))
                    raise
        if date_range2:
            assert date_range1 < date_range2, "The end date should be larger then the start date"
            for key, value in job_dict.items():
                if value['end'] > date_range2:
                    try:
                        del job_dict_copy[key]
                        job_order.remove(key)
                    except KeyError:
                        print(value['start'], date_range1, value['end'], date_range2)
                        print("Key {} not found".format(key))
                        raise
        self.job_dict = job_dict_copy
        self.job_order = job_order

    
    def limit_range_disruptions(self, date_range1, date_range2=None):
        '''
        Version of limit_range used for disruption handling.
        
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
        job_dict_copy = job_dict.copy()
        job_order = self.job_order
        #res_dict = {}
        for key, value in job_dict.items():
            if value['end'] <= date_range1: # Finished jobs: end time earlier than the timpstamp of the disruption.
                try:
                    del job_dict_copy[key]
                    job_order.remove(key)
                except KeyError:
                    print(value['start'], date_range1, value['end'], date_range2)
                    print("Key {} not found".format(key))
                    raise
        if date_range2:
            assert date_range1 < date_range2, "The end date should be larger then the start date"
            for key, value in job_dict.items():
                if value['end'] > date_range2:
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
                        'duedate': datetime.max, 'releasedate': datetime.min}
            job_dict[min_key] = new_dict
            job_order.append(min_key)
            break_hours -= 2
        self.job_dict = job_dict
        self.job_order = job_order

    def remove_all_breaks(self):
        ''' 
        Remove all breaks from the file
        '''


    

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

def make_df(timing_dict):
    '''
    Make a dataframe from a dictionary
    '''
    #all_cols = ['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName', 'Type', 'Down_duration', 'Changeover_duration', 'Cleaning_duration']
    df = pd.DataFrame.from_dict(timing_dict, orient='index')
    df = df.rename(columns={'start': 'Start', 'end':'End', 'totaltime': 'Totaltime', 'uptime': 'Uptime',  
                                       'product': 'Product', 'type': 'Type', 'releasedate': 'Releasedate', 'duedate': 'Duedate', 'quantity': 'Quantity'})
    df = df.reindex(list(timing_dict))
    df = df[['Uptime', 'Totaltime', 'Quantity', 'Start', 'End', 'Product', 'Type', 'Releasedate', 'Duedate']]
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


class SchedulerInitiator(object):
    def __init__(configfile):
        config_entries = read_config_file(configfile)
        
        


def my_config_parser(in_dict, config_section):
    out_dict = {}
    for key, value in in_dict.items():
        try:
            out_dict[value[0]] = value[1](config_section[key])
        except:
            out_dict[value[0]] = value[2](key)
    return out_dict
      
        

def read_config_file(path):
    '''
    Read a configuration file using a certain path
    '''
    config = configparser.ConfigParser()
    config.read(path)
    sections = config.sections()
    return_sections = {}
    pathname = os.path.dirname(path)
    #configfolder = pathname
    
    def join_path(x):
        return os.path.join(configfolder, x)
    def raise_failure(section):
        raise NameError(f'{section} not found in the config file')
    def raise_no_failure(section):
        return None
    def read_bool(x):
        if (x == 'False') or (x == 'F') or (x == ''):
            return False
        else:
            return True
    
    if 'input-config' in sections:
        #input_config = {}
        this_section = config['input-config']
        
        configfolder = None
        def config_folder(x):
            nonlocal configfolder
            configfolder = os.path.join(pathname, x)
            return configfolder
        
        def read_xml_file(x):
            return read_failure_info(os.path.join(configfolder, x, 'outputfile.xml'))

        input_actions = {
            'original_folder': ['original', config_folder, raise_failure],
            'product_related_characteristics_file': ['prc_file', join_path, raise_failure],
            'precendence_file': ['prec_file', join_path, raise_no_failure],
            'energy_price_file': ['ep_file', join_path, raise_failure],
            'historical_down_periods_file': ['hdp_file', join_path, raise_failure],
            'job_info_file': ['ji_file', join_path, raise_failure],
            'urgent_job_info_file': ['urgent_ji_file', join_path, raise_no_failure],
            'breakdown_record_file': ['bd_rec_file', join_path, raise_no_failure],
            'failure_info_path': ['failure_info', read_xml_file, raise_no_failure],
            'failure_rate': ['fr_file', join_path, raise_no_failure]
        }
        
        return_sections['input_config'] = my_config_parser(input_actions, this_section)
    
    if 'output-config' in sections:
        #output_config = {}
        this_section = config['output-config']
        
        def join_path_curdate(x):
            return os.path.join(pathname, str(x) + '_' + strftime("%Y%m%d_%H%M", localtime()))
        def return_false(x):
            return False
        
        output_actions = {
            'export_folder': ['export_folder', join_path_curdate, raise_failure],
            'output_init': ['output_init', join_path, raise_failure],
            'output_final': ['output_final', join_path, raise_failure],
            'interactive': ['interactive', read_bool, raise_failure],
            'export': ['export', read_bool, raise_failure],
            'export_paper': ['export_paper', read_bool, return_false]
        }
        
        return_sections['output_config'] = my_config_parser(output_actions, this_section)

    if 'scenario-config' in sections:
        scenario_config = {}
        this_section = config['scenario-config']
        
        def read_stringlist(x):
            list_x = x.replace(' ', '').split(',')
            str_list = map(str, list_x)
            return [*str_list]
        
        def return_0(x):
            return 0
        
        def read_intlist(x):
            list_x = x.replace(' ', '').split(',')
            int_list = map(int, list_x)
            return [*int_list]
        
        weight_actions = {
            'weight_energy': ['weight_energy', float, return_0],
            'weight_constraint': ['weight_constraint', float, return_0],
            'weight_failure': ['weight_failure', float, return_0],
            'weight_virtual_failure': ['weight_failure', float, return_0],
            'weight_flowtime': ['weight_flowtime', float, return_0],
            'weight_conversion': ['weight_conversion', float, return_0],
        }
        
        scenario_actions = {
            'test': ['test', read_stringlist, raise_failure],
            'scenario': ['scenario', int, raise_failure],
            'validation': ['validation', read_bool, raise_failure],
            'pre_selection': ['pre_selection', read_bool, raise_failure],
            'pop_size': ['pop_size', int, raise_failure],
            'crossover_rate': ['crossover_rate', float, raise_failure],
            'mutation_rate': ['mutation_rate', float, raise_failure],
            'num_mutations': ['num_mutations', int, raise_failure],
            'iterations': ['iterations', int, raise_failure],
            'stop_condition': ['stop_condition', str, raise_failure],
            'stop_value': ['stop_value', int, raise_failure],
            'duration_str': ['duration_str', str, raise_failure],
            'evolution_method': ['evolution_method', str, raise_failure],
            'working_method': ['working_method', str, raise_failure],
            'adapt_ifin': ['adapt_ifin', read_intlist, raise_failure],
            'add_time': ['add_time', int, return_0],
            'add_time_list': ['add_time_list', read_intlist, raise_no_failure],
        }
        
        scenario_config = my_config_parser(scenario_actions, this_section)
        scenario_config['weights'] = my_config_parser(weight_actions, this_section)
        
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
