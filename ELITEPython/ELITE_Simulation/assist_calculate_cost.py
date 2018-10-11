''' This file is used to calculate cost of a given schedule.
'''

from datetime import datetime
from geneticAlgorithm013 import get_energy_cost, get_failure_cost, read_price, select_jobs, read_maintenance
from geneticAlgorithm013 import read_product_related_characteristics, read_job

start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)
    
price_dict_new = read_price("price.csv")
job_dict_new = select_jobs(start_time, end_time, read_job("jobInfoProd_ga_013.csv"))
failure_dict_new = read_maintenance("maintenanceInfluenceb4a4.csv", price_dict_new)
product_related_characteristics_dict = read_product_related_characteristics("productProd_ga_013.csv")

    
DNA_SIZE = len(job_dict_new)
waiting_jobs = [*job_dict_new]
    
if not waiting_jobs:
    raise ValueError("No waiting jobs!")
else:
    first_start_time = job_dict_new.get(waiting_jobs[0])[1] # Find the start time of original schedule  

# original_schedule = [511, 515, 516, 513, 517, 514, 510, 512]    # C2 optimal / minimizing failure cost
# original_schedule = [513, 517, 512, 515, 514, 516, 511, 510]
# original_schedule = [510, 511, 512, 513, 514, 515, 516, 517] # C1 original
# original_schedule = [510, 512, 517, 511, 514, 513, 515, 516] # C3 shortest job first
original_schedule = [510, 511, 513, 514, 517, 515, 512, 516]    # C4 minimizing energy cost

energy_cost = get_energy_cost(original_schedule, first_start_time, job_dict_new, price_dict_new, product_related_characteristics_dict)
failure_cost = get_failure_cost(original_schedule, first_start_time, job_dict_new, 
                                             failure_dict_new, product_related_characteristics_dict)
print("Energy_cost:", energy_cost)
print("Failure_cost:", failure_cost)
print("Cost:", energy_cost+failure_cost)