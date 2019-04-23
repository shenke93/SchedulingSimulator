from SchedulerV000 import run_opt, run_bf
from datetime import datetime
from time import localtime, strftime
from visualize_lib import show_ga_results, plot_gantt, show_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
#from configfile import adapt_ifin

plt.style.use('seaborn-darkgrid')
plt.rcParams.update({'figure.autolayout': True, 'figure.dpi': 144})

import time
import random
import os, sys
import configparser
import logging

pathname = os.path.dirname(sys.argv[0]) 

configFile = os.path.join(pathname, 'config_test.ini')

#print(sys.path)

# Deprecated configuration
# from configfile import * # default configuration file
# from configfile_test2 import * # customized configuration file

# print(sys.path[0])
# os.chdir(sys.path[0])

def print_ul(strin):
    print(strin)
    print('-'*len(strin))

def make_df(dict):
        all_cols = ['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName', 'Type', 'Down_duration', 'Changeover_duration']
        key = random.choice(list(dict))
        item = dict[key]
        all_cols = all_cols[0:len(item)]
        df = pd.DataFrame.from_dict(dict, orient='index')
        df.columns = all_cols
        df = df.reindex(list(dict.keys()))
        return df

class writer :
        def __init__(self, *writers) :
                self.writers = writers

        def write(self, text) :
                for w in self.writers :
                        w.write(text)
        
        def flush(self):
                pass

def read_failure_info(file):
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

        cleaning_file = root.find('files').find('cleaning_time').text
        cleaning_time = pd.read_csv(os.path.join(os.path.split(file)[0], cleaning_file), index_col = 0)        

        failure_info = (fail_dict, rep_dist, mean, maint_time, repair_time, conversion_times, cleaning_time)
        return failure_info

def read_config_file(path):
        config = configparser.ConfigParser()
        config.read(path)
        sections = config.sections()
        return_sections = {}
        if 'input-config' in sections:
                input_config = {}
                this_section = config['input-config']
                input_config['original'] = orig_folder =  this_section['original_folder']
                orig_folder = os.path.join(pathname, orig_folder)
                input_config['prc_file'] = os.path.join(orig_folder, this_section['product_related_characteristics_file'])
                input_config['ep_file'] = os.path.join(orig_folder, this_section['energy_price_file'])
                input_config['hdp_file'] = os.path.join(orig_folder, this_section['historical_down_periods_file'])
                input_config['ji_file'] = os.path.join(orig_folder, this_section['job_info_file'])
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
                output_config['export_folder'] = export_folder = os.path.abspath(this_section['export_folder'] + '_' + strftime("%Y%m%d_%H%M", localtime()))
                os.makedirs(export_folder, exist_ok=True)
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
                return_sections['scenario_config'] = scenario_config
        
        if ('start-end' in sections):
                start_end = {}
                start_end['start_time'] = datetime(config.getint('start-end', 'start_year'), config.getint('start-end', 'start_month'), 
                                config.getint('start-end', 'start_day'), config.getint('start-end', 'start_hour'), 
                                config.getint('start-end', 'start_minute'), config.getint('start-end', 'start_second')) # Date range of jobs to choose
                start_end['end_time'] = datetime(config.getint('start-end', 'end_year'), config.getint('start-end', 'end_month'), 
                                        config.getint('start-end', 'end_day'), config.getint('start-end', 'end_hour'), 
                                        config.getint('start-end', 'end_minute'), config.getint('start-end', 'end_second'))
                return_sections['start_end'] = start_end
        elif 'start' in sections:
                start_end = {}
                start_end['start_time'] = datetime(config.getint('start', 'start_year'), config.getint('start', 'start_month'), 
                                      config.getint('start', 'start_day'), config.getint('start', 'start_hour'), 
                                      config.getint('start', 'start_minute'), config.getint('start', 'start_second')) # Date range of jobs to choose
                start_end['end_time'] = None
                return_sections['start_end'] = start_end
        else:
                raise NameError('No section with start date found!')
        
        return return_sections

