from SchedulerV000 import run_opt
from datetime import datetime
from visualize_lib import show_results, plot_gantt, show_energy_plot
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('seaborn-darkgrid')

def print_ul(strin):
    print(strin)
    print('-'*len(strin))


print_ul('Scheduler v0.0.0')
print('Execution Start!')

historical_down_periods_file='historicalDownPeriod.csv'
failure_rate_file='hourlyFailureRate_false.csv'
product_related_characteristics_file='productRelatedCharacteristics.csv'
energy_price_file='energyPrice.csv'
job_info_file='jobInfo.csv'
scenario=1
pop_size=8
iterations=10000
crossover_rate=0.6
mutation_rate=0.8
start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)



schedule, best_result, worst_result, begin, end = run_opt(start_time, end_time, historical_down_periods_file, failure_rate_file, 
                                        product_related_characteristics_file, energy_price_file, job_info_file, 
                                        scenario, iterations, crossover_rate, mutation_rate, pop_size)

print('Execution finished.')
print('Start visualization')

show_results(best_result, worst_result)

def make_df(dict):
        df = pd.DataFrame.from_dict(dict, orient='index', columns=['StartDateUTC', 'EndDateUTC', 'TotalTime', 'ArticleName'])
        df['ReasonId'] = 100
        return df

begin = make_df(begin)
end = make_df(end)
energy_price = pd.read_csv(energy_price_file, index_col=0, parse_dates=True)
prod_char = pd.read_csv(product_related_characteristics_file)

plt.figure(dpi=50, figsize=[20, 10])
show_energy_plot(begin, energy_price, prod_char)
plt.show()





#exec(compile(open('visualization.py').read(), 'visualization.py', 'exec'))