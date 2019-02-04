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
scenario=1
pop_size=18
iterations = 5000
crossover_rate=0.7
mutation_rate=0.5
start_time = datetime(2016, 1, 25, 18, 20)
end_time = datetime(2016, 1, 28, 10, 0)