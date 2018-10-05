''' Features: 1. Add energy profile
              2. Add product price
              3. Add unit production price
'''
''' This script initializes the input file of the simulator. 
Some preliminary data processing is done here.
'''
import sys
import csv
import numpy as np


# try:
#     with open('jobInfoProd.csv', 'r', encoding='utf-8') as csvInput:
#         with open('jobInfoProd_ga_013.csv', 'w', encoding='utf-8') as csvOutput:
#             writer = csv.writer(csvOutput, lineterminator='\n')
#             reader = csv.reader(csvInput)
#          
#             all = []
#             row = next(reader)
#             row.append('Power')
#             all.append(row)
#              
#             for row in reader:
#                 row.append(round(np.random.uniform(3, 5), 2))
#                 all.append(row)
#             writer.writerows(all)
# except:
#     print("Unexpected error when pre-processing job information:", sys.exc_info()[0]) 
#     exit()

try:
    with open('productProd.csv', 'r', encoding='utf-8') as csvInput:
        with open('productProd_ga_013.csv', 'w', encoding='utf-8') as csvOutput:
            writer = csv.writer(csvOutput, lineterminator='\n')
            reader = csv.reader(csvInput)
         
            all = []
            row = next(reader)
            row.append('UnitPrice')
            row.append('Power')
            all.append(row)
             
            for row in reader:
                row.append(round(np.random.uniform(1, 2), 2))   # unit price
                row.append(round(np.random.uniform(3, 5), 2))   # power profile
                all.append(row)
            writer.writerows(all)
except:
    print("Unexpected error when pre-processing product unit price:", sys.exc_info()[0]) 
    exit()
    
''' List of problem: 2016.3.27 2:00:00 no price
                     2017.3.26 2:00:00 no price
'''

    