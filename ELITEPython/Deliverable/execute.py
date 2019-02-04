from SchedulerV000 import run_opt, run_bf
from datetime import datetime
from visualize_lib import show_results, plot_gantt, show_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('seaborn-darkgrid')

from configfile_analyse import *

def print_ul(strin):
    print(strin)
    print('-'*len(strin))

def make_df(dict):
        df = pd.DataFrame.from_dict(dict, orient='index', columns=['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName'])
        df['ReasonId'] = 100
        return df

print_ul('Scheduler v0.0.0')
print('Execution Start!')

if 'GA' in test:
        schedule, best_result, worst_result, begin, end = run_opt(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                                product_related_characteristics_file, energy_price_file, job_info_file, 
                                                scenario, iterations, crossover_rate, mutation_rate, pop_size)

        show_results(best_result, worst_result)
        begin = make_df(begin)
        end = make_df(end)
        energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
        prod_char = pd.read_csv(product_related_characteristics_file)
        

        plt.figure(dpi=50, figsize=[20, 10])
        show_energy_plot(begin, energy_price, prod_char)
        plt.show()

        plt.figure(dpi=50, figsize=[20, 10])
        show_energy_plot(end, energy_price, prod_char)
        plt.show()

if 'BF' in test:
        best_result, worst_result, best_sched, worst_sched = run_bf(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                product_related_characteristics_file, energy_price_file, job_info_file,
                scenario)

        print('Execution finished.')
        # print('Start visualization')

        print('Best:',best_result, '\t', * best_sched)
        print('Worst:', worst_result, '\t', * worst_sched)

        begin = make_df(best_sched)
        end = make_df(worst_sched)
        energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
        prod_char = pd.read_csv(product_related_characteristics_file)

        plt.figure(dpi=50, figsize=[20, 10])
        show_energy_plot(begin, energy_price, prod_char)
        plt.show()

        plt.figure(dpi=50, figsize=[20, 10])
        show_energy_plot(end, energy_price, prod_char)
        plt.show()