from SchedulerV000 import run_opt
from datetime import datetime

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
iterations=200
crossover_rate=0.6
mutation_rate=0.8
start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)

run_opt(start_time, end_time, historical_down_periods_file, failure_rate_file, 
        product_related_characteristics_file, energy_price_file, job_info_file, 
        scenario, iterations, crossover_rate, mutation_rate, pop_size)

print('Excution finished.')
print('Start visualization')

exec(compile(open('visualization.py').read(), 'visualization.py', 'exec'))