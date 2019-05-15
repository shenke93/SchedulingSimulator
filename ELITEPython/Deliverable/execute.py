from SchedulerV000 import run_opt, run_opt_urgent, run_bf
from datetime import datetime
from time import localtime, strftime
from visualize_lib import show_ga_results, plot_gantt, show_energy_plot, save_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
import math
#from configfile import adapt_ifin

plt.style.use('seaborn-darkgrid')
plt.rcParams.update({'figure.autolayout': True, 'figure.dpi': 144})

import time
import random
import os, sys
import logging

from helperfunctions import *

pathname = os.path.dirname(sys.argv[0])
configFile = os.path.join(pathname, 'config.ini')

def main():
        print_ul('Scheduler v0.0.0')
        
        if os.path.exists(configFile):
                config = read_config_file(configFile)
        else:
                raise ValueError("{} not found!".format(configFile))

        print('Execution Starts!')

        if not os.path.exists(config['output_config']['export_folder']):
                os.mkdir(config['output_config']['export_folder'])
        start_logging(os.path.join(config['output_config']['export_folder'], 'out.log'))
        logging.info('Starting logging')

        downtimes = None
        if config['scenario_config']['weights']['weight_failure'] and config['scenario_config']['working_method']=='historical':
                try:
                        downtimes = pd.read_csv(config['input_config']['hdp_file'], parse_dates=['StartDateUTC', 'EndDateUTC'], index_col=0)

                        downtimes = downtimes[downtimes.StartDateUTC.between(config['start_end']['start_time'], 
                                                                             config['start_end']['end_time'])]
                except:
                        pass

        # copy the config file to the export folder
        logging.info('Copying the config file to the export folder')
        
        if config['output_config']['export']:
                import shutil
                export_folder = config['output_config']['export_folder']
                shutil.copy2(configFile, os.path.join(export_folder, r"config_bu.ini"))

        for value in config['scenario_config']['test']:
                if value == 'GA':
                        best_result, orig_result, best_sched, \
                        orig_sched, best_curve, mean_curve, worst_curve, gen = \
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
                        failure_info=config['input_config']['failure_info'],
                        add_time=config['scenario_config']['add_time'],
                        urgent_job_info = config['input_config']['urgent_ji_file']
                        )

                        logging.info('Execution finished.')
                        logging.info('Number of generations was '+ str(gen))
                        # print('Start visualization')

                        result_dict = best_sched.get_time()
                        result_dict_origin = orig_sched.get_time()

                        if config['scenario_config']['working_method'] == 'expected' and config['input_config']['failure_info'] is not None:
                                orig_failure = orig_sched.get_failure_prob()
                                best_failure = best_sched.get_failure_prob()
                        else:
                                orig_failure = None
                                best_failure = None

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

                        print(result_dict)
                        
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

                        show_energy_plot(best, energy_price, prod_char, 'Best schedule (GA) ({:} gen) - Fitness {:.1f} €'.format(gen, fitn), 
                                                                                             namecolor, downtimes=downtimes, failure_rate=best_failure)
                        
                        if export:
                                print('Export to {}'.format(export_folder))
                                plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
                        if export_paper is True:
                                print('Export to {}'.format(export_folder))
                                plt.savefig(os.path.join(export_folder, r"best_sched.pdf"))
                                save_energy_plot(best, energy_price, prod_char, name='Best', folder=export_folder, title='Best schedule (GA) ({:} gen)'.format(gen), colors=namecolor, downtimes=downtimes)
                        if interactive:
                                plt.show()

                        fitn = orig_sched.get_fitness()

                        show_energy_plot(orig, energy_price, prod_char, 'Original schedule - Fitness {:.1f} €'.format(fitn), namecolor, downtimes=downtimes, failure_rate=orig_failure)
                        if export:
                                plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
                        if export_paper is True:
                                plt.savefig(os.path.join(export_folder, r"orig_sched.pdf"))
                                save_energy_plot(best, energy_price, prod_char, name='Original', folder=export_folder, title='Original schedule', colors=namecolor, downtimes=downtimes)

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

                        best_result_dict = best_sched.get_time()
                        worst_result_dict = worst_sched.get_time()

                        print('Best:',best_result, '\t', * best_result_dict)
                        print('Worst:', worst_result, '\t', * worst_result_dict)

                        best = make_df(best_result_dict)
                        worst = make_df(worst_result_dict)

                        energy_price = pd.read_csv(config['input_config']['ep_file'], index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(config['input_config']['prc_file'])

                        if 'Type' in best.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'
                        plt.figure(dpi=50, figsize=[20, 15])

                        fitn = best_sched.get_fitness()

                        poss = math.factorial(len(best_sched.job_dict))

                        show_energy_plot(best, energy_price, prod_char, 'Best schedule (BF) {:} possiblities - Fitness {:.1f}'.format(poss, fitn), namecolor, downtimes=downtimes)

                        export = config['output_config']['export']
                        interactive = config['output_config']['interactive']
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"best_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()

                        plt.figure(dpi=50, figsize=[20, 15])

                        fitn = worst_sched.get_fitness()

                        show_energy_plot(worst, energy_price, prod_char, 'Worst schedule (BF) - Fitness {:.1f}'.format(fitn), namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"worst_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()
                if value == 'PAR':
                        list_added = []
                        list_result = []
                        for time in config['scenario_config']['add_time_list']:
                                best_result, orig_result, best_sched, \
                                orig_sched, best_curve, mean_curve, worst_curve, gen = \
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
                                failure_info=config['input_config']['failure_info'],
                                add_time=time
                                )

                                logging.info('Execution finished.')
                                logging.info('Number of generations was {:}'.format(gen))
                                # print('Start visualization')

                                fitn = best_sched.get_fitness()

                                list_added.append(time)
                                list_result.append(fitn)

                                logging.info("When adding {:} hours of breaks, the result is {:.1f}".format(time, fitn))
                        
                        print(list_added)
                        print(list_result)
                
        logging.shutdown()

def executeUrgentJobs():
    # Reuse read_jobs to read urgent job information
    print_ul('Scheduler v0.0.0 for urgent jobs')
        
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
    urgent_job_info_file = os.path.join(original_folder, configParser.get('input-config', 'urgent_job_info_file'))
    failure_rate_file = os.path.join(original_folder, configParser.get('input-config', 'failure_rate_file'))
  
    # Read output-config
    export_folder = os.getcwd() + configParser.get('output-config', 'export_folder') + strftime("%Y%m%d_%H%M", localtime())
    os.makedirs(export_folder, exist_ok=True)
    output_init = os.path.join(export_folder, configParser.get('output-config', 'output_init_urgent')) # New output files for urgent jobs
    output_final = os.path.join(export_folder, configParser.get('output-config', 'output_final_urgent')) # New output files for urgent jobs
    interactive = configParser.getboolean('output-config', 'interactive')
    export = configParser.getboolean('output-config', 'export')  
    
    # Read scenario-config
    test = configParser.get('scenario-config', 'test').replace(' ', '').split(',')
    scenario = configParser.getint('scenario-config', 'scenario')
    validation = configParser.getboolean('scenario-config', 'validation')
    pre_selection = configParser.getboolean('scenario-config', 'pre_selection')
        
    weight_energy = configParser.getint('scenario-config', 'weight_energy')
    weight_constraint = configParser.getint('scenario-config', 'weight_constraint')
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
    
    fout = open(os.path.join(export_folder, 'out_urgent_jobs.log'), 'w+')
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
                print("Using GA")
                # TODO: Generate new urgent job file, using original job file and urgent job file
                
                best_result, orig_result, best_sched, orig_sched, best_curve, mean_curve, worst_curve, gen = \
                                                        run_opt_urgent(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                                        product_related_characteristics_file, energy_price_file, job_info_file, urgent_job_info_file,
                                                        scenario, iterations, crossover_rate, mutation_rate, pop_size, weight_conversion=weight_conversion, num_mutations=num_mutations,
                                                        weight_constraint=weight_constraint, adaptive=adapt_ifin, stop_condition=stop_condition, stop_value=stop_value, weight_energy=weight_energy,
                                                        weight_failure=weight_failure, duration_str=duration_str, evolution_method=evolution_method, validation=validation, 
                                                        pre_selection=pre_selection, working_method=working_method)
                print('Execution finished.')
                print('Number of generations was', gen)
                        # print('Start visualization')

                print('Best:', best_result, '\t', * best_sched)
                print('Original:', orig_result, '\t', * orig_sched)
                
                fig = show_ga_results(best_curve, worst_curve, mean_curve)
                if export is True:
                        plt.savefig(os.path.join(export_folder, r"evolution_emerge_jobs.png"), dpi=300)
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
#                         show_energy_plot(best, energy_price, prod_char, 'Best schedule (GA) ({:} gen)'.format(gen), namecolor, downtimes=downtimes)
                if export is True:
                        print('Export to', export_folder)
#                                 plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
                        save_energy_plot(best, energy_price, prod_char, name='Emerge_Best', folder=export_folder, title='Best schedule (GA) ({:} gen)'.format(gen), colors=namecolor, downtimes=downtimes)

                if interactive:
                        plt.show()

                plt.figure(dpi=50, figsize=[20, 15])
#                         show_energy_plot(orig, energy_price, prod_char, 'Original schedule', namecolor, downtimes=downtimes)
                if export is True:
#                                 plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
                        save_energy_plot(best, energy_price, prod_char, name='Emerge_Original', folder=export_folder, title='Original schedule', colors=namecolor, downtimes=downtimes)

                if interactive:
                        plt.show()        
                        
                        
                        
                        
                        
                        
            else:
                print("No matching method!")              
    pass
    
if __name__ == "__main__":
    while True:
        main()
        #print('Dealing with urgent jobs?')
        #n = input("Your answer:")
        #if n.strip() in ['Yes', 'yes', 'y', 'Y']: 
        #    print('Do next step')
        #    executeUrgentJobs()
        #break
        