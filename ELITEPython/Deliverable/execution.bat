::execution.bat
@echo off
echo Scheduler v0.0.0
echo Executin start!

set file1=SchedulerV000.py
set file2=visualization.py

::Input parameters
set historical_down_periods_file=historicalDownPeriods.csv
set failure_rate_file=hourlyFailureRate.csv
set product_related_characteristics_file=productRelatedCharacteristics.csv
set energy_price_file=energyPrice.csv
set job_info_file=jobInfo.csv
set scenario=1
set pop_size=8
set generations=200
set crossover_rate=0.6
set mutation_rate=0.8

python %file1% %historical_down_periods_file% %failure_rate_file% %product_related_characteristics_file% %energy_price_file% %job_info_file% %scenario% %pop_size% %generations% %crossover_rate% %mutation_rate%

echo:
echo Execution finished.
echo Start visualization.
python %file2%

@echo on