def start_logging(filename):
        f = open(filename, "a", encoding="utf-8")
        logger = logging.getLogger('simple')
        logger.setLevel(logging.DEBUG)
        # create file handler
        fh = logging.StreamHandler(f)
        fh.setLevel(logging.DEBUG)
        # create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # add handlers
        logger.addHandler(ch)
        logger.addHandler(fh)
        return logger

    
def main():
        print_ul('Scheduler v0.0.0')
        
        # Taking config file path from the user.
        #configParser = configparser.RawConfigParser()   

        pathname = os.path.dirname(sys.argv[0]) 
        
        if os.path.exists(configFile):
                config = read_config_file(configFile)
        else:
                raise ValueError("{} not found!".format(configFile))

        print('Execution Starts!')
        #logger = start_logging('Output_file')

        fout = open(os.path.join(config['output_config']['export_folder'], 'out.log'), 'w+')
        sys.stdout = writer(sys.stdout, fout)

        downtimes = None
        if config['scenario_config']['weights']['weight_failure'] and config['scenario_config']['working_method']=='historical':
                try:
                        downtimes = pd.read_csv(config['input_config']['hdp_file'], parse_dates=['StartDateUTC', 'EndDateUTC'], index_col=0)

                        downtimes = downtimes[downtimes.StartDateUTC.between(config['start_end']['start_time'], 
                                                                             config['start_end']['end_time'])]
                except:
                        pass

        print(config)

        # copy the config file to the export folder
        if config['output_config']['export']:
                import shutil
                export_folder = config['output_config']['export_folder']
                shutil.copy2(configFile, os.path.join(export_folder, r"config_bu.ini"))

        for value in config['scenario_config']['test']:
                if value == 'GA':
                        best_result, orig_result, best_sched, orig_sched, best_curve, mean_curve, worst_curve, gen = \
                                                        run_opt(config['start_end']['start_time'], config['start_end']['end_time'], 
                                                        config['input_config']['hdp_file'], config['input_config']['fr_file'], 
                                                        config['input_config']['prc_file'], config['input_config']['ep_file'], config['input_config']['ji_file'], 
                                                        config['scenario_config']['scenario'], config['scenario_config']['iterations'], 
                                                        config['scenario_config']['crossover_rate'], config['scenario_config']['mutation_rate'], 
                                                        config['scenario_config']['pop_size'],  
                                                        num_mutations=config['scenario_config']['num_mutations'],
                                                        adaptive=config['scenario_config']['adapt_ifin'], 
                                                        stop_condition=config['scenario_config']['stop_condition'], 
                                                        stop_value=config['scenario_config']['stop_value'], 
                                                        weights = config['scenario_config']['weights'],
                                                        duration_str=config['scenario_config']['duration_str'], 
                                                        evolution_method=config['scenario_config']['evolution_method'], 
                                                        validation=config['scenario_config']['validation'], 
                                                        pre_selection=config['scenario_config']['pre_selection'], 
                                                        working_method=config['scenario_config']['working_method'], 
                                                        failure_info=config['input_config']['failure_info']
                                                        )

                        
                        #logger = start_logging(os.path.join(config['output_config']['export_folder'], 'out.log'))

                        #logger = start_logging(os.path.join(config['output_config']['export_folder'], 'out.log'))

                        print('Execution finished.')
                        print('Number of generations was', gen)
                        # print('Start visualization')

                        result_dict = best_sched.get_time()
                        result_dict_origin = orig_sched.get_time()

                        if config['scenario_config']['working_method'] == 'expected' and config['input_config']['failure_info'] is not None:
                                orig_failure = orig_sched.get_failure_prob()
                                best_failure = best_sched.get_failure_prob()
                        else:
                                orig_failure = None
                                best_failure = None
                        

                        #import pdb; pdb.set_trace()

                        outputlist = ' '.join([str(l) for l in list(result_dict.keys())])
                        outputlist_orig = ' '.join([str(l) for l in list(result_dict_origin.keys())])

                        print('Best: {}\t {}'.format(best_result, outputlist))
                        print('Original: {}\t {}'.format(orig_result, outputlist_orig))

                        fig = show_ga_results(best_curve, mean_curve, worst_curve)
                        export = config['output_config']['export']
                        export_paper = config['output_config']['export_paper']
                        interactive = config['output_config']['interactive']
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"evolution.png"), dpi=300)
                        if export_paper is True:
                                plt.savefig(os.path.join(export_folder, r"evolution.pdf"))
                        if config['output_config']['interactive']:
                                fig.show()

                        
                        # make dataframes from dicts
                        best = make_df(result_dict)
                        orig = make_df(result_dict_origin)
                        

                        # output files to csv's
                        orig.to_csv(config['output_config']['output_init'])
                        best.to_csv(config['output_config']['output_final'])

                        energy_price = pd.read_csv(config['input_config']['ep_file'], index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(config['input_config']['prc_file'])
                        
                        
                        if 'Type' in best.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'

                        if export_paper is True:
                                print('Export to {}'.format(export_folder))
                                fig = plt.figure(figsize=(10, 6), dpi=50)
                                plot_gantt(best, namecolor, namecolor, downtimes=downtimes)
                                plt.title('Gantt plot')
                                plt.savefig(os.path.join(export_folder, r"gantt_plot.pdf"))
                                plt.close()

                        fitn = best_sched.get_fitness()

                        show_energy_plot(best, energy_price, prod_char, 'Best schedule (GA) ({:} gen) - Fitness {:.1f} €'.format(gen, fitn), namecolor, downtimes=downtimes, failure_rate=best_failure)
                        


                        if export:
                                print('Export to {}'.format(export_folder))
                                plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
                        if export_paper is True:
                                print('Export to {}'.format(export_folder))
                                plt.savefig(os.path.join(export_folder, r"best_sched.pdf"))
                        if interactive:
                                plt.show()

                        fitn = best_sched.get_fitness()

                        show_energy_plot(orig, energy_price, prod_char, 'Original schedule - Fitness {:.1f} €'.format(fitn), namecolor, downtimes=downtimes, failure_rate=orig_failure)
                        if export:
                                plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
                        if export_paper is True:
                                plt.savefig(os.path.join(export_folder, r"orig_sched.pdf"))
                        if interactive:
                                plt.show()

                if value == 'BF':
                        timer0 = time.monotonic()
                        best_result, worst_result, best_sched, worst_sched = run_bf(config['start_end']['start_time'], config['start_end']['end_time'], 
                                                                                config['input_config']['hdp_file'], config['input_config']['fr_file'], 
                                                                                config['input_config']['prc_file'], config['input_config']['ep_file'], 
                                                                                config['input_config']['ji_file'], 
                                                                                config['scenario_config']['scenario'],
                                                                                weights = config['scenario_config']['weights'], 
                                                                                duration_str=config['scenario_config']['duration_str'],
                                                                                working_method=config['scenario_config']['working_method'],
                                                                                failure_info=config['input_config']['failure_info'])
                        timer1 = time.monotonic()
                        elapsed_time = timer1-timer0
                        print()
                        print('Elapsed time: {:.2f} s'.format(elapsed_time))

                        print('Execution finished.')
                        # print('Start visualization')

                        print('Best:',best_result, '\t', * best_sched)
                        print('Worst:', worst_result, '\t', * worst_sched)

                        best = make_df(best_sched)
                        worst = make_df(worst_sched)

                        energy_price = pd.read_csv(config['input_config']['ep_file'], index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(config['input_config']['prc_file'])

                        if 'Type' in best.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'
                        plt.figure(dpi=50, figsize=[20, 15])

                        fitn = best_sched.get_fitness()

                        show_energy_plot(best, energy_price, prod_char, 'Best schedule (BF) - Fitness {.1f}'.format(fitn), namecolor, downtimes=downtimes)

                        export = config['output_config']['export']
                        interactive = config['output_config']['interactive']
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"best_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()

                        plt.figure(dpi=50, figsize=[20, 15])

                        fitn = worst_sched.get_fitness()

                        show_energy_plot(worst, energy_price, prod_char, 'Worst schedule (BF)- Fitness {.1f}'.format(fitn), namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"worst_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()
                
                logging.shutdown()

if __name__ == "__main__":
        main()