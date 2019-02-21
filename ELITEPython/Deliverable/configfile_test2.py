# This configurationfile should be loaded for the idealised case with variable energy prices
from datetime import datetime
from time import localtime, strftime
import os

''' Input / Output Configuration
'''
historical_down_periods_file=[]
failure_rate_file=[]
filepath='original_data'
product_related_characteristics_file=os.path.join(filepath, 'generated_productRelatedCharacteristics.csv')
energy_price_file=os.path.join(filepath, 'generated_hourly_energy_price.csv')
historical_down_periods_file = os.path.join(filepath, 'historicalDownPeriods.csv')
failure_rate_file='hourlyFailureRate.csv'
#energy_price_file='energyPrice.csv'
job_info_file=os.path.join(filepath, 'generated_jobInfoProd.csv')
output_init=os.path.join(filepath, 'original_jobs.csv')
output_final=os.path.join(filepath, 'final_jobs.csv')

interactive = False
export = True
cwd = os.getcwd()
export_folder = cwd + '\Results' + strftime("%Y%m%d_%H%M", localtime())
# export_folder = r"D:\users\jdavid\ELITE project\Figures\Results"+strftime("%Y%m%d_%H%M", gmtime())
os.makedirs(export_folder, exist_ok=True) 


''' Scenario Configuration
'''
test = ['GA'] # Choices: GA, BF
scenario = 1  
duration_str = 'duration' # ['quantity', 'duration']
validation = False # ['True', 'False']



evolution_method = 'roulette' #['random', 'roulette']
pop_size = 12
crossover_rate = 0.9
mutation_rate = 0.4
num_mutations = 1
iterations = 20
adapt_ifin = [5000, 15000, 20000, 30000, 35000]

start_time = datetime(2016, 11, 3, 6, 0) # Date range of jobs to choose
end_time = datetime(2016, 12, 3, 0, 0) # Year, Month, Day, Hour, Minute, Second

weight_energy = 1
weight_before = 10
weight_failure = 0.001
weight_conversion = 5

stop_condition = 'num_iterations'
stop_value = iterations