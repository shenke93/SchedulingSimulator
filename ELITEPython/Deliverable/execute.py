from SchedulerV000 import run_opt, run_bf
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

#pathname = os.path.dirname(sys.argv[0])
configFile = 'config.ini'

def main(config):
    logging.info('Scheduler v0.0.5')

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
            config['input_config']['prc_file'], config['input_config']['prec_file'],
            config['input_config']['ep_file'], config['input_config']['ji_file'], 
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
            urgent_job_info=config['input_config']['urgent_ji_file'],
            breakdown_record_file=config['input_config']['bd_rec_file']
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
            
            # make dataframes from dicts
            best = make_df(result_dict)
            orig = make_df(result_dict_origin)
            

            # output files to csv's
            orig.to_csv(os.path.join(export_folder, config['output_config']['output_init']))
            best.to_csv(os.path.join(export_folder, config['output_config']['output_final']))

            energy_price = pd.read_csv(config['input_config']['ep_file'], index_col=0, parse_dates=True)
            prod_char = pd.read_csv(config['input_config']['prc_file'])
            
            if 'Type' in best.columns:
                namecolor='Type'
            else:
                namecolor='ArticleName'

            downtimes = None
            if config['scenario_config']['weights']['weight_failure'] and config['scenario_config']['working_method']=='historical':
                try:
                    downtimes = pd.read_csv(config['input_config']['hdp_file'], parse_dates=['StartDateUTC', 'EndDateUTC'], index_col=0)

                    downtimes = downtimes[downtimes.StartDateUTC.between(config['start_end']['start_time'], 
                                                                    config['start_end']['end_time'])]
                except:
                        pass

            if export_paper is True:
                print('Export to {}'.format(export_folder))
                fig = plt.figure(figsize=(10, 6), dpi=50)
                plot_gantt(best, namecolor, namecolor, startdate='Start', enddate='End', downtimes=downtimes)
                plt.title('Gantt plot')
                plt.savefig(os.path.join(export_folder, r"gantt_plot.pdf"))
                plt.close()

            fitn = best_sched.get_fitness()

            # Make the columns be the correct format for plotting
            best = best[['Start', 'End', 'Totaltime', 'Product', 'Type']]
            best.columns = ['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName', 'Type']
            show_energy_plot(best, energy_price, prod_char, 'Best schedule (GA) ({:} gen) - Fitness {:.1f} €'.format(gen, fitn), 
                                                                                    namecolor, downtimes=downtimes, failure_rate=best_failure)
            
            if export:
                print('Export to {}'.format(export_folder))
                plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
            if export_paper is True:
                print('Export to {}'.format(export_folder))
                plt.savefig(os.path.join(export_folder, r"best_sched.pdf"))
                #save_energy_plot(best, energy_price, prod_char, name='Best', folder=export_folder, title='Best schedule (GA) ({:} gen)'.format(gen), colors=namecolor, downtimes=downtimes)
            if interactive:
                plt.show()

            fitn = orig_sched.get_fitness()

            orig = orig[['Start', 'End', 'Totaltime', 'Product', 'Type']]
            orig.columns = ['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName', 'Type']
            show_energy_plot(orig, energy_price, prod_char, 'Original schedule - Fitness {:.1f} €'.format(fitn), namecolor, downtimes=downtimes, failure_rate=orig_failure)
            if export:
                plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
            if export_paper is True:
                plt.savefig(os.path.join(export_folder, r"orig_sched.pdf"))
                #save_energy_plot(best, energy_price, prod_char, name='Original', folder=export_folder, title='Original schedule', colors=namecolor, downtimes=downtimes)
            if interactive:
                plt.show()
            
            plt.clf()
                
        # if value == 'BF': #NOT REALLY supported any more
        #         timer0 = time.monotonic()
        #         best_result, worst_result, best_sched, worst_sched = run_bf(config['start_end']['start_time'], config['start_end']['end_time'], 
        #                                                                 config['input_config']['hdp_file'], config['input_config']['fr_file'], 
        #                                                                 config['input_config']['prc_file'], config['input_config']['ep_file'], 
        #                                                                 config['input_config']['ji_file'], 
        #                                                                 config['scenario_config']['scenario'],
        #                                                                 weights = config['scenario_config']['weights'], 
        #                                                                 duration_str=config['scenario_config']['duration_str'],
        #                                                                 working_method=config['scenario_config']['working_method'],
        #                                                                 failure_info=config['input_config']['failure_info'])
        #         timer1 = time.monotonic()
        #         elapsed_time = timer1-timer0
        #         print()
        #         print('Elapsed time: {:.2f} s'.format(elapsed_time))

        #         print('Execution finished.')
        #         # print('Start visualization')

        #         best_result_dict = best_sched.get_time()
        #         worst_result_dict = worst_sched.get_time()

        #         print('Best:',best_result, '\t', * best_result_dict)
        #         print('Worst:', worst_result, '\t', * worst_result_dict)

        #         best = make_df(best_result_dict)
        #         worst = make_df(worst_result_dict)

        #         energy_price = pd.read_csv(config['input_config']['ep_file'], index_col=0, parse_dates=True)
        #         prod_char = pd.read_csv(config['input_config']['prc_file'])

        #         if 'Type' in best.columns:
        #                 namecolor='Type'
        #         else:
        #                 namecolor='ArticleName'
        #         plt.figure(dpi=50, figsize=[20, 15])

        #         fitn = best_sched.get_fitness()

        #         poss = math.factorial(len(best_sched.job_dict))

        #         show_energy_plot(best, energy_price, prod_char, 'Best schedule (BF) {:} possiblities - Fitness {:.1f}'.format(poss, fitn), namecolor, downtimes=downtimes)

        #         export = config['output_config']['export']
        #         interactive = config['output_config']['interactive']
        #         if export is True:
        #                 plt.savefig(os.path.join(export_folder, r"best_sched_BF.png"), dpi=300)
        #         if interactive:
        #                 plt.show()

        #         plt.figure(dpi=50, figsize=[20, 15])

        #         fitn = worst_sched.get_fitness()

        #         show_energy_plot(worst, energy_price, prod_char, 'Worst schedule (BF) - Fitness {:.1f}'.format(fitn), namecolor, downtimes=downtimes)
        #         if export is True:
        #                 plt.savefig(os.path.join(export_folder, r"worst_sched_BF.png"), dpi=300)
        #         if interactive:
        #                 plt.show()
        if value == 'PAR':
            logging.info('Generating pareto solutions')
            list_added = []
            list_result = []
            for time in config['scenario_config']['add_time_list']:
                best_result, orig_result, best_sched, \
                orig_sched, best_curve, mean_curve, worst_curve, gen = \
                run_opt(config['start_end']['start_time'], config['start_end']['end_time'], 
                config['input_config']['hdp_file'], config['input_config']['fr_file'], 
                config['input_config']['prc_file'], config['input_config']['prec_file'],
                config['input_config']['ep_file'], config['input_config']['ji_file'], 
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
                urgent_job_info=config['input_config']['urgent_ji_file'],
                breakdown_record_file=config['input_config']['bd_rec_file']
                )
                logging.info('Execution finished.')
                logging.info('Number of generations was {:}'.format(gen))
                # print('Start visualization')

                fitn = best_sched.get_fitness(split_types=True)

                list_added.append(time)
                list_result.append(fitn)

                logging.info("When adding {:} hours of breaks, the result is {:.1f}".format(time, fitn))
            
            logging.info('Final result')
            logging.info(list_added)
            logging.info(list_result)

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
    if os.path.exists(configFile):
            config = read_config_file(configFile)
    else:
            raise ValueError("'{}' not found!".format(configFile))

    # Make the export folder and start logging in the logging file
    export_folder = config['output_config']['export_folder']

    if not os.path.exists(export_folder):
            os.makedirs(export_folder)
    start_logging(os.path.join(export_folder, 'out.log'))
    logging.info('Starting logging')
    
    main(config)

        