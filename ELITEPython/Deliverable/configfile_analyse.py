# This configurationfile should be loaded for the idealised case with variable energy prices
from datetime import datetime
import os

test = ['GA']

historical_down_periods_file=[]
failure_rate_file=[]
filepath='original_data'
product_related_characteristics_file=os.path.join(filepath, 'generated_productRelatedCharacteristics.csv')
energy_price_file=os.path.join(filepath, 'generated_hourly_energy_price.csv')
job_info_file=os.path.join(filepath, 'generated_jobInfoProd.csv')
output_init=os.path.join(filepath, 'original_jobs.csv')
output_final=os.path.join(filepath, 'final_jobs.csv')
pop_size = 12
crossover_rate = 0.9
mutation_rate = 0.4
num_mutations = 1
iterations = 5000
adapt_ifin = [5000, 15000, 20000, 30000, 35000]

# start_time = datetime(2016, 1, 19, 14, 20)
# end_time = datetime(2016, 1, 25, 14, 20)

start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)

weight_energy = 1
weight_before = 1
weight_conversion = 5
stop_condition = 'num_iterations'
stop_value = iterations
export_folder = r"D:\users\jdavid\ELITE project\Figures\Results080219_lastrun"