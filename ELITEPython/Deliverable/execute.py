from SchedulerV000 import run_opt, run_bf
from datetime import datetime
from time import localtime, strftime
from visualize_lib import show_ga_results, plot_gantt, show_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
import math
#from CONFIGFILE import adapt_ifin

plt.style.use('seaborn-darkgrid')
plt.rcParams.update({'figure.autolayout': True, 'figure.dpi': 144})

import time
import random
import os, sys
import logging

from helperfunctions import *

#pathname = os.path.dirname(sys.argv[0])
os.chdir(os.path.dirname(sys.argv[0]))

CONFIGFILE = os.path.join(os.path.abspath(os.curdir), 'config.ini')

def main(config):
    '''
    Main loop of the executable file
    There are two options:
    - GA (Genetic Algorithm) - run the file as a genetic algorithm
    - PAR (Pareto) - run the pareto front file, this will use multiple configurations of 
      the program, by adding different amounts of breaks in the production and exit 
      by showing an overview of the Pareto front for these configurations
    '''
    logging.info('Scheduler v0.0.5')

    # copy the config file to the export folder
    logging.info('Copying the config file to the export folder')

    export = config['output_config']['export']
    export_paper = config['output_config']['export_paper']
    interactive = config['output_config']['interactive']
    # export_folder = config['output_config']['export_folder']

    if export:
        import shutil
        shutil.copy2(CONFIGFILE, os.path.join(export_folder, r"config_bu.ini"))
        
    schedule_list, settings = config_to_sched_objects(config)
    test = config['scenario_config']['test']
    
    if test == 'GA':
        schedule = schedule_list[0]
        best_result, orig_result, best_sched, \
        orig_sched, lists_result, list_result_nc = run_opt(schedule, settings)

        logging.info('Execution finished.')
        
        # Show iteration results
        show_ga_results(lists_result)
        if export:
            out_df = lists_result
            out_df.to_csv(os.path.join(export_folder, 'iterations_results.csv'))
            plt.savefig(os.path.join(export_folder, r"evolution.png"), dpi=300)
        if export_paper:
            plt.savefig(os.path.join(export_folder, r"evolution.pdf"))
        if interactive:
            plt.show()
            
        show_ga_results(list_result_nc)
        if export:
            out_df = list_result_nc
            out_df.to_csv(os.path.join(export_folder, 'iterations_results_noconstraintcost.csv'))
            plt.savefig(os.path.join(export_folder, r"evolution.png"), dpi=300)
        if export_paper:
            plt.savefig(os.path.join(export_folder, r"evolution.pdf"))
        if interactive:
            plt.show()            
            
        # Show in Gantt plot 
        # -----------------
        result_dict = best_sched.get_time()
        result_dict_origin = orig_sched.get_time()

        # make dataframes from dicts
        best = make_df(result_dict)
        orig = make_df(result_dict_origin)
        
        # output files to csv's
        orig.to_csv(os.path.join(export_folder, config['output_config']['output_init']))
        best.to_csv(os.path.join(export_folder, config['output_config']['output_final']))

        # get the failure probabilities
        downtimes = None
        if config['scenario_config']['working_method'] == 'expected' \
            and config['input_config']['failure_info'] is not None:
            orig_failure = orig_sched.get_failure_prob()
            best_failure = best_sched.get_failure_prob()
        else:
            # Or the actual failure times
            orig_failure = None
            best_failure = None
            try:
                downtimes = schedule.downdur_dict
                downtimes = pd.DataFrame(downtimes).T
                downtimes.columns = ['StartDateUTC', 'EndDateUTC', 'Time']
                # downtimes = pd.read_csv(config['input_config']['hdp_file'], parse_dates=['Start', 'End'], index_col=0)

                # downtimes = downtimes[downtimes['Start'].between(config['start_end']['start_time'], 
                #                                                 config['start_end']['end_time'])]
                # downtimes = downtimes[['Start', 'End']]
                # downtimes.columns = ['StartDateUTC', 'EndDateUTC']
            except:
                raise

        if 'Type' in best.columns:
            namecolor='Type'
        else:
            namecolor='ArticleName'
           
        # Make the columns be the correct format for plotting
        best = best[['Start', 'End', 'Totaltime', 'Product', 'Type', 'Power']]

        if export_paper is True:
            print('Export to {}'.format(export_folder))
            fig = plt.figure(figsize=(15, 7), dpi=2400)
            plot_gantt(best, 'Type', 'Product', startdate='Start', enddate='End', downtimes=downtimes)
            plt.title('Gantt plot')
            plt.savefig(os.path.join(export_folder, r"gantt_plot.pdf"))
            plt.close()

        energy_price = pd.read_csv(config['input_config']['ep_file'], index_col=0, parse_dates=True)
        #prod_char = pd.read_csv(config['input_config']['prc_file'])


        show_energy_plot(best, energy_price, 
                         'Best schedule - Fitness {:.1f} €'.format(best_sched.get_fitness()), 
                         colors='Type', productions='Product', downtimes=downtimes, failure_rate=best_failure,
                         startdate='Start', enddate='End')
        if export:
            print('Export to {}'.format(export_folder))
            plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
        if export_paper is True:
            print('Export to {}'.format(export_folder))
            plt.savefig(os.path.join(export_folder, r"best_sched.pdf"))
        if interactive:
            plt.show()

        orig = orig[['Start', 'End', 'Totaltime', 'Product', 'Type', 'Power']]

        show_energy_plot(orig, energy_price,
                         'Original schedule - Fitness {:.1f} €'.format(orig_sched.get_fitness()),
                         colors='Type', productions='Product', downtimes=downtimes, failure_rate=orig_failure,
                         startdate='Start', enddate='End')
        if export:
            plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
        if export_paper is True:
            plt.savefig(os.path.join(export_folder, r"orig_sched.pdf"))
        if interactive:
            plt.show()
        
        plt.clf()

    if test == 'PAR':
        logging.info('Generating pareto solutions')
        list_added = []
        list_result = []

        i = 0
        for schedule in schedule_list:
            best_result, orig_result, best_sched, \
            orig_sched, lists_result, list_result_nc = run_opt(schedule, settings)

            logging.info('Execution finished.')
            #logging.info('Number of generations was {:}'.format(gen))
            
            time = config['scenario_config']['add_time_list'][i]
            i += 1

            fitn = best_sched.get_fitness(split_types=False)
            logging.info("When adding {:} hours of breaks, the result is {:.1f}".format(time, fitn))

            list_added.append(time)
            list_result.append(fitn)

        logging.info('Final result')
        logging.info(list_added)
        logging.info(list_result)

        df = pd.DataFrame({'added_time': list_added, 'result':list_result})
        df.to_csv(os.path.join(export_folder, 'results.csv'))

        plt.plot(list_added, list_result, 'ro')
        plt.xlim(0, max(list_added)+1)
        plt.ylim(min(list_result) * 0.95, max(list_result) * 1.05)
        plt.xlabel('Added breaks (hours)')
        plt.ylabel('Total cost (Euros)')
        plt.savefig(os.path.join(export_folder, 'output.pdf'))
        plt.savefig(os.path.join(export_folder, 'output.png'), dpi=300)
        plt.show()
        
    logging.shutdown()
    
if __name__ == "__main__":
    
    curdir = os.path.dirname(sys.argv[0])
    os.chdir(curdir)
    
    # Read the config file
    if os.path.exists(CONFIGFILE):
        config = read_config_file(CONFIGFILE)
    else:
        raise ValueError("'{}' not found!".format(CONFIGFILE))

    # Make the export folder and start logging in the logging file
    export_folder = config['output_config']['export_folder']

    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
    start_logging(os.path.join(export_folder, 'out.log'))
    logging.info('Starting logging')

    main(config)