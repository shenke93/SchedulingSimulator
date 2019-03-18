from SchedulerV000 import run_opt, run_bf
from datetime import datetime
from time import localtime, strftime
from visualize_lib import show_results, plot_gantt, show_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
from configfile import adapt_ifin
plt.style.use('seaborn-darkgrid')
import time
import random
import os, sys
import configparser

#print(sys.path)

# Deprecated configurtaion
# from configfile import * # default configuration file
# from configfile_test2 import * # customized configuration file

# print(sys.path[0])
# os.chdir(sys.path[0])

def print_ul(strin):
    print(strin)
    print('-'*len(strin))

def make_df(dict):
        all_cols = ['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName', 'Type']
        key = random.choice(list(dict))
        item = dict[key]
        all_cols = all_cols[0:len(item)]
        df = pd.DataFrame.from_dict(dict, orient='index')
        df.columns = all_cols
        #df['ReasonId'] = 100
        return df

class writer :
        def __init__(self, *writers) :
                self.writers = writers

        def write(self, text) :
                for w in self.writers :
                        w.write(text)
        
        def flush(self):
                pass
    
def main():
        print_ul('Scheduler v0.0.0')
        
        # Taking config file path from the user.
        configParser = configparser.RawConfigParser()   
        configFilePath = 'config.ini'
        configParser.read(configFilePath)
        
        # Read input-config
        original_folder = configParser.get('input-config', 'original_folder')
        product_related_characteristics_file = os.path.join(original_folder, configParser.get('input-config', 'product_related_characteristics_file'))
        energy_price_file = os.path.join(original_folder, configParser.get('input-config', 'energy_price_file'))
        historical_down_periods_file = os.path.join(original_folder, configParser.get('input-config', 'historical_down_periods_file'))
        job_info_file = os.path.join(original_folder, configParser.get('input-config', 'job_info_file'))
        failure_rate_file = os.path.join(original_folder, configParser.get('input-config', 'failure_rate_file'))
        
        # Read output-config
        export_folder = os.getcwd() + configParser.get('output-config', 'export_folder') + strftime("%Y%m%d_%H%M", localtime())
        os.makedirs(export_folder, exist_ok=True)
        output_init = os.path.join(export_folder, configParser.get('output-config', 'output_init'))
        output_final = os.path.join(export_folder, configParser.get('output-config', 'output_final'))
        interactive = configParser.getboolean('output-config', 'interactive')
        export = configParser.getboolean('output-config', 'export')
        
        # Read scenario-config
        test = configParser.get('scenario-config', 'test').replace(' ', '').split(',')
        scenario = configParser.getint('scenario-config', 'scenario')
        validation = configParser.getboolean('scenario-config', 'validation')
        pre_selection = configParser.getboolean('scenario-config', 'pre_selection')
        
        weight_energy = configParser.getint('scenario-config', 'weight_energy')
        weight_before = configParser.getint('scenario-config', 'weight_before')
        weight_failure = configParser.getint('scenario-config', 'weight_failure')
        weight_conversion = configParser.getint('scenario-config', 'weight_conversion')
        
        pop_size = configParser.getint('scenario-config', 'pop_size')
        crossover_rate = configParser.getfloat('scenario-config', 'crossover_rate')
        mutation_rate = configParser.getfloat('scenario-config', 'mutation_rate')
        num_mutations = configParser.getint('scenario-config', 'num_mutations')
        iterations = configParser.getint('scenario-config', 'iterations')
        
        stop_condition = configParser.get('scenario-config', 'stop_condition')
        stop_value = configParser.getint('scenario-config', 'stop_value')
        duration_str = configParser.get('scenario-config', 'duration_str')
        evolution_method = configParser.get('scenario-config', 'evolution_method')
        working_method = configParser.get('scenario-config', 'working_method')
        
        adapt_ifin_low = configParser.getint('scenario-config', 'adapt_ifin_low')
        adapt_ifin_high = configParser.getint('scenario-config', 'adapt_ifin_high')
        adapt_ifin_step = configParser.getint('scenario-config', 'adapt_ifin_step')
        adapt_ifin = [i for i in range(adapt_ifin_low, adapt_ifin_high+adapt_ifin_step, adapt_ifin_step)]
        
        if configParser.has_section('start-end'):
                start_time = datetime(configParser.getint('start-end', 'start_year'), configParser.getint('start-end', 'start_month'), 
                                configParser.getint('start-end', 'start_day'), configParser.getint('start-end', 'start_hour'), 
                                configParser.getint('start-end', 'start_minute'), configParser.getint('start-end', 'start_second')) # Date range of jobs to choose
                end_time = datetime(configParser.getint('start-end', 'end_year'), configParser.getint('start-end', 'end_month'), 
                                configParser.getint('start-end', 'end_day'), configParser.getint('start-end', 'end_hour'), 
                                configParser.getint('start-end', 'end_minute'), configParser.getint('start-end', 'end_second'))
        elif configParser.has_section('start'):
                start_time = datetime(configParser.getint('start', 'start_year'), configParser.getint('start', 'start_month'), 
                                configParser.getint('start', 'start_day'), configParser.getint('start', 'start_hour'), 
                                configParser.getint('start', 'start_minute'), configParser.getint('start', 'start_second')) # Date range of jobs to choose
                end_time = None
        else:
                raise NameError('No section with start date found!')

        print('Execution Start!')

        fout = open(os.path.join(export_folder, 'out.log'), 'w+')
        sys.stdout = writer(sys.stdout, fout)

        downtimes = None
        if weight_failure and working_method=='historical':
                try:
                        downtimes = pd.read_csv(historical_down_periods_file, parse_dates=['StartDateUTC', 'EndDateUTC'])
                        downtimes = downtimes[downtimes.StartDateUTC.between(start_time, end_time)]
                except:
                        pass
        for value in test:
                if value == 'GA':
                        best_result, orig_result, best_sched, orig_sched, best_curve, mean_curve, worst_curve, gen = \
                                                        run_opt(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                                        product_related_characteristics_file, energy_price_file, job_info_file, 
                                                        scenario, iterations, crossover_rate, mutation_rate, pop_size, weight_conversion=weight_conversion, num_mutations=num_mutations,
                                                        weight_before=weight_before, adaptive=adapt_ifin, stop_condition=stop_condition, stop_value=stop_value, weight_energy=weight_energy,
                                                        weight_failure=weight_failure, duration_str=duration_str, evolution_method=evolution_method, validation=validation, 
                                                        pre_selection=pre_selection, working_method=working_method)
                        print('Execution finished.')
                        print('Number of generations was', gen)
                        # print('Start visualization')

                        print('Best:', best_result, '\t', * best_sched)
                        print('Original:', orig_result, '\t', * orig_sched)

                        fig = show_results(best_curve, worst_curve, mean_curve)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"evolution.png"), dpi=300)
                        if interactive:
                                fig.show()
                        best = make_df(best_sched)
                        orig = make_df(orig_sched)

                        # output files to csv's
                        orig.to_csv(output_init)
                        best.to_csv(output_final)

                        energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(product_related_characteristics_file)
                        
                        plt.figure(dpi=50, figsize=[20, 15])
                        if 'Type' in best.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'
                        show_energy_plot(best, energy_price, prod_char, 'Best schedule (GA) ({:} gen)'.format(gen), namecolor, downtimes=downtimes)
                        if export is True:
                                print('Export to', export_folder)
                                plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
                        if interactive:
                                plt.show()

                        plt.figure(dpi=50, figsize=[20, 15])
                        show_energy_plot(orig, energy_price, prod_char, 'Original schedule', namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
                        if interactive:
                                plt.show()

                if value == 'BF':
                        timer0 = time.monotonic()
                        best_result, worst_result, best_sched, worst_sched = run_bf(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                                                                product_related_characteristics_file, energy_price_file, job_info_file,
                                                                                scenario, weight_failure=weight_failure, weight_conversion=weight_conversion, 
                                                                                weight_before=weight_before, weight_energy=weight_energy, duration_str=duration_str,
                                                                                working_method=working_method)
                        timer1 = time.monotonic()
                        elapsed_time = timer1-timer0
                        print('Elapsed time: {:.2f} s'.format(elapsed_time))

                        print('Execution finished.')
                        # print('Start visualization')

                        print('Best:',best_result, '\t', * best_sched)
                        print('Worst:', worst_result, '\t', * worst_sched)

                        best = make_df(best_sched)
                        worst = make_df(worst_sched)

                        energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(product_related_characteristics_file)

                        if 'Type' in best.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'
                        plt.figure(dpi=50, figsize=[20, 15])
                        show_energy_plot(best, energy_price, prod_char, 'Best schedule (BF)', namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"best_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()

                        plt.figure(dpi=50, figsize=[20, 15])
                        show_energy_plot(worst, energy_price, prod_char, 'Worst schedule (BF)', namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"worst_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()
                
                if export:
                        import shutil
                        shutil.copy2('config.ini', os.path.join(export_folder, r"config_bu.ini"))

if __name__ == "__main__":
        main()