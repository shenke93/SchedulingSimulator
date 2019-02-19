from SchedulerV000 import run_opt, run_bf
from datetime import datetime
from visualize_lib import show_results, plot_gantt, show_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('seaborn-darkgrid')
import time
import random
import os, sys

from configfile import * # default configuration file
from configfile_test2 import * # customized configuration file

print(sys.path[0])
os.chdir(sys.path[0])

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

def main():
        print_ul('Scheduler v0.0.0')
        print('Execution Start!')

        downtimes = None
        if weight_failure:
                try:
                        downtimes = pd.read_csv(historical_down_periods_file, parse_dates=['StartDateUTC', 'EndDateUTC'])
                        downtimes = downtimes[downtimes.StartDateUTC.between(start_time, end_time)]
                except:
                        pass
        for value in test:
                if value == 'GA':
                        best_result, orig_result, best_sched, orig_sched, best_curve, worst_curve, gen = \
                                                        run_opt(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                                        product_related_characteristics_file, energy_price_file, job_info_file, 
                                                        scenario, iterations, crossover_rate, mutation_rate, pop_size, weight_conversion=weight_conversion, num_mutations=num_mutations,
                                                        weight_before=weight_before, adaptive=adapt_ifin, stop_condition=stop_condition, stop_value=stop_value, weight_energy=weight_energy,
                                                        weight_failure=weight_failure, duration_str=duration_str, evolution_method=evolution_method, validation=validation)
                        print('Execution finished.')
                        print('Number of generations was', gen)
                        # print('Start visualization')

                        print('Best:', best_result, '\t', * best_sched)
                        print('Original:', orig_result, '\t', * orig_sched)

                        fig = show_results(best_curve, worst_curve)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"evolution.png"), dpi=300)
                        if interactive:
                                fig.show()
                        begin = make_df(best_sched)
                        end = make_df(orig_sched)

                        # output files to csv's
                        begin.to_csv(output_init)
                        end.to_csv(output_final)

                        energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(product_related_characteristics_file)
                        


                        plt.figure(dpi=50, figsize=[20, 15])
                        if 'Type' in begin.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'
                        show_energy_plot(begin, energy_price, prod_char, 'Best schedule (GA) ({:} gen)'.format(gen), namecolor, downtimes=downtimes)
                        if export is True:
                                print('Export to', export_folder)
                                plt.savefig(os.path.join(export_folder, r"best_sched.png"), dpi=300)
                        if interactive:
                                plt.show()

                        plt.figure(dpi=50, figsize=[20, 15])
                        show_energy_plot(end, energy_price, prod_char, 'Original schedule', namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"orig_sched.png"), dpi=300)
                        if interactive:
                                plt.show()

                if value == 'BF':
                        timer0 = time.monotonic()
                        best_result, worst_result, best_sched, worst_sched = run_bf(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                                                                product_related_characteristics_file, energy_price_file, job_info_file,
                                                                                scenario, weight_failure=weight_failure, weight_conversion=weight_conversion, 
                                                                                weight_before=weight_before, weight_energy=weight_energy)
                        timer1 = time.monotonic()
                        elapsed_time = timer1-timer0
                        print('Elapsed time: {:.2f} s'.format(elapsed_time))

                        print('Execution finished.')
                        # print('Start visualization')

                        print('Best:',best_result, '\t', * best_sched)
                        print('Worst:', worst_result, '\t', * worst_sched)

                        begin = make_df(best_sched)
                        end = make_df(worst_sched)
                        energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
                        prod_char = pd.read_csv(product_related_characteristics_file)

                        if 'Type' in begin.columns:
                                namecolor='Type'
                        else:
                                namecolor='ArticleName'
                        plt.figure(dpi=50, figsize=[20, 15])
                        show_energy_plot(begin, energy_price, prod_char, 'Best schedule (BF)', namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"best_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()

                        plt.figure(dpi=50, figsize=[20, 15])
                        show_energy_plot(end, energy_price, prod_char, 'Worst schedule (BF)', namecolor, downtimes=downtimes)
                        if export is True:
                                plt.savefig(os.path.join(export_folder, r"worst_sched_BF.png"), dpi=300)
                        if interactive:
                                plt.show()

if __name__ == "__main__":
        main()