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
iterations = 40000
adapt_ifin = [5000, 15000, 20000, 30000, 35000]
start_time = datetime(2016, 1, 19, 14, 20)
end_time = datetime(2016, 2, 19, 14, 20)
weight_energy = 1
weight_before = 0
weight_conversion = 1
stop_condition = 'end_value'
stop_value = 0