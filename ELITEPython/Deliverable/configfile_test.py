# This configurationfile should be loaded for the idealised case with variable energy prices
from datetime import datetime

test = ['BF']

historical_down_periods_file='historicalDownPeriods.csv'
failure_rate_file='hourlyFailureRate.csv'
product_related_characteristics_file='productRelatedCharacteristics.csv'
energy_price_file='energyPrice.csv'
job_info_file='jobInfo.csv'
pop_size=6
iterations = 2000
start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)
weight_failure=1
weight_energy=1
weight_conversion=0
weight_before=0
stop_condition = 'end_value'
stop_value = 622.30