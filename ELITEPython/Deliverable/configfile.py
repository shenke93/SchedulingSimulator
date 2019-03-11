# This configurationfile should be loaded for the idealised case with variable energy prices
from datetime import datetime

test = ['GA'] # GA, BF (Genetic, Brute Force)

historical_down_periods_file='historicalDownPeriods.csv'
failure_rate_file='hourlyFailureRate.csv'
product_related_characteristics_file='productRelatedCharacteristics.csv'
energy_price_file='energyPrice.csv'
job_info_file='jobInfo.csv'

output_init='original_job_order.csv'
output_final='final_job_order.csv'

scenario=1
pop_size=8
iterations = 200
crossover_rate=0.7
mutation_rate=0.5
num_mutations=1
start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)
weight_failure=1
weight_energy=1
weight_conversion=1
weight_before=1
adapt_ifin = []
stop_condition = 'num_iterations'   # ['num_iterations', 'end_value', 'abs_time']
stop_value = iterations
duration_str = 'quantity' #['quantity', 'duration']
evolution_method = 'random' #['random', 'roulette']
working_method = 'expected' #['historical', 'expected']
validation = False

export = True
export_folder = r"D:\users\jdavid\ELITE project\Figures\Dump"
interactive = False