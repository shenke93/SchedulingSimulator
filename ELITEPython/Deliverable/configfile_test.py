# This configurationfile should be loaded for the idealised case with variable energy prices
from datetime import datetime

test = ['GA']

historical_down_periods_file='historicalDownPeriod_false.csv'
failure_rate_file='hourlyFailureRate_false.csv'
product_related_characteristics_file='productRelatedCharacteristics.csv'
energy_price_file='energyPrice.csv'
job_info_file='jobInfo.csv'
scenario=1
pop_size=6
iterations = 2000
crossover_rate=0.7
mutation_rate=0.3
start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